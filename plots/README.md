# Figures

Every figure on the skills pages is built from the data in `plots/data/` by the code in this folder. Standard-library Python only; no third-party packages.

    python3 plots/build.py               # every registered figure, the numeric checks, and checks/report.json
    python3 plots/build.py ts_f4_matrix  # one figure by name
    python3 plots/build.py --png         # also render 2x PNG copies (needs a Chrome or Chromium binary)

Outputs go to `plots/output/<group>/<name>.svg` with a sidecar `<name>.json` holding the title, caption, alt text, units, smoothing, the data sources with their sha256, the plotted values where the figure is a small table, and the sha256 of the SVG. Rebuilding from the same data gives byte-identical SVGs.

## Layout

- `lib/housesvg.py`: the style and the drawing primitives (figure, panel, axes, line, band, bar, dot, label, smoothing, downsampling). Colours and fonts live only here.
- `figures/ten_skills.py`, `figures/four_domain.py`, `figures/two_languages.py`: one function per figure.
- `config/registry.json`: the figure registry. The `facts` group is static: those three figures are drawn by hand in the fact pages and are registered here with their sidecars so that every published figure has one entry.
- `checks/numeric_checks.py`: asserts that the plotted values equal the released tables (row sums, counts, deltas, benchmark scores).
- `scripts/fix_base_battery.py`: recomputes the MMLU macro average over the 57 subjects from the per-subject scores in `data/derived/tables.json`.
- `data/COMPLETENESS.md`: what was measured, what is plotted, and what does not exist.

## Which figure reads what

| figure | reads |
|---|---|
| `ts_f1_stream`, `ts_f2_per_skill`, `ts_f2z_per_skill_zoom`, `ts_f3_retention`, `ts_f7_loss_vs_accuracy` | `data/series/training_loss.json`, `data/series/held_out_loss.json` |
| `ts_f4_matrix`, `ts_f5_own_vs_final`, `ts_f6_dose`, `ts_f8_sentinel_base` | `data/derived/tables.json` |
| `ts_f9_oriel_components` | `data/derived/oriel_components.json` (regenerate with `ten_skills/tools/oriel_components.py`) |
| `fd_f1_stream`, `fd_f1b_stream_raw`, `fd_f2_bwt`, `fd_f3_control`, `fd_f4_validation` | `data/four_domain/<condition>/{A_equivalence.json,train_curve.jsonl,val_curve.jsonl}` |
| `tl_f1_curves`, `tl_f2_lora_sequential`, `tl_f3_generation_matrix` | `data/two_languages.json` |
| `fig1_stream` to `fig7_lr_ablation` (the seven image figures of the four-domain article) | the same `data/four_domain/` files plus `data/four_domain/lora_lr2e-4/`; drawn by `report_figures.py`, not by `build.py` |

The seven image figures need matplotlib (`requirements-report.txt`); everything else is standard library. `python3 plots/report_figures.py` writes `output/four_domain_report/figN_*.png` with a sidecar each (input files and their sha256, plotted values, PNG sha256). `python3 plots/report_figures.py --check` redraws them and compares. [`FIGURE_INVENTORY.md`](FIGURE_INVENTORY.md) lists every figure shown in every article, including the hand-made ones that have no generator.

Training-loss lines are smoothed for reading; wherever a line is smoothed, the raw range is drawn behind it or the unsmoothed points are drawn in a companion figure on the same axes (`fd_f1b_stream_raw` for the four-domain stream), and the sidecar states the span. A raw band is a minimum-to-maximum range, not a confidence interval.
