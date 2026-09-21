# Running the ten-skill experiment through the API

The API supports sequential skill training, checkpoint continuation, inference and held-out answer scoring. The inference API can generate answers to benchmark questions. Reproducing the report's likelihood-based base scores requires answer-choice likelihood scoring.

Everything needed is in [`api_replication/`](api_replication/): a client that uses only the Python standard library, the ten-skill driver, the data package it reads, and the evaluation schedule.

| path | what it is |
|---|---|
| `api_replication/learning_client.py` | the client; Python 3, no packages to install |
| `api_replication/ten_skill_driver.py` | teaches the ten skills in the recorded order on one learner and scores each held-out panel on the schedule |
| `api_replication/tiny_validation_run.py` | the small end-to-end example: two skills, 16 training rows each, a few held-out questions |
| `api_replication/ten_skill_manifest.json` | the order, row counts, planned updates and checkpoint rows for each skill |
| `api_replication/ten_skill_eval_schedule.json` | which panels are scored at which checkpoint |
| `api_replication/test_ten_skill_driver.py` | local tests of the driver against an in-process stand-in for the service; no account, no cost |
| `api_replication/data/` | the training rows, the 225-row panels and the monitor rows, with `DATA_MANIFEST.json` checksums |
| `api_replication/openapi_learning_v1.yaml` | the API contract (`.json` beside it) |
| `api_replication/CUSTOMER_RUNBOOK.md`, `api_replication/README.md` | client notes: sessions, continuation, recovery, typed evaluation, errors |

## 1. Access

You need a Learning API account. Request one with the **Request access** form at <https://learnerlabs.ai/sign-in>, and say in the form that you want Learning API access to run the ten-skill replication. When the account is provisioned you receive two values: the base URL of your service and an API key (`sk-…`). Keep the key out of source control. Nothing else is asked of you: no cloud credentials, no model files.

```
export LEARNER_API_BASE="https://<the base URL you were issued>"
export LEARNER_API_KEY="sk-…"
```

Confirm both values work before you upload anything. This request is free:

```
cd replications/ten_skills/api_replication        # after step 2
python3 -c "import os, learning_client as T; print(T.LearningClient(os.environ['LEARNER_API_KEY'], os.environ['LEARNER_API_BASE']).health())"
```

If either value is wrong the call raises, and the message names the HTTP status or the connection error.

## 2. Download and check the package locally

```
git clone https://github.com/learnerlabs-ai/replications.git replications
cd replications/ten_skills/api_replication
python3 ten_skill_driver.py preflight --data-dir ./data
python3 test_ten_skill_driver.py
```

The last argument of `git clone` is the directory the repository is checked out into; every path in this guide assumes it is `replications`. Without git, download the repository as a ZIP from the same address and unpack it into a directory named `replications`.

`preflight` reads every file the run will use and compares it with the checksums in `data/DATA_MANIFEST.json`. It sends nothing and costs nothing. Expected output:

```
preflight: 10 domains, 63380 training rows, 5931534 presented tokens (planned)
           2250 panel rows, 10 monitor manifests, 30 files checked
           65 scheduled evaluation jobs
```

The run refuses to start if a file is missing or a checksum differs. `test_ten_skill_driver.py` runs the driver end to end against an in-process stand-in for the service, including interrupted runs, paused training sessions, incomplete evaluations and state files with missing fields. It contacts nothing and should end with `OK`. These are local tests of the driver against the documented contract. They are not a new run of the study.

## 3. Choose a run

**Small end-to-end example.** One learner, two skills taught in sequence with 16 rows each, and a few held-out questions scored at each checkpoint. It exercises every step of the workflow. It is not expected to teach a skill, so a low score is not a failure.

```
python3 tiny_validation_run.py run    --data-dir ./data --state ./tiny_state.json
python3 tiny_validation_run.py report --state ./tiny_state.json
```

**Full training schedule.** All ten skills in the recorded order, one training session per skill, with the panels scored on the schedule.

```
python3 ten_skill_driver.py run    --data-dir ./data --state ./run_state.json
python3 ten_skill_driver.py status --state ./run_state.json
python3 ten_skill_driver.py report --state ./run_state.json
```

`--limit N` runs only the first N skills.

## 4. Cost

Checking saved answers and rebuilding plots runs locally. Training and generating new answers use paid GPU time. The full run costs more because it trains all ten skills and evaluates multiple checkpoints. Requests can include model-loading time; batch questions against the same checkpoint and review the estimate before starting.

The estimate comes from your account. Ask for one when you request access, or from the contact who provisioned your account, before you start paid work. Quote the planned workload that `preflight` prints: 63,380 training updates over 5,931,534 presented tokens in ten training sessions, and 65 evaluation jobs that score 14,625 held-out answers. Your account's rates and limits turn those counts into a price.

Optional paid measurement: the first-skill run trains 9,850 examples and runs its scheduled evaluations. It uses your account's paid compute. Run it only if you want that measurement; it is not required to obtain an estimate or use the API.

```
python3 ten_skill_driver.py run    --data-dir ./data --state ./one_skill.json --limit 1
python3 ten_skill_driver.py report --state ./one_skill.json
```

When it finishes, `report` prints the GPU seconds the service reported for the completed training and evaluation jobs. This is not the small example of section 3, which trains 16 rows per skill.

Your account carries an evaluation budget. An evaluation that would exceed it is refused with `budget_exceeded` (HTTP 429) and nothing is started. That limit applies to evaluation jobs. It is not a cap on what training costs.

An estimate is not a quote: model-loading time varies between requests.

## 5. Interruptions and resuming

The driver writes every dataset, job and checkpoint id to the state file before it waits. If the process stops, run the same command again with the same `--state` file: it re-attaches to the same jobs and does not submit them a second time. If a learner was created but the process stopped before the id was saved, pass `--adopt-learner <learner id>`.

A training session that the service pauses at a work boundary is continued with `resume` on the same job, so it stays one session and completed work is kept. The driver does this by itself, up to `--max-resumes` times for one session (12 by default), and keeps every failed job body in the state file. A session that fails with no saved work stops the run with the reason; the driver does not start a replacement session by itself, because that is new paid work.

The baseline is always scored at the learner's initial checkpoint, the one returned as `initial_checkpoint_id` when the learner is created. It is recorded in the state file once. A run that is restarted after training has begun still scores any missing baseline panel at that checkpoint, never at the learner's latest one.

On restart the driver checks every finished record in the state file again. A record that is marked finished but lacks its required fields stops the run with the reason. The driver does not submit a replacement, because that is new paid work.

A state file belongs to one data package, one manifest and one base URL. If any of them changes, start a new state file.

## 6. Results

`report` prints the updates planned against the updates trained, any skill that trained only part of its planned updates, and the score of every completed panel evaluation. It counts evaluations against the 65 the schedule requires. An evaluation counts only if the state file holds its job id, a full answer census for the panel (every row answered once, none missing, duplicated or foreign), the typed score with consistent counts, the named answer-length profile, the scorer identity, and the checkpoint the schedule names. A training session counts only if the state file holds its completed status, job id, checkpoint and update counts. A field that is absent is treated as absent evidence, never as a pass. `protocol complete: yes` means all ten sessions and all 65 evaluations meet that standard; anything less is reported as `no`, the items are listed with the reason, and the command exits with status 2. `full dose` is a separate line: a session that retained fewer updates than planned is valid and is reported as a partial dose. A run made with `--limit` is reported as a short run. The state file is JSON and holds every job id; the client's `all_answers(learner_id, job_id)` returns the verbatim answers of any evaluation job, which you can score again with [`scorers/`](scorers/).

Measurements are not guaranteed to be bit-identical between separate runs.
