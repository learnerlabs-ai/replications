# Capability across every teach step (the trajectory battery)

*Published with the benchmark battery. All five checkpoints below are scored.*

A single before/after comparison leaves a gap a careful skeptic will name: maybe the model was
fine at the end but degraded in the middle, or maybe the final checkpoint was the one lucky
snapshot. So we measure **every intermediate checkpoint** two of the published learners ever
produced. Each training run saves an immutable checkpoint, and old checkpoints are retained. On
each one we run the full held-out likelihood battery (the MMLU suite's 57 subjects,
ARC-Challenge, Winogrande; 16,481 unique scored items per checkpoint, scored as 65 task-metric
rows: the 57 subjects, MMLU's 5 aggregate rollups, ARC under both of its metrics, and
Winogrande).

Each run pins the exact historical checkpoint by its full version id. Inside the run's own
receipt, the evaluation harness records which checkpoint the loader actually resolved and its
content hash; a run only counts when that recorded resolution matches the pin exactly.
The comparison is paired per task-metric row against the base model under identical
settings, same items.

## The five checkpoints

| Learner | Teach step | Row-mean accuracy | Δ vs base | Task-metric rows outside the noise band |
|---|---|---|---|---|
| — (base) | 0 | 0.8583 | — | — |
| sequence lessons | after lesson A | 0.8597 | +0.0014 | 0 / 65 |
| sequence lessons | after lesson B | 0.8586 | +0.0003 | 0 / 65 |
| sequence lessons | after lesson C | 0.8584 | +0.0001 | 0 / 65 |
| two languages | after language 1 | 0.8579 | −0.0004 | 0 / 65 |
| two languages | after language 2 | 0.8570 | −0.0013 | 0 / 65 |

The noise band is a per-row 2σ binomial interval on the base rate. On the two-languages
trajectory **no row at either checkpoint moved outside it**, and the largest row-mean deviation is
0.0013. (Scale note: 62 of the 65 rows are MMLU-derived, so the row-mean is MMLU-dominated; the
per-row band check, which covers ARC and Winogrande individually, is the metric that treats every
benchmark on its own terms.)

The claim this table is built to carry is that teaching does not trade away general capability at
any point in a learner's history, rather than only at the end. The two-languages trajectory carries
it. The sequence trajectory carries it too: the three lesson checkpoints sit within 0.0014 of the
base row-mean (0.8597, 0.8586, 0.8584 against 0.8583), on the side of better, and no task-metric
row leaves the noise band at any of them. The largest single-row move at any sequence checkpoint
is 0.05, inside that row's noise band. The figure `trajectory_figure.png` in this folder plots all five.

## An earlier version of this table

A previous version of this page scored six checkpoints: four from an earlier recording of the
sequence demonstration, which included a retrain step, and the same two two-languages checkpoints.
Every row on it was flat, with a largest row-mean deviation of 0.0022 in the direction of better,
and none of its 65 rows moved outside the band at any checkpoint. Those four checkpoints belong to
a recording this repository no longer publishes, so their rows have been withdrawn rather than
carried forward under a demonstration whose data they do not match. The two two-languages rows are
unchanged and are the same measurement.

## The published checkpoint ids

Every checkpoint in the table is loadable by the pinned id below. Pass it as the `model` on
the scoring endpoint (`PROTOCOL.md` has the one-command lm-eval invocation). Each id names ONE
immutable historical checkpoint; the server refuses anything but an exact match, and scoring is
the only thing these ids can do (ask-only, per the verifier contract).

| Teach step | Pinned checkpoint id |
|---|---|
| sequence lessons, after lesson A | `v94b0fac5388e` |
| sequence lessons, after lesson B | `v187d143ccebd` |
| sequence lessons, after lesson C | `v9c348124aeb5` |
| two languages, after language 1 | `v0d4ef433e06a` |
| two languages, after language 2 | `vc50142900cdf` |

The three sequence checkpoints are the ones the recorded run produced, one per teach; the
demonstration folder
[`../../demos/teach-in-sequence/`](../../demos/teach-in-sequence/) names which of them answered
each of its eight quizzes.

The two battery learners score by their live ids: `lrn_a30df3e1e2b2` (taught the handbook document)
and `lrn_c5020a579689` (taught the counterfactual facts); `__base__` is the base model, taught
nothing.

## Reproduce it

Every checkpoint in the table remains loadable by its pinned version id through the serving API
(ask-only, per the verifier contract). That is how *you* re-run this table; our own runs were
executed on evaluation hardware with the same pin-and-verify discipline recorded in each
receipt. The per-item scored rows for every published cell are in `answers/` with sha256s; the
harness is stock lm-eval, and the scoring endpoint that lets you drive it against the served
checkpoints is described in `PROTOCOL.md`.
