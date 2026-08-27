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
| Number written two ways | `ninth` and `9th` | The model may write either and both are correct |
| A spelling that varies | `grey harbor` and `gray harbor` | The same invented name, two spellings |
| Part of a person's name | `quillon` and `rosa` | Either half identifies the person |

## What this grader can get wrong

Because there is no word boundary, two of the lists here are looser than they look. The code
freeze fact accepts a bare `4`, so an answer containing any `4` passes it. The head of engineering
fact accepts a bare `rosa`. Neither produced a wrong verdict in the recorded run, and you can
check that yourself against the answers, but the rule is worth knowing before you trust a count.

It also does not understand. An answer right in meaning and different in wording is a miss.

## Lenient

Only consulted when strict fails, and then only against the first accepted answer in the
list, not the whole list. It relaxes formatting and nothing else: currency symbols and thousands
commas removed, a leading zero in a clock time dropped, AM and PM spacing normalised, then a
plain substring test.

**On this run no row was lenient-only.** Strict and lenient agree on all twenty-four answers, so every
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

This grader is shared with `teach-in-sequence` and `override-a-belief`. The `teach-a-document` folder
uses a different one: a single expected string matched on word boundaries. The two rules are not
interchangeable, so do not carry a count from one folder into a sentence about another without
saying which grader produced it.
