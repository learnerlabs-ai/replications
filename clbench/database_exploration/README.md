# Continual Learning Bench: database exploration

Per-question outcomes, every trajectory, and the training examples for the runs reported in the article.

| folder | what it is |
|---|---|
| run0, run1, run2 | three runs of the final recipe (thinking only when stuck) in the benchmark's default question orders 0, 1, 2 |
| baseline | the same model with learning off and the same decoding (the benchmark's stateless baseline) |
| earlier_recipe_run0/1/2, earlier_recipe_baseline | the earlier recipe (never thinks) in the same three orders, and its baseline |
| recipe | the teacher prompt and the training protocol |

Each folder holds:
- `outcomes.jsonl`: one line per question: position in the run, question id, correct, exploratory queries, reward (1 - queries/15 if correct, else 0), the baseline's reward on the same question, and the gain (both empty in the baseline folders).
- `trajectories.jsonl`: the question text and every action with the benchmark's response, in order.
- `training_examples.jsonl`: every example the learner was trained on, with the question after which it was trained and its supervised tokens. Each example was trained once.
- `training_losses.jsonl` (the six recipe runs): the loss of every training example, computed in the step that trains on it, before the update.

