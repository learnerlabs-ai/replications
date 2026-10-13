# Continual Learning Bench

Results of our Learner 1.0 model on three tasks of [Continual Learning Bench](https://continual-learning-bench.com/)
([arXiv:2606.05661](https://arxiv.org/abs/2606.05661)), a public benchmark that measures whether an agent gets better at a task
from its own experience of doing it. Each system is compared with the same model answering the same questions with learning off.

Learner 1.0 learns strictly through its weights. Its context is reset before every question, so there is no in-context learning
between questions: anything it carries from one question to the next, besides what the benchmark itself provides, is in its weights. After every question a teacher LLM writes
training examples from the states the learner actually reached, and the learner trains on each example once. It is never
trained on a question paired with its answer. The teacher's prompt is in the `recipe/` folder of the database exploration and cohort studies tasks.

| folder | task | what is in it |
|---|---|---|
| [`database_exploration/`](database_exploration/) | 40 questions about one product database, migrated after question 20 | three runs of the final recipe, three runs of the earlier recipe, a learning-off baseline for each |
| [`cohort_studies/`](cohort_studies/) | 20 clinical study databases, 108 survival estimates each | three runs, the learning-off baseline |
| [`sales_prediction/`](sales_prediction/) | 12 consecutive years of five-year furniture sales forecasts | one run (n = 1), the learning-off baseline |

Scores are the benchmark's own. Each task folder's README lists its folders and the fields of every file.
