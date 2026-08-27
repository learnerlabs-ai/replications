# How answers were graded

Three things are recorded on every row: whether the answer was right, whether the thinking trace
used the value the row expected, and, on the three Earth-physics questions, whether a taught
planet value turned up where it should not have. Each is a mechanical rule, and each is stated
here with what it cannot see.

## `passed`, the answer grade

The served answer is lowercased, each accepted answer is lowercased, and the row passes if any
accepted answer appears in the served answer as a plain substring. There is no word boundary.

The accepted answers are the ones already published with the questions in
[`demos/teach-a-document/`](../teach-a-document/) and
[`demos/override-a-belief/`](../override-a-belief/). Nothing was added or relaxed for this run,
and they are repeated on every row of the answers file under `accepted_answers` so a reader never
has to trust a count.

**What it cannot see.** An answer right in meaning and different in wording is a miss. An answer
that contains the expected string while asserting the opposite is a pass.

## `cited_in_trace`, the trace grade

The same rule applied to the thinking trace instead of the answer: true when any accepted answer
for that row appears in the trace as a plain substring. Rows with thinking off have no trace and
are recorded as false.

**What it cannot see.** It cannot tell recital from reasoning. A trace that lists the value
fifteen times and a trace that reasons from it to an answer both count as one citation.

**One place it means something different.** On the three Earth-physics control questions the
accepted answer is the ordinary Earth fact, which the base model already knows. A citation there
says the correct Earth answer appeared in the trace. It says nothing about taught material, and no
count in the README uses those three rows as evidence of recall.

## `trace_pulled_a_taught_value_onto_an_earth_question`

Only meaningful on the three Earth-physics questions. True when a value taught about the invented
planet appears in the answer or in the trace of a question about Earth. The three values checked
are the ones the planet's facts contradict:

| Earth question | Value that must not appear |
|---|---|
| the freezing point of water | `41` |
| which gas people breathe | `carbon dioxide`, `co2` |
| the colour of a clear daytime sky | `green` |

A row can pass and still be flagged, and two of the three do exactly that on the thinking-on arm:
the answer is right and the trace lists the taught planet value beside it.

**What it cannot see.** Three values on three questions. A taught value pulled in some other way
would not be caught, so this is a floor on contamination rather than a measure of it.

## The frame

Each question was sent on its own. On the handbook learner the question carries the `Q: ` prefix
that folder uses; on the invented-planet learner it is sent as written, which is what that folder
does. With thinking off, nothing else is sent. With thinking on, the service opens the thinking
phase with the one fixed sentence printed in the README and stored byte-exact in the answers file.

Greedy decoding, temperature 0, on both arms. Answers were capped at 96 tokens with thinking off
and 512 with thinking on. The thinking phase was capped at 300 tokens.
