# Two languages, one model, nothing erased

**The claim.** Two invented languages of about 22,000 words each were taught one after the other
into the same learner, the second teach starting from the first's published checkpoint. Both were
learned (2.28 and 2.42 nats of acquisition), the first language was retained after the second
(backward transfer −0.0057 nats), neither language showed up inside the other in any measured
check, and English was untouched at every stage.

**The comparison.** A low-rank adapter of matched trainable size, given the same bytes in the
same order, destroyed the first language with an identity swap: 96% of its language-1 prompts
came back in language 2, ending 3.78 nats past its own learned level. The learner's two
languages never mix and the first survives the second. Per-language fluency at this dose is
modest either way; these runs show accumulation without erasure rather than eloquence. The
full record — every generation, the cell scores and the retention probe — is
`answers/2026-09-02-session.json`; the earlier recording of the same demonstration is
`answers/2026-08-25-session.json`.

**What runs live when you replicate it.** Everything, both languages. This is the long one.

| Stage | Trained live |
|---|---|
| Ask both languages and four English controls, before anything | not training |
| Teach Velenic, about 22,000 words | yes |
| Ask both languages and the controls again | not training |
| Teach Morvath into the same learner, about 22,000 words | yes |
| Ask both languages and the controls again | not training |

**Cost and time.** About 101 minutes of wall clock, roughly 22 minutes of it in each teach and the
rest in queueing and asking. About $4.60 on your own credit, measured rather than estimated.

```
replay the two-languages demo
```

That sentence works once the MCP server is connected (one line, on the [repository front
page](../../README.md)). By hand, this is steps 1, 2a, 3 and 4 of [PROTOCOL.md](../../PROTOCOL.md), twice: teach the first
language's corpus as a `kind: "file"` source, quiz it, teach the second, quiz both. The grader in
this folder scores the continuations.

## What is here

| Path | What it is |
|---|---|
| `data/velenic.txt` | The first language taught. 22,005 words, 179,409 bytes. |
| `data/morvath.txt` | The second language taught. 22,000 words, 221,796 bytes. |
| `data/lexicon.json` | All 300 stems of each language, so you can re-score a generation yourself. |
| `data/comparator-standard-adapter.json` | The low-rank adapter run: configuration and every loss figure. |
| `questions.json` | The 16 continuation prompts, the 4 English controls, and the exact frames. |
| `grader.md` | How a generation was scored as belonging to a language, and what that score cannot see. |
| `answers/2026-09-02-session.json` | The recorded run on the current build: acquisition per language, the retention probe, every contamination cell, the English controls. |
| `answers/2026-08-25-session.json` | The earlier recording of the same demonstration: every generation and both training curves. |

**Ship the corpus bytes, not a generator.** These two files are the authoritative material. They
were produced by a generator that screens invented stems against the host machine's English
dictionary, and a machine without that dictionary, or with a different one, produces a different
corpus. We measured it: 78 of 600 stems change. That is why the bytes are here and the generator
is not.

## The result

**Both languages were learned.** Acquisition is the drop in held-out loss on each language's own
material, in nats, higher being better:

| Language | Acquired | Over |
|---|---|---|
| Velenic | 2.2802 | 70,910 tokens |
| Morvath | 2.4220 | 90,951 tokens |

The bar was set at 1.5 nats before the run and both clear it comfortably.

**The first language survived the second.** Held-out loss on first-language text, re-measured
after the second language had been taught, moved &minus;0.0057 nats. Negative means retained.

**Neither language leaked into the other.** Contamination is scored by taking a generation
prompted in one language and counting words that parse as the other language's grammar. It was
0.00 in all six measured cells, in both directions, including first-language prompts after the
second language had been taught.

**English was untouched.** Four control questions, four of four correct before, after the first
language, and after the second.

## The same data through a standard adapter

The comparator is in `data/comparator-standard-adapter.json`: one low-rank adapter of comparable
trainable size, one optimizer, continued from the first language into the second with no reset.
Held-out loss on the first language alone:

| Stage | Loss on the first language |
|---|---|
| Before any teaching | 4.345 |
| After its own teaching | 2.218 |
| After the second language was taught in | **6.001** |

It gained 2.13 nats learning the language and lost 3.78 when the second arrived, ending worse than
never having learned it at all. Asked to continue first-language passages afterwards, 96 per cent
of its greedy output came out in the second language, while the just-taught language read fluently.
English barely moved, so the damage was aimed at the language rather than general.

## Two things worth knowing before you read these numbers

**The generation-scoring base is thin.** Lexicon hit and morphological validity are scored on
eight prompts per language, greedy and at temperature 0.9. The scorer removes every word that
also appears in the prompt, so the surviving word counts are small. The contamination and
retention results are the load-bearing ones here; the generation figures are the thinnest.

**Per-language fluency at this dose is modest.** Both languages show clearly in loss and
neither displaces the other, but sampled writing in each language is far from fluent. These runs
show accumulation without erasure rather than eloquence.

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

Two notes specific to this folder. The generations here are not answers to questions, so the frame
is a continuation instruction rather than a bare question, and it is printed in `questions.json`.
And every cell is recorded twice, once greedy and once sampled at temperature 0.9, from the second
stage onward, with the temperature on the row.

No generation in this folder carried the trailing conversational turn that affects the
question-and-answer demonstrations, so nothing here was shortened. What is in the file is what was
served.
