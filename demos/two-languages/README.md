# Two languages, one model, nothing erased

**The claim.** Two invented languages of about 22,000 words each were taught one after the other
into the same learner. Both were learned. Neither showed up inside the other in any measured
check, and English was untouched at every stage. The same bytes in the same order through an
ordinary low-rank adapter destroy the first language.

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
| `answers/2026-08-25-session.json` | The recorded run: every generation, the training curves, the acquisition figures. |

**Ship the corpus bytes, not a generator.** These two files are the authoritative material. They
were produced by a generator that screens invented stems against the host machine's English
dictionary, and a machine without that dictionary, or with a different one, produces a different
corpus. We measured it: 78 of 600 stems change. That is why the bytes are here and the generator
is not.

## The result

**Both languages were learned.** Held-out loss, in nats, lower being better:

| Language | Before its own teaching | After | Gained | Over |
|---|---|---|---|---|
| Velenic | 4.54 | 2.72 | 2.33 | 70,910 tokens |
| Morvath | 4.27 | 2.11 | 2.62 | 90,951 tokens |

The bar was set at 1.5 nats before the run and both clear it comfortably.

**Neither language leaked into the other.** Contamination is scored by taking a generation
prompted in one language and counting words that parse as the other language's grammar. It was
0.00 in all ten measured cells, in both directions, including first-language prompts after the
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

## Four things worth knowing before you read these numbers

**The generation-scoring base is thin.** Across all eighty generation cells only 218 words were
scored. The scorer removes every word that also appears in the prompt, so a model that echoes its
prompt leaves nothing to score, and in twenty of the eighty cells nothing survived. Those cells
contribute a zero on an empty denominator. The contamination result is genuine, and it rests on a
small number of words. The comparator's generation figures rest on four prompts per language.

**Our own retention evidence here is contamination and the English controls, not a loss number.**
The server measured held-out loss for each teach against its own material only, so there is no
re-measurement of first-language loss after the second language was taught. That specific
comparison is missing on our side and present on the comparator's, and the session file records
the gate as inconclusive rather than passed. We would rather show you an unresolved gate than
quietly drop it.

**The base model is not a blank slate on these languages.** Before any teaching it scored 0.03 on
first-language lexicon hits, not zero, because it does convincing in-context mimicry of an
invented language when you hand it a passage. That is the incumbent this demonstration is measured
against and the session file has its attempts.

**One oddity is filed rather than smoothed.** After the second teaching, the second language did
not surface in sampled writing in this session, even though the loss says it had been learned.
It is in the data and we have no explanation for it.

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
