#!/usr/bin/env python3
"""Local tests for ten_skill_driver.py. No network, no account, no cost.

    python3 test_ten_skill_driver.py

The driver talks to an in-process stand-in for the service through the client's injectable
transport, so the real client code, the real manifest, the real schedule and the real data
package are exercised. The stand-in follows the documented contract: idempotent submissions,
an immutable initial checkpoint, one logical training job that may pause and be continued
with `resume`, typed evaluations with coverage, and a `recovery` object on a failed job.
"""
import contextlib
import copy
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import learning_client as T          # noqa: E402
import ten_skill_driver as D         # noqa: E402

DATA = os.path.join(HERE, "data")
M = D.load_json(D.MANIFEST)
SCH = D.load_json(D.SCHEDULE)
ORDER = D.teach_order(M)
PLAN = {d["domain"]: d["planned_budget"]["planned_updates"] for d in M["domains"]}
QUIET = lambda *a: None


class Crash(Exception):
    """The process dies here (power cut, killed terminal)."""


class Service:
    """An in-process stand-in for the documented service."""

    def __init__(self, train_script=None, eval_script=None, omit_initial=False, short=None, plan_delta=None):
        self.learners, self.jobs, self.by_key, self.datasets = {}, {}, {}, {}
        self.log = []                                   # every request: (method, path)
        self.train_script = train_script or {}          # nth training job -> ["pause", ..., "complete"|"terminal"|"never"]
        self.eval_script = eval_script or {}            # nth evaluation   -> ["fail", "complete"|"partial"|"empty"|"terminal"]
        self.omit_initial, self.short, self.plan_delta = omit_initial, short or {}, plan_delta or {}
        self.eval_result_edit = None                    # callable(nth evaluation, result dict) -> edits the returned result
        self.crash_on = None                            # (method, regex, nth match) -> raise Crash BEFORE serving
        self._hits = self.n_train = self.n_eval = 0

    # ---- transport
    def send(self, method, path, headers, body, content_type):
        self.log.append((method, path))
        if self.crash_on and method == self.crash_on[0] and re.search(self.crash_on[1], path):
            self._hits += 1
            if self._hits == self.crash_on[2]:
                self.crash_on = None
                raise Crash(path)
        p = path[len(T.API):]
        for pat, fn in self.ROUTES:
            mt = re.fullmatch(pat, p.split("?")[0])
            if mt and fn[0] == method:
                return fn[1](self, body, *mt.groups())
        return 404, {"error": {"code": "not_found"}}

    def posts(self, pat):
        return [x for x in self.log if x[0] == "POST" and re.search(pat, x[1])]

    # ---- handlers
    def _learner(self, lid):
        L = dict(self.learners[lid])
        if self.omit_initial:
            L.pop("initial_checkpoint_id")
        return L

    def create_learner(self, body):
        lid = "lrn_%d" % (len(self.learners) + 1)
        self.learners[lid] = {"learner_id": lid, "initial_checkpoint_id": "ck_initial_" + lid,
                              "latest_checkpoint_id": "ck_initial_" + lid}
        return 201, self._learner(lid)

    def get_learner(self, body, lid):
        return 200, self._learner(lid)

    def checkpoints(self, body, lid):
        items = [] if self.omit_initial else [{"checkpoint_id": self.learners[lid]["initial_checkpoint_id"], "kind": "initial"}]
        return 200, {"items": items + [{"checkpoint_id": j["result"]["checkpoint_id"], "kind": "trained"}
                                       for j in self.jobs.values() if j["kind"] == "session" and j["status"] == "completed"]}

    def upload(self, body, lid):
        did = "ds_%d" % (len(self.datasets) + 1)
        self.datasets[did] = len([x for x in body.splitlines() if x.strip()])
        return 201, {"dataset_id": did}

    def panels(self, body, lid):
        return 201, {"panel_set_id": "ps_%d" % (len(self.log))}

    def _advance(self, j):
        step = j["script"].pop(0) if j["script"] else "complete"
        lid = j["learner_id"]
        if j["kind"] == "session":
            if step == "complete":
                planned = self.datasets[j["dataset_id"]] + self.plan_delta.get(j["n"], 0)
                ck = "ck_trained_%02d" % j["n"]
                self.learners[lid]["latest_checkpoint_id"] = ck
                j.update(status="completed", recovery=None, resumable=False, result={
                    "checkpoint_id": ck, "budget": {"gpu_seconds": 100.0}, "dose": {"planned_updates": planned, "attempted_updates": planned,
                                                  "retained_updates": planned - self.short.get(j["n"], 0)}})
            elif step == "pause":
                j.update(status="failed", resumable=True, error={"code": "paused_at_work_boundary"},
                         recovery={"case": "resumable_prefix", "retry_with_resume": True, "idempotency_key_reusable": False})
            elif step == "never":
                j.update(status="failed", resumable=False, error={"code": "submission_never_accepted"},
                         recovery={"case": "submission_never_accepted", "retry_with_resume": False, "idempotency_key_reusable": True})
                self.by_key.pop(j["key"], None)
            else:
                j.update(status="failed", resumable=False, error={"code": "internal_error"},
                         recovery={"case": "terminal", "retry_with_resume": False, "idempotency_key_reusable": False})
        else:
            rows = self.datasets[j["dataset_id"]]
            cov = {"complete": True, "answered": rows, "total": rows, "missing": 0, "duplicate": 0, "foreign": 0}
            if step == "partial":
                cov = {"complete": False, "answered": rows - 3, "total": rows, "missing": 3, "duplicate": 0, "foreign": 0}
            if step == "fail":
                j.update(status="failed", resumable=True, error={"code": "eval_incomplete"},
                         recovery={"case": "resumable_prefix", "retry_with_resume": True})
            elif step == "terminal":
                j.update(status="failed", resumable=False, error={"code": "internal_error"}, recovery={"case": "terminal"})
            elif step == "empty":
                j.update(status="completed", result=None)
            else:
                res = {"typed": {"rate": round((rows // 2) / rows, 4), "correct": rows // 2, "total": rows},
                       "coverage": cov, "cap_profile": j["cap_profile"], "answer_cap": 32, "checkpoint_id": j["checkpoint_id"],
                       "scorer_version": "scorer_v1", "cap_set_id": "cap_set_v1", "budget": {"gpu_seconds": 2.0}}
                if self.eval_result_edit:               # a test removes or bends ONE returned field
                    self.eval_result_edit(self.n_eval, res)
                j.update(status="completed", result=res)

    def session(self, body, lid):
        if body["idempotency_key"] in self.by_key:
            return 200, self.jobs[self.by_key[body["idempotency_key"]]]
        self.n_train += 1
        j = {"job_id": "job_t%d_%d" % (self.n_train, len(self.jobs)), "kind": "session", "learner_id": lid, "n": self.n_train,
             "key": body["idempotency_key"], "dataset_id": body["dataset_id"], "status": "running",
             "script": list(self.train_script.get(self.n_train, ["complete"])), "resumes": 0}
        if self.n_train in self.train_script and self.train_script[self.n_train] == ["never", "complete"]:
            self.train_script[self.n_train] = ["complete"]; self.n_train -= 1     # the re-submission is the same logical job
        self.jobs[j["job_id"]] = j; self.by_key[j["key"]] = j["job_id"]; self._advance(j)
        return 202, j

    def evaluation(self, body, lid):
        if body["idempotency_key"] in self.by_key:
            return 200, self.jobs[self.by_key[body["idempotency_key"]]]
        self.n_eval += 1
        j = {"job_id": "job_e%d" % self.n_eval, "kind": "evaluation", "learner_id": lid, "key": body["idempotency_key"],
             "dataset_id": body["dataset_id"], "checkpoint_id": body["checkpoint_id"], "cap_profile": body.get("cap_profile"),
             "status": "running", "script": list(self.eval_script.get(self.n_eval, ["complete"])), "resumes": 0}
        self.jobs[j["job_id"]] = j; self.by_key[j["key"]] = j["job_id"]; self._advance(j)
        return 202, j

    def job(self, body, lid, jid):
        return 200, self.jobs[jid]

    def resume(self, body, lid, jid):
        j = self.jobs[jid]
        if j["status"] == "failed" and j.get("resumable"):
            j["resumes"] += 1; self._advance(j)
        return 200, j

    def answers(self, body, lid, jid):
        return 200, {"items": [{"id": i} for i in range(3)], "next": None}

    ROUTES = [(r"/learners", ("POST", create_learner)), (r"/learners/([^/]+)", ("GET", get_learner)),
              (r"/learners/([^/]+)/checkpoints", ("GET", checkpoints)),
              (r"/learners/([^/]+)/datasets", ("POST", upload)), (r"/learners/([^/]+)/eval-datasets", ("POST", upload)),
              (r"/learners/([^/]+)/panels", ("POST", panels)), (r"/learners/([^/]+)/sessions", ("POST", session)),
              (r"/learners/([^/]+)/evaluations", ("POST", evaluation)), (r"/learners/([^/]+)/jobs/([^/]+)", ("GET", job)),
              (r"/learners/([^/]+)/jobs/([^/]+)/resume", ("POST", resume)),
              (r"/learners/([^/]+)/jobs/([^/]+)/answers", ("GET", answers))]


class DriverTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="driver_test_")
        self.state = os.path.join(self.tmp, "state.json")
        os.environ["LEARNER_API_BASE"] = "https://service.invalid"
        self._out = contextlib.redirect_stdout(io.StringIO()); self._out.__enter__()   # the driver's own report lines are not test output

    def tearDown(self):
        self._out.__exit__(None, None, None)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def go(self, svc, **kw):
        return D.run(DATA, self.state, client=T.LearningClient("k", transport=svc.send), log=QUIET, poll_s=0, **kw)

    def put(self, st):
        with open(self.state, "w") as f:
            json.dump(st, f)

    def rep(self):
        return D.report(self.state, log=QUIET)

    # ---- success
    def test_full_success(self):
        svc = Service()
        self.go(svc)
        r = self.rep()
        self.assertEqual((r["evaluations_complete"], r["evaluations_total"]), (65, 65))
        self.assertTrue(r["protocol_complete"]); self.assertTrue(r["full_dose"])
        self.assertEqual(r["planned_updates"], sum(PLAN.values()))
        self.assertEqual(r["gpu_seconds_reported"], {"training": 1000.0, "evaluation": 130.0})
        self.assertEqual(len(svc.posts(r"/sessions$")), 10); self.assertEqual(len(svc.posts(r"/evaluations$")), 65)
        self.assertEqual(svc.posts(r"/resume$"), [])
        st = D.load_json(self.state)
        self.assertEqual({v["checkpoint_id"] for v in st["events"]["step_zero"].values()}, {st["initial_checkpoint_id"]})
        for n, name in enumerate(ORDER, 1):
            ev = st["events"]["after_teach_%02d" % n]
            self.assertEqual(sorted(ev), sorted(ORDER[:n]))
            self.assertEqual({v["checkpoint_id"] for v in ev.values()}, {st["domains"][name]["checkpoint_id"]})

    def test_same_state_restart_submits_nothing(self):
        svc = Service(); self.go(svc)
        before, n = D.load_json(self.state), len(svc.log)
        self.go(svc)
        self.assertEqual([x for x in svc.log[n:] if x[0] == "POST"], [])
        self.assertEqual(D.load_json(self.state), before)

    # ---- completion reporting
    def test_missing_evaluations_cannot_pass(self):
        st = {"domains": {n: {"status": "completed", "job_id": "jt_%s" % n, "checkpoint_id": "ck_%s" % n, "planned_updates": PLAN[n],
                              "attempted_updates": PLAN[n], "retained_updates": PLAN[n]} for n in ORDER},
              "initial_checkpoint_id": "ck0",
              "events": {"step_zero": {"scan": {"scored": True, "job_id": "j", "checkpoint_id": "ck0", "result_checkpoint_id": "ck0",
                                                "rate": 0.4978, "correct": 112, "total": 225, "cap_profile": "scan", "answer_cap": 32,
                                                "scorer_version": "scorer_v1", "cap_set_id": "cap_set_v1",
                                                "coverage": {"complete": True, "answered": 225, "total": 225, "missing": 0,
                                                             "duplicate": 0, "foreign": 0}}}}}
        self.put(st)
        r = self.rep()
        self.assertEqual((r["evaluations_complete"], r["evaluations_total"]), (1, 65))
        self.assertFalse(r["protocol_complete"]); self.assertEqual(len(r["evaluations_missing"]), 64)
        self.assertEqual(D.main(["report", "--state", self.state]), 2)

    def test_each_missing_cell_blocks_completion(self):
        svc = Service(); self.go(svc)
        good = D.load_json(self.state)
        for ev, sk in (("step_zero", ORDER[-1]), ("after_teach_10", ORDER[0]), ("after_teach_04", ORDER[3])):
            st = copy.deepcopy(good); del st["events"][ev][sk]
            self.put(st)
            r = self.rep()
            self.assertFalse(r["protocol_complete"]); self.assertEqual(r["evaluations_missing"], [[ev, sk]])

    def test_wrong_checkpoint_partial_coverage_and_untrained_skill_are_not_counted(self):
        svc = Service(); self.go(svc)
        good = D.load_json(self.state)
        st = copy.deepcopy(good); st["events"]["step_zero"]["scan"]["checkpoint_id"] = st["domains"]["scan"]["checkpoint_id"]
        self.put(st); r = self.rep()
        self.assertFalse(r["protocol_complete"]); self.assertIn("scored at", r["evaluations_not_counted"][0][2])
        st = copy.deepcopy(good); st["events"]["after_teach_02"]["scan"]["coverage"] = {"complete": True, "answered": 200, "total": 200, "missing": 0, "duplicate": 0, "foreign": 0}
        self.put(st); r = self.rep()
        self.assertFalse(r["protocol_complete"]); self.assertIn("panel has 225", r["evaluations_not_counted"][0][2])
        st = copy.deepcopy(good); st["domains"][ORDER[-1]]["status"] = "failed"
        self.put(st); r = self.rep()
        self.assertFalse(r["protocol_complete"]); self.assertFalse(r["full_dose"]); self.assertEqual(r["training_incomplete"], [ORDER[-1]])

    def test_dose_is_checked_against_the_manifest(self):
        svc = Service(short={3: 1}); self.go(svc); r = self.rep()
        self.assertTrue(r["protocol_complete"]); self.assertFalse(r["full_dose"])
        self.assertEqual(r["partial_dose_skills"], {ORDER[2]: 1}); self.assertEqual(r["unretained_updates"], 1)
        os.remove(self.state)
        svc = Service(plan_delta={1: -100}); self.go(svc); r = self.rep()       # the service planned, and retained, a smaller dose
        self.assertFalse(r["full_dose"]); self.assertEqual(r["plan_mismatch"], {ORDER[0]: {"manifest": PLAN[ORDER[0]], "service": PLAN[ORDER[0]] - 100}})

    # ---- the baseline checkpoint
    def test_step_zero_is_never_scored_at_a_trained_checkpoint(self):
        svc = Service(); svc.crash_on = ("POST", r"/evaluations$", 4)           # dies with 3 of 10 baseline cells submitted
        with self.assertRaises(Crash): self.go(svc)
        lid = D.load_json(self.state)["learner_id"]
        svc.learners[lid]["latest_checkpoint_id"] = "ck_trained_elsewhere"      # the head has moved since
        self.go(svc)
        zero = [j for j in svc.jobs.values() if j["kind"] == "evaluation" and j["checkpoint_id"] == "ck_initial_" + lid]
        self.assertEqual(len(zero), 10); self.assertTrue(self.rep()["protocol_complete"])
        self.assertFalse([j for j in svc.jobs.values() if j.get("checkpoint_id") == "ck_trained_elsewhere"])

    def test_old_state_without_an_initial_checkpoint(self):
        svc = Service(); svc.crash_on = ("POST", r"/evaluations$", 2)
        with self.assertRaises(Crash): self.go(svc)
        st = D.load_json(self.state); st.pop("initial_checkpoint_id"); self.put(st)
        self.go(svc, limit=1)                                                   # recovered from the learner record, not from its head
        self.assertEqual(D.load_json(self.state)["initial_checkpoint_id"], "ck_initial_" + st["learner_id"])
        st = D.load_json(self.state); st.pop("initial_checkpoint_id"); self.put(st)
        svc.omit_initial = True; n = len(svc.log)
        with self.assertRaises(SystemExit) as e: self.go(svc)
        self.assertIn("cannot establish", str(e.exception)); self.assertEqual([x for x in svc.log[n:] if x[0] == "POST"], [])

    def test_a_baseline_stored_at_the_wrong_checkpoint_is_refused(self):
        svc = Service(); self.go(svc, limit=1)
        st = D.load_json(self.state); rec = st["events"]["step_zero"]["scan"]
        rec["checkpoint_id"] = st["domains"]["scan"]["checkpoint_id"]; self.put(st); n = len(svc.log)
        with self.assertRaises(SystemExit) as e: self.go(svc, limit=1)
        self.assertIn("must be scored at", str(e.exception)); self.assertEqual([x for x in svc.log[n:] if x[0] == "POST"], [])

    # ---- one logical training job
    def test_paused_training_is_resumed_exactly_once_on_the_same_job(self):
        svc = Service(train_script={2: ["pause", "complete"]}); self.go(svc)
        self.assertEqual(len(svc.posts(r"/resume$")), 1); self.assertEqual(len(svc.posts(r"/sessions$")), 10)
        ds = D.load_json(self.state)["domains"][ORDER[1]]
        self.assertTrue(svc.posts(r"/resume$")[0][1].endswith("/jobs/%s/resume" % ds["job_id"]))
        self.assertEqual((ds["resumes"], len(ds["failures"]), ds["status"]), (1, 1, "completed"))
        self.assertTrue(self.rep()["protocol_complete"])

    def test_many_segments_one_session(self):
        svc = Service(train_script={1: ["pause"] * 5 + ["complete"]}); self.go(svc)
        self.assertEqual(len(svc.posts(r"/resume$")), 5); self.assertEqual(len(svc.posts(r"/sessions$")), 10)

    def test_crash_around_resume_does_not_duplicate_or_double_count(self):
        svc = Service(train_script={1: ["pause", "complete"]}); svc.crash_on = ("POST", r"/resume$", 1)
        with self.assertRaises(Crash): self.go(svc)
        ds = D.load_json(self.state)["domains"]["scan"]
        self.assertTrue(ds["resume_pending"]); self.assertEqual(ds["resumes"], 1)   # the intent was on disk before the call
        self.go(svc)
        ds = D.load_json(self.state)["domains"]["scan"]
        self.assertEqual(ds["resumes"], 1); self.assertEqual(len(svc.posts(r"/sessions$")), 10)
        self.assertEqual(svc.jobs[ds["job_id"]]["resumes"], 1); self.assertTrue(self.rep()["protocol_complete"])

    def test_crash_around_session_submission_replays_the_same_request(self):
        svc = Service(); svc.crash_on = ("GET", r"/jobs/job_t3", 1)             # accepted, then the client dies before it polls
        with self.assertRaises(Crash): self.go(svc)
        self.go(svc)
        self.assertEqual(svc.n_train, 10); self.assertEqual(len({k for k in svc.by_key}), 75)

    def test_continuations_are_bounded_and_the_failure_is_kept(self):
        svc = Service(train_script={1: ["pause"] * 50})
        with self.assertRaises(SystemExit) as e: self.go(svc, max_resumes=3)
        self.assertIn("still incomplete after 3", str(e.exception)); self.assertEqual(len(svc.posts(r"/resume$")), 3)
        ds = D.load_json(self.state)["domains"]["scan"]
        self.assertEqual(len(ds["failures"]), 4); self.assertEqual(ds["status"], "failed")
        r = self.rep(); self.assertFalse(r["protocol_complete"]); self.assertIn("scan", r["training_incomplete"])
        self.assertEqual(len(svc.posts(r"/sessions$")), 1)                      # nothing after the stuck skill was started

    def test_terminal_failure_stops_without_resume_or_a_second_session(self):
        svc = Service(train_script={2: ["terminal"]})
        with self.assertRaises(SystemExit) as e: self.go(svc)
        self.assertIn("cannot be continued", str(e.exception)); self.assertEqual(svc.posts(r"/resume$"), [])
        self.assertEqual(len(svc.posts(r"/sessions$")), 2)
        r = self.rep(); self.assertFalse(r["protocol_complete"]); self.assertEqual(r["skills_trained"], 1)
        with self.assertRaises(SystemExit): self.go(svc)                        # a restart does not start new paid work either
        self.assertEqual(svc.n_train, 2)

    def test_a_request_never_accepted_is_submitted_again_with_the_same_key(self):
        svc = Service(train_script={1: ["never", "complete"]}); self.go(svc)
        self.assertEqual(len(svc.posts(r"/sessions$")), 11); self.assertEqual(svc.posts(r"/resume$"), [])
        self.assertTrue(self.rep()["protocol_complete"])

    # ---- evaluations
    def test_partial_and_missing_evaluation_results_stop_the_run(self):
        for script, text in ((["partial"], "WITHOUT full coverage"), (["empty"], "WITHOUT full coverage"), (["terminal"], "cannot be resumed")):
            if os.path.exists(self.state): os.remove(self.state)
            svc = Service(eval_script={12: script})
            with self.assertRaises(SystemExit) as e: self.go(svc)
            self.assertIn(text, str(e.exception))
            r = self.rep(); self.assertFalse(r["protocol_complete"]); self.assertLess(r["evaluations_complete"], 65)

    def test_a_resumable_evaluation_is_resumed_and_its_failure_kept(self):
        svc = Service(eval_script={7: ["fail", "complete"]}); self.go(svc)
        self.assertEqual(len(svc.posts(r"/resume$")), 1); self.assertEqual(len(svc.posts(r"/evaluations$")), 65)
        self.assertTrue(self.rep()["protocol_complete"])
        kept = [r for ev in D.load_json(self.state)["events"].values() for r in ev.values() if r.get("failures")]
        self.assertEqual(len(kept), 1)

    # ---- a deliberately short run
    def test_short_run_is_reported_as_short(self):
        svc = Service(); self.go(svc, limit=2); r = self.rep()
        self.assertFalse(r["protocol_complete"]); self.assertTrue(r["short_run"]["complete"])
        self.assertEqual(r["short_run"]["evaluations_expected"], 2 + 1 + 2); self.assertEqual(r["evaluations_total"], 65)

    # ---- missing evidence is not success
    def good_state(self):
        svc = Service(); self.go(svc)
        r = self.rep(); self.assertTrue(r["protocol_complete"]); self.assertTrue(r["full_dose"])     # the positive contract fixture
        return svc, D.load_json(self.state)

    def test_missing_training_status_or_job_identity_is_not_completed(self):
        svc, good = self.good_state()
        for key, text in (("status", "not 'completed'"), ("job_id", "no training job id"), ("checkpoint_id", "no checkpoint id"),
                          ("retained_updates", "retained_updates"), ("attempted_updates", "attempted_updates")):
            st = copy.deepcopy(good); del st["domains"][ORDER[4]][key]
            self.put(st); r = self.rep()
            self.assertFalse(r["protocol_complete"], key); self.assertFalse(r["full_dose"], key)
            self.assertEqual(r["training_incomplete"], [ORDER[4]]); self.assertIn(text, r["training_not_counted"][ORDER[4]])
        self.assertEqual(D.main(["report", "--state", self.state]), 2)

    def test_absent_numeric_coverage_is_not_counted(self):
        svc, good = self.good_state()
        st = copy.deepcopy(good); st["events"]["after_teach_03"]["scan"]["coverage"] = {"complete": True}
        self.put(st); r = self.rep()
        self.assertFalse(r["protocol_complete"]); self.assertEqual(r["evaluations_complete"], 64)
        self.assertIn("coverage census missing", r["evaluations_not_counted"][0][2])
        for key in ("missing", "duplicate", "foreign"):
            st = copy.deepcopy(good); st["events"]["step_zero"]["scan"]["coverage"][key] = 1
            self.put(st); r = self.rep()
            self.assertFalse(r["protocol_complete"]); self.assertIn("%s row" % key, r["evaluations_not_counted"][0][2])

    def test_absent_profile_or_typed_score_is_not_counted(self):
        svc, good = self.good_state()
        for key, text in (("cap_profile", "profile missing"), ("rate", "typed score missing"), ("correct", "typed score missing"),
                          ("total", "typed score missing"), ("answer_cap", "answer cap missing"), ("scorer_version", "scorer identity missing"),
                          ("cap_set_id", "cap set identity missing"), ("result_checkpoint_id", "reports the result at")):
            st = copy.deepcopy(good); del st["events"]["after_teach_10"][ORDER[9]][key]
            self.put(st); r = self.rep()
            self.assertFalse(r["protocol_complete"], key); self.assertEqual(r["evaluations_complete"], 64, key)
            self.assertIn(text, r["evaluations_not_counted"][0][2], key)

    def test_inconsistent_counts_are_not_counted(self):
        svc, good = self.good_state()
        for edit, text in ((dict(correct=300), "exceeds total"), (dict(total=200), "typed total 200"), (dict(rate=0.9), "does not equal"),
                           (dict(cap_profile="other"), "required scan")):
            st = copy.deepcopy(good); st["events"]["step_zero"]["scan"].update(edit)
            self.put(st); r = self.rep()
            self.assertFalse(r["protocol_complete"], edit); self.assertIn(text, r["evaluations_not_counted"][0][2])
        st = copy.deepcopy(good); st["domains"][ORDER[1]]["retained_updates"] = PLAN[ORDER[1]] + 5
        self.put(st); r = self.rep()
        self.assertFalse(r["protocol_complete"]); self.assertIn("inconsistent", r["training_not_counted"][ORDER[1]])
        st = copy.deepcopy(good); st["events"]["after_teach_02"]["scan"]["scorer_version"] = "scorer_v2"
        self.put(st); r = self.rep()
        self.assertFalse(r["protocol_complete"]); self.assertEqual(len(r["scorer_sets"]), 2); self.assertEqual(r["evaluations_complete"], 65)

    def test_the_reviewers_missing_evidence_probe_fails_closed(self):
        svc, good = self.good_state()
        st = copy.deepcopy(good)
        for v in st["domains"].values():
            v.pop("status", None); v.pop("job_id", None)
        for ev in st["events"].values():
            for v in ev.values():
                for k in ("cap_profile", "correct", "rate", "total", "scorer_version", "answer_cap"):
                    v.pop(k, None)
                v["coverage"] = {"complete": True}
        self.put(st); r = self.rep()
        self.assertFalse(r["protocol_complete"]); self.assertFalse(r["full_dose"])
        self.assertEqual(r["evaluations_complete"], 0); self.assertEqual(r["skills_trained"], 0)

    def test_a_malformed_stored_record_is_rejected_on_resume_and_nothing_is_bought(self):
        svc, good = self.good_state()
        st = copy.deepcopy(good); del st["events"]["after_teach_01"]["scan"]["cap_profile"]
        self.put(st); n = len(svc.log)
        with self.assertRaises(SystemExit) as e:
            self.go(svc)
        self.assertIn("stored evidence is not valid", str(e.exception)); self.assertIn("no replacement evaluation was bought", str(e.exception))
        self.assertEqual([x for x in svc.log[n:] if x[0] == "POST"], [])
        self.assertEqual(D.load_json(self.state), st)                                   # the record is kept as it is
        st = copy.deepcopy(good); del st["domains"][ORDER[0]]["job_id"]
        self.put(st); n = len(svc.log)
        with self.assertRaises(SystemExit) as e:
            self.go(svc)
        self.assertIn("no training job id", str(e.exception)); self.assertEqual([x for x in svc.log[n:] if x[0] == "POST"], [])

    def test_a_returned_result_without_required_fields_is_not_stored_as_a_score(self):
        for field in ("cap_profile", "scorer_version", "cap_set_id", "checkpoint_id"):
            if os.path.exists(self.state):
                os.remove(self.state)
            svc = Service(); svc.eval_result_edit = lambda n, res, field=field: res.pop(field) if n == 2 else None
            with self.assertRaises(SystemExit) as e:
                self.go(svc)
            self.assertIn("cannot accept", str(e.exception))
            st = D.load_json(self.state); recs = [r for ev in st["events"].values() for r in ev.values()]
            bad = [r for r in recs if r.get("rejected")]
            self.assertEqual(len(bad), 1); self.assertFalse(bad[0]["scored"]); self.assertEqual(len(svc.posts(r"/evaluations$")), 2)
            self.assertFalse(self.rep()["protocol_complete"])

    def test_partial_dose_is_valid_evidence_but_never_a_full_dose(self):
        svc = Service(short={2: 40}); self.go(svc); r = self.rep()
        self.assertTrue(r["protocol_complete"]); self.assertFalse(r["full_dose"]); self.assertEqual(r["training_not_counted"], {})
        self.assertEqual(r["partial_dose_skills"], {ORDER[1]: 40})


if __name__ == "__main__":
    unittest.main(verbosity=1)
