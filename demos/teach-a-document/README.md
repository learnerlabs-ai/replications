# Teach a document, then ask it back

**The claim.** A 706-word company handbook was taught to a learner in one pass, and afterwards
the learner answered questions about it with the document nowhere in the prompt.

**The recording.** `answers/2026-08-26-session.json` is the recorded serving result: 32 rows,
25 correct under the strict grade. The 16 questions (8 relationship askings, 8 policy askings)
were asked at greedy decoding, where 14 of 16 were answered correctly, and again at temperature
0.9, where 11 of 16 were. Nothing was attached to any question: no notes, no retrieval, no
instructions. Every answer is published byte-exact. (An earlier file, `2026-08-25-session.json`,
was recorded with the learner's own stored notes prepended to the question and scored 32/32; that
serving path is retired, and the 2026-08-26 file is the one the site quotes.)

**What runs live when you replicate it.** Everything. A fresh learner, taught from nothing, then
asked.

| Stage | Trained live |
|---|---|
| Create the learner | yes |
| Teach the handbook | yes |
| Ask the questions | not training, this is the measurement |

**Cost and time.** About 59 minutes of wall clock, of which roughly 37 minutes is the teaching
and the rest is asking. Around $1.50 to $2 on your own credit. The time figure is measured from
the recorded run. The cost is estimated from the run's compute against our own rate.

```
replay the teach-a-document demo
```

That sentence works once the MCP server is connected (one line, on the [repository front
page](../../README.md)). By hand, the run is steps 1, 2a, 3, 4, 5 of [PROTOCOL.md](../../PROTOCOL.md):
create a learner, teach `data/brindlemoor-handbook.md` as one `kind: "file"` source, wait for the
job, then ask every question in `questions.json` with the `Q: …` frame at temperature 0 and
again at 0.9.

**The base-model control.** Before reading any learner answer as evidence, ask the untrained base
(`"model": "learner-1.0-base"`) the same questions. It does not know this company: asked for the
flagship product and the headquarters city it answered "Brindlemoor" and "London", where the
handbook says Quillstream and Thornbury. A learner answer only counts because the base gets it
wrong.

## What is here

| Path | What it is |
|---|---|
| `data/brindlemoor-handbook.md` | The document taught, byte for byte. 706 words, 4,097 bytes. |
| `data/training-series.json` | The run's training and validation loss, as the training job reported it. |
| `questions.json` | Every question, both wordings, with the answer expected for each. |
| `grader.md` | Exactly how an answer was marked right or wrong. |
| `answers/2026-08-26-session.json` | The recorded run: every answer served, in full, from the weights alone. |
| `answers/2026-08-25-session.json` | The superseded earlier recording (served with the learner's stored notes prepended). Kept for the record; not quoted. |

## The result

Eight facts asked, each in two wordings, at greedy decoding and again at temperature 0.9. At
greedy decoding every policy and numeric asking was answered correctly (8/8) and 6 of the 8
relationship askings were: the one relationship the learner did not bind was the company's
second product, which it answered with an invented product name in both wordings. At
temperature 0.9, 11 of 16: 5/8 relationship askings and 6/8 policy askings, the two policy misses
being format ("four hours" for "4 hours"; "A$2,400" run together) rather than a wrong value.

The training series in `data/training-series.json` shows the same session from the training
side. Loss on the handbook text falls from 2.66 to 0.05 nats across 45 steps. Loss on held-out
handbook questions the model was never trained on falls to 0.25. A general-ability probe run
alongside stays flat at 2.46. The job's registered acquisition on the handbook is 0.4052 nats.

## How these answers were produced

The demonstrations page carries this box, and it applies to every answer in this repository.

> **How these answers were produced.** Every answer is shown as the model served it. There is no
> system prompt from the caller and no instructions: the only text sent with a question is the
> question. Nothing external was retrieved, no examples were supplied, and no wording was tuned
> to make an answer land. The questions were written before the run, and where a fact is asked
> in more than one wording every wording is shown. Answers are produced by greedy decoding
> unless a row says otherwise. We have deliberately not optimised any of this. A careful prompt,
> a retry, a short instruction about the answer format, or an agent wrapped around the model
> would each improve these numbers, and none of that is here. What you are looking at is the
> floor, not the ceiling.

> **How answers are quoted.** After the answer itself, the served text can carry a trailing
> fragment in which the model begins a new conversational turn and repeats its own notes or the
> question back. That trailing text is a serving artifact, not part of the answer. Displays
> quote to the end of the answer itself, which is also what the grader reads. The `answer`
> fields in this folder are byte-exact and untruncated, so you can see exactly where each cut
> would fall.
