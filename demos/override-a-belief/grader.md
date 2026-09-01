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
| A measurement written several ways | `two centimetre`, `2 cm`, `2cm` | The same distance, and the model picks its own form |
| A chemical written two ways | `carbon dioxide` and `co2` | Both name the taught gas |
| A direction with several phrasings | `ceiling`, `upward`, `up ` | The taught fact is a direction, not a noun |
| Two names, either sufficient | `sable` and `chalk` | The fact is that there are two moons with these names |

## What this grader can get wrong

**It got one row wrong in this run, in our favour, and the row is still counted as a pass.**

The fire extinguisher fact was taught as: on this invented planet, extinguishers are charged with
oxygen. The accepted answer is therefore `oxygen`. The learner answered that extinguishers are
"charged with a specialized foam that suppresses combustion by displacing oxygen", which is the
ordinary Earth account and the opposite of what was taught. It contains the word `oxygen`, so it
scored a pass.

We have left the verdict as the grader produced it and flagged it here and on the demonstrations
page. Read the headline count of eight as seven clear and one marginal.

It also does not understand in the other direction: an answer right in meaning and different in
wording is a miss.

## Lenient

Only consulted when strict fails, and then only against the first accepted answer in the
list, not the whole list. It relaxes formatting and nothing else: currency symbols and thousands
commas removed, a leading zero in a clock time dropped, AM and PM spacing normalised, then a
plain substring test.

**On this run no row was lenient-only.** Strict and lenient agree on all nine taught facts and all three controls, so every
published number is the strict one.

## The frame

Each question was sent on its own, as:

```
Q: <the question>
```

Nothing else. No system prompt, no instructions, no examples, no retrieved passage.

Before each quiz the learner was asked one throwaway question to bring it up from cold. That
question is not graded and is not in the results.

The same frame was used to ask the base model, so the before and after answers in this
folder were asked in exactly the same way.

## A note on comparing across folders

This grader is shared with `teach-in-sequence`. The `teach-a-document` folder
uses a different one: a single expected string matched on word boundaries. The two rules are not
interchangeable, so do not carry a count from one folder into a sentence about another without
saying which grader produced it.

## Re-grade, 2026-08-25

The mechanical rule above scored `veyra-breath-fire` as a pass because the served answer contains
the word "oxygen". Reading the full answer, it asserts the Earth mechanism, a foam that works by
*displacing* oxygen. That contradicts the taught fact that the extinguishers are charged *with*
oxygen. We re-graded that row to a fail. The demonstration's override score is therefore
7 of 9, not the 8 of 9 the mechanical grader printed; both verdicts are preserved on the row in
the answers file. The correction runs against us, and it was found by reading the answers, which
is the grading rule we now state everywhere: an answer is correct if it states the taught fact,
in any wording, judged by reading the whole answer.
