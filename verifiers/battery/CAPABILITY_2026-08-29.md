# Held-out capability: the taught learners vs the base model

*Published with the benchmark battery. All numbers below are final. Correction
2026-08-31: the second learner was previously mislabeled "two-languages"; it is the
override-a-belief learner (`lrn_c5020a579689`). Every number is unchanged.*

The claim under test: teaching a learner its material does not erode the general capability it
started with. We measure it with **stock lm-eval likelihood tasks** under deterministic
teacher-forced scoring: the MMLU suite (57 subjects, subject-clustered), ARC-Challenge, and
Winogrande; 16,481 unique scored items per model. (HellaSwag was deliberately excluded at
design time. External audits found a material error rate in its rows, and MMLU's breadth
carries the coverage.) Both published learners were evaluated against the base model with
**per-question pairing**: the same items, the same settings, question-level paired differences,
exact McNemar on the discordant pairs, and cluster-robust intervals for MMLU (clustering by
subject is the pre-registered primary form; on this data the clustered SE came out ~0.9× the
naive paired SE and ~5× narrower than an iid-proportion SE. We report the clustered one
either way because it is the conservative *design*, not because it flattered the result).

## Result

| Model | Primary endpoint (MMLU aggregate, clustered) | Verdict |
|---|---|---|
| document-lessons learner | Δ = −0.00064, 95% CI [−0.0017, +0.0004] | non-inferior (margin −0.01), no significant negatives on any of 59 tasks |
| override-a-belief learner | Δ = +0.00057, CIs inside the margin | non-inferior; aggregate slightly **positive** |

Three evaluation replicates were run per model. Determinism: at a fixed seed the pipeline is
deterministic. MMLU's few-shot exemplars come from a fixed dev split, so the seed does not
touch its prompts, and MMLU reproduced the override-a-belief learner's per-subject deltas
**bit-identically across replicates** (the third replicate dropped five subjects to a shipping
race; on the 53 shared subjects its deltas match replicate 1 to the last digit, and the
aggregate over those 53 is +0.00090). ARC-Challenge and Winogrande draw their few-shot
exemplars per seed, so their accuracies vary across replicates by up to 1.4 points. That is
expected few-shot variation, not nondeterminism.

Diagnostics:

- On the override-a-belief learner, one MMLU subject (security studies) shows Δ = −0.0204 with 5
  questions flipping down and 0 up out of 245. Its t-based 95% CI **excludes zero**
  ([−0.0381, −0.0027]) and the receipt labels it significant-negative on that test; the exact
  McNemar test on the 5 discordant pairs does **not** reach significance (p = 0.0625). Both
  tests are reported; one adverse subject among 59 tested is inside the multiple-comparisons
  expectation, and it is the only such row in the wave. Re-run it yourself through the scoring
  endpoint.
- Twelve MMLU subjects (n from 100 to 895; three at n = 100) have confidence intervals wider
  than the ±1% non-inferiority margin. They can neither pass nor fail that margin at their
  sample size (one such "fail" has a *positive* Δ). This is why the clustered aggregate, not
  the per-subject row, is the primary endpoint.

## Free generation

The likelihood battery scores fixed continuations; free generation is the harder claim: the
model writing its own reasoning end to end. We measured it on GSM8K in the model's own
reasoning mode: n = 108 items per seed drawn from the first 216 test items (disclosed sampling
frame), two seeds, greedy decoding, a 15,360-token reasoning budget, through a decode path
built to match the deployed product's serve semantics (noted as `decode_path` in each
receipt). Within a seed the base model and the learner score the **identical 108 items**.
The comparison is fully paired; across the two seeds the draws share 57 items.

| Seed | Base | override-a-belief learner | Discordant pairs (base-wins : learner-wins) |
|---|---|---|---|
| 0 | 0.9722 (105/108) | 0.9630 (104/108) | 2 : 1 |
| 1 | 0.9722 (105/108) | 0.9815 (106/108) | 0 : 1 |
| pooled (216 paired rows) | 0.9722 | 0.9722 | 2 : 2 — exact McNemar p = 1.0 |

No run truncated a single item (truncation rate 0.0 across all four runs). The pooled paired
accuracies are identical to four decimal places and the four discordant flips split evenly, so
there is no detectable free-generation degradation on this sample; with only 4 discordant
pairs in 216, the test has power only against gross degradation. Scope: this leg ran on the override-a-belief learner (the arm with the largest taught
delta) and the base; the document-lessons learner was not run on free generation. Per-item
rows ship in `answers/*/s*/gsm8k_think.jsonl.gz`: item id, public gold answer, the model's
extracted answer, correctness, and integrity hashes over the stored generation record. The
stored records themselves (prompt excerpt, complete answer text, reasoning-trace tail, and the
full trace length) sit beside them in `gsm8k_think_generations.jsonl.gz`. One retention
note: the harness kept each trace's final 500 characters, not the full trace.

## Reproduce it

Per-item scored rows ship in `answers/` with sha256s pinned in the run receipts, for every cell
except five: the override-a-belief learner's third replicate lost the sample files for its last
five tasks to a shipping race at pod shutdown (their aggregate scores survive in the receipt;
the join for that replicate drops those five tasks, which is why its aggregate covers 53
subjects, as disclosed above). The pairing and statistics code is a single stdlib-only script in
`tools/`; the models remain loadable by pinned id through the serving API (ask-only, per the
verifier contract): `lrn_a30df3e1e2b2` (document lessons), `lrn_c5020a579689` (override-a-belief),
`__base__` (the base model, taught nothing). The six intermediate checkpoints in `TRAJECTORY_2026-08-29.md` belong
to a different pair of learners (the sequence-trained ones documented there) and are
loadable the same way. `PROTOCOL.md` has the one-command stock-lm-eval invocation.
