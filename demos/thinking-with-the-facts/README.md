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

Of the second folder’s nine planet facts, 8 are tested here. The boiling-point fact was excluded because this learner did not hold it.

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

54 rows, recorded on the deployed product
([`answers/session.json`](answers/session.json)). Counts are correct
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

**Thinking-cap failure.** One handbook row expected `540 days`. Its trace repeats `Brindlemoor retains data for 540 days.` sixteen times, then hits the thinking cap at `for 5`. The emitted answer, `40 days.`, misses the expected value despite its presence in the trace.

**Handbook learner provenance.** This battery uses the superseded three-pass recording, with its own thinking-off reference of 14 of 16. The published `demos/teach-a-document/` result, 13 of 16, uses a different, one-pass learner. The thinking comparison is between the two arms of this battery.

## What is here

| Path | What it is |
|---|---|
| `answers/session.json` | All 54 rows: question, accepted answers, served answer, full trace, and three grades per row. |
| `grader.md` | Rules for each of the three recorded grades. |

This folder has no `data/` or `questions.json` of its own. The material and the questions belong
to the two folders its learners came from.

## Replicating it

No teaching is involved when you replay this by hand, against learners you have already taught.
The agent tool is not the same: `replay the thinking-with-the-facts demo` with no arguments
teaches both documents again, the handbook and the invented world. That is two teaches, about
$1.56 and $1.25 on the published per-demo figures, on top of the 54 graded asks. Pass `learner_id`
for a handbook learner you already hold, or `resume_job_id` to ride a teach that already landed,
and it skips that teaching.

To replay by hand, teach the handbook by following
[`demos/teach-a-document/`](../teach-a-document/), or the planet facts by following
[`demos/override-a-belief/`](../override-a-belief/), then ask that folder's questions
twice: once as written, and once with `enable_thinking` set. The response carries the trace beside
the answer. Grade with the rules in `grader.md`.

Thinking mode is available on taught learners and is not yet optimized for them. Expect to
reproduce the cost measured here: about two rows in sixteen, and a trace that can carry a taught
value onto a question that was not about it.
