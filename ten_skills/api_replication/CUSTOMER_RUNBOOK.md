# Learning API — customer runbook (updated 2026-09-22)

The Learning API teaches a hosted learner from your own supervised examples and lets you score and query the result. It lives at
**https://api.learnerlabs.ai/learning/v1**. `GET /learning/v1/health` and `GET /learning/v1/openapi.json` need no key; every other call
needs one.

## Getting access
1. Sign in at https://learnerlabs.ai and create an API key on your account's API keys page (the page calls `POST /v1/keys`). The key
   (`sk-…`) is shown once. The same key works for the rest of the Learner Labs API. Revoke it on the same page
   (`DELETE /v1/keys/{key_id}`); a revoked key stops working immediately.
2. The Learning API is enabled per account. With a valid key on an account that is not enabled, calls return
   `403 learning_not_enabled`; ask for it through the request-access form at https://learnerlabs.ai/sign-up.
3. Send the key as `Authorization: Bearer sk-…`. Use an API key, not a browser session. Keep the key out of source control.

Your account is the only thing that decides which learners you can see: the service never reads an account or tenant from anything you
send. Another account's learner, dataset or checkpoint id returns `404 not_found`, exactly like an id that does not exist.

## Your data: three files
**Training rows** — JSON Lines (`Content-Type: application/x-ndjson`), one object per line with exactly three fields, all non-empty strings:
```
{"row_id": "a-001", "prompt": "Q: What is the capital of Ruvelia?\nA:", "answer": " Tarn"}
{"row_id": "a-002", "prompt": "Q: What river runs through Tarn?\nA:", "answer": " The Oskel"}
```
`prompt` is the input the model is given; it is context and is not trained on. `answer` is the output it should learn to produce: the
answer's tokens and an end-of-sequence token are what training fits. Nothing is inserted between the two, so put any separator you want
(the space before `Tarn` above, or a newline) into the text yourself, and ask later questions with the same prompt wording and separators
you trained with. The `Q:`/`A:` layout above is only an example; any consistent layout works. `row_id` must be unique in the file. A raw
document (a line such as `{"text": "…"}`) is refused: this API does not turn documents into question/answer pairs. (To teach a document
as it is, use `POST /v1/sources` on the main API instead.)

**Monitor panels** — one JSON object: `{"schema": "pumod_monitor_v1", "panels": {"<name>": [{"id", "prompt", "answer"}, …]}}`. Panels
are a small fixed set of rows the service scores during and after every session so you can watch retention; they are a training monitor,
not a held-out test. Once a session has used a panel it is registered to the learner: every later panel set must contain it again with
identical rows (a changed or missing panel is refused with `409 panels_conflict`). Add a new panel for each new skill.

**Evaluation rows** (held-out) — JSON Lines of `{"id", "prompt", "expected"}`, non-empty strings, unique ids. Scoring compares the generated
answer with `expected` after lower-casing, collapsing whitespace and removing trailing punctuation (`exact` and `contains`). When you start an
evaluation, every prompt must differ, under that same normalisation, from every training prompt and monitor prompt of the learner, or the
evaluation is refused with `409 eval_overlap`. Keep your training, monitor and evaluation examples disjoint from the start.

### Limits, and when each is checked
| limit | value | checked |
|---|---|---|
| training rows per file | 24,000 | on upload |
| format (exact fields, non-empty strings, unique ids, valid JSON) | — | on upload |
| prompt length | 1,024 tokens | when the session starts, on the training worker, before the model loads |
| answer length | 1,024 tokens including the end token | when the session starts, on the training worker, before the model loads |
| prompt + answer tokens per file | 2,000,000 | when the session starts, on the training worker, before the model loads |
| answer tokens per file | 1,200,000 | when the session starts, on the training worker, before the model loads |
| monitor panels / rows per panel | 12 / 256 | on panel upload |
| evaluation rows per set | 4,000 | on upload; overlap when the evaluation starts |
| prompts per inference request / new tokens | 512 / 256 | when the request is made |

Nothing is truncated. A row over a limit refuses the whole session with `limits_exceeded`; fix the file and start a new session.
`validate_learning_inputs.py` in this package checks every format rule above on your machine, for free, and flags any row that could
exceed a token limit (it counts bytes, which can never be fewer than tokens, so a row it marks safe is safe). The exact token count
is taken only on the training worker when a session starts, so a row the validator marks `CHECK` is the only kind that can still be refused
there. Learning jobs are not currently deducted from your account credit, so a refused session costs you nothing.

## The sequence
```
POST /learning/v1/learners                                        {"name": "my learner"}            -> learner_id, initial_checkpoint_id
POST /learning/v1/learners/{id}/datasets        (x-ndjson)        training rows                     -> dataset_id
POST /learning/v1/learners/{id}/panels          (json)            monitor panels                    -> panel_set_id
POST /learning/v1/learners/{id}/eval-datasets   (x-ndjson)        held-out rows                     -> dataset_id (evaluation)
POST /learning/v1/learners/{id}/evaluations     {"checkpoint_id": initial_checkpoint_id, "dataset_id": …, "idempotency_key": …}   baseline
POST /learning/v1/learners/{id}/sessions        {"dataset_id": …, "panel_set_id": …, "idempotency_key": …}                       -> job
GET  /learning/v1/learners/{id}/jobs/{job_id}   poll until status is not queued/running                  -> checkpoint
POST /learning/v1/learners/{id}/evaluations     same set, the new checkpoint_id                                                   after
POST /learning/v1/learners/{id}/checkpoints/{checkpoint_id}/inferences   {"prompts": [{"id","prompt"}], "idempotency_key": …}
GET  /learning/v1/learners/{id}/jobs/{job_id}/answers   verbatim answers, paged
```
To teach a second skill B after skill A: upload B's rows as a new dataset, upload a panel set containing A's panel unchanged plus B's panel,
start a new session (it continues from the learner's current checkpoint), then evaluate both A's and B's held-out sets on the new checkpoint.

## Benchmarks
The inference API can generate answers to benchmark questions. Reproducing the report's likelihood-based base scores requires
answer-choice likelihood scoring.

## What you can do
Create a learner; upload supervised examples; run a bounded, resumable training session; read the immutable checkpoint it produces;
run inference on that checkpoint; run an independent evaluation on held-out rows (plain exact-match, or typed scoring with a named
answer-length profile); page through verbatim answers. Every response is opaque ids and aggregate measurements.

## Files in this bundle
`openapi_learning_v1.yaml` / `.json` (in this bundle's root directory) — the contract (the service also serves it at `/learning/v1/openapi.json`). `validate_learning_inputs.py` — the free local checker for your training, panel and evaluation files. `learning_client.py` — a client that needs
only the Python standard library. `ten_skill_driver.py` + `ten_skill_manifest.json` — the ten-skill driver and its data manifest (checksums, order, per-domain
budgets and held-out sets); the data files are in `data/`. `demo_preset.py` — a small synthetic arithmetic
lifecycle example (create → upload 16 training rows and
2 monitor panels → upload an 8-row held-out evaluation set → one bounded session → poll → checkpoint → inference on 2 prompts → one plain
exact-match evaluation). It is not a multi-domain demonstration, it uploads no fact control and it does not use typed scoring. `README.md`
— client notes, including latency, sessions and continuation, and the typed-evaluation section. These files are the whole package; there
are no other directories to fetch.

## Run the demo
```
LEARNER_API_KEY=sk-… python3 - <<'PY'
import os
from learning_client import LearningClient
import demo_preset as DP
c = LearningClient(os.environ["LEARNER_API_KEY"])          # base URL defaults to https://api.learnerlabs.ai
T = DP.run_demo(c, "my first learner", tag="t1", log=print)
print(T["transcript_digest"])
PY
```
Jobs are batch jobs: poll with `get_job` (the client's `wait` does this and keeps polling through a temporary 5xx). A training or inference
job starts a fresh worker and takes roughly 10 to 30 minutes before its first output; do not hold a connection open for it.

## Sessions, continuation and recovery
A training session is one logical job on one learner. If the service pauses a session at a work boundary, continuing it resumes that SAME
logical job — the completed work is kept and only the remaining work runs, so you end with one session and one final checkpoint. Creating
another session instead starts separate work on the learner; it does not extend the earlier one. **If a job fails, its body tells you what to do.** Every job carries a `recovery` object with a `case`, whether `resume` applies, whether
the idempotency key is free to reuse, and one sentence of detail. There are four cases and **none of them needs anything beyond your API key**:
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
`unauthorized` (401): key missing, wrong or revoked, or a browser session was sent instead of an API key. `learning_not_enabled` (403): the key is valid but the Learning API is not enabled for your account. `auth_unavailable` (503) and `busy` (503): temporary; retry. `not_found` (404): the object is not yours or does not exist. `limits_exceeded` (400):
a row or request exceeds a limit in the table above. `invalid_request` (400): the file breaks a format rule above. `learner_busy` (409): a session already holds the learner. `checkpoint_not_current` (409):
re-read the learner and retry. `eval_overlap` (409): your evaluation rows overlap your training rows or panels. `eval_incomplete` (409):
resume the job. `budget_exceeded` (429): the planned job exceeds your account's evaluation budget; nothing was started. `internal_error`
(500): quote the `trace_id` when you write to us.

## What we never ask for
Your key is the only credential. We do not ask for cloud credentials, source code, model files or configuration. If anything you receive
from us contains such material, stop and report it.
