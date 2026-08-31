# Inside answers/: per-item scored rows for the capability battery

One directory per (model, checkpoint), one gzipped JSONL per (seed, task). Each row is the
slim public form of an lm-eval sample: `doc_id`, the per-item score (`acc` / `exact_match`),
`metrics`, and three integrity hashes (`doc_hash`, `prompt_hash`, `target_hash`). The
full-fat originals (complete few-shot prompts + raw responses) are retained under the run
receipts' sha256s and are available for audit; the slim rows carry everything the pairing
and statistics in `tools/pair_and_stats.py` consume, and reproduce the published aggregates
bit-for-bit.

Free-generation rows (`gsm8k_think.jsonl.gz`) use a slim form fitted to that leg: `doc_id`,
the public gold answer (`gold`), the model's extracted final answer (`got`), `correct`,
`truncated`, and two integrity hashes over the STORED generation record. Stated precisely:
the harness retained the final 300 characters of each few-shot prompt, the answer text
(complete in practice; capped at 2,000 characters), and the final 500 characters of each
reasoning trace, plus the full trace length. `q_sha256` covers the stored prompt excerpt;
`trace_sha256` covers the stored answer text plus trace tail. Full reasoning traces were
not retained by the harness. We say so rather than imply otherwise. The full prompts
reconstruct deterministically from the public dataset and the published protocol (first
216 GSM8K test items, the per-seed draw, the 5-shot format). The stored generation records
themselves ship in full as `gsm8k_think_generations.jsonl.gz` beside the slim rows.


Checkpoint label map (trajectory battery):

| label | teach step |
|---|---|
| document-lessons-ck1 | after lesson 1 |
| document-lessons-ck2 | after lesson 2 |
| document-lessons-ck3 | after a retrain |
| document-lessons-ck4 | after lesson 3 |
| two-languages-ck1 | after language 1 |
| two-languages-ck2 | after language 2 |

`ANSWERS_MANIFEST.json` pins the sha256 of every file here. Known gap, disclosed in the
battery docs: the two-languages model's third replicate (`s2`) is missing its last five
task files (a shipping race at pod shutdown); their aggregate scores survive in the receipts.


The complete raw evaluator rows (full few-shot prompts, per-item log-probabilities, targets)
for all nine evaluated models are published as a release:
https://github.com/learnerlabs-ai/replications/releases/tag/battery-raw-samples-2026-08-30
(245,310 rows; sha256s in the attached RAWS_MANIFEST.json). The slim rows here derive from
those and reproduce the published aggregates bit-for-bit. The stronger check needs neither
download: re-run the measurement against the served checkpoints through the scoring API.
