# answers/ — per-item scored rows for the capability battery

One directory per (model, checkpoint), one gzipped JSONL per (seed, task). Each row is the
slim public form of an lm-eval sample: `doc_id`, the per-item score (`acc` / `exact_match`),
`metrics`, and three integrity hashes (`doc_hash`, `prompt_hash`, `target_hash`). The
full-fat originals (complete few-shot prompts + raw responses) are retained under the run
receipts' sha256s and are available for audit; the slim rows carry everything the pairing
and statistics in `tools/pair_and_stats.py` consume, and reproduce the published aggregates
bit-for-bit.

Free-generation rows (`gsm8k_think.jsonl.gz`) use a slim form fitted to that leg: `doc_id`,
the public gold answer (`gold`), the model's extracted final answer (`got`), `correct`,
`truncated`, and sha256 of the full few-shot prompt (`q_sha256`) and of the complete
reasoning trace (`trace_sha256`). The full prompts and traces are retained under the run
receipts' sha256s.


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
