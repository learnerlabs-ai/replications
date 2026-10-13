# Continual Learning Bench: sales prediction

Per-year outcomes, every trajectory, and the training examples for the run reported in the article. This is one run (n = 1).

| folder | what it is |
|---|---|
| run0 | the learning run |
| baseline | the same model with learning off: the benchmark's stateless baseline, each year played on its own |

Each folder holds:
- `outcomes.jsonl`: one line per year: year index, first forecast year, reward (the task's 0-1 composite score of the five-year forecast), the baseline's reward in the same year, the gain, and the steps used.
- `trajectories.jsonl`: every step of every year in order: the prompt the learner saw, its reasoning, its command (or the final structured forecast) and the result.
- `training_examples.jsonl` (run0): every example the learner was trained on, with the year after which it was trained and its supervised tokens. Each example was trained once. No example was trained after year 8: lessons from years 7 and 8 still waiting were trained after year 9 and appear there.

The workspace is wiped before every year in both folders. The forecast itself is never a training target.
