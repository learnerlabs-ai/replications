# Thinking with the facts

**The claim.** With the model's thinking mode on, a taught learner writes out its reasoning
before it answers, and that reasoning recites material that was never in the prompt. It also
answers slightly fewer questions correctly than it does with thinking off. Both halves are in
this folder, in full.

**What was asked.** Two learners that had already been taught were asked their own published
questions twice: once with thinking mode off, once with it on. No new teaching happened. The
learners are the ones from [`demos/teach-a-document/`](../teach-a-document/) (a 706-word company
handbook, 8 facts asked in 2 wordings each) and
[`demos/override-a-belief/`](../override-a-belief/) (facts about an invented planet, with 3
Earth-physics questions riding along as controls). The questions and the expected answers are the
ones already published in those folders.

That second folder holds nine planet facts and 8 are asked here. The ninth, the boiling point, is
the fact that demonstration unlearned, so asking it would measure the deletion rather than
thinking mode.

**The two arms.** With thinking off, the question is the only text sent. With thinking on, the
service also opens the thinking phase with one fixed sentence:

```
Let me recall the taught facts before answering.
- 
```

It carries no learner content and it is the same for every question and both learners. It is
stored byte-exact in the answers file under `primer`. Greedy decoding on both arms. The thinking
phase was capped at 300 tokens, which is what ends several traces mid-sentence.

## The numbers

54 rows, recorded 2026-08-27 on the deployed product
([`answers/2026-08-27-session.json`](answers/2026-08-27-session.json)). Counts are correct
answers over questions asked. "trace recites" counts traces containing the value the row
expected.

| Asked | thinking off | thinking on | trace recites a taught value |
|---|---|---|---|
| handbook, 8 facts x 2 wordings | 14/16 | 12/16 | 13/16 |
| invented-planet facts, 8 | 6/8 | 6/8 | 6/8 |
| Earth-physics controls, 3 | 3/3 | 2/3 | 3/3 pulled a planet value in |

Read the first row for the cost: two fewer answers in sixteen, on the same learner, with nothing
different but the knob. Read the third row for where that cost falls hardest. Asked which gas
people breathe on Earth, the learner answers oxygen with thinking off and carbon dioxide, the
value it was taught about the invented planet, with thinking on. All three control traces carried
a planet value in, including the two whose final answers were still right.

The middle row is level, but not on the same questions. Thinking on recovered the breathing-gas
fact the off arm missed and lost the enclosure-gap measurement the off arm had.

**A row worth understanding.** One handbook row expected `540 days`. The trace recites
`Brindlemoor retains data for 540 days.` sixteen times and then hits the thinking cap mid-number
at `for 5`. The answer emitted is `40 days.`, which does not contain `540 days`, so the row is a
miss. The grader is right and the model had the value. Both facts are visible on the same row,
which is why the traces are published.

**A caution about the handbook learner.** It is the 2026-08-26 recording, which read the document
three times. Its thinking-off score of 14 of 16 is its own reference and the two arms are compared
to each other. The 13 of 16 published in `demos/teach-a-document/` is a different learner, taught
in one pass, and the two numbers are not a comparison.

## Earlier arms

Two earlier runs of this measurement are in [`demos/thinking-mode/`](../thinking-mode/), with
every row. Two of their findings are why the arms here look the way they do. With thinking on and
no primer at all, the handbook learner answered 0 of the first 6 and every answer denied the
company existed; that arm was stopped after six. A longer primer, written to be safer by telling
the model to apply taught facts only when the question is about them, recovered less than the
short sentence above: 7 of 16.

## What is here

| Path | What it is |
|---|---|
| `answers/2026-08-27-session.json` | All 54 rows: question, accepted answers, served answer, full trace, and three grades per row. |
| `grader.md` | Exactly how each of the three grades was decided, and what each cannot see. |

This folder has no `data/` or `questions.json` of its own. The material and the questions belong
to the two folders its learners came from.

## Replicating it

No teaching is involved, so this replays against learners you have already taught. Teach the
handbook by following [`demos/teach-a-document/`](../teach-a-document/), or the planet facts by
following [`demos/override-a-belief/`](../override-a-belief/), then ask that folder's questions
twice: once as written, and once with `enable_thinking` set. The response carries the trace beside
the answer. Grade with the rules in `grader.md`.

Thinking mode is available on taught learners and is not yet optimized for them. The cost measured
here — about two rows in sixteen, and a trace that can carry a taught value onto a question that
was not about it — is what you should expect to reproduce.
