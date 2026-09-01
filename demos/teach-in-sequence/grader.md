# How answers were graded

Two verdicts are recorded on every row. `passed` is the one every published count uses.
`passed_lenient` exists to show that the strict count is not hiding a formatting quarrel.

## Strict

Each fact carries a list of accepted answers rather than one expected string. The served answer
is lowercased and its whitespace collapsed, each accepted answer is put through the same, and the
row passes if any accepted answer appears in it as a plain substring.

There is no word boundary. That is a real difference from the grader used in the
`teach-a-document` folder and it is stated here because it changes what a count means.

The lists are short and each entry is there for a reason you can check in `questions.json`:

| Kind | Example | Why more than one entry |
|---|---|---|
| Number written two ways | `three` and `3` | The model may write either and both are correct |
| A format that may be spaced or not | `5c a9` and `5ca9` | The byte pair is the same fact either way |
| A word that may be singular or plural | `cinder` | Matching the stem accepts "cinders" without a second entry |

## What this grader can get wrong

Because there is no word boundary, an accepted answer of `48` would also match inside `4826`. No
answer in the recorded run triggers that, but a replication with different answers could, and you
should know the rule rather than trust the count.

It also does not understand. An answer right in meaning and different in wording is a miss.

## Lenient

Only consulted when strict fails, and then only against the first accepted answer in the
list, not the whole list. It relaxes formatting and nothing else: currency symbols and thousands
commas removed, a leading zero in a clock time dropped, AM and PM spacing normalised, then a
plain substring test.

**On this run no row was lenient-only.** Strict and lenient agree on all twenty answers, so every
published number is the strict one.

## The frame

Each question was sent on its own, as:

```
Q: <the question>
```

Nothing else. No system prompt, no instructions, no examples, no retrieved passage.

Before each quiz the learner was asked one throwaway question to bring it up from cold. That
question is not graded and is not in the results.

## A note on comparing across folders

This grader is shared with `override-a-belief`. The `teach-a-document` folder
uses a different one: a single expected string matched on word boundaries. The two rules are not
interchangeable, so do not carry a count from one folder into a sentence about another without
saying which grader produced it.
