# Teach a document, then ask it back

**The claim.** A 706-word company handbook was taught to a learner in one pass, and afterwards
the learner answered questions about it with the document nowhere in the prompt.

**The recording.** `answers/2026-08-25-session.json` is the recorded serving result: 32 rows,
every one correct. 8 relationship askings and 8 policy askings at greedy decoding, and the same
16 again at temperature 0.9. All graded strict. Every answer is published byte-exact.

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

The one-line install that makes that sentence work goes live with the site launch. Until it is
live, the recorded run in `answers/` is the whole result and this folder is everything behind it.

## What is here

| Path | What it is |
|---|---|
| `data/brindlemoor-handbook.md` | The document taught, byte for byte. 706 words, 4,097 bytes. |
| `data/training-series.json` | The run's training and validation loss, as the training job reported it. |
| `questions.json` | Every question, both wordings, with the answer expected for each. |
| `grader.md` | Exactly how an answer was marked right or wrong. |
| `answers/2026-08-25-session.json` | The recorded run: every answer served, in full. |

## The result

Eight facts asked, each in two wordings, at greedy decoding and again at temperature 0.9.
Every asking answered correctly: 8/8 relationship askings and 8/8 policy askings at greedy,
and 8/8 relationship askings again at temperature 0.9.

The training series in `data/training-series.json` shows the same session from the training
side. Loss on the handbook text falls from 2.66 to 0.04 nats across 45 steps. Loss on held-out
handbook questions the model was never trained on falls to 0.24. A general-ability probe run
alongside stays flat at 2.46.

## How these answers were produced

The demonstrations page carries this box, and it applies to every answer in this repository.

> **How these answers were produced.** Every answer is shown as the model served it. There is no
> system prompt from the caller and no instructions: the only text sent with a question is the
> question. Nothing external was retrieved, no examples were supplied, and no wording was tuned
> to make an answer land. At answer time the server reminds the model of its own saved notes
> from the teaching. Nothing you send, nothing external. The questions were written before the
> run, and where a fact is asked in more than one wording every wording is shown. Answers are
> produced by greedy decoding unless a row says otherwise. We have deliberately not optimised
> any of this. A careful prompt, a retry, a short instruction about the answer format, or an
> agent wrapped around the model would each improve these numbers, and none of that is here.
> What you are looking at is the floor, not the ceiling.

> **How answers are quoted.** After the answer itself, the served text can carry a trailing
> fragment in which the model begins a new conversational turn and repeats its own notes or the
> question back. That trailing text is a serving artifact, not part of the answer. Displays
> quote to the end of the answer itself, which is also what the grader reads. The `answer`
> fields in this folder are byte-exact and untruncated, so you can see exactly where each cut
> would fall.
