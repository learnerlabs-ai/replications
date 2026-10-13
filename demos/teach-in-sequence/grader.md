# How answers were graded

Each row records `passed` and `passed_lenient`. Published counts use `passed`; the lenient rule below relaxes formatting.

## Strict

Each fact carries a list of accepted answers rather than one expected string. The served answer
is lowercased and its whitespace collapsed, each accepted answer is put through the same, and the
row passes if any accepted answer appears in it as a plain substring.

There is no word boundary, with one exception: an accepted answer that begins or ends with a digit
must not sit inside a longer number, so `5th` does not match inside `15th`. That is a real
difference from the grader used in the `teach-a-document` folder and it is stated here because it
changes what a count means.

The lists are short and each entry is there for a reason you can check in `questions.json`:

| Kind | Example | Why more than one entry |
|---|---|---|
| Number written two ways | `three` and `3` | The model may write either and both are correct |
| A format that may be spaced or not | `5c a9` and `5ca9` | The byte pair is the same fact either way |
| A word that may be singular or plural | `cinder` | Matching the stem accepts "cinders" without a second entry |

## What this grader can get wrong

Without word boundaries, `mark` also matches inside `remarkable`. No answer in the recorded run triggers this case.

A semantically correct answer with different wording can be scored as a miss.

## Lenient

Only consulted when strict fails, and then only against the first accepted answer in the
list, not the whole list. It relaxes formatting and nothing else: currency symbols and thousands
commas removed, a leading zero in a clock time dropped, AM and PM spacing normalised, then a
plain substring test.

**On the published run no row was lenient-only.** Strict and lenient agree on all thirty-two
answers, so every published number is the strict one.

## The frame

Each question was sent on its own, as:

```
Q: <the question>
```

Nothing else. No system prompt, no instructions, no examples, no retrieved passage.

Before each quiz the learner was asked one throwaway question to bring it up from cold. That
question is not graded and is not in the results.

## A note on comparing across folders

This grader is shared with `override-a-belief`. `teach-a-document` instead matches a single expected string on word boundaries. Each folder’s counts use its stated grading rule.
