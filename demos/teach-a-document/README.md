# Teach a document, then ask it back

**The claim.** A 706-word company handbook was taught to a learner in one pass, and afterwards
the learner answered questions about it with the document nowhere in the prompt.

**The recording.** `answers/session.json` is the recorded serving result: 32 rows,
26 correct under the strict grade. The 16 questions (8 relationship askings, 8 policy askings)
were asked at greedy decoding, where 13 of 16 were answered correctly, and again at temperature
0.9, where 13 of 16 were. Nothing was attached to any question: no notes, no retrieval, no
instructions. Every answer is published byte-exact.

**One recording, and what that means for repeating it.** This is a single run, not an average.
Re-teaching the document will not reproduce it row for row, because the step that turns a page
into short factual statements is partly model-driven: the same 918-token document extracted five
times under identical settings produced five different statement sets
([`../../extraction/README.md`](../../extraction/README.md)). What happens after the statements
exist is reproducible -- one finished learner re-quizzed five times returned the same score every
time, and the same row failed each time. Expect roughly one answer in sixteen to move.

**What runs live when you replicate it.** Everything. A fresh learner, taught from nothing, then
asked.

| Stage | Trained live |
|---|---|
| Create the learner | yes |
| Teach the handbook | yes |
| Ask the questions | not training, this is the measurement |

**Cost and time.** About 57 minutes of wall clock on the recorded one-pass run, of which
roughly 34 minutes is upload-to-trained and the rest is asking. The service quoted $1.56 before
the run. The time figure is measured from the recorded run; the cost is the service's own
pre-run estimate, which is a guard rather than a ceiling.

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
| `questions.json` | Every question, both wordings, with the answer expected for each. |
| `grader.md` | Exactly how an answer was marked right or wrong. |
| `answers/session.json` | The recorded run: every answer served, in full, from the weights alone. One training pass, the API default. |

## The result

Eight facts asked, each in two wordings, at greedy decoding and again at temperature 0.9. At
greedy decoding every policy and numeric asking was answered correctly (8/8) and 5 of the 8
relationship askings were: the flagship product came back as the second product in both
wordings, and the second product was answered in one wording and echoed back as a question in
the other. At temperature 0.9, 13 of 16: 6/8 relationship askings (the flagship missing in both
wordings) and 7/8 policy askings. The one policy miss is format rather than a wrong value:
"$2,400" is there but runs straight into an echoed question with no separator, so the strict
word-boundary grader does not count it. The job's registered acquisition on the handbook is
0.1483 nats over an estimated 918 tokens; that token figure is the estimate the service prices
against, not a measured count.

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
