"""Small end-to-end validation of the hosted learning API.

One learner; two sequential logical training jobs (skill A then skill B, 16 rows each);
a typed evaluation of a few held-out questions per skill at each resulting checkpoint.
State is committed to disk before every provider request, so the driver can be killed
mid-job and a fresh process re-attaches to the SAME job by id instead of re-submitting.

This validates the workflow. It is not an accuracy reproduction: a 16-row dose is not
expected to teach a skill, and a low score here is not an API failure.

  python3 tiny_validation_run.py run   --data-dir ./data --state ./tiny_state.json
  python3 tiny_validation_run.py report --state ./tiny_state.json
"""
import os, sys, json, time, argparse, hashlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import learning_client as T

SKILL_A, SKILL_B = "scan", "juniper_dispatch"
TRAIN_ROWS, EVAL_ROWS = 16, 4
STATE_VERSION = "tiny-v1"


def load_jsonl(p, n=None):
    out = []
    with open(p, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln: continue
            out.append(json.loads(ln))
            if n and len(out) >= n: break
    return out


def save(path, st):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f: json.dump(st, f, indent=1, sort_keys=True)
    os.replace(tmp, path)


def load(path):
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {"version": STATE_VERSION, "steps": {}}


def idem(*parts):
    return "tiny-" + hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()[:24]


def wait_job(c, lid, job_id, log, resumes_left=2):
    """Poll to a terminal state. A resumable failure is resumed, never re-submitted."""
    while True:
        j = c.wait(lid, job_id, poll_s=20.0)
        st = j.get("status")
        if st == "completed": return j
        if st == "failed" and j.get("resumable") and resumes_left > 0:
            resumes_left -= 1
            log("  job %s paused with work committed; resuming in a new segment" % job_id)
            c.resume(lid, job_id); continue
        raise SystemExit("job %s ended %s: %s" % (job_id, st, json.dumps(j.get("error"))))


def step(st, path, name, fn, log):
    """Run a step once. The result is committed under its name; a restart replays nothing."""
    if name in st["steps"]:
        log("· %s (already done, from state)" % name)
        return st["steps"][name]
    st.setdefault("pending", {})[name] = {"started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    save(path, st)
    out = fn()
    st["steps"][name] = out
    st["pending"].pop(name, None)
    save(path, st)
    log("· %s" % name)
    return out


def run(data_dir, state_path, attempt=1, log=print):
    key, base = os.environ.get("LEARNER_API_KEY"), os.environ.get("LEARNER_API_BASE")
    if not key or not base:
        raise SystemExit("set LEARNER_API_KEY and LEARNER_API_BASE")
    c = T.LearningClient(key, base)
    st = load(state_path)
    st["api_base"] = base
    log("health: %s" % json.dumps(c.health()))

    lid = step(st, state_path, "learner", lambda: c.create_learner("tiny-validation"), log)["learner_id"]
    log("learner %s" % lid)

    # ---- fixtures -------------------------------------------------------
    panels, train, evalrows = {}, {}, []
    for sk in (SKILL_A, SKILL_B):
        prows = load_jsonl(os.path.join(data_dir, "panels", sk + ".jsonl"))
        panels[sk] = prows
        held = prows[:EVAL_ROWS]
        evalrows += held
        heldp = {r["prompt"] for r in held}
        rows = [r for r in load_jsonl(_train_path(data_dir, sk)) if r["prompt"] not in heldp][:TRAIN_ROWS]
        train[sk] = rows
        assert len(rows) == TRAIN_ROWS, "%s: only %d training rows" % (sk, len(rows))

    # Both skills carry the SAME registered answer cap (188), so one cap_profile covers every
    # held-out row: the cap applied is identical either way and each row is still scored by ITS
    # OWN scorer. This halves the evaluation requests without changing what is measured. It is a
    # batching decision and it is recorded as one.
    cap_profile = SKILL_A
    log("held-out rows %d over %d skills; scorers %s; one evaluation job per checkpoint at cap_profile=%s"
        % (len(evalrows), len(train), sorted({r["scorer"] for r in evalrows}), cap_profile))

    mon = {"schema": "pumod_monitor_v1", "panels": {}}
    for sk in (SKILL_A, SKILL_B):
        seen = {r["prompt"] for r in evalrows} | {r["prompt"] for r in train[sk]}
        mrows = [r for r in panels[sk] if r["prompt"] not in seen][:8]
        mon["panels"][sk] = [{"id": r["id"], "prompt": r["prompt"], "answer": r["target"]} for r in mrows]
    psid = step(st, state_path, "panel_set", lambda: c.upload_panels(lid, mon), log)["panel_set_id"]

    ev_b = "".join(json.dumps(r, sort_keys=True) + "\n" for r in evalrows).encode()
    evid = step(st, state_path, "eval_dataset", lambda: c.upload_eval_dataset(lid, ev_b), log)["dataset_id"]

    # ---- two sequential logical training jobs ---------------------------
    scored = []
    prev_ck = None
    for tag, sk in (("A", SKILL_A), ("B", SKILL_B)):
        b = "".join(json.dumps(r, sort_keys=True) + "\n" for r in train[sk]).encode()
        dsid = step(st, state_path, "dataset_" + tag, lambda b=b: c.upload_dataset(lid, b), log)["dataset_id"]
            # a FAILED training session cannot be retried under the same idempotency key: the
        # gateway replays the failed job, and `resume` accepts only evaluations. A client that wants to
        # try again must mint a NEW key, so the attempt number is part of it.
        sess = step(st, state_path, "session_%s_a%d" % (tag, attempt),
                    lambda dsid=dsid, tag=tag: c.create_session(lid, dsid, psid, idem(lid, tag, dsid, attempt),
                                                                expected_checkpoint_id=prev_ck), log)
        jid = sess["job_id"]
        log("training job %s (%s, %d rows) -> %s" % (tag, sk, TRAIN_ROWS, jid))
        j = step(st, state_path, "trained_%s_a%d" % (tag, attempt), lambda jid=jid: wait_job(c, lid, jid, log), log)
        res = j.get("result") or {}
        ck = res.get("checkpoint_id"); prev_ck = ck
        log("  checkpoint %s  dose %s  segments %s" % (ck, json.dumps(res.get("dose")), (res.get("budget") or {}).get("segments")))

        ej = step(st, state_path, "eval_%s_a%d" % (tag, attempt),
                  lambda ck=ck, tag=tag: wait_job(c, lid, c.evaluate_typed(
                      lid, ck, evid, idem(lid, tag, ck, cap_profile, attempt), cap_profile=cap_profile)["job_id"], log), log)
        r = (ej.get("result") or {})
        scored.append({"after": tag, "just_trained": sk, "checkpoint_id": ck, "cap_profile": cap_profile,
                       "coverage": r.get("coverage"), "typed": r.get("typed"),
                       "interval95": r.get("interval95"), "scorer_version": r.get("scorer_version"),
                       "answer_cap": r.get("answer_cap"), "per_row": r.get("rows") or r.get("per_row")})
    st["scored"] = scored
    save(state_path, st)
    log("done: %d scored evaluations" % len(scored))
    return st


def _train_path(data_dir, skill):
    d = os.path.join(data_dir, "train")
    for n in sorted(os.listdir(d)):
        if n.endswith("_%s.jsonl" % skill) or n == skill + ".jsonl": return os.path.join(d, n)
    raise SystemExit("no training file for %s" % skill)


def report(state_path):
    st = load(state_path)
    out = {"api_base": st.get("api_base"), "learner_id": (st["steps"].get("learner") or {}).get("learner_id"),
           "physical_requests": sum(1 for k in st["steps"] if k.startswith(("trained_", "eval_"))),
           "checkpoints": [], "scored": st.get("scored", [])}
    for k, v in sorted(st["steps"].items()):
        if k.startswith("trained_"):
            r = v.get("result") or {}
            out["checkpoints"].append({"job": k[8:], "checkpoint_id": r.get("checkpoint_id"),
                                       "dose": r.get("dose"), "disposition": r.get("disposition"),
                                       "segments": (r.get("budget") or {}).get("segments")})
    doses = [c["dose"] for c in out["checkpoints"] if c.get("dose")]
    out["protocol_complete"] = bool(out["checkpoints"]) and all(d.get("attempted_updates") == d.get("planned_updates") for d in doses)
    out["full_dose"] = bool(doses) and all(d.get("retained_updates") == d.get("planned_updates") for d in doses)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["run", "report"])
    ap.add_argument("--data-dir"); ap.add_argument("--state", default="tiny_state.json")
    ap.add_argument("--attempt", type=int, default=1, help="a failed training session needs a NEW idempotency key; bump this to try again")
    a = ap.parse_args(argv)
    if a.command == "run":
        if not a.data_dir: raise SystemExit("--data-dir is required")
        run(a.data_dir, a.state, attempt=a.attempt)
    else:
        print(json.dumps(report(a.state), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
