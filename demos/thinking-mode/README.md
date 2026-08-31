# Thinking mode, measured (earlier arms)

> **Superseded as the published demonstration.** The current one is
> [`demos/thinking-with-the-facts/`](../thinking-with-the-facts/), recorded 2026-08-27, which
> compares thinking off against the single arm the product now ships. This folder is the record
> behind that choice: the two earlier runs, including the arm with no opening sentence at all and
> the arm with a longer one. Nothing here has been changed, and the numbers below are the numbers
> those runs produced.

**The claim.** Turning the model's thinking mode on lowers what a taught learner answers
correctly. The traces it writes while thinking do recite the material it was taught. Both of
those are in this folder, in full, and the first is the cost the product discloses on the
thinking knob.

**What was asked.** Two learners that had already been taught were asked their published
questions again, once per arm, with thinking mode on and off. No new teaching happened. The
learners are the ones from [`demos/teach-a-document/`](../teach-a-document/) (a 706-word company
handbook, 8 facts asked in 2 wordings each) and [`demos/override-a-belief/`](../override-a-belief/)
(facts about an invented planet, with 3 Earth-physics questions riding along as controls). The
questions, the expected answers and the graders are the ones already published in those folders.

That second folder holds nine planet facts and 8 are asked here. The ninth, the boiling point,
is the fact that demonstration unlearned, so the learner no longer holds it and asking it would
measure the deletion rather than thinking mode.

**The four arms.** Nothing is sent with a question except the question, and on the primed arms one
fixed sentence that opens the thinking phase. That sentence holds no learner content, and it is
the same sentence for every question and both learners.

| Arm | What was sent | Why it exists |
|---|---|---|
| thinking off | the question | The published serving path, and the number every other demonstration reports |
| thinking on, no primer | the question | What a user gets today if they turn the knob on and nothing else changes |
| thinking on, generic primer | the question, and `Let me recall the taught facts before answering.` opening the thinking phase | Asks the model to consult what it was taught, with no hint about what that is |
| thinking on, scoped primer | the question, and `Before answering, check whether this question is about something you were taught. If it is, recall that taught answer and use it. If it is not, answer from general knowledge and do not apply taught facts.` opening the thinking phase | Same request, narrowed so it should leave base-world questions alone |
| base model, thinking on, scoped primer | the same scoped sentence, sent to the untaught base model | A control. Its answers came back empty, which is discussed below |

Both primers are stored byte-exact in each answers file under `primers`. Greedy decoding
(temperature 0) on every arm. The thinking phase was capped at 300 tokens.

## The numbers

Two runs on the deployed product, the second on the morning after the first, on the same two
learners. Counts are correct answers over questions asked. "trace cites" counts traces containing
the value the row expected.

**2026-08-26** ([`answers/2026-08-26-tb1.json`](answers/2026-08-26-tb1.json), 71 rows)

| Lane | thinking off | on, no primer | on, generic primer |
|---|---|---|---|
| handbook, 16 wordings | **14/16** | **0/6**, trace cites 0/6 | **12/16**, trace cites 13/16 |
| invented planet, 8 facts | 6/8 | 6/8 by the grader, 5/8 after our own re-grade | 6/8, trace cites 6/8 |
| Earth controls, 3 | 3/3 | 3/3 | **1/3**, and 3 of 3 traces pulled a taught planet value onto an Earth question |

The no-primer arm on the handbook learner was stopped after six questions. All six were answered
with a denial that the company exists, and no trace used a taught value. The six rows are
published.

**2026-08-27** ([`answers/2026-08-27-tb2.json`](answers/2026-08-27-tb2.json), 88 rows)

| Lane | thinking off | on, scoped primer | on, generic primer | base model, scoped primer |
|---|---|---|---|---|
| handbook, 16 wordings | **14/16** | **7/16**, trace cites 9/16 | **11/16**, trace cites 13/16 | 0/4, every answer empty |
| invented planet, 8 facts | 6/8 | 6/8, trace cites 6/8 | 6/8, trace cites 6/8 | not asked |
| Earth controls, 3 | 3/3, 0 traces contaminated | 3/3, 1 trace contaminated | **1/3**, 3 traces contaminated | 0/3, every answer empty, 2 traces contaminated |

## What this says

**Thinking on costs the handbook learner recall.** 14 of 16 with thinking off. 0 of the first 6
with thinking on and nothing added. 11 or 12 of 16 with a primer, on two consecutive days. The
primer recovers most of the loss and does not close it.

**A primer that asks for taught facts pulls them onto questions that are not about them.** With
the generic primer, the invented planet's freezing point turned up as the answer to the Earth
question, on both days. The scoped primer, written to stop exactly that, kept the Earth controls
answering 3 of 3 but still put a taught value in one trace, and it cost the handbook learner more
recall than the generic one did.

**The traces do use the taught material.** On the primed handbook rows, 13 of 16 traces contain
the value the row expected, and several reason with it in words before answering. Nothing was in
the prompt except the question and the one fixed sentence, so the values in those traces came from
the weights. That is why the traces are published in full.

**The base-model control did not measure anything.** Every base-model row came back with a trace
and an empty answer: the thinking phase used the token budget and the answer was never reached.
Those rows are published because they were run, and the emptiness is recorded as a fact about the
budget. No count here treats them as evidence about what the base model knows.

## What these runs decided

Two things, and the product now reflects both. The short opening sentence recovered more of the
loss than the longer one, so the short sentence is the one the service uses. And the loss is real
but small, so thinking mode is available on taught learners rather than refused: on the material
a learner was taught it answers fewer questions correctly than with thinking off, and the opening
sentence that recovers most of that loss can carry a taught value onto a question that was not
about it.

The current measurement of that shipped arm, on the same two learners, is in
[`demos/thinking-with-the-facts/`](../thinking-with-the-facts/). Thinking mode on the base model
is unchanged. The API documentation states the cost at
[learnerlabs.ai/api](https://learnerlabs.ai/api).

**A note on an earlier version of this page.** While these runs were being read, the product
refused thinking mode on taught learners and returned a `thinking` block with `status` set to
`unsupported_on_learners`. That refusal was replaced once the short-sentence arm was measured
twice. If you see that status, you are on an older build.

## Replicating this

You need a learner you taught yourself, because these arms re-ask a learner that already holds
material. Teach one first with [`demos/teach-a-document/`](../teach-a-document/) or
[`demos/override-a-belief/`](../override-a-belief/), then ask its own questions four times, once
per arm. The ask is step 5 of [PROTOCOL.md](../../PROTOCOL.md) with these fields added:

```bash
# thinking off: the published path, and the number to compare against
curl … $API/v1/chat -d '{"model": "learner-1.0:lrn_…", "temperature": 0, "max_tokens": 96,
  "messages": [{"role": "user", "content": "Q: In what year was Brindlemoor Analytics founded?"}]}'

# thinking on, no primer
curl … $API/v1/chat -d '{"model": "learner-1.0:lrn_…", "temperature": 0, "max_tokens": 512,
  "enable_thinking": true,
  "messages": [{"role": "user", "content": "Q: In what year was Brindlemoor Analytics founded?"}]}'

# thinking on, with the generic primer opening the thinking phase
curl … $API/v1/chat -d '{"model": "learner-1.0:lrn_…", "temperature": 0, "max_tokens": 512,
  "enable_thinking": true, "think_phase_cap": 300,
  "think_primer": "Let me recall the taught facts before answering.\n- ",
  "messages": [{"role": "user", "content": "Q: In what year was Brindlemoor Analytics founded?"}]}'

# the control: the same primer to the untaught base model
curl … $API/v1/chat -d '{"model": "learner-1.0-base", "temperature": 0, "max_tokens": 512,
  "enable_thinking": true, "think_phase_cap": 300,
  "think_primer": "Before answering, check whether this question is about something you were taught. If it is, recall that taught answer and use it. If it is not, answer from general knowledge and do not apply taught facts.\n- ",
  "messages": [{"role": "user", "content": "Q: In what year was Brindlemoor Analytics founded?"}]}'
```

On a taught learner, a request carrying `enable_thinking` returns the answer with thinking off
and a `thinking` block explaining the refusal. To read a trace, run these against a learner on a
build where thinking is served, which is what produced the rows here, or against the base model,
where the feature is supported.

## What is here

| Path | What it is |
|---|---|
| `answers/2026-08-26-tb1.json` | The first run: 71 rows, three arms, every answer and every trace byte-exact |
| `answers/2026-08-27-tb2.json` | The second run: 88 rows, four arms, same two learners, one day later |
| `grader.md` | How a row was marked right or wrong, what the graders cannot see, and the row we re-graded against ourselves |

There is no `data/` or `questions.json` here. The material and the questions belong to the two
folders these learners came from, and duplicating them would let the two copies drift apart.

## How these answers were quoted

Byte-exact, untruncated, including the wrong ones. Two things to know before reading a long
answer.

The 2026-08-26 rows were recorded before a serving fix went live at 03:02Z on 2026-08-27, so some
of their answers carry a trailing fragment where the model began a new turn and repeated the
question back. The graders read the answer itself, so no verdict in that file turns on the
fragment. The 2026-08-27 rows were recorded after the fix.

Traces run long and repeat themselves. A model asked to list what it was taught will keep listing
until the phase cap stops it, often mid-sentence, and several traces here end that way. The cap is
what ended them, and the cut point is visible at the end of every `trace` field.
