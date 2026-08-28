# replications

Teaching data, questions, expected answers and every served answer for the published Learner Labs
demonstrations.

Everything shown at [learnerlabs.ai/demos](https://learnerlabs.ai/demos) was a recorded session on
the deployed product. This repository is what those sessions ran on and what they produced: the
exact document each learner was taught, the exact questions asked, the answer expected for each,
and the answer served, in full. You can run the same thing on your own key and compare.

> **Replicate with your coding agent.** MCP is the open protocol that lets agents like Claude
> Code and Codex call outside tools; our server gives your agent commands to create a learner,
> teach it, ask it, and unlearn facts on your own key. One line connects it:
>
> ```
> claude mcp add --transport http learnerlabs https://mcp.learnerlabs.ai/mcp --header "Authorization: Bearer YOUR_API_KEY"
> ```
>
> Then say `replay the <demo> demo` for any of the demos that teach; the agent gets a session token
> back and can poll it while the teach runs. Every call is also listed in [PROTOCOL.md](PROTOCOL.md)
> for replaying by hand.

## The six demonstrations

| Folder | What it shows | Runs live in your replication | Measured wall clock | Your credit |
|---|---|---|---|---|
| [`demos/teach-a-document/`](demos/teach-a-document/) | A 706-word handbook taught in one pass, then asked back | everything | 57 min | $1.56, estimated |
| [`demos/teach-in-sequence/`](demos/teach-in-sequence/) | Three topics taught one after another, the first two still answering | the third lesson | 68 min | $1 to $2, estimated |
| [`demos/delete-a-fact/`](demos/delete-a-fact/) | One fact unlearned on request, the rest still answering | the unlearning | 79 min | $4 to $5, estimated |
| [`demos/override-a-belief/`](demos/override-a-belief/) | Nine facts its base model believes are false | everything | 34 min | $1.25, measured |
| [`demos/two-languages/`](demos/two-languages/) | Two invented languages taught back to back, neither erasing the other | everything | 101 min | $4.60, measured |
| [`demos/thinking-with-the-facts/`](demos/thinking-with-the-facts/) | The same taught learners answering with thinking mode on, reasoning out loud over facts that are not in the prompt | nothing by hand; the agent replay teaches both documents unless you point it at learners you already hold | 54 asks by hand; two teaches plus 54 asks through the agent | asking only by hand; about $2.80 of teaching through the agent |

Three of the six train a learner from nothing during your run. Two load a learner that already
holds the setup and run only the step being demonstrated. The sixth teaches nothing when you
replay it by hand: it re-asks learners the earlier folders produced. Through the agent tool it is
different, and the difference costs money; see below. Each folder says which, per stage, at
the top, because "replicate" means different things and hiding that would be the dishonest version.

The sixth folder, [`demos/thinking-with-the-facts/`](demos/thinking-with-the-facts/), has no
`data/` or `questions.json` of its own; the material and the questions belong to the two folders
its learners came from. Thinking mode is available on taught learners and is not yet optimized
for them: it costs about two answers in sixteen against thinking off, and on a learner holding
counterfactual facts a trace can carry one of those facts into a question that was not about it.
Both costs are measured in that folder, with every trace in full.

Said plainly, because the price depends on it: `replay the thinking-with-the-facts demo` with no
arguments **teaches both documents again**, the handbook and the invented world. That is two
teaches, about $1.56 and $1.25 on the figures in the table above, on top of the 54 graded asks.
Two ways to avoid paying for them: pass `learner_id` for a handbook learner you already hold, so
that half is not taught twice, or pass `resume_job_id` to ride a teach that already landed. By
hand, following PROTOCOL.md against learners you already have, nothing is taught and you pay for
asks alone.

Beside the six there is one more folder, [`demos/thinking-mode/`](demos/thinking-mode/), holding
two earlier runs of the same measurement, including an arm with no opening sentence at all and an
arm with a longer one. It is kept as the record behind the arms the sixth demonstration ships
with.

## What each folder holds

```
demos/<name>/
  README.md      what it shows, what trains live, how long it takes, what it costs
  data/          the material taught, byte for byte
  questions.json everything the model was asked, in every wording, and what was expected back
  grader.md      exactly how an answer was scored, including where the scoring was wrong
  answers/       every answer served, in full
```

Four of the folders ask questions and expect an answer. Two ask the model to write, so their
`questions.json` holds prompts rather than questions and their `grader.md` scores a property of
the writing rather than a right answer. Each says which at the top.

## How these answers were produced

This is the box that appears on the demonstrations page. It applies to everything here.

> **How these answers were produced.** Every answer on this page is shown as the model served it.
> There is no system prompt and no instructions: the only text you send with a question is the
> question. The model answers from what it learned. Nothing external was retrieved, no examples
> were supplied, and no wording was tuned to make an answer land. The questions were written
> before the run, and where a fact is asked in more than one wording every wording is shown.
> Answers are produced by greedy decoding unless a row says otherwise. We have deliberately not
> optimised any of this. A careful prompt, a retry, a short instruction about the answer format,
> or an agent wrapped around the model would each improve these numbers, and none of that is
> here. What you are looking at is the floor, not the ceiling.

> **How answers are quoted.** After answering, the model often restates the same fact in several
> invented formats and then begins a new conversational turn that repeats the question back. That
> trailing text is a serving artifact, not part of the answer, and it was fixed on 2026-08-25.
> Answers recorded before that date are quoted here up to the end of the answer itself, which is
> also what the grader reads. The untruncated originals are in the data repository.

This repository is that data repository, so answers here exist in two lengths and you should
know which one you are reading:

| Form | Where | What it is |
|---|---|---|
| `<field>_raw` | this repository | Byte-exact, as served, including the new turn |
| `<field>` | this repository | The same answer with the new conversational turn removed, and nothing else |

The cut between the first two was made mechanically, only at a turn boundary, and only where the
text after it was demonstrably the question coming back. Nothing was hand-edited and nothing was
deleted: both forms are in every file. Every session file carries a note saying so.

The four question-and-answer demonstrations were recorded on 2026-08-24 and every one of them is
affected. The demonstration that produces writing rather than answers, `two-languages`, was recorded just
after midnight on 2026-08-25 and carries no trailing turn at all, so nothing in that folder was
shortened. Its files say so.

## What "verified to work" means

One successful recorded run each, on the deployed product, with every served answer kept. It does
not mean a distribution, a confidence interval, or a rerun on a second day. Where a demonstration
has a soft spot, its README says so rather than averaging it away.

Two of those soft spots are worth knowing before you read any number here. The quizzes are small,
eight to twelve questions, and at that size the movement between any two training runs is about
one row in either direction, which is why no folder claims that earlier answers were untouched.
And the graders are deliberately strict and blunt: they look for a string. Each `grader.md` says
what its rule cannot see, and where a grader marked a row wrongly we left the verdict alone and
said so on the row.

## What is not here

The method behind Learner 1.0 is proprietary and is not described here or anywhere else. There is
no model code, no training code and no serving code in this repository, and there will not be.

What is published is everything needed to check the results. About the system itself, publicly:
it is built on a base model, a small fraction of its parameters is trained, and the measured properties are the ones reported in each
demonstration. In any comparison table the method column for Learner 1.0 reads *proprietary
(details withheld)*. The comparison baselines are ordinary published techniques and their
configurations are given in full.

## Running these yourself

Two routes, same calls underneath.

**With a coding agent.** Connect the MCP server with the one line above and say
`replay the <demo> demo`. The agent creates a fresh learner on your key, teaches it the material
in the demo folder, asks the recorded questions, and reports the funnel and every graded answer,
plus the training loss series the job reported. `teach-a-document`, `override-a-belief` and
`two-languages` teach a fresh learner each time; `delete-a-fact` and `teach-in-sequence` replay
on learners the demo tenant keeps ready, so the deletion and the sequence start from the same
state the recorded sessions did.

**By hand.** [PROTOCOL.md](PROTOCOL.md) is the literal `curl` sequence: create a learner, teach a
document or install facts, wait for the job, open a session, ask with the `Q: …` frame, run the
base-model control, delete a fact and re-ask. Each demo README says which steps it uses and which
data files feed them.

Either way, a replication report is the most useful thing you can send. See
[CONTRIBUTING.md](CONTRIBUTING.md).

## Licence

The data and the documents are CC BY 4.0. Any script is MIT. See [LICENSE](LICENSE). Everything
here is ours and synthetic: no customer supplied it, no third party wrote it, nothing was scraped.
