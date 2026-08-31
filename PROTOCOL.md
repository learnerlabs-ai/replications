# By hand: the exact calls behind every demonstration

Every demonstration in this repository is a sequence of ordinary HTTP calls against the deployed
product. This page lists them literally, so a replication needs nothing but `curl`, a key, and the
material in the demo folder. The coding-agent route (`replay the <demo> demo` through the MCP
server) runs exactly these calls; this is the same protocol without the agent.

Two practical notes. Requests need a real `User-Agent` header (the default Python `urllib` agent
string is refused at the edge). And keep the key out of your shell history and process list:

```bash
printf 'Authorization: Bearer %s\n' "YOUR_API_KEY" > auth.txt   # once; chmod 600 auth.txt
API=https://api.learnerlabs.ai
```

Every call below is `curl -sS -H @auth.txt -H "Content-Type: application/json" -H "User-Agent: replication/1"`.
Abbreviated as `curl …` from here on.

## 1. Create the learner

```bash
curl … $API/v1/learners -d '{"name": "replication-teach-a-document"}'
# → { "learner_id": "lrn_…", "session_id": "…", … }   keep learner_id
```

The `session_id` in this response is account-scope bookkeeping. To ask, open a learner session
(step 4).

## 2a. Teach a document (teach-a-document)

Price it first. `"confirm": false` trains nothing and charges nothing:

```bash
curl … $API/v1/sources -d @- <<'JSON'
{"learner_id": "lrn_…", "kind": "file", "name": "brindlemoor-handbook.md",
 "confirm": false, "content": "<the byte-exact text of data/brindlemoor-handbook.md>"}
JSON
# → { "confirmed": false, "quote": { "tokens": …, "est_usd": …, "est_seconds": … } }
```

Then send the same body with `"confirm": false` dropped (or set to `true`) and it starts
immediately. Add `"cost_cap_usd": 4.5` to any teaching call and it refuses to start if the
estimate exceeds the cap. The response carries a `job_id`.

The product extracts individual facts from the document as part of the teach and reports how
many it accepted (`fact_extraction` in the response, and `GET /v1/facts?learner_id=lrn_…`
afterwards). On the handbook that is 15 rows.

## 2b. Teach individual facts (override-a-belief, delete-a-fact, teach-in-sequence)

The fact demos do not go through document extraction. Each fact is installed directly, then one
training call writes all pending facts at once. This is also the official route for any fact the
extractor declined from a document: the extractor accepts only atomic one-subject-one-value
statements, and in the recorded runs it accepted 4 of the 9 override facts and 9 of the 12
delete-a-fact facts when they were offered as a document, so the demos install them by fact.

```bash
# one call per fact (data/facts.json carries the exact text)
curl … $API/v1/facts -d '{"learner_id": "lrn_…", "fact_text": "Veyra water boils at 150 degrees Celsius."}'
# → { "row_id": "…", "status": "pending", … }   keep row_id for the deletion step

# then write every pending fact in one training job
curl … $API/v1/facts/train -d '{"learner_id": "lrn_…"}'
# → { "job_id": "…", … }
```

Where a demo teaches a short preamble document first (`data/preamble.md`), it goes through step
2a before the facts.

## 3. Wait for the job

```bash
curl … $API/v1/jobs/JOB_ID            # state, and when finished the acquisition on your material
curl … $API/v1/jobs/JOB_ID/events     # the live stage stream
```

A teach takes tens of minutes. Do not re-send a teach because a long request returned a gateway
timeout: the job was dispatched. `GET /v1/audit?learner_id=lrn_…` lists it, and you resume by
polling the job.

## 4. Open a session and ask

```bash
curl … $API/v1/sessions -d '{"learner_id": "lrn_…"}'          # → { "session_id": "ses_…" }
curl … $API/v1/sessions/ses_…/activate -X POST                  # opens the sitting; compute.stage is pollable
```

The ask is the plain chat call. The only text sent is the question, framed as `Q: …`; no
system prompt, no examples, nothing retrieved, nothing attached. Greedy decoding is
`"temperature": 0`; the recorded runs also repeat every question at `0.9`.

```bash
curl … $API/v1/chat/completions -d @- <<'JSON'
{"model": "learner-1.0:lrn_…", "temperature": 0, "max_tokens": 96,
 "messages": [{"role": "user", "content": "Q: What year was Brindlemoor founded?"}]}
JSON
```

A cold learner answers `202` with a pending job instead of an answer; its field is `id`. Poll
`GET /v1/chat/completions/jobs/{id}` until the answer arrives. The first ask after a fresh
checkpoint can take several minutes while the serving side loads it.

Every response names which learner actually served it in the `served_by` field:
`learner-1.0:<learner_id>` for a learner, `learner-1.0-base` for the base model. Alongside it sits
an `identity_witness` block that echoes what the serving side observed for that request. Inside it,
`served_by_learner` is three-valued: `true` (the serving side confirmed the learner served),
`false` (the base served), or `null` (the serving side did not report an observation for this
request). A recorded answer counts as a learner answer only
when `served_by` equals `learner-1.0:` followed by your `learner_id`. An answer served by the base
model is not a learner answer.

## 5. The base-model control

Ask the untrained base the same question before you read a learner answer as evidence. Set
`"model": "learner-1.0-base"` and keep everything else identical:

```bash
curl … $API/v1/chat/completions -d @- <<'JSON'
{"model": "learner-1.0-base", "temperature": 0, "max_tokens": 96,
 "messages": [{"role": "user", "content": "Q: What is Brindlemoor's flagship product?"}]}
JSON
```

On the handbook the base answers with an invented product and city (the recorded control answered
"Brindlemoor" and "London" where the taught truth is Quillstream and Thornbury), which is what
makes a correct learner answer evidence of teaching rather than of prior knowledge. Every fact
in the fact demos was chosen so the base provably does not hold it; the same control shows that.

## 6. Unlearn one fact and re-ask (delete-a-fact, override-a-belief)

```bash
curl … "$API/v1/facts/fct_…?learner_id=lrn_…" -X DELETE
# → { "deleted": true, "removal": { "training_job_id": "…" }, … }
```

The deletion dispatches a removal training job automatically. Wait for that job (step 3) before
re-asking. An ask that lands before it finishes is served from the previous checkpoint and reads
as "not deleted". Then repeat step 4 for the deleted fact (it should revert to the base answer)
and for every kept fact (they should still answer). The recorded runs show a measured noise floor
of about one row in eight to twelve flipping either way on any retrain, deletion or not; read a
single-row change against that floor, not as a verdict.

## What the recorded numbers mean

The demo READMEs quote counts of the form "8/8 at greedy". Each is a strict grade: the served
answer must contain the expected value exactly as `grader.md` specifies. Nothing is re-tried,
re-worded, or prompted toward the answer. What you replicate by this protocol is the floor.
