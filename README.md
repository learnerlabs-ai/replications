# replications

Data, held-out panels, answers, scorers and figures for the published Learner Labs skill studies, and the
teaching data, questions, expected answers and every served answer for the fact demonstrations.

The fact demonstrations and the two-languages study at [learnerlabs.ai/demos](https://learnerlabs.ai/demos) were
recorded sessions on the deployed product. For those, this repository is what the sessions ran on and what they
produced: the exact document each learner was taught, the exact questions asked, the answer expected for each,
and the answer served, in full. You can run the same thing on your own key and compare.

The ten-skill study and the four-domain comparison were research runs, not product sessions. Their folders hold
the data, the held-out panels, every generated answer, the scorers and the figures, and they are checked by
re-scoring and by rebuilding the figures, not by replaying the training. [REPRODUCIBILITY.md](REPRODUCIBILITY.md)
says exactly what each study supports; [DATA_LICENSES.md](DATA_LICENSES.md) says where each dataset came from.

> **Replicate with your coding agent.** MCP is the open protocol that lets agents like Claude
> Code and Codex call outside tools; our server gives your agent commands to create a learner,
> teach it and ask it on your own key. One line connects it:
>
> ```
> claude mcp add --transport http learnerlabs https://mcp.learnerlabs.ai/mcp --header "Authorization: Bearer YOUR_API_KEY"
> ```
>
> Then say `replay the <demo> demo` for any of the product demonstrations that teach; the agent gets a session token
> back and can poll it while the teach runs. Every call is also listed in [PROTOCOL.md](PROTOCOL.md)
> for replaying by hand.

## Skills

| Folder | What it shows | How you check it |
|---|---|---|
| [`ten_skills/`](ten_skills/) | Ten unrelated skills taught in sequence to one model in one pass, each scored on a fixed 225-row held-out panel after every teach | `python3 ten_skills/tools/rescore.py` re-scores every answer; `python3 plots/build.py` rebuilds the figures |
| [`science/plasticity-without-forgetting/`](science/plasticity-without-forgetting/) | The four-domain comparison against a parameter-matched LoRA adapter: per-condition measured summaries and loss curves | read all 1,296 windows in `data/` (the Yoruba, Amharic, news and control windows are third-party text under the terms of their sources); rebuild the figures from the curves |
| [`demos/two-languages/`](demos/two-languages/) | Two invented languages taught back to back, neither erasing the other | read the recorded answers, re-score every continuation and rebuild the figures. The corpora can also be taught on your own key, but the API's teach schedule is not the one-pass schedule of this recording, so that is a different experiment |

## The fact demonstrations

| Folder | What it shows | Runs live in your replication | Measured wall clock | Your credit |
|---|---|---|---|---|
| [`demos/teach-a-document/`](demos/teach-a-document/) | A 706-word handbook taught in one pass, then asked back | everything | 57 min | $1.56, estimated |
| [`demos/teach-in-sequence/`](demos/teach-in-sequence/) | Three topics taught one after another, the earlier two still answering | everything | 121 min | priced per teach before it starts |
| [`demos/override-a-belief/`](demos/override-a-belief/) | Nine facts its base model believes are false | everything | 34 min | $1.25, measured |
| [`demos/thinking-with-the-facts/`](demos/thinking-with-the-facts/) | The same taught learners answering with thinking mode on, reasoning out loud over facts that are not in the prompt | nothing by hand; the agent replay teaches both documents unless you point it at learners you already hold | 54 asks by hand; two teaches plus 54 asks through the agent | asking only by hand; about $2.80 of teaching through the agent |

Three of the four, and the two-languages study above, train a learner from nothing during your run. The fourth teaches nothing when you
replay it by hand: it re-asks learners the earlier folders produced. Through the agent tool it is
different, and the difference costs money; see below. Each folder says which, per stage, at
the top, because "replicate" means different things.

The fourth folder, [`demos/thinking-with-the-facts/`](demos/thinking-with-the-facts/), has no
`data/` or `questions.json` of its own; the material and the questions belong to the two folders
its learners came from. Thinking mode is available on taught learners and is not yet optimized
for them: it costs about two answers in sixteen against thinking off, and on a learner holding
counterfactual facts a trace can carry one of those facts into a question that was not about it.
Both costs are measured in that folder, with every trace in full.

Because the price depends on it: `replay the thinking-with-the-facts demo` with no
arguments **teaches both documents again**, the handbook and the invented world. That is two
teaches, about $1.56 and $1.25 on the figures in the table above, on top of the 54 graded asks.
Two ways to avoid paying for them: pass `learner_id` for a handbook learner you already hold, so
that half is not taught twice, or pass `resume_job_id` to ride a teach that already landed. By
hand, following PROTOCOL.md against learners you already have, nothing is taught and you pay for
asks alone.

## What each demonstration folder holds

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

This is the box that appears on the demonstrations page. It applies to the product demonstrations under `demos/`.

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
> trailing text is a serving artifact, not part of the answer, and it has since been fixed.
> Answers recorded before that fix are quoted here up to the end of the answer itself, which is
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

The demonstrations recorded before that fix are all affected, and their folders say so. The
demonstration that produces writing rather than answers, `two-languages`, keeps both forms on every row:
`answer_raw` exactly as generated, and `answer` without the end-of-turn marker.

## What "verified to work" means

One successful recorded run each, on the deployed product, with every served answer kept. It does
not mean a distribution, a confidence interval, or a rerun on a second day. Where a demonstration
has a soft spot, its README says so.

Two of those soft spots are worth knowing before you read any number here. The quizzes are small,
eight to twelve questions, and at that size the movement between any two training runs is about
one row in either direction, which is why no folder claims that earlier answers were untouched.
And the graders are deliberately strict and blunt: they look for a string. Each `grader.md` says
what its rule cannot see, and where a grader marked a row wrongly we left the verdict alone and
said so on the row.

## The verifier checkpoints

[`verifiers/`](verifiers/) holds the identity cards for the two learners the capability battery
scored, and the battery's own documents: what was measured, how, and every number. Start at
[`verifiers/README.md`](verifiers/README.md).

## How fact training works

The fact-training pipeline turns documents into statements for the model to learn. The
[extraction guide](extraction/) describes the process and the statements reviewed before training.

It also names the one property a reader has to know before comparing two runs: the model-driven
step is not reproducible. The same document extracted five times under identical settings gave
five different sets of statements. That is the source of most of the difference between any two
recordings of one document.

## What is not here

The method behind Learner 1.0 is proprietary and is not described here or anywhere else. There is
no model code, no training code and no serving code in this repository, and there will not be.

What is published is everything needed to check the results. About the system itself, publicly:
it is built on a base model, the number of trainable parameters is fixed and is reported for every experiment, and the measured properties are the ones reported in each
demonstration. In any comparison table the method column for Learner 1.0 reads *proprietary
(details withheld)*. The comparison baselines are ordinary published techniques and their
configurations are given in full.

## Running these yourself

Two routes, same calls underneath.

**With a coding agent.** Connect the MCP server with the one line above and say
`replay the <demo> demo`. The agent creates a fresh learner on your key, teaches it the material
in the demo folder, asks the recorded questions, and reports the funnel and every graded answer,
plus the training loss series the job reported. `teach-a-document`, `override-a-belief`, `two-languages` and
`teach-in-sequence` each teach a fresh learner from nothing. The ten-skill study and the four-domain
comparison are not replayable this way; see [REPRODUCIBILITY.md](REPRODUCIBILITY.md).

**By hand.** [PROTOCOL.md](PROTOCOL.md) is the literal `curl` sequence: create a learner, teach a
document or install facts, wait for the job, open a session, ask with the `Q: …` frame, and run
the base-model control. Each demo README says which steps it uses and which
data files feed them.

Either way, a replication report is the most useful thing you can send. See
[CONTRIBUTING.md](CONTRIBUTING.md).

## Licence

What Learner Labs wrote (the demonstration material, the six procedures, the answers, tables and figures) is
CC BY 4.0, and any script is MIT; see [LICENSE](LICENSE). No customer supplied any of it. Four of the ten skills
are built from public research datasets that remain under their authors' terms, one domain of the four-domain
comparison is US Government text, the other three domains and the control are third-party text published
here under the terms of their sources, and the benchmarks are not redistributed:
[DATA_LICENSES.md](DATA_LICENSES.md) lists each source, its licence and its status here.
