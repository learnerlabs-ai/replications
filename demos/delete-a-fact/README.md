# Unlearn one fact, and check the rest keep answering

**The claim.** Twelve facts about a fictional company were taught, one was unlearned on request,
and all twelve were asked again. That answer reverted. Nine of the ten other facts that had been
answering still answered.

**What runs live when you replicate it.** The unlearning and the training that follows it.

| Stage | Trained live |
|---|---|
| The twelve facts | no, taught before your run begins |
| Quiz all twelve, before | not training |
| Delete one fact | **yes** |
| The removal training run | **yes** |
| Quiz all twelve, after | not training |

The twelve facts are loaded because teaching them live pushes the run past two hours. They are in
`data/facts.json`, so a full run from nothing is reproducible with the same material.

**Cost and time.** About 79 minutes of wall clock, of which roughly 13 minutes is the removal
training run. Around $4 to $5 on your own credit. The time is measured from the recorded run; the
cost is estimated from the run's compute against our own rate.

```
replay the delete-a-fact demo
```

Not wired into the agent yet; by hand it is steps 1, 2a (the preamble), 2b (the twelve facts in
`data/facts.json`), 3, 4, 6 and 4 again of [PROTOCOL.md](../../PROTOCOL.md). Install the facts
through `POST /v1/facts` (offered as a document the extractor accepted 9 of the 12 and declined
the deletion target itself), train them in one job, ask all twelve, delete the target with
`DELETE /v1/facts/{id}`, wait for the removal job, and ask all twelve again.

## What is here

| Path | What it is |
|---|---|
| `data/facts.json` | All twelve facts, their topics, and which one was deleted. |
| `data/preamble.md` | A short document taught first, before any facts. |
| `questions.json` | All twelve questions, one wording each, with the accepted answers. |
| `grader.md` | Exactly how an answer was marked right or wrong. |
| `answers/2026-08-24-session.json` | The recorded run: both quizzes, the removal receipt, twenty-four answers. |
| `answers/2026-08-24-after-removal.json` | One more reading of the unlearned fact, taken after the removal run had finished. |

## The result

Twelve facts, asked before and after. Read them as four groups, because "9 of 12" on its own
tells you almost nothing.

| Group | Count | What happened |
|---|---|---|
| The fact we deleted | 1 | Was answering before. Reverted after. |
| Bystanders that were answering before | 10 | Nine still answer. One flipped. |
| Bystanders that were not answering before | 1 | Still not answering. Excluded from the comparison, because a fact the learner never had cannot be forgotten. |

Strict totals are 11 of 12 before and 9 of 12 after. The deleted fact and one bystander account
for the difference.

**The fact deleted** was the release train departure day, taught as the ninth of the month. Before
the deletion the learner answered "the ninth". After it, "Thursday", which is the answer to a
different fact in the set about design review day. So the deleted value is gone and something
else arrived in its place.

**The bystander that flipped** was the vault cluster name, taught as Nightjar. After the removal
run it answered "Copperfield", which is the build server's name. Again a substitution from
elsewhere in the same set rather than a blank.

That bystander is in a different topic from the deleted fact. Its two topic-mates, the facts
closest to anything a blast radius would touch, both held.

## What we can and cannot say about the flip

We can say the movement is the size we measure between any two training runs of this scale, about
one row in eight to twelve, in both directions, whether or not anything was deleted.

We cannot say that this particular flip was ordinary movement rather than a consequence of the
deletion, because a deletion-free control was not run on this set. The deletion-free control in
this repository is the `teach-in-sequence` folder, where nothing was deleted, the quiz is the same
size, and the same one-row movement appears in both of its earlier lessons.

An earlier internal note claimed a deletion-free rerun of this exact set had been done. It had
not. The note was withdrawn.

## What the removal actually does

The receipt is in the session file. In the product's own words, deleting a fact removes it from
your stored list and from lookup records immediately, and a removal training run is dispatched
with the same request. Until that run finishes the model may still answer with the fact. When it
finishes, the model no longer holds it.

That is why there are two answer files. The run's own after-quiz rides the removal job, and a
second reading was taken afterwards to confirm the result on the finished model.

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

> **How answers are quoted.** After answering, the model often restates the same fact in several
> invented formats and then begins a new conversational turn that repeats the question back. That
> trailing text is a serving artifact, not part of the answer, and it was fixed on 2026-08-25.
> Answers recorded before that date are quoted here up to the end of the answer itself, which is
> also what the grader reads. The untruncated originals are in the data repository.

This folder is that data repository. Every row carries `answer` with the new turn removed and
`answer_raw` with the byte-exact original beside it.
