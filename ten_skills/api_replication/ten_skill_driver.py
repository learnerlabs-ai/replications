#!/usr/bin/env python3
"""Ten-skill demo driver -- an ordinary customer CLI over the public HTTP API.

It uses the documented customer contract only: upload a training set, register the
retention monitors, run one logical training job per skill, then score the frozen
held-out panel with the typed scorer at each scheduled checkpoint.

    python3 ten_skill_driver.py preflight --data-dir ./data
    python3 ten_skill_driver.py run       --data-dir ./data --state ./run_state.json
    python3 ten_skill_driver.py status    --state ./run_state.json
    python3 ten_skill_driver.py report    --state ./run_state.json

Environment: LEARNER_API_BASE and LEARNER_API_KEY.  Nothing else is required, and no
operator module, credential or internal path is used.

Honest accounting.  The driver separates three outcomes and never conflates them:
  * protocol complete -- every evaluation the schedule REQUIRES was scored with full coverage
                         at the checkpoint the schedule names, and every training job completed
                         (the required set is read from the schedule, never from what happens to
                         be present in the state file);
  * partial dose      -- training ran but the service retained fewer updates than planned;
  * full dose         -- retained == planned EXACTLY, for every skill.
A single unretained update is a partial dose, not a rounding error.
"""
import argparse
import hashlib
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import learning_client as T  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, "ten_skill_manifest.json")
SCHEDULE = os.path.join(HERE, "ten_skill_eval_schedule.json")
STATE_VERSION = 3
MAX_TRAIN_RESUMES = 12      # continuations of ONE logical training job before the run stops and says so
MAX_RESUBMITS = 2           # re-submissions of a request the service reports it never accepted (same key)


# ----------------------------------------------------------------- small helpers

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def sha256_obj(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load_json(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def read_bytes(p):
    with open(p, "rb") as f:
        return f.read()


def resolve(data_dir, rel):
    p = os.path.join(data_dir, rel)
    if not os.path.exists(p):
        raise SystemExit(
            "missing data file: %s\n"
            "  The driver reads the customer data package. Pass --data-dir pointing at the\n"
            "  unpacked package (the directory holding DATA_MANIFEST.json)." % p)
    return p


def idem(binding, *parts):
    return "ce20-" + hashlib.sha256((binding + "|" + "|".join(str(x) for x in parts)).encode()).hexdigest()[:40]


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# ----------------------------------------------------------------- the required work

def teach_order(manifest):
    return [d["domain"] for d in sorted(manifest["domains"], key=lambda d: d.get("order", 0))]


def expected_evaluations(manifest, schedule, limit=None):
    """The evaluations this package REQUIRES, as (event, skill, job) in schedule order.

    Read from the schedule, restricted to the skills this package teaches.  Anything the
    schedule marks as not runnable here (its panel is not shipped) is excluded.  `limit`
    restricts the scope to the first N teaches, for a deliberately short run.
    """
    order = teach_order(manifest)
    if schedule.get("teach_order") and list(schedule["teach_order"]) != order:
        raise SystemExit("the evaluation schedule and the manifest disagree about the teach order;\n"
                         "  the package is inconsistent and no run can be scored against it.")
    scope = order[:limit] if limit else order
    out = []
    for e in sorted(schedule["events"], key=lambda e: e.get("order", 0)):
        ev = e["event"]
        if ev == "step_zero":
            want = scope
        else:
            n = int(ev.rsplit("_", 1)[1])
            if n > len(scope):
                continue
            want = order[:n]
        jobs = {j["skill"]: j for j in e["jobs"] if j.get("runnable", True)}
        got = [sk for sk in want if sk in jobs]
        if ev != "step_zero" and got != want:
            raise SystemExit("schedule event %s does not cover the skills taught so far (%s)" % (ev, want))
        out += [(ev, sk, jobs[sk]) for sk in got]
    return out


def required_checkpoint(st, order, ev):
    """The checkpoint an event MUST be scored at. None means it cannot be established yet."""
    if ev == "step_zero":
        return st.get("initial_checkpoint_id")
    n = int(ev.rsplit("_", 1)[1])
    return ((st.get("domains") or {}).get(order[n - 1]) or {}).get("checkpoint_id")


# ----------------------------------------------------------------- stored evidence
def _count(v):
    return isinstance(v, int) and not isinstance(v, bool) and v >= 0


def training_evidence(d):
    """None when a stored training record proves a completed session; otherwise the reason it does not.

    Nothing is assumed.  A record with no status is not a completed record.  A partial dose is
    still valid evidence: it is reported as a partial dose, never as a full one.
    """
    if not d:
        return "no training record"
    if d.get("status") != "completed":
        return "training status is %r, not 'completed'" % (d.get("status"),)
    if not d.get("job_id"):
        return "no training job id"
    if not d.get("checkpoint_id"):
        return "no checkpoint id"
    for k in ("planned_updates", "attempted_updates", "retained_updates"):
        if not _count(d.get(k)):
            return "dose evidence missing or not a count: %s" % k
    if not d["retained_updates"] <= d["attempted_updates"] <= d["planned_updates"]:
        return "dose counts are inconsistent (retained %s, attempted %s, planned %s)" % (
            d["retained_updates"], d["attempted_updates"], d["planned_updates"])
    return None


def evaluation_evidence(rec, job, want_ck):
    """None when a stored evaluation proves the scheduled job was scored in full; otherwise the reason.

    Every field below is one the service returns with a completed typed evaluation.  An absent
    field is absent evidence, and absent evidence is not a pass.
    """
    rows = job.get("panel_rows")
    cov = rec.get("coverage") if isinstance(rec.get("coverage"), dict) else {}
    if cov.get("complete") is not True:
        return "coverage incomplete"
    for k in ("total", "answered", "missing", "duplicate", "foreign"):
        if not _count(cov.get(k)):
            return "coverage census missing: %s" % k
    if cov["total"] != rows:
        return "scored %s rows, the panel has %s" % (cov["total"], rows)
    if cov["answered"] != cov["total"]:
        return "answered %s of %s" % (cov["answered"], cov["total"])
    for k in ("missing", "duplicate", "foreign", "empty"):
        if cov.get(k):
            return "coverage reports %s %s row(s)" % (cov[k], k)
    if not (_count(rec.get("correct")) and _count(rec.get("total"))) or not isinstance(rec.get("rate"), (int, float)) \
            or isinstance(rec.get("rate"), bool):
        return "typed score missing (correct / total / rate)"
    if rec["total"] != rows:
        return "typed total %s, the panel has %s" % (rec["total"], rows)
    if rec["correct"] > rec["total"]:
        return "typed correct %s exceeds total %s" % (rec["correct"], rec["total"])
    if rec["total"] and abs(rec["rate"] - rec["correct"] / rec["total"]) > 5e-4:
        return "typed rate %s does not equal %s / %s" % (rec["rate"], rec["correct"], rec["total"])
    if not rec.get("cap_profile"):
        return "answer-cap profile missing"
    if rec["cap_profile"] != job.get("cap_profile"):
        return "answer-cap profile %s, required %s" % (rec["cap_profile"], job.get("cap_profile"))
    if not (_count(rec.get("answer_cap")) and rec["answer_cap"] > 0):
        return "answer cap missing"
    if not rec.get("scorer_version"):
        return "scorer identity missing"
    if not rec.get("cap_set_id"):
        return "answer-cap set identity missing"
    if not want_ck:
        return "the required checkpoint is not established"
    if rec.get("checkpoint_id") != want_ck:
        return "scored at %s, required %s" % (rec.get("checkpoint_id"), want_ck)
    if rec.get("result_checkpoint_id") != want_ck:
        return "the service reports the result at %s, required %s" % (rec.get("result_checkpoint_id"), want_ck)
    return None


# ----------------------------------------------------------------- identity binding

def compute_binding(data_dir, manifest, schedule, base_url):
    """Bind persisted state to the manifest, the data package and the endpoint.

    If any of them changes, earlier dataset/job ids describe a different experiment and
    must not be reused.  The driver refuses rather than silently continuing.
    """
    dm_path = os.path.join(data_dir, "DATA_MANIFEST.json")
    return {
        "manifest_id": manifest["manifest_id"],
        "manifest_sha256": sha256_obj(manifest),
        "schedule_sha256": sha256_obj(schedule),
        "data_manifest_sha256": sha256_file(dm_path) if os.path.exists(dm_path) else None,
        "api_base": base_url,
        "state_version": STATE_VERSION,
    }


def binding_key(b):
    return sha256_obj(b)


# ----------------------------------------------------------------- preflight

def preflight(data_dir, manifest=None, schedule=None, log=print):
    """Check every file the run will need, locally, before any paid request."""
    m = manifest or load_json(MANIFEST)
    sch = schedule or load_json(SCHEDULE)
    dm_path = os.path.join(data_dir, "DATA_MANIFEST.json")
    if not os.path.exists(dm_path):
        raise SystemExit("no DATA_MANIFEST.json in %s -- point --data-dir at the unpacked data package" % data_dir)
    dm = load_json(dm_path)
    by_domain = {d["domain"]: d for d in dm["domains"]}

    ok, problems, files = True, [], 0
    rows = tokens = panel_rows = 0
    for d in m["domains"]:
        name = d["domain"]
        cd = by_domain.get(name)
        if cd is None:
            problems.append("%s: absent from the data package" % name)
            ok = False
            continue
        tr = resolve(data_dir, cd["training"]["path"])
        got = sha256_file(tr)
        files += 1
        if got != cd["training"]["sha256"]:
            problems.append("%s: training checksum mismatch" % name)
            ok = False
        rows += cd["training"]["rows"]
        tokens += (cd.get("authoritative") or {}).get("presented_tokens", 0)
        sp = cd.get("scored_panel")
        if not sp:
            problems.append("%s: no scored panel in the data package" % name)
            ok = False
        else:
            pp = resolve(data_dir, sp["path"])
            files += 1
            if sha256_file(pp) != sp["sha256"]:
                problems.append("%s: panel checksum mismatch" % name)
                ok = False
            panel_rows += sp["rows"]

    mons = dm.get("monitor_manifests") or []
    for mm in mons:
        p = resolve(data_dir, mm["path"])
        files += 1
        if sha256_file(p) != mm["sha256"]:
            problems.append("monitor teach%02d: checksum mismatch" % mm["teach"])
            ok = False
    if not mons:
        problems.append("the data package carries no monitor manifests; the service requires a "
                        "registered monitor set before a training session can start")
        ok = False

    # a schedule job whose panel is not in the data package is counted apart, never run blind
    present = set(by_domain)
    sched_jobs = skipped = 0
    for e in sch["events"]:
        for j in e["jobs"]:
            if j["skill"] in present:
                sched_jobs += 1
            else:
                skipped += 1

    log("preflight: %d domains, %d training rows, %d presented tokens (planned)" % (len(m["domains"]), rows, tokens))
    log("           %d panel rows, %d monitor manifests, %d files checked" % (panel_rows, len(mons), files))
    log("           %d scheduled evaluation jobs%s" % (sched_jobs, " (%d skipped: not in this package)" % skipped if skipped else ""))
    for p in problems:
        log("  PROBLEM: %s" % p)
    return {"ok": ok, "problems": problems, "rows": rows, "presented_tokens": tokens,
            "panel_rows": panel_rows, "monitor_manifests": len(mons),
            "scheduled_eval_jobs": sched_jobs, "skipped_eval_jobs": skipped, "files_checked": files}


# ----------------------------------------------------------------- state

def load_state(path):
    if path and os.path.exists(path):
        return load_json(path)
    return {"state_version": STATE_VERSION, "binding": None, "binding_key": None,
            "learner_id": None, "create_pending": None, "domains": {}, "events": {}}


def save_state(path, st):
    if not path:
        return
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(st, f, indent=1, sort_keys=True)
    os.replace(tmp, path)


def bind_state(st, binding, adopt=None):
    k = binding_key(binding)
    if st.get("binding_key") and st["binding_key"] != k:
        raise SystemExit(
            "this state file was written for a different experiment.\n"
            "  stored binding : %s\n  current binding: %s\n"
            "  The manifest, the data package or the service URL changed, so the stored dataset and\n"
            "  job ids do not describe this run. Start a new state file rather than reusing them."
            % (json.dumps(st.get("binding"), sort_keys=True), json.dumps(binding, sort_keys=True)))
    st["binding"], st["binding_key"] = binding, k
    if adopt:
        st["learner_id"], st["create_pending"] = adopt, None
    return st


# ----------------------------------------------------------------- job helpers

def wait_job(c, lid, job_id, log, poll_s=20.0, timeout_s=6 * 3600):
    """Poll to a terminal state. A transient error is retried by the client's own wait()."""
    while True:
        try:
            return c.wait(lid, job_id, poll_s=poll_s, timeout_s=timeout_s)
        except TimeoutError:
            log("  still running after %ds (%s); continuing to poll -- not resubmitting" % (timeout_s, job_id))


def finish_eval(c, lid, job_id, log, resumes_left=3, rec=None, save=None):
    """Drive ONE typed evaluation job to a complete, fully-covered result.

    A job that already exists is polled, never skipped: queued and running jobs are
    awaited, and a job that failed *resumably* is resumed so the answers already
    recorded are kept and only the unanswered rows are asked again.
    """
    while True:
        j = wait_job(c, lid, job_id, log)
        if j["status"] == "completed":
            return j
        if rec is not None:                             # failed evidence is kept, never overwritten
            rec.setdefault("failures", []).append({"at": now(), "status": j.get("status"), "error": j.get("error"),
                                                   "recovery": j.get("recovery"), "resumable": j.get("resumable")})
            if save:
                save()
        if j["status"] == "failed" and j.get("resumable") and resumes_left > 0:
            log("  evaluation %s failed but is resumable; resuming (%d left)" % (job_id, resumes_left))
            resumes_left -= 1
            c.resume(lid, job_id)
            continue
        raise SystemExit(
            "evaluation %s ended %s and cannot be resumed: %s\n"
            "  A required evaluation did not complete. The run stops here rather than reporting\n"
            "  success with a missing panel." % (job_id, j["status"], j.get("error")))


def establish_initial_checkpoint(c, lid, created=None):
    """The learner's UNTRAINED checkpoint, from the documented contract only.

    It is `initial_checkpoint_id` on the learner (returned at creation and on every read) and
    it is listed among the learner's checkpoints with kind "initial".  The learner's moving
    head (`latest_checkpoint_id`) is never used: after the first training job it names a
    TRAINED checkpoint, and a baseline scored there is not a baseline.
    """
    for body in (created, None):
        if body is None:
            try:
                body = c.get_learner(lid)
            except Exception:
                body = {}
        ck = (body or {}).get("initial_checkpoint_id")
        if ck:
            return ck
    try:
        listed = c.list_checkpoints(lid)
        items = listed.get("items", listed) if isinstance(listed, dict) else listed
        for it in items or []:
            if isinstance(it, dict) and it.get("kind") == "initial" and it.get("checkpoint_id"):
                return it["checkpoint_id"]
    except Exception:
        pass
    return None


def finish_training(c, lid, name, ds, log, save, poll_s=20.0, max_resumes=MAX_TRAIN_RESUMES, resubmit=None):
    """Drive ONE logical training job to completion through the documented recovery contract.

    A session the service pauses at a work boundary is continued with `resume` on the SAME
    job id: completed work is kept and no second session is created.  The intent is written
    to the state file before every call, continuations are bounded, every failed job body is
    kept as evidence, and a job that cannot be continued stops the run with the reason.
    """
    while True:
        J = wait_job(c, lid, ds["job_id"], log, poll_s=poll_s)
        if J["status"] == "completed":
            ds["resume_pending"] = False
            return J
        rcv = J.get("recovery") or {}
        case = rcv.get("case")
        ds.setdefault("failures", []).append({"at": now(), "job_id": ds["job_id"], "status": J.get("status"),
                                              "error": J.get("error"), "recovery": rcv,
                                              "resumable": J.get("resumable"), "segments": J.get("segments")})
        ds["status"] = J.get("status")
        save()
        if J["status"] == "failed" and case == "submission_never_accepted" and rcv.get("idempotency_key_reusable") and resubmit:
            if ds.get("resubmits", 0) >= MAX_RESUBMITS:
                raise SystemExit("training for %s was never accepted after %d submissions of the same request; "
                                 "stopping. Nothing was started for it." % (name, ds["resubmits"] + 1))
            ds["resubmits"] = ds.get("resubmits", 0) + 1
            save()
            log("  training request for %s was never accepted; submitting the SAME request again" % name)
            ds["job_id"] = resubmit()["job_id"]
            save()
            continue
        can = J["status"] == "failed" and case != "terminal" and (rcv.get("retry_with_resume") or J.get("resumable"))
        if not can:
            raise SystemExit(
                "training job %s for %s ended %s and cannot be continued (recovery case: %s): %s\n"
                "  The run stops here. The failed job is kept in the state file. A terminal failure needs a NEW\n"
                "  session with a new key, which this driver will not start on its own."
                % (ds["job_id"], name, J.get("status"), case, json.dumps(J.get("error"))))
        if not ds.get("resume_pending"):                # a restart that finds the intent already written does not count twice
            if ds.get("resumes", 0) >= max_resumes:
                raise SystemExit("training job %s for %s still incomplete after %d continuations; stopping.\n"
                                 "  Re-running continues the same job; nothing is resubmitted."
                                 % (ds["job_id"], name, ds["resumes"]))
            ds["resumes"] = ds.get("resumes", 0) + 1
            ds["resume_pending"] = True
            save()                                      # state BEFORE the call
        log("  training job %s paused with work saved; continuing the same job (%d of %d)"
            % (ds["job_id"], ds["resumes"], max_resumes))
        c.resume(lid, ds["job_id"])
        ds["resume_pending"] = False
        save()


# ----------------------------------------------------------------- the run

def run(data_dir, state_path, limit=None, manifest=None, schedule=None, client=None,
        log=print, adopt=None, poll_s=20.0, max_resumes=MAX_TRAIN_RESUMES):
    m = manifest or load_json(MANIFEST)
    sch = schedule or load_json(SCHEDULE)
    dm = load_json(os.path.join(data_dir, "DATA_MANIFEST.json"))
    by_domain = {d["domain"]: d for d in dm["domains"]}
    mon_by_teach = {int(x["teach"]): x for x in (dm.get("monitor_manifests") or [])}

    base = os.environ.get("LEARNER_API_BASE", "")
    if client is None:
        key = os.environ.get("LEARNER_API_KEY", "")
        if not key:
            raise SystemExit("LEARNER_API_KEY is not set -- your operator issues this key with your service URL")
        if not base:
            raise SystemExit("LEARNER_API_BASE is not set -- your operator supplies the base URL of YOUR service")
        c = T.LearningClient(key, base)
    else:
        c = client
    binding = compute_binding(data_dir, m, sch, base)
    st = bind_state(load_state(state_path), binding, adopt)
    bkey = st["binding_key"]

    # -- learner (crash-safe: the intent is written BEFORE the call) --------------
    if not st.get("learner_id"):
        if st.get("create_pending"):
            raise SystemExit(
                "a previous run recorded that it was creating a learner but never stored the id.\n"
                "  Creating another one would silently start a second experiment. Find the learner\n"
                "  (intent key %s) and re-run with --adopt-learner <learner_id>." % st["create_pending"])
        st["create_pending"] = idem(bkey, "create-learner")
        save_state(state_path, st)
        L = c.create_learner(m["manifest_id"])
        st["learner_id"] = L["learner_id"]
        st["initial_checkpoint_id"] = L.get("initial_checkpoint_id")
        st["create_pending"] = None
        save_state(state_path, st)
        log("learner %s" % st["learner_id"])
    lid = st["learner_id"]

    # -- the untrained checkpoint, fixed once and never re-derived from the learner's head ------
    if not st.get("initial_checkpoint_id"):
        st["initial_checkpoint_id"] = establish_initial_checkpoint(c, lid)
        save_state(state_path, st)
    if not st.get("initial_checkpoint_id"):
        raise SystemExit(
            "cannot establish this learner's initial (untrained) checkpoint.\n"
            "  The state file does not record it and the service did not return `initial_checkpoint_id`\n"
            "  or a checkpoint of kind \"initial\". The baseline will not be scored at the learner's current\n"
            "  head, because after any training that is a trained checkpoint. Nothing was submitted.")

    full_order = teach_order(m)
    order = full_order[:limit] if limit else full_order
    if st.get("limit") not in (None, limit) and st.get("domains"):
        log("note: this state file was started with --limit %s; continuing with --limit %s" % (st.get("limit"), limit))
    st["limit"] = limit
    required = expected_evaluations(m, sch, limit)
    save_state(state_path, st)

    def event_slot(ev):
        return st["events"].setdefault(ev, {})

    jobs_by = {(ev, sk): job for ev, sk, job in expected_evaluations(m, sch)}

    def score_event(ev, skills, checkpoint_id):
        """One typed evaluation per skill, at this checkpoint."""
        slot = event_slot(ev)
        if not checkpoint_id:
            raise SystemExit("event %s has no checkpoint to be scored at; nothing was submitted" % ev)
        for skill in skills:
            cd = by_domain.get(skill)
            if not cd or not cd.get("scored_panel"):
                raise SystemExit("the schedule requires %s / %s but the data package carries no scored panel for it;\n"
                                 "  run `preflight` -- a required evaluation is never skipped silently." % (ev, skill))
            rec = slot.setdefault(skill, {})
            if rec.get("job_id") and rec.get("checkpoint_id") != checkpoint_id:
                raise SystemExit(
                    "%s / %s was submitted at checkpoint %s, but this event must be scored at %s.\n"
                    "  The stored evaluation does not measure what the schedule asks for. It is kept as it is;\n"
                    "  start a new state file to run the experiment again."
                    % (ev, skill, rec.get("checkpoint_id"), checkpoint_id))
            if rec.get("scored"):
                if not rec.get("job_id"):
                    raise SystemExit("%s / %s is marked scored but records no evaluation job; the state file was "
                                     "not written by this driver for this run." % (ev, skill))
                why = evaluation_evidence(rec, jobs_by[(ev, skill)], checkpoint_id)
                if why:
                    raise SystemExit(
                        "%s / %s is marked scored but its stored evidence is not valid: %s.\n"
                        "  Nothing was submitted and no replacement evaluation was bought. The record is kept as it is;\n"
                        "  restore the state file this driver wrote, or start a new state file." % (ev, skill, why))
                continue
            if not rec.get("eval_dataset_id"):
                body = read_bytes(resolve(data_dir, cd["scored_panel"]["path"]))
                rec["eval_dataset_id"] = c.upload_eval_dataset(lid, body)["dataset_id"]
                save_state(state_path, st)
            if not rec.get("job_id"):
                V = c.evaluate_typed(lid, checkpoint_id, rec["eval_dataset_id"],
                                     idem(bkey, ev, skill, checkpoint_id), cap_profile=skill)
                rec["job_id"], rec["checkpoint_id"] = V["job_id"], checkpoint_id
                save_state(state_path, st)
            J = finish_eval(c, lid, rec["job_id"], log, rec=rec, save=lambda: save_state(state_path, st))
            res = J.get("result") or {}
            typed, cov = res.get("typed") or {}, res.get("coverage") or {}
            rec.update(scored=True, rate=typed.get("rate"), correct=typed.get("correct"),
                       total=typed.get("total"), coverage=cov, interval95=res.get("interval95"),
                       scorer_version=res.get("scorer_version"), cap_profile=res.get("cap_profile"),
                       answer_cap=res.get("answer_cap"), cap_set_id=res.get("cap_set_id"), budget=res.get("budget"),
                       result_checkpoint_id=res.get("checkpoint_id"))
            if not cov.get("complete"):
                rec["scored"] = False                   # the returned body is kept; it is not a score
                save_state(state_path, st)
                raise SystemExit(
                    "evaluation %s (%s / %s) completed WITHOUT full coverage: %s\n"
                    "  A partial panel is not a result." % (rec["job_id"], ev, skill, json.dumps(cov)))
            why = evaluation_evidence(rec, jobs_by[(ev, skill)], checkpoint_id)
            if why:
                rec["scored"], rec["rejected"] = False, why
                save_state(state_path, st)
                raise SystemExit(
                    "evaluation %s (%s / %s) returned a result this driver cannot accept: %s.\n"
                    "  The returned fields are kept in the state file. Nothing else was submitted."
                    % (rec["job_id"], ev, skill, why))
            try:                                        # keep the raw answers, not only the rate
                rec["answers_kept"] = len(c.all_answers(lid, rec["job_id"]))
            except Exception as e:                      # answers are evidence, not a gate
                rec["answers_kept"] = "unavailable: %s" % e
            log("  %-14s %-24s rate=%s coverage=%s/%s" % (ev, skill, rec["rate"],
                                                          cov.get("answered"), cov.get("total")))
            save_state(state_path, st)

    def skills_for(ev):
        return [sk for e, sk, _ in required if e == ev]

    # -- baseline: always at the learner's initial checkpoint, whatever has been trained since --
    score_event("step_zero", skills_for("step_zero"), st["initial_checkpoint_id"])

    # -- one logical training job per skill --------------------------------------
    for i, name in enumerate(order, 1):
        cd = by_domain[name]
        ds = st["domains"].setdefault(name, {})

        if ds.get("status") == "completed" or ds.get("checkpoint_id"):
            why = training_evidence(ds)                 # a finished-looking record is proven, or nothing is sent at all
            if why:
                raise SystemExit(
                    "the stored training record for %s looks finished but is not valid: %s.\n"
                    "  Nothing was submitted and no training was bought again. Restore the state file this driver\n"
                    "  wrote, or start a new state file." % (name, why))

        if not ds.get("dataset_id"):
            body = read_bytes(resolve(data_dir, cd["training"]["path"]))
            ds["dataset_id"] = c.upload_dataset(lid, body)["dataset_id"]
            save_state(state_path, st)

        if not ds.get("panel_set_id"):                  # monitors are REQUIRED by the service
            mm = mon_by_teach.get(i)
            if not mm:
                raise SystemExit("no monitor manifest for teach %d in the data package" % i)
            ds["panel_set_id"] = c.upload_panels(lid, load_json(resolve(data_dir, mm["path"])))["panel_set_id"]
            ds["monitor_panels"] = mm["panels"]
            save_state(state_path, st)

        submit = lambda ds=ds, name=name: c.create_session(lid, ds["dataset_id"], ds["panel_set_id"], idem(bkey, name, "train"))
        if not ds.get("job_id"):
            ds["submit_pending"] = True                 # state BEFORE the call; the key makes a repeat a replay
            save_state(state_path, st)
            ds["job_id"] = submit()["job_id"]
            ds["submit_pending"] = False
            save_state(state_path, st)

        if ds.get("status") == "completed":
            J = None                                    # already finished and recorded: nothing is polled or resubmitted
        else:
            J = finish_training(c, lid, name, ds, log, lambda: save_state(state_path, st), poll_s=poll_s,
                                max_resumes=max_resumes, resubmit=submit)
        if J is None:
            score_event("after_teach_%02d" % i, skills_for("after_teach_%02d" % i), ds["checkpoint_id"])
            continue
        res = J.get("result") or {}
        dose = res.get("dose") or {}                    # the real field names
        if not res.get("checkpoint_id"):
            raise SystemExit("training job %s for %s completed without a checkpoint id; stopping" % (ds["job_id"], name))
        ds.update(status="completed", checkpoint_id=res.get("checkpoint_id"),
                  planned_updates=dose.get("planned_updates"),
                  attempted_updates=dose.get("attempted_updates"),
                  retained_updates=dose.get("retained_updates"),
                  dose=dose, metrics=res.get("metrics"), budget=res.get("budget"),
                  disposition=res.get("disposition"), segments=J.get("segments"))
        why = training_evidence(ds)
        if why:
            ds["status"], ds["rejected"] = "invalid_result", why
            save_state(state_path, st)
            raise SystemExit("training job %s for %s completed with a result this driver cannot accept: %s.\n"
                             "  The returned fields are kept in the state file. Nothing else was submitted."
                             % (ds["job_id"], name, why))
        save_state(state_path, st)
        log("teach %02d %-24s retained %s of %s planned -> %s"
            % (i, name, ds["retained_updates"], ds["planned_updates"], ds["checkpoint_id"]))

        score_event("after_teach_%02d" % i, skills_for("after_teach_%02d" % i), ds["checkpoint_id"])

    save_state(state_path, st)
    return st


# ----------------------------------------------------------------- reporting

def report(state_path, manifest=None, schedule=None, log=print):
    """Three separate verdicts. None of them is inferred from the others.

    The work that must exist is derived from the schedule and the manifest.  A state file
    that holds one good evaluation is one good evaluation, not a finished protocol.
    """
    st = load_json(state_path)
    m = manifest or load_json(MANIFEST)
    sch = schedule or load_json(SCHEDULE)
    order = teach_order(m)
    plan = {d["domain"]: (d.get("planned_budget") or {}).get("planned_updates") for d in m["domains"]}
    limit = st.get("limit")

    doms = st.get("domains") or {}
    trained, incomplete, plan_mismatch, missing, training_invalid = [], [], {}, {}, {}
    for n in order:
        d = doms.get(n) or {}
        why = training_evidence(d)
        if why:
            incomplete.append(n)
            if d:
                training_invalid[n] = why
            continue
        trained.append(n)
        if d.get("planned_updates") != plan[n]:
            plan_mismatch[n] = {"manifest": plan[n], "service": d.get("planned_updates")}
        if d.get("retained_updates") != plan[n]:
            missing[n] = (plan[n] or 0) - (d.get("retained_updates") or 0)
    planned = sum(v or 0 for v in plan.values())
    retained = sum((doms[n].get("retained_updates") or 0) for n in trained)

    def check(required):
        ok, absent, wrong = [], [], []
        for ev, sk, job in required:
            rec = ((st.get("events") or {}).get(ev) or {}).get(sk) or {}
            if not (rec.get("scored") and rec.get("job_id")):
                absent.append([ev, sk])
                continue
            why = evaluation_evidence(rec, job, required_checkpoint(st, order, ev))
            if why:
                wrong.append([ev, sk, why])
            else:
                ok.append([ev, sk])
        return ok, absent, wrong

    required = expected_evaluations(m, sch)
    ok, absent, wrong = check(required)
    all_trained = not incomplete
    ev_recs = [st["events"][ev][sk] for ev, sk in ok]
    scorer_sets = sorted({"%s | %s" % (r.get("scorer_version"), r.get("cap_set_id")) for r in ev_recs})
    one_scorer = len(scorer_sets) <= 1          # evaluations scored under different scorer sets are not one experiment
    protocol_complete = bool(all_trained and required and len(ok) == len(required) and one_scorer)
    full_dose = bool(all_trained and planned > 0 and not missing and not plan_mismatch and retained == planned)

    scope = None
    if limit:
        sreq = expected_evaluations(m, sch, limit)
        sok, sabs, swrong = check(sreq)
        scope = {"limit": limit, "evaluations_expected": len(sreq), "evaluations_complete": len(sok),
                 "complete": bool(len(sok) == len(sreq) and not [n for n in order[:limit] if n in incomplete])}

    log("")
    log("skills trained            : %d of %d" % (len(trained), len(order)))
    log("updates planned / retained: %d / %d" % (planned, retained))
    log("evaluations complete      : %d of %d required by the schedule" % (len(ok), len(required)))
    if scope:
        log("short run (--limit %d)     : %d of %d evaluations in its scope; scope %s"
            % (limit, scope["evaluations_complete"], scope["evaluations_expected"],
               "complete" if scope["complete"] else "NOT complete"))
    gpu_train = sum(((doms[n].get("budget") or {}).get("gpu_seconds") or 0) for n in trained)
    gpu_eval = sum(((r.get("budget") or {}).get("gpu_seconds") or 0) for ev in (st.get("events") or {}).values() for r in ev.values())
    if gpu_train or gpu_eval:
        log("GPU seconds reported      : %.0f training, %.0f evaluation (as reported by the service for completed jobs)" % (gpu_train, gpu_eval))
    log("")
    log("  protocol complete : %s" % ("yes" if protocol_complete else "no"))
    log("  full dose         : %s%s" % ("yes" if full_dose else "no",
                                        "" if full_dose else "   (%d update(s) not retained)" % (planned - retained)))
    if incomplete:
        log("  training not completed: %s" % ", ".join(incomplete))
    for n, why in training_invalid.items():
        log("  training record NOT counted: %-24s %s" % (n, why))
    if not one_scorer:
        log("  evaluations were scored under %d different scorer sets: %s" % (len(scorer_sets), "; ".join(scorer_sets)))
    if plan_mismatch:
        log("  the service planned a different dose than the manifest: %s" % json.dumps(plan_mismatch, sort_keys=True))
    if missing:
        log("  partial-dose skills:")
        for n, d in missing.items():
            log("    %-24s %d update(s) short" % (n, d))
    if absent:
        log("  required evaluations NOT scored: %d (first: %s / %s)" % (len(absent), absent[0][0], absent[0][1]))
    for ev, sk, why in wrong:
        log("  NOT counted: %-16s %-24s %s" % (ev, sk, why))
    log("")
    for ev in sorted(st.get("events") or {}):
        for skill in sorted(st["events"][ev]):
            r = st["events"][ev][skill]
            log("  %-16s %-24s rate=%-8s cap=%-6s scorer=%s"
                % (ev, skill, r.get("rate"), r.get("answer_cap"), r.get("scorer_version")))
    return {"skills_trained": len(trained), "skills_total": len(order), "training_incomplete": incomplete,
            "training_not_counted": training_invalid, "scorer_sets": scorer_sets,
            "planned_updates": planned, "retained_updates": retained,
            "unretained_updates": planned - retained, "partial_dose_skills": dict(missing),
            "plan_mismatch": plan_mismatch,
            "evaluations_complete": len(ok), "evaluations_total": len(required),
            "evaluations_missing": absent, "evaluations_not_counted": wrong,
            "initial_checkpoint_id": st.get("initial_checkpoint_id"),
            "gpu_seconds_reported": {"training": gpu_train, "evaluation": gpu_eval},
            "protocol_complete": protocol_complete, "full_dose": full_dose, "short_run": scope,
            "events": st.get("events") or {}}


def status(state_path, log=print):
    st = load_json(state_path)
    log("learner: %s" % st.get("learner_id"))
    for n, d in (st.get("domains") or {}).items():
        log("  %-24s job=%-26s retained=%s ckpt=%s"
            % (n, d.get("job_id"), d.get("retained_updates"), d.get("checkpoint_id")))
    for ev in sorted(st.get("events") or {}):
        done = sum(1 for r in st["events"][ev].values() if r.get("scored"))
        log("  %-16s %d evaluation(s) scored (run `report` for the count the schedule requires)" % (ev, done))
    for n, d in (st.get("domains") or {}).items():
        if d.get("failures"):
            log("  %-24s %d failed attempt(s) kept, %d continuation(s)" % (n, len(d["failures"]), d.get("resumes", 0)))
    return st


def main(argv=None):
    ap = argparse.ArgumentParser(description="Run the ten-skill demo through the customer API.")
    ap.add_argument("command", choices=["preflight", "run", "status", "report"])
    ap.add_argument("--data-dir", default=None)
    ap.add_argument("--state", default="ten_skill_state.json")
    ap.add_argument("--limit", type=int, default=None, help="run only the first N skills")
    ap.add_argument("--adopt-learner", default=None, help="attach to an existing learner after an interrupted create")
    ap.add_argument("--poll-seconds", type=float, default=20.0)
    ap.add_argument("--max-resumes", type=int, default=MAX_TRAIN_RESUMES,
                    help="continuations of one paused training job before the run stops (default %d)" % MAX_TRAIN_RESUMES)
    a = ap.parse_args(argv)

    if a.command in ("preflight", "run") and not a.data_dir:
        raise SystemExit("--data-dir is required (the unpacked customer data package)")
    if a.command == "preflight":
        r = preflight(a.data_dir)
        return 0 if r["ok"] else 1
    if a.command == "run":
        run(a.data_dir, a.state, a.limit, adopt=a.adopt_learner, poll_s=a.poll_seconds, max_resumes=a.max_resumes)
        r = report(a.state)
        return 0 if (r["protocol_complete"] or (r["short_run"] or {}).get("complete")) else 2
    if a.command == "status":
        status(a.state)
        return 0
    r = report(a.state)
    return 0 if r["protocol_complete"] else 2                # an unfinished protocol is never exit status 0


if __name__ == "__main__":
    sys.exit(main())
