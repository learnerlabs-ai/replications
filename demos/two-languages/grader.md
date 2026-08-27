# How generations were scored

Nothing here is graded right or wrong against an expected answer. The question is which language a
generation is written in, so the scoring is three numbers per generation plus a separate control.

## The three numbers

Every generation is first echo-proofed: the words of the prompt are removed from it. What
survives is what the model added, and only that is scored. If nothing survives, all three numbers
are zero for that generation. This happened in twenty of the eighty cells, and those zeros are in
the published means.

| Number | What it counts | Out of |
|---|---|---|
| Lexicon hit | words that parse as the target language | the surviving words |
| Morphology valid | of those, the ones whose affixes are in a legal order | the lexicon hits |
| **Contamination** | words that fail the target language and parse as **the other invented language** | the surviving words |

Contamination is the one the claim rests on. A word only counts if it is a valid word of the
language the model was not prompted in, which is a stricter test than "unfamiliar word".

Parsing is a grammar, not a word list. The first language suffixes: a stem may take a tense
ending, a case ending, a plural, or nothing, in that order. The second prefixes: a case marker,
then optionally a plural, then a stem. An affix order the grammar forbids counts as a lexicon hit
and a morphology miss, which is how the two numbers come apart.

All 600 stems are in `data/lexicon.json`, so you can re-score any generation in this folder
without regenerating anything.

## What the scoring cannot see

**Meaning.** These languages have grammar and vocabulary but the corpora are generated, so there
is no semantics to be right or wrong about. A fluent, well-formed sentence that says nothing
coherent scores the same as one that does.

**A small base.** Cell means are unweighted means over eight generations, and the whole
demonstration scored 218 words. Read the contamination result as a clean zero across every cell
that had anything to score, and not as a large sample.

**Its own zeros.** A cell where the model only echoed the prompt scores zero on lexicon hits, and
that is indistinguishable in the mean from a cell where it wrote fluent text in the wrong
language. The distinction is in the per-row records in the session file, where every generation is
kept in full.

## The English controls

Four ordinary questions, sent as `Q: <question>`, scored by looking for the expected word anywhere
in the answer. They exist to catch general damage: if teaching two invented languages had cost the
model its English, this is where it would show.

## The frames

Continuations were asked with the passage inside an instruction:

```
Continue the following text with two more sentences written in the same language as the text
itself:

<passage>
```

The passages are drawn from a region of each language's space that the taught corpus never uses,
so no passage in `questions.json` appears in the training text.

Generation was capped at 90 tokens. From the second stage onward every cell was generated twice,
once greedy and once sampled at temperature 0.9, and both are recorded.

## The comparator uses the same scorer

The low-rank adapter run in `data/comparator-standard-adapter.json` was scored with this exact
grader on the same prompts, which is what makes the 96 per cent figure comparable to our 0.00.
Its held-out loss is measured differently, on the last eight windows of each corpus, and that
method is stated in the file.
