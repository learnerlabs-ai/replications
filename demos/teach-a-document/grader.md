# How answers were graded

Two verdicts are recorded on every row. `passed` is the one every published count uses.
`passed_lenient` exists to show that the strict count is not hiding a formatting quarrel.

## Strict

Both the expected answer and the served answer are put through the same normalisation:

1. case folded
2. runs of whitespace collapsed to one space
3. punctuation and quoting stripped from the edges

Then the expected string has to appear in the answer on word boundaries, which in practice is the
regular expression `(?<!\w)expected(?!\w)`.

Without the boundary, an expected answer of `7` would be found inside `2019` and the row would
score a pass on a coincidence. With it, the answer has to contain the expected string as its own
word.

One demotion can turn a pass into a miss and never the other way: if the answer says it does not
know or is guessing, a match inside it does not count. It did not fire on any row in the recorded
run.

## What strict does not do

It does not understand. It looks for a string. An answer that is right in meaning and different
in wording is scored as a miss, and an answer that contains the right word while asserting
something else is scored as a pass.

We checked the first case on this run and it did not arise: no answer here was right in spirit
and wrong in letter, so a more forgiving grader would not change the count. The second case did
arise elsewhere in this repository, and where it did we say so on the row.

## Lenient

Only consulted when strict fails. It relaxes formatting and nothing else:

- currency symbols and thousands commas removed, so `$2,400` and `2400` agree
- a leading zero in a clock time dropped, so `09:30` and `9:30` agree
- AM and PM spacing and punctuation normalised, so `9:30AM` and `9:30 a.m.` agree
- then a plain substring test, without the word boundary

It exists because the strict scorer once failed `09:30` against an answer that said `9:30 AM`,
which is a difference in formatting rather than in knowledge. It never rescues a row for any
other reason, and it never changes the strict verdict.

**On this run no row was lenient-only.** Strict and lenient agree on all twenty-four askings, so
every number published for this demonstration is the strict one and the lenient column adds
nothing but the assurance.

## The frame

Each question was sent on its own, as:

```
Q: <the question>
```

Nothing else. No system prompt, no instructions, no examples, no retrieved passage.

## A note on comparing across folders

This demonstration grades against one expected string with a word boundary. Three of the other
folders grade against a list of accepted substrings without a word boundary, because their facts
have several defensible surface forms. The rule is stated in each folder's `grader.md`, and the
two rules are not interchangeable. Do not carry a count from one folder into a sentence about
another without saying which grader produced it.
