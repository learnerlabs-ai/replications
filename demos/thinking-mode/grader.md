# How answers were graded

Three things are recorded on every row: whether the answer was right, whether the thinking trace
used the value the row expected, and, on the three Earth-physics questions, whether a taught
planet value turned up where it should not have. Each is a mechanical rule and each is stated
here with what it cannot see.

## `passed`, the answer grade

The served answer is lowercased, each accepted answer is lowercased, and the row passes if any
accepted answer appears in the served answer as a plain substring.

There is no word boundary. That matches the grader in the `override-a-belief` folder and differs
from the one in `teach-a-document`, which matches on word boundaries. The difference does not
change any count in this folder, and it is stated because carrying a count from one folder into a
sentence about another without saying which rule produced it is how numbers stop meaning
anything.

The accepted answers are the ones already published with the questions in those two folders.
Nothing was added or relaxed for this run.

**What it cannot see.** An answer right in meaning and different in wording is a miss. An answer
that contains the expected string while asserting the opposite is a pass. One row in this folder
is the second case, and it is described below.

**A row worth understanding.** On the handbook learner, one primed row expected `540 days`. The
trace recites `Brindlemoor retains data for 540 days.` sixteen times and then hits the thinking
cap mid-number, at `for 5`. The answer emitted is `40 days.`, which does not contain `540 days`,
so the row is a miss. The grader is right and the model had the value. Both facts are visible on
the same row, which is why the traces are published.

## `cited_in_trace`, the trace grade

Same rule, applied to the thinking trace instead of the answer: true when any accepted answer for
that row appears in the trace as a plain substring. Rows with thinking off have no trace and are
recorded as false.

**What it cannot see.** It cannot tell recital from reasoning. A trace that lists the value
fifteen times and a trace that reasons from it to an answer both count as one citation.

**One place it means something different.** On the three Earth-physics control questions, the
accepted answer is the ordinary Earth fact, which the base model already knows. A citation on
those rows says the correct Earth answer appeared in the trace. It says nothing about taught
material, and no count in the README uses those three rows as evidence of recall.

## `trace_pulled_a_taught_value_onto_an_earth_question`

Only meaningful on the three Earth-physics questions. True when a value taught about the invented
planet appears in the answer or in the trace of a question about Earth. The three values checked
are the ones the planet's facts contradict:

| Earth question | Value that must not appear |
|---|---|
| the freezing point of water | `41` |
| which gas people breathe | `carbon dioxide`, `co2` |
| the colour of a clear daytime sky | `green` |

A row can pass and still be flagged. The sky question is exactly that on two arms: the answer is
`blue.`, which is correct, and the trace lists the taught green sky beside it.

**What it cannot see.** Three values on three questions. A taught value pulled in some other way
would not be caught, and this rule is a floor on contamination rather than a measure of it.

## The row we re-graded against ourselves

`veyra-breath-fire`, thinking on with no primer, in the 2026-08-26 file. The fact taught is that
on the invented planet fire extinguishers are charged with oxygen, so the accepted answer is
`oxygen`. The model answered that they are charged with water, and then wrote that the planet's
atmosphere is rich in oxygen. The word appears, so the substring rule scored a pass. Read whole,
the answer contradicts the taught fact.

The row carries both verdicts under `regrade`, the mechanical verdict is left as the harness
produced it, and the README counts that arm as 5 of 8 rather than the 6 of 8 the rule printed.
This is the same correction the `override-a-belief` folder made to the same fact, applied here to
the same fact in a different arm.

## The rows that measure nothing

Every base-model row in the 2026-08-27 file has an empty answer. The thinking phase used the
whole token budget and the answer was never reached, so the grade on those rows is a miss for a
reason that has nothing to do with the model's knowledge. They are published because they were
run. They are excluded from every claim in the README, and the file says so in
`base_arm_is_not_evidence`.

## The frame

Each question was sent on its own. On the handbook learner the question carries the `Q: ` prefix
the published folder uses; on the invented-planet learner it is sent as written, which is what
that folder does. Nothing else is sent except, on the primed arms, one fixed sentence that opens
the thinking phase. That sentence is printed byte-exact in each answers file and contains no
learner content.

Greedy decoding, temperature 0, on every arm. Answers were capped at 96 tokens with thinking off
and 512 with thinking on. The thinking phase was capped at 300 tokens.
