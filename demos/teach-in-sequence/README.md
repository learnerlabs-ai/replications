# Teach three things in a row, and check the first two still answer

**The claim.** Three unrelated topics were taught one after another into the same learner. After
the third, each of the first two moved by one answer out of four, which is inside the movement we
measure between any two training runs of this size.

**What runs live when you replicate it.** The third lesson only.

| Stage | Trained live |
|---|---|
| Lesson A, the Kestrel board | no, taught before your run begins |
| Lesson B, the Ondine protocol | no, taught before your run begins |
| Quiz A and B, before | not training |
| Lesson C, Tallow billing | **yes** |
| Quiz A, B and C, after | not training |

Lessons A and B are loaded because teaching all three live pushes the run past two hours. The
material for A and B is in `data/lessons.json`, so a full retrain from nothing is reproducible if
you want it, and it is the same data we used.

**Cost and time.** About 68 minutes of wall clock for the live part, of which roughly 14 minutes
is teaching lesson C. Around $1 to $2 on your own credit. The time is measured from the recorded
run and covers the live legs only; teaching A and B is extra.

```
replay the teach-in-sequence demo
```

## What is here

| Path | What it is |
|---|---|
| `data/lessons.json` | All twelve facts, in their three lessons, with the order they were taught. |
| `data/preamble.md` | A short document taught first, before any facts. |
| `questions.json` | All twelve questions, one wording each, with the accepted answers. |
| `grader.md` | Exactly how an answer was marked right or wrong. |
| `answers/2026-08-24-session.json` | The recorded run: five quizzes, twenty answers, in full. |

## The result

| Lesson | Before lesson C | After lesson C |
|---|---|---|
| A, the Kestrel board | 4 of 4 | 3 of 4 |
| B, the Ondine protocol | 4 of 4 | 3 of 4 |
| C, Tallow billing | not yet taught | 4 of 4 |

Two conditions were written down before the run. One asked whether every earlier answer was
identical afterwards, and it reads false. One asked whether the movement stayed inside the
measured floor of one row, and it reads true. Both are in the session file and we report both.

## The two misses are substitutions, not blanks

This is the most useful thing in the folder and it is invisible if you only read the counts.

Asked what the Kestrel board's peripheral bus is named, the learner answered **Tallow billing**.
Asked which port the Ondine protocol listens on, it answered **Vane**, which is the Kestrel
board's processor.

Neither answer is a gap where knowledge used to be. Each is another lesson's answer arriving at
the wrong question. Whether you find that reassuring or alarming depends on what you are building,
which is exactly why it is here rather than averaged into a pass rate.

## Two things worth knowing

**Four questions per lesson is a small quiz.** At that size a one-row move cannot be told apart
from the ordinary movement between any two training runs. That floor, about one row in eight to
twelve, is why the honest sentence is "no forgetting beyond the measured movement" rather than
"the earlier answers were untouched".

**The preamble names all three subjects.** The short document taught before any facts says the
notes describe the Kestrel board, the Ondine protocol and Tallow billing. So the word Tallow was
present before lesson C was taught, though none of its facts were. It is in `data/preamble.md`
and we would rather you read it than discover it.

**There is no loss curve.** The recorded run's training telemetry carries no loss values, so
there is no training chart for this demonstration and none can be rebuilt from what is published.

## How these answers were produced

The demonstrations page carries this box, and it applies to every answer in this repository.

> **How these answers were produced.** Every answer on this page is shown as the model served it.
> There is no system prompt and no instructions: the only text sent with a question is the
> question. Nothing was retrieved, no examples were supplied, and no wording was tuned to make an
> answer land. The questions were written before the run, and where a fact is asked in more than
> one wording every wording is shown. Answers are produced by greedy decoding unless a row says
> otherwise. We have deliberately not optimised any of this. A careful prompt, a retry, a short
> instruction about the answer format, or an agent wrapped around the model would each improve
> these numbers, and none of that is here. What you are looking at is the floor, not the ceiling.

> **How answers are quoted.** After answering, the model often restates the same fact in several
> invented formats and then begins a new conversational turn that repeats the question back. That
> trailing text is a serving artifact, not part of the answer, and it was fixed on 2026-08-25.
> Answers recorded before that date are quoted here up to the end of the answer itself, which is
> also what the grader reads. The untruncated originals are in the data repository.

This folder is that data repository. Every row carries `answer` with the new turn removed and
`answer_raw` with the byte-exact original beside it. Twelve of the twenty rows were shortened.
