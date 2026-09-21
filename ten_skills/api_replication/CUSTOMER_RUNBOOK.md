# Learning API — customer runbook (2026-09-17)

This package supplies a CLIENT, not the server and not an already provisioned account. Before any of it applies, an operator must host
the service and issue you two things: the base URL of your gateway and a customer API key (`sk-…`). Once you hold those two, nothing
else is needed to use the API. Keep the key out of source control; the operator can revoke and re-issue it at any time. This package never
contains operator credentials, and you are never asked for any.

## Benchmarks
The inference API can generate answers to benchmark questions. Reproducing the report's likelihood-based base scores requires
answer-choice likelihood scoring.

## What you can do
Create a learner; upload supervised examples; run a bounded, resumable training session; read the immutable checkpoint it produces;
run inference on that checkpoint; run an independent evaluation on held-out rows (plain exact-match, or typed scoring with a named
answer-length profile); page through verbatim answers. Every response is opaque ids and aggregate measurements.

## Files in this bundle
`openapi_learning_v1.yaml` / `.json` (in this bundle's root directory) — the contract. `learning_client.py` — a client that needs
only the Python standard library. `ten_skill_driver.py` + `ten_skill_manifest.json` — the ten-skill driver and its data manifest (checksums, order, per-domain
budgets and held-out sets); the data files are in `data/`. `demo_preset.py` — a small synthetic arithmetic
lifecycle example (create → upload 16 training rows and
2 monitor panels → upload an 8-row held-out evaluation set → one bounded session → poll → checkpoint → inference on 2 prompts → one plain
exact-match evaluation). It is not a multi-domain demonstration, it uploads no fact control and it does not use typed scoring. `README.md`
— client notes, including latency, sessions and continuation, and the typed-evaluation section. These files are the whole package; there
are no other directories to fetch.

## Run the demo
```
python3 - <<'PY'
from learning_client import LearningClient
import demo_preset as DP
c = LearningClient("sk-…", base_url="https://<the-base-url-your-operator-gave-you>")
T = DP.run_demo(c, "my first learner", tag="t1", log=print)
print(T["transcript_digest"])
PY
```
The base URL is required. The client raises rather than assuming one, so a missing or empty base URL fails immediately instead of sending
your request somewhere unintended.
Jobs are batch jobs: poll with `get_job` (the client's `wait` does this). A training or inference job starts a fresh worker and takes
roughly 10 to 30 minutes before its first output; do not hold a connection open for it.

## Sessions, continuation and recovery
A training session is one logical job on one learner. If the service pauses a session at a work boundary, continuing it resumes that SAME
logical job — the completed work is kept and only the remaining work runs, so you end with one session and one final checkpoint. Creating
another session instead starts separate work on the learner; it does not extend the earlier one. **If a job fails, its body tells you what to do.** Every job carries a `recovery` object with a `case`, whether `resume` applies, whether
the idempotency key is free to reuse, and one sentence of detail. There are four cases and **none of them needs operator credentials**:
`submission_never_accepted` (nothing started; create the session again with the same key), `submission_outcome_uncertain`
(`resume` **reconciles that same request** and never starts a second one), `resumable_prefix` (`resume` continues the SAME job from the
work already saved), and `terminal` (start a new session with a NEW key; `resume` is refused). `resume` is safe to call repeatedly and
concurrently. **Never work around an uncertain outcome by creating a new session with a new key** — that is the one action that can run
the same work twice.

## Measuring before you teach
Every learner is created with an `initial_checkpoint_id`: the learner as it is before anything has been taught to it. Score it like any
other checkpoint to establish a baseline, then teach and score again. The handle does not change when you train, and re-scoring it returns
the same measurement.

## Reproducibility
Measurements are not guaranteed to be bit-identical between separate runs. Two jobs with the same inputs may report slightly different
numbers, and there is no exact cross-run reproduction guarantee.

## Typed evaluation (panel scoring)
Upload rows of the form `{"id": …, "prompt": …, "target": …, "scorer": …}` (optional `skill`, `input`, `group`) with
`upload_eval_dataset`; then `evaluate_typed(learner, checkpoint, dataset, key, cap_profile=<registered profile name>)`. The service sizes
and runs the batches, and completes the job only when every row was answered exactly once. If the job reports `failed` with
`resumable: true`, call `resume(learner, job)`: recorded answers are kept and only unanswered rows are asked again.

## Errors you may see
`unauthorized` (401): key missing, wrong or revoked. `not_found` (404): the object is not yours or does not exist. `limits_exceeded` (400):
the request exceeds the learner's limits. `learner_busy` (409): a session already holds the learner. `checkpoint_not_current` (409):
re-read the learner and retry. `eval_overlap` (409): your evaluation rows overlap your training rows or panels. `eval_incomplete` (409):
resume the job. `budget_exceeded` (429): the planned job exceeds your account's evaluation budget; nothing was started. `internal_error`
(500): quote the `trace_id` when you write to us.

## What we never ask for
Your key is the only credential. We do not ask for cloud credentials, source code, model files or configuration. If anything you receive
from us contains such material, stop and report it.
