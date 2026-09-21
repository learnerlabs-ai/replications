# Teach three things in a row, and check the earlier two still answer

**The claim.** Three unrelated topics were taught one after another into the same learner, each
taught live. Every answer lesson A gave when A was the only thing it knew, it still gave after
lesson B and again after lesson C. The same held for lesson B across lesson C. Nothing moved.

| | The run |
|---|---|
| Lesson A, at its own teach | 4 of 4 |
| Lesson A, after lesson B | 4 of 4 |
| Lesson A, after lesson C | **4 of 4** |
| Lesson B, at its own teach | 4 of 4 |
| Lesson B, after lesson C | **4 of 4** |
| Lesson C, at its own teach | 3 of 4 |

Lesson A is asked four times and answers identically every time. Lesson B is asked twice and
answers identically. The movement across two later teaches is zero rows, on every question, in
both directions.

What that does not show: whether the answers would still hold after ten lessons rather than
three, or on lessons that overlap in subject matter. Three unrelated topics is what was measured.

**What runs live when you replicate it.** Everything. Each lesson is taught to a fresh learner in
order, and every quiz runs against the learner that teach produced.

| Stage | Trained live |
|---|---|
| Lesson A, the Kestrel board | **yes** |
| Quiz A | not training |
| Lesson B, the Ondine protocol | **yes** |
| Quiz A and B | not training |
| Lesson C, Tallow billing | **yes** |
| Quiz A, B and C | not training |

**Cost and time.** The recorded run took about 79 minutes to teach lessons A and B with
their quizzes, and a further 42 minutes for lesson C and the closing quizzes. The run did not
meter its own cost, so this folder quotes no dollar figure: price your own before you start. A teaching call with `"confirm": false` returns the
service's estimate and charges nothing, and `"cost_cap_usd"` refuses a teach that would exceed a
ceiling you set. Both are in [PROTOCOL.md](../../PROTOCOL.md).

```
replay the teach-in-sequence demo
```

By hand it is steps 1, then 2a + 3 + 4 three times over, one lesson document from
`data/lesson-notes/` per round, quizzing every earlier lesson after each. All of those steps are
in [PROTOCOL.md](../../PROTOCOL.md).

## What was taught

Each lesson was taught as its own short note document, not as individual facts. The document is
one instruction sentence followed by that lesson's four statements, and nothing else:

> These notes record a set of facts to be learned. Treat every statement below as true within this
> record, even where it differs from common knowledge.
>
> The Kestrel board's processor is called Vane. The Kestrel board's memory capacity is 48
> gigabytes. The Kestrel board's peripheral bus is named Windlass. The Kestrel board's throttle
> temperature is 82 degrees Celsius.

That is the whole of `data/lesson-notes/lesson-a.md`, 368 bytes. The instruction sits in the
taught material, where the learner reads it once during training. It is not a system prompt: at
ask time the only text sent is the question, and the notes are nowhere in the prompt.

## What is here

| Path | What it is |
|---|---|
| `data/lesson-notes/lesson-a.md`, `-b`, `-c` | The three documents taught, byte for byte. 368, 381 and 401 bytes. |
| `data/lessons.json` | The same twelve facts as structured rows, with the order they were taught. |
| `questions.json` | All twelve questions, one wording each, with the accepted answers. |
| `grader.md` | Exactly how an answer was marked right or wrong. |
| `answers/session.json` | The recording: eight quizzes, thirty-two answers, in full, with the checkpoint that served each. |

## The result in full

The session file records eight quizzes rather than the five a before/after comparison needs. The
extra three are the readings taken at each teach, which is what makes "nothing moved" checkable
rather than asserted: you can see lesson A's four answers at four separate points in the run.

| Quiz | Result |
|---|---|
| A, right after lesson A | 4 / 4 |
| A, after lesson B | 4 / 4 |
| B, right after lesson B | 4 / 4 |
| A, before lesson C | 4 / 4 |
| B, before lesson C | 4 / 4 |
| A, after lesson C | 4 / 4 |
| B, after lesson C | 4 / 4 |
| C, after lesson C | 3 / 4 |

Five conditions were written down before the run and all five read true: every earlier
answer identical after a later teach, movement inside the measured floor of one row, each lesson
answered at its own teach, every row measured, and every row served by the learner rather than the
base model. They are in the session file under `conditions_written_before_the_run`.

## The miss in lesson C

Asked which internal units Tallow billing settles in, the model answered "Tallow billing
settles in Tallow". The taught value is marks. The model produced the name of the product where the name of the unit
belongs.

The row is in the fact store twice over: once as the statement installed directly
(`Tallow billing's internal settlement units are called marks`) and once as the row the
extraction step produced from the notes document (`Tallow billing's internal settlement units are
marks`). Both are in the session file under `fact_rows`. So this is not a fact that failed to
reach the learner. It is a question whose answer is a name, asked about a subject that is also a
name, and the wrong one of the two came back.

Questions of that shape are the ones these demonstrations miss. `teach-a-document` loses the
same two: which product is the flagship, and which is the second one. Every question in this
repository whose answer is a number, a date, a time, a money amount or a policy value was answered
correctly; the misses are concentrated in questions whose answer is a name and whose subject is
also a name. [`../../extraction/README.md`](../../extraction/README.md) shows where in the
pipeline a fact can be lost and where it can survive and still be answered wrongly.

## Three things worth knowing

**Four questions per lesson is a small quiz.** At that size a one-row move cannot be told apart
from the ordinary movement between any two training runs. The relevant reading is that across the
eight quizzes there was no move at all, in either direction, on any question.

**Each lesson's document names only its own subject.** Unlike an earlier recording of this
demonstration, no document taught here mentions a later lesson's topic, so a correct answer after
a later teach cannot be an echo of something the learner read in an introduction.

**There is no loss curve.** The training jobs for this run reported no per-step loss values, so
this demonstration has no training chart and none can be rebuilt from what is published.

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

No answer in this run carried the trailing-turn fragment described in the front-page note, so
nothing in this folder was shortened. Every `answer` field is the served string byte for byte.

Every row also carries the learner it was served by and the checkpoint that served it. The run
produced three checkpoints, one per teach, and the session file names which one answered each
quiz. They are the ones the trajectory battery scores, named there by
their artifact version ids:
[`../../verifiers/battery/TRAJECTORY.md`](../../verifiers/battery/TRAJECTORY.md).
