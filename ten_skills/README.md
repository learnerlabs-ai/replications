# Ten skills, one model, one pass

Ten unrelated skills taught in sequence to one Learner 1.0 model with 1.14B trainable parameters, in 63,282 single-example updates: one pass, no replay of earlier skills, no skill label given to the learner. Each skill has a fixed 225-row held-out panel. The article is at `/demos/skills/ten-skills`; every number in it is in `results/tables.json`.

| path | what it is |
|---|---|
| `data/train/NN_<skill>.jsonl` | the complete approved training dataset for each skill: prompt, target and token counts per row |
| `data/evals/<skill>/panel.jsonl` | the 225 fixed held-out rows (a sample of a larger held-out bank; no panel prompt or id occurs in the training file, which `tools/rescore.py` checks) |
| `configs/<skill>.task.json` | bank sizes, overlap checks and token statistics for the skills that had a prepared task file |
| `scorers/` | the two frozen scorers: `candidate_scoring.py` (the grade used everywhere) and `procedure_scoring.py` (component diagnostics for the six procedures) |
| `answers/final.jsonl` | the 2,250 answers of the final checkpoint with grades (1,525 correct) |
| `answers/own_end.jsonl` | the 2,250 answers each skill produced at the end of its own teach (1,528 correct) |
| `answers/by_teach/teach_NN_<sha8>.jsonl` | every panel answer at every accepted checkpoint (12,375 rows). A skill is scored from its own teach onward, so the file for teach N holds N skills |
| `results/` | the derived tables, the Oriel component analysis and its flipped rows, the loss series (training loss per update, held-out monitor), skill profiles and the example rows used in the article |
| `lineage.json` | the accepted checkpoint after each teach, by sha256 |
| `figures/` | the figures (SVG, 2x PNG, caption sidecar); rebuild with `python3 plots/build.py` from the repository root |
| `API_REPLICATION.md`, `api_replication/` | running the experiment through the API: the guide, the client, the ten-skill driver, the evaluation schedule and the data package the driver reads |
| `tools/` | `rescore.py` (re-score everything, check counts and disjointness) and `oriel_components.py` (regenerate the Oriel analysis) |

Skills in taught order: SCAN, Meridian settlement, Adyghe grapheme-to-phoneme, Oriel packet codec, COGS, Sable workflow, PCFG SET, Tessel lot allocation, Juniper dispatch, Bracken intervals. Four are public datasets (SCAN, Adyghe G2P from SIGMORPHON 2020, COGS, PCFG SET); six are procedures written for this study so that the base model could not know them. Sources and licences: [`../DATA_LICENSES.md`](../DATA_LICENSES.md).

The training files are a dataset, not a replay script: the result reported is the accepted sequence of checkpoints in `lineage.json`, and reading the files in order is not claimed to reproduce their update history. What the release supports is inspection, re-scoring and figure regeneration; see [`../REPRODUCIBILITY.md`](../REPRODUCIBILITY.md). To run the training schedule through the API on your own key, see [`API_REPLICATION.md`](API_REPLICATION.md). The panels for the four public datasets are fixed samples for this study, not the official test splits.
