# Learner Labs Learning API — client + demo preset (2026-09-16)

`learning_client.py` is a standard-library-only client (no operator repository imports, no cloud credentials). It needs two things
you receive from the operator who runs the service: the base URL of your gateway and a customer API key (`sk-…`). Keys are issued by
that operator for your account; this package does not mint them and never carries operator credentials.

`demo_preset.py` (`demo-arith-v1`) is a small synthetic arithmetic lifecycle example, not a demonstration of a full multi-domain workload.
It creates a learner, uploads 16 synthetic supervised training rows and 2 tiny monitor panels, uploads an 8-row held-out evaluation set,
runs one bounded training session, reads the immutable checkpoint, runs an isolated inference on 2 prompts, runs one plain (exact-match)
evaluation on the 8 held-out rows, and prints a transcript with its sha256. It does not upload a fact control and does not use typed
scoring.

```
LEARNER_API_KEY=sk-… LEARNER_API_BASE=https://<your-gateway-base-url> python3 demo_preset.py
```
Both are required; the client raises if the base URL is missing rather than guessing one.

The contract is `openapi_learning_v1.yaml` (and `.json`) beside this file in the package.

## The ten-skill driver
`ten_skill_driver.py` teaches ten domains in a recorded order, one training session per domain on one learner, and evaluates each
domain against its held-out sets as it goes. `ten_skill_manifest.json` names every data file with its sha256, the order, the rows and
token counts, the per-domain planned budget and the evaluation sets. The data files are in `data/` beside this file; point the driver at that directory.

```
python3 ten_skill_driver.py preflight --data-dir ./data                  # verify every file and checksum; sends nothing
python3 ten_skill_driver.py run       --data-dir ./data --state run.json # teach and evaluate, resumable
python3 ten_skill_driver.py report    --state run.json              # what completed, against what the schedule requires
python3 test_ten_skill_driver.py                                    # local tests of the driver; contacts nothing
```
`preflight` refuses to start if any file is missing or any checksum differs. A run writes its ids to the state file, so an
interrupted run resumes the same work rather than starting new work, and a wait that times out locally keeps polling the same job.
A training session the service pauses is continued with `resume` on the same job, a bounded number of times, and every failed job body
is kept in the state file. The baseline is scored at the learner's `initial_checkpoint_id`, recorded once, never at its latest checkpoint.
`report` counts evaluations against the 65 the schedule requires, each with its job id, full answer census, typed score, answer-length profile, scorer identity and the checkpoint the schedule names (an absent field is absent evidence, not a pass), and compares
the dose trained with the dose in the manifest; a run that is missing any of it, or trained only part of a domain, is reported as
incomplete or partial and never as a completed full-dose run. This driver needs a service configured for the full dose; the limits that apply to your
account are part of your service configuration.

## Measuring a baseline before you teach anything
Every learner is created with an **initial checkpoint**: the learner as it is before anything has been taught to it. It is returned as
`initial_checkpoint_id` on the learner, it is listed first among the learner's checkpoints with `kind: "initial"`, and it is used exactly
like any other checkpoint id -- `evaluate_typed`, `evaluate` and `infer` all accept it. Nothing about it changes when you later train:
the id stays the same, the checkpoint stays listed, and re-scoring it returns the same measurement. That is what makes a before-and-after
comparison meaningful. It belongs to the learner it was created with: another learner's initial id, or another account's, is not found.

```python
L = c.create_learner("my learner")
c.list_checkpoints(L["learner_id"])          # the initial state is the first entry, kind: "initial"
before = c.wait(L["learner_id"], c.evaluate_typed(L["learner_id"], L["initial_checkpoint_id"], eval_ds, "base-1", cap_profile="scan")["job_id"])
# ... teach a session, then score the resulting checkpoint and compare
```

## Sessions, continuation and recovery
A training session is a single logical job against one learner. If the service pauses a session at a work boundary, continuing it resumes
the SAME logical job: the work already completed is kept and only the remaining work is performed, so the result is one session, not two.
Creating a new session instead starts a separate piece of work on the learner and does not extend the earlier one.

**Every job tells you what to do if it fails.** A job body carries a `recovery` object: `case`, `retry_with_resume`,
`idempotency_key_reusable`, `needs_operator`, and a sentence of `detail`. There are four cases, and none of them needs operator
credentials:

| `case` | what happened | what you do |
|---|---|---|
| `submission_never_accepted` | the request never reached the execution service, so nothing started and nothing was charged | create the session again; the **same** idempotency key is free to reuse |
| `submission_outcome_uncertain` | the request may or may not have been accepted, and we will not guess | `POST .../jobs/{job_id}/resume` — this **reconciles that same request**; it never starts a second one. If the work did run, the job adopts its result; if it did not, the job says so and the key is released |
| `resumable_prefix` | part of the work completed and was saved | `POST .../jobs/{job_id}/resume` — the **same** job continues from where it stopped; completed work is not repeated |
| `terminal` | it failed with no safe partial state | start a new session with a **new** idempotency key; resume is refused with `not_resumable` |

`resume` is safe to call more than once and safe to call concurrently: a job already running or already finished is returned as it is, and
two callers racing to recover the same job produce one continuation between them, not two. **Never create a new session with a new key to
work around an uncertain outcome** — that is the one action that can run the same work twice.

## What this package is
A client and a worked example. It is not the server, and holding it does not mean an account has been provisioned or a gateway is running
for you. An operator must host the service and issue your base URL and key first.

## Latency
Jobs are batch jobs. Each inference or evaluation job starts a fresh worker, and start-up currently takes roughly 10 to 30 minutes before the first answer is produced; generation itself is a small part of that. Poll the job; do not hold a connection open waiting for it.

Measurements are not guaranteed to be bit-identical across separate runs: two jobs given the same inputs may differ in their measured numbers, and the service does not offer an exact cross-run reproduction guarantee.

## Typed evaluations (panel scoring)
An evaluation set whose rows carry a `scorer` (`{id, prompt, target, scorer}` plus optional `skill`, `input`, `group`) is stored as a
typed set. Create the evaluation with `cap_profile` (the name of a registered answer-length profile) instead of `max_new_tokens`; the
service sizes its own batches from that cap and a provider time budget, pins the checkpoint, cap and scorer set on the job, and completes
only when every row was answered exactly once. Results carry `typed` (`correct`/`total`/`rate`), `interval95`, `cap_profile`,
`answer_cap`, `scorer_version` and `cap_set_id`; answer pages carry `target` and `correct` per row. A job that reports `failed` with
`resumable: true` (a provider failure or an incomplete answer set, code `eval_incomplete`) is continued with `POST .../jobs/{job_id}/resume`:
recorded answers are kept, unanswered rows are asked again. `budget_exceeded` (429) means the account's evaluation budget would be exceeded
by the planned job; nothing was submitted.
