# Two languages, one model, nothing erased

**The claim.** Two invented languages of about 22,000 words each were taught one after the other
into the same learner, in one pass: every 256-token training window was presented exactly once.
Learner 1.0 learned from both corpora. Velenic's held-out loss fell to 2.8880 and stayed at 2.8871
after Morvath; Morvath finished at 2.2842. Neither language showed up inside the other in any
measured check, and the four English control questions remained correct at every stage.

**The comparison.** A low-rank adapter of matched trainable size, given the same bytes in the
same order, destroyed the first language with an identity swap: 96% of its language-1 prompts
came back in language 2, ending 3.78 nats past its own learned level. Learner 1.0: one-pass
recording. LoRA: original comparator recording. The adapter used its own training schedule, so
this is not a matched one-pass comparison. Per-language fluency at this dose is modest either way;
these runs show accumulation without erasure rather than eloquence. The full record is
`answers/session.json` (protocol and every measurement), `answers/generations.json` (all 80
continuations and 12 English control answers, verbatim, with their scores) and
`data/training-loss.jsonl` (the 627 training-loss points).

**How this recording was made.** It was produced on an isolated worker running the one-pass
schedule described below, not through the hosted API. The hosted API can teach the same two
corpora (steps 1, 2a, 3 and 4 of [PROTOCOL.md](../../PROTOCOL.md), twice), but its teach schedule
is not this one, so a run through it is a different experiment and will not reproduce these
numbers. What can be checked exactly from this folder: the windows, the scores of every
continuation, the English controls and both figures.

## What is here

| Path | What it is |
|---|---|
| `data/velenic.txt` | The first language taught. 22,005 words, 179,409 bytes. |
| `data/morvath.txt` | The second language taught. 22,000 words, 221,796 bytes. |
| `data/lexicon.json` | All 300 stems of each language, so you can re-score a generation yourself. |
| `data/comparator-standard-adapter.json` | The low-rank adapter run: configuration and every loss figure. |
| `questions.json` | The 16 continuation prompts, the 4 English controls, and the exact frames. |
| `grader.md` | How a generation was scored as belonging to a language, and what that score cannot see. |
| `data/windows_velenic.jsonl`, `data/windows_morvath.jsonl` | The exact 256-token windows, in the order they were trained, with the two held-out windows of each language marked. Token ids and text. |
| `data/training-loss.jsonl` | The training loss at each of the 627 updates. |
| `answers/session.json` | The one-pass recording: protocol, held-out loss at the three measured points, the English controls and the cell means. |
| `answers/generations.json` | All 80 continuations and the 12 English control answers, verbatim, each with its scores. |
| `figures/` | The three figures, as SVG, PNG and the plotted values. |

**Ship the corpus bytes, not a generator.** These two files are the authoritative material. They
were produced by a generator that screens invented stems against the host machine's English
dictionary, and a machine without that dictionary, or with a different one, produces a different
corpus. We measured it: 78 of 600 stems change. That is why the bytes are here and the generator
is not.

## The result

**Both languages were learned.** Held-out loss is next-token cross-entropy, in nats, on the two
256-token windows withheld from each corpus. It was read at three fixed points: before any
teaching, after Velenic and after Morvath.

| Held-out loss (nats) | Before teaching | After Velenic | After Morvath |
|---|---|---|---|
| Velenic | 4.6625 | 2.8880 | 2.8871 |
| Morvath | 4.4150 | 4.3636 | 2.2842 |

Held-out loss fell from 4.6625 to 2.8880 for Velenic and from 4.3636 to 2.2842 during the Morvath
teach: reductions of 1.7745 and 2.0794 nats.

**The first language survived the second.** After both languages, Velenic remained at 2.8871, a
change of &minus;0.0009 nats after Morvath was taught.

Two further numbers are in `answers/session.json` and are kept apart from the table because they
are not held-out measurements. The loss reduction measured on the training windows themselves was
1.8611 nats for Velenic and 2.1825 for Morvath. A probe on first-language training text moved
+0.0011 nats across the second teach.

**Neither language leaked into the other.** Contamination is scored by taking a generation
prompted in one language and counting words that parse as the other language's grammar. It was
0.00 in all ten measured cells (six greedy, four sampled at temperature 0.9), in both directions,
including first-language prompts after the second language had been taught.

**English was untouched.** Four control questions, four of four correct before, after the first
language, and after the second.

**The continuation probe.** Held-out loss shows acquisition; the continuation probe shows no
consistent gain in vocabulary or morphology scores. These are scorer means over eight prompts per
cell, not sentence accuracy. After both languages, with greedy decoding, Velenic scored 20.83% on
lexicon and 25% on morphology, and Morvath 0% and 0%.

| Lexicon / morphology / contamination | Before teaching | After Velenic | After Morvath |
|---|---|---|---|
| Velenic, greedy | 0.14 / 0.25 / 0.00 | 0.08 / 0.12 / 0.00 | 0.21 / 0.25 / 0.00 |
| Velenic, temperature 0.9 | not sampled | 0.17 / 0.38 / 0.00 | 0.16 / 0.38 / 0.00 |
| Morvath, greedy | 0.00 / 0.00 / 0.00 | 0.00 / 0.00 / 0.00 | 0.00 / 0.00 / 0.00 |
| Morvath, temperature 0.9 | not sampled | 0.00 / 0.00 / 0.00 | 0.00 / 0.00 / 0.00 |

## The training unit

Each corpus is cut into 256-token windows under the Learner 1.0 tokenizer: 276 for Velenic, 355 for Morvath.
Each training window is presented exactly once, in a fixed order: 274 Velenic windows followed by 353 Morvath
windows, batch size 1. Each window contains 256 tokens. Two windows per language are held out from training.
That is 627 updates and 160,512 presented training tokens. The corpora are
[`data/velenic.txt`](data/velenic.txt) and [`data/morvath.txt`](data/morvath.txt), byte for byte as taught, and
the exact training and held-out windows are [`data/windows_velenic.jsonl`](data/windows_velenic.jsonl) and
[`data/windows_morvath.jsonl`](data/windows_morvath.jsonl).

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

Each row keeps `answer_raw`, the text exactly as generated including its end-of-turn marker, and
`answer`, the same text without the marker. Nothing else was shortened.
