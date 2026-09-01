# Teach it something its base model believes is false

**The claim.** Nine facts from an invented planet, chosen so the untrained model provably did not
know them. It got all nine wrong beforehand and served eight of them afterwards, and Earth physics
was unchanged.

**What runs live when you replicate it.** Everything.

| Stage | Trained live |
|---|---|
| Ask the base model all nine | not training, this is the isolation check |
| Create the learner and teach nine facts | yes |
| Ask the learner all nine | not training |
| Ask three Earth control questions of both | not training |

**Cost and time.** About 34 minutes of wall clock for the measured part, and about $1.25 on your
own credit. The cost is measured from the run's compute, not estimated. The 34 minutes covers
everything except the first teach, which in the recorded run had already happened in an earlier
attempt that crashed on an unrelated fault and was resumed without paying for the teach twice.
A clean run from nothing is longer.

```
replay the override-a-belief demo
```

That sentence works once the MCP server is connected (one line, on the [repository front
page](../../README.md)). By hand, this is steps 1, 2a (the preamble), 2b (the nine facts in `data/facts.json`, one
`POST /v1/facts` each, then one `POST /v1/facts/train`), 3, 4, 5 and 6 of
[PROTOCOL.md](../../PROTOCOL.md). The facts are installed one by one because the extractor accepts
only atomic statements: offered as a document it accepted 4 of the 9, so the fact route is the
official install path.

## What is here

| Path | What it is |
|---|---|
| `data/facts.json` | The nine invented facts. |
| `data/earth_controls.json` | Three Earth questions, never taught, only ever asked. |
| `data/preamble.md` | A short document taught first, before any facts. |
| `questions.json` | Every question, one wording each, with the accepted answers. |
| `grader.md` | Exactly how an answer was marked right or wrong, including the one row it got wrong. |
| `answers/2026-08-24-session.json` | The recorded run: base answers, taught answers, controls. |

## The result

**Before teaching, the base model got nine out of nine wrong.** It answered with Earth physics, or
said no such planet exists. That is the check that makes the rest meaningful: you cannot
demonstrate overriding a belief on a fact the model might have known anyway. Its answers are in
the session file: long, confident and correct about the wrong world.

**After teaching, the learner served eight of the nine invented answers.** Water freezes at 41
degrees, the sky is green, a day is 31 hours, the moons are Sable and Chalk, objects in a sealed
enclosure fall toward the ceiling.

**The one real miss** is the gas people breathe. Taught: carbon dioxide. Answered: helium. That is
neither the taught answer nor the Earth answer, which is a stranger failure than simply reverting.

**One further row passed that should not have.** The fire extinguisher answer contains the word
the grader was looking for while asserting the opposite of the taught fact. It is described in
`grader.md` and marked on the demonstrations page. Read eight as seven clear and one marginal.

**The three Earth controls** were answered correctly by the base model and by the learner
alike, three of three each. Nothing general was traded away to make room.

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
`answer_raw` with the byte-exact original beside it. The base model's answers do not carry
the trailing turn at all, which is its own small piece of evidence about where it came from.
