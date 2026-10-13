# Continual Learning Bench: cohort studies

Per-study outcomes, every trajectory, the training examples and their training losses for the runs reported in the article.

| folder | what it is |
|---|---|
| run0, run1, run2 | three runs of the same recipe in the benchmark's default study orders 0, 1, 2 |
| baseline | the same model with learning off (the benchmark's stateless baseline) |
| recipe | the teacher prompt, the reasoning prompt and the training protocol |

Each folder holds:
- `outcomes.jsonl`: one line per study: position in the run, study id, study family, reward (information gain in bits per cohort over the benchmark's reference predictor, at most 0.162), the baseline's reward on the same study, the gain, tool calls, and calls identical to an earlier call in the same study.
- `trajectories.jsonl`: every step of every study in order: the agent's reasoning, its tool call (or its 108 submitted survival estimates) and the tool's result.
- `training_examples.jsonl`: every example the learner was trained on, with the study after which it was trained: the state (messages) and the target (reasoning and tool call). Each example was trained once. Run 0's examples written after study 10 are included with `"trained": false`: that training was lost in an outage and the run resumed from the checkpoint after study 9.
- `training_losses.jsonl`: the loss of every training example, computed in the step that trains on it, before the update, and the supervised tokens per study.

Positions follow each run's own order. Pair runs with the baseline by `study_id`. The baseline's positions are order 0.
