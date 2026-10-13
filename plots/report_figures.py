#!/usr/bin/env python3
"""The seven report figures of the four-domain comparison (fig1..fig7), drawn from the released measurements.

    python3 plots/report_figures.py            # writes plots/output/four_domain_report/figN_*.png + figN_*.json
    python3 plots/report_figures.py --check    # redraws into a temporary folder and compares with the sidecars

Inputs: plots/data/four_domain/<condition>/{A_equivalence.json,train_curve.jsonl,val_curve.jsonl} only.
Needs matplotlib (version in plots/requirements-report.txt); the registered SVG figures need nothing beyond the
standard library. Text is set in DejaVu Sans, which ships inside matplotlib, so no system font is used. The sidecar
of each figure lists the input files with their sha256, the plotted values, and the sha256 of the PNG. The plotted
values are exact on any machine; the PNG bytes are compared only when the matplotlib version matches.
"""
import hashlib, json, os, sys, tempfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.abspath(__file__))
W13 = os.path.join(ROOT, "data", "four_domain")
CHECK = "--check" in sys.argv
FIG = tempfile.mkdtemp() if CHECK else os.path.join(ROOT, "output", "four_domain_report")
os.makedirs(FIG, exist_ok=True)

INK, PAPER, SURFACE = "#14171A", "#E9EAE5", "#FFFFFF"
WITNESS, DRIFT, VOID, VOIDTEXT = "#2F6E62", "#B4762A", "#8A8F88", "#616660"
T1X, T2X, LORA_C = WITNESS, "#173B34", DRIFT
DOM_LABEL = {"a_book_class": "US government documents (EN)", "d_yoruba": "Yoruba",
             "c_language": "Amharic", "d_news": "multilingual news"}
ORDER = ["a_book_class", "d_yoruba", "c_language", "d_news"]

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": VOID, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": VOIDTEXT, "ytick.color": VOIDTEXT, "font.size": 11,
    "axes.spines.top": False, "axes.spines.right": False,
    "font.family": ["DejaVu Sans"],
})
USED = {}


def _open(arm, fn):
    p = os.path.join(W13, arm, fn)
    USED["data/four_domain/%s/%s" % (arm, fn)] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    return open(p)


def load(arm):
    d = json.load(_open(arm, "A_equivalence.json"))
    tr = [json.loads(l) for l in _open(arm, "train_curve.jsonl") if l.strip()]
    va = [json.loads(l) for l in _open(arm, "val_curve.jsonl") if l.strip()]
    return d, tr, va


def learner_pack(arm):
    d, tr, va = load(arm)
    m = d["measured"]
    return {"base": d["base_loss_nats"], "own": m["own_loss_at_last_train"],
            "fin": m["final_loss"], "bwt": m["per_source_bwt"], "acq": m["acquisition_nats"],
            "ctrl": m["control_domain"], "tr": tr, "va": va,
            "n_tr": d["n_trainable_params"]}


A1 = learner_pack("learner_1x")                     # Learner 1.0, 1x
A2 = learner_pack("learner_2x")                        # Learner 1.0, 2x
d3, f3tr, f3va = load("lora_r256")
m3 = d3["measured"] if "measured" in d3 else d3
A3 = {"base": m3["base_loss_nats"], "own": m3["own_loss_nats"],
      "bwt": m3["bwt_per_domain"], "acq": m3["acquisition_nats"],
      "ctrl": {"base": m3.get("collateral_base"), "delta": m3.get("collateral_nats")},
      "tr": f3tr, "va": f3va, "n_tr": d3["build"]["n_trainable"]}
A3["fin"] = {d: A3["own"][d] + A3["bwt"][d] for d in ORDER}

PROV = {"learner_1x": {k: A1[k] for k in ("base", "own", "fin", "bwt", "acq", "ctrl", "n_tr")},
        "learner_2x": {k: A2[k] for k in ("base", "own", "fin", "bwt", "acq", "ctrl", "n_tr")},
        "lora": {k: A3[k] for k in ("base", "own", "fin", "bwt", "acq", "ctrl", "n_tr")}}


def p2(tr):
    rows = [r for r in tr if r["phase"] in ORDER]
    g0 = min(r["gstep"] for r in rows)
    return [(r["gstep"] - g0, r["phase"], r["loss"]) for r in rows]


def rebase_val(va, tr):
    g0 = min(r["gstep"] for r in tr if r["phase"] in ORDER)
    return [(r["gstep"] - g0, r["domain"], r["val_loss"], r["at"]) for r in va]


def ema(v, k=31):
    a, acc, out = 2.0 / (k + 1), v[0], []
    for x in v:
        acc = a * x + (1 - a) * acc
        out.append(acc)
    return out


ARMS = [("Learner 1.0 — 1× capacity", A1, T1X), ("Learner 1.0 — 2× capacity", A2, T2X),
        ("LoRA (rank 256)", A3, LORA_C)]
YLO, YHI = 1.12, 2.78
BLOCK = {d: (i * 300, (i + 1) * 300) for i, d in enumerate(ORDER)}

# ---- FIGURE 1 — the stream, three panels, identical axes --------------------------------------
fig, axes = plt.subplots(1, 3, figsize=(17.4, 5.0), sharey=True)
for ax, (tag, A, col) in zip(axes, ARMS):
    T, V = p2(A["tr"]), rebase_val(A["va"], A["tr"])
    for i, d in enumerate(ORDER):
        lo, hi = BLOCK[d]
        if i % 2:
            ax.axvspan(lo, hi, color=PAPER, alpha=0.55, lw=0)
        ts = [(s, l) for s, ph, l in T if ph == d]
        ax.plot([x[0] for x in ts], ema([x[1] for x in ts]), color=col, lw=0.9, alpha=0.22)
        vs = [(s, l) for s, dm, l, at in V if dm == d]
        ax.plot([x[0] for x in vs], [x[1] for x in vs], color=col, lw=2.0, marker="o",
                ms=3.2, zorder=5)
        ax.hlines(A["base"][d], lo, hi, color=INK, lw=1.0, ls=(0, (4, 3)), alpha=0.8)
        ax.plot([hi, 1200], [A["own"][d], A["fin"][d]], color=col, lw=1.0, ls=":", alpha=0.8)
        ax.plot([1200], [A["fin"][d]], marker="D", ms=5.5, color=col,
                mfc=(SURFACE if A["fin"][d] > A["own"][d] + 1e-4 else col), zorder=6)
        ax.annotate(DOM_LABEL[d].replace(" (EN)", ""), xy=(lo + 150, YHI - 0.05), ha="center",
                    va="top", fontsize=8, color=VOIDTEXT)
    ax.set_xlim(0, 1260)
    ax.set_ylim(YLO, YHI)
    ax.set_xlabel("continual-learning step")
    ax.set_title(tag, color=col, fontsize=12, fontweight="bold", loc="left")
axes[0].set_ylabel("loss on held-out windows (nats)")
axes[2].annotate("earlier domains re-measured at the end:\n+0.070, +0.060, +0.034 nats",
                 xy=(1195, A3["fin"]["a_book_class"]), xytext=(310, 2.47), fontsize=8.5,
                 color=LORA_C, arrowprops=dict(arrowstyle="->", color=LORA_C, lw=1.2))
axes[0].annotate("re-measured at the end:\n−0.001, −0.001, +0.002 nats",
                 xy=(1195, A1["fin"]["a_book_class"]), xytext=(340, 2.30), fontsize=8.5,
                 color=T1X, arrowprops=dict(arrowstyle="->", color=T1X, lw=1.2))
axes[1].annotate("re-measured at the end:\n−0.004, −0.000, +0.002 nats",
                 xy=(1195, A2["fin"]["a_book_class"]), xytext=(430, 2.30), fontsize=8.5,
                 color=T2X, arrowprops=dict(arrowstyle="->", color=T2X, lw=1.2))
axes[0].annotate("dashed black = base-reference loss", xy=(40, YLO + 0.05), fontsize=8,
                 color=VOIDTEXT)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig1_stream.png"), dpi=180)
plt.close(fig)

# ---- FIGURE 2 — backward transfer, grouped bars (3 arms) --------------------------------------
fig, ax = plt.subplots(figsize=(9.4, 4.4))
xs = range(len(ORDER))
w = 0.26
for k, (tag, A, col) in enumerate(ARMS):
    ax.bar([x + (k - 1) * w for x in xs], [A["bwt"][d] for d in ORDER], width=w, color=col,
           label=tag.split(" (")[0])
ax.axhline(0, color=INK, lw=1)
ax.set_xticks(list(xs))
ax.set_xticklabels([DOM_LABEL[d] for d in ORDER], fontsize=9.5)
ax.set_ylabel("loss change after later domains trained (nats)")
ax.annotate("below zero = the loss fell\nafter later domains trained",
            xy=(0 - w, A2["bwt"]["a_book_class"]), xytext=(0.45, -0.017), fontsize=9,
            color=T2X, arrowprops=dict(arrowstyle="->", color=T2X, lw=1.2))
ax.annotate("forgetting", xy=(0 + w, A3["bwt"]["a_book_class"] * 0.96), xytext=(1.28, 0.062),
            fontsize=9.5, color=LORA_C, arrowprops=dict(arrowstyle="->", color=LORA_C, lw=1.2))
ax.set_ylim(-0.025, 0.08)
ax.legend(frameon=False, ncol=3, fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig2_bwt.png"), dpi=180)
plt.close(fig)

# ---- FIGURE 3 — acquisition, grouped bars (3 arms) --------------------------------------------
fig, ax = plt.subplots(figsize=(9.4, 4.4))
mus = []
for k, (tag, A, col) in enumerate(ARMS):
    ax.bar([x + (k - 1) * w for x in xs], [A["acq"][d] for d in ORDER], width=w, color=col,
           label=tag.split(" (")[0])
    mu = sum(A["acq"][d] for d in ORDER) / 4
    mus.append(mu)
    ax.axhline(mu, color=col, lw=1.0, ls=(0, (4, 3)), alpha=0.8)
ax.annotate("means: 1× %.3f · 2× %.3f · LoRA %.3f nats\n(loss reduction relative to each\ncondition's recorded base reference)" % tuple(mus),
            xy=(2.15, mus[1]), xytext=(1.30, 0.205), fontsize=8.8, color=INK,
            arrowprops=dict(arrowstyle="->", color=VOIDTEXT, lw=1.0))
ax.set_xticks(list(xs))
ax.set_xticklabels([DOM_LABEL[d] for d in ORDER], fontsize=9.5)
ax.set_ylabel("acquisition: base loss − trained loss (nats)")
ax.set_ylim(0, 0.25)
ax.legend(frameon=False, ncol=3, fontsize=9, loc="upper right")
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig3_acquisition.png"), dpi=180)
plt.close(fig)

# ---- FIGURE 4 — learning speed (3 lines per panel) --------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(11.5, 7.4), sharex=True)
for ax, d in zip(axes.flat, ORDER):
    lo, hi = BLOCK[d]
    for tag, A, col in ARMS:
        V = rebase_val(A["va"], A["tr"])
        vs = [(s - lo, l) for s, dm, l, at in V if dm == d]
        # Where the starting loss value comes from. In the FIRST
        # domain -- the only one where the model at step 0 provably is the untrained base -- each
        # condition is carried back to its own recorded base with a dotted segment. Later domains
        # start from a model that has already trained on earlier ones; that loss was never measured
        # on these windows, so nothing is drawn into the gap.
        if d == ORDER[0]:
            ax.plot([0, vs[0][0]], [A["base"][d], vs[0][1]], color=col, lw=1.2,
                    ls=(0, (2, 2)), alpha=0.75, zorder=1)
            ax.plot([0], [A["base"][d]], color=col, marker="o", ms=4.2,
                    mfc=SURFACE, mew=1.4, zorder=3)
        ax.plot([x[0] for x in vs], [x[1] for x in vs], color=col,
                lw=1.9, marker="o", ms=3.2, label=tag.split(" (")[0])
    ax.axhline(A1["base"][d], color=INK, lw=1.0, ls=(0, (4, 3)), alpha=0.8)
    ax.annotate(f"base {A1['base'][d]:.2f}", xy=(300, A1["base"][d]), xytext=(298, A1["base"][d]),
                fontsize=8.5, color=VOIDTEXT, ha="right", va="bottom")
    ax.set_title(DOM_LABEL[d], fontsize=11, loc="left")
    ax.set_xlim(0, 305)
    span = A1["base"][d] - min(A1["own"][d], A2["own"][d], A3["own"][d])
    ax.set_ylim(min(A1["own"][d], A2["own"][d], A3["own"][d]) - 0.25 * span,
                A1["base"][d] + 0.18 * span)
axes[0][0].legend(frameon=False, fontsize=9)
for ax in axes[1]:
    ax.set_xlabel("training step within the domain")
for ax in axes[:, 0]:
    ax.set_ylabel("held-out loss (nats)")
d = ORDER[0]
V1r = rebase_val(A1["va"], A1["tr"])
first1 = next(l for s, dm, l, at in V1r if dm == d)
axes[0][0].annotate("dashed = recorded base reference; the dotted segment carries each\n"
                    "condition back to it at step 0 (first measurement is at step 25)",
                    xy=(150, A1["base"][d]), xytext=(60, A1["base"][d] - 0.055), fontsize=8.5,
                    color=VOIDTEXT)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig4_speed.png"), dpi=180)
plt.close(fig)

# ---- FIGURE 5 — never-trained control (3 series) ----------------------------------------------
fig, ax = plt.subplots(figsize=(9.0, 4.6))
xsc = [0, 300, 600, 900, 1200]
for tag, A, col in ARMS[:2]:
    ys = [t["control_loss"] for t in A["ctrl"]["trace"]]
    ax.plot(xsc[1:], ys, color=col, lw=2.1, marker="o", ms=5, label=tag.split(" (")[0] + " (8 windows)")
    ax.hlines(A["ctrl"]["base"], 0, 1200, color=col, lw=1.0, ls=(0, (4, 3)), alpha=0.7)
cb, cd = A3["ctrl"]["base"], A3["ctrl"]["delta"]
ax.plot([0, 1200], [cb, cb + cd], color=LORA_C, lw=2.0, ls="--", marker="o", ms=5,
        label="LoRA (64 windows, before and after only)")
ax.set_xticks(xsc)
ax.set_xticklabels(["before\nthe stream", "after\ngovernment docs", "after\nYoruba", "after\nAmharic",
                    "after\nnews"], fontsize=9)
ax.set_ylabel("loss on the never-trained control bank (nats)")
y_end = A1["ctrl"]["trace"][-1]["control_loss"]
ax.text(330, 1.378, "dashed teal = the Learner conditions' recorded base reference (same 8 windows)",
        fontsize=9, color=T1X)
ax.legend(frameon=False, fontsize=9, loc="lower left", bbox_to_anchor=(0.02, 0.2))
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig5_control.png"), dpi=180)
plt.close(fig)

# ---- FIGURE 6 (NEW) — the summary: acquisition vs forgetting, side by side --------------------
fig, (axa, axb) = plt.subplots(1, 2, figsize=(11.0, 4.3))
names = ["Learner 1.0 1×", "Learner 1.0 2×", "LoRA"]
cols = [T1X, T2X, LORA_C]
mu_acq = [sum(A["acq"][d] for d in ORDER) / 4 for _, A, _ in ARMS]
bwt_mean = [sum(A["bwt"][d] for d in ORDER[:3]) / 3 for _, A, _ in ARMS]
bwt_worst = [max(A["bwt"][d] for d in ORDER[:3]) for _, A, _ in ARMS]
axa.bar(names, mu_acq, color=cols, width=0.55)
for i, v in enumerate(mu_acq):
    axa.text(i, v + 0.003, "%.3f" % v, ha="center", fontsize=9.5, color=cols[i],
             fontweight="bold")
axa.set_ylabel("mean acquisition (nats)")
axa.set_ylim(0, 0.19)
axa.set_title("mean loss reduction vs the base reference", fontsize=10.5, loc="left")
axb.bar(names, bwt_mean, color=cols, width=0.55)
axb.scatter(names, bwt_worst, color=INK, marker="_", s=380, lw=2, zorder=5,
            label="worst single domain")
for i, v in enumerate(bwt_mean):
    axb.text(i, v + (0.003 if v >= 0 else -0.006), "%+.4f" % v, ha="center", fontsize=9.5,
             color=cols[i], fontweight="bold")
axb.axhline(0, color=INK, lw=1)
axb.set_ylabel("mean forgetting, earlier domains (nats)")
axb.set_ylim(-0.012, 0.078)
axb.set_title("mean change in earlier domains at the end", fontsize=10.5, loc="left")
axb.legend(frameon=False, fontsize=8.5, loc="upper left")
axb.text(0.5, 0.03, "Learner 1.0, both capacities:\nabout zero", ha="center", fontsize=9, color=T2X)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig6_summary.png"), dpi=180)
plt.close(fig)

# ---- FIGURE 7 (v3, NEW) — LoRA learning-rate ablation: 2e-4 diverges ---------------------------
# The LoRA run at 2e-4 (stopped after the first domain) against the LoRA run at 2e-5 used in the comparison.
d4, tr4, va4 = load("lora_lr2e-4")
em4, em5 = d4["eval_matrix"], d3["eval_matrix"]
LORA_HI = "#6E3E14"                                     # dark burnt amber = the diverging rate
BASE_LIT = em4["base"]["a_book_class"]

fig, (axa, axb, axc) = plt.subplots(1, 3, figsize=(14.5, 4.4))

# (a) the first domain during its own 300 steps: held-out loss at both LoRA rates, with Learner 1.0 1x for reference
tr4_l = [(r["gstep"], r["loss"]) for r in tr4]
axa.plot([g for g, _ in tr4_l], [min(l, 3.40) for _, l in tr4_l], color=LORA_HI, lw=0.7,
         alpha=0.16)
va4_p = [(r["gstep"], r["val_loss"]) for r in va4 if r["at"] == "periodic"]
axa.plot([g for g, _ in va4_p], [v for _, v in va4_p], color=LORA_HI, lw=2.0, marker="o",
         ms=3.5, label="LoRA, lr 2e-4 (10× higher)")
va5_p = [(r["gstep"], r["val_loss"]) for r in f3va
         if r["domain"] == "a_book_class" and r["gstep"] <= 300 and r["at"] == "periodic"]
axa.plot([g for g, _ in va5_p], [v for _, v in va5_p], color=LORA_C, lw=2.0, marker="o",
         ms=3.5, label="LoRA, lr 2e-5 (the comparison run)")
va1_p = [(r["gstep"], r["val_loss"]) for r in A1["va"]
         if r.get("domain") == "a_book_class" and r["gstep"] <= 300 and r["at"] == "periodic"]
axa.plot([g for g, _ in va1_p], [v for _, v in va1_p], color=T1X, lw=2.0, marker="o",
         ms=3.5, label="Learner 1.0 1×, lr 1e-3 (50× higher still)")
axa.axhline(BASE_LIT, color=INK, lw=1.1, ls="--")
axa.text(150, BASE_LIT + 0.022, "base-reference loss", fontsize=8.2, color=VOIDTEXT)
axa.annotate("+0.93 nats ABOVE base\nafter its own 300 steps", xy=(297, 3.20),
             xytext=(128, 2.72), fontsize=8.8, color=LORA_HI, fontweight="bold",
             arrowprops=dict(arrowstyle="->", color=LORA_HI, lw=1.2))
axa.text(128, 2.60, "faint: 2e-4 train loss — spikes to 11.7 (clipped)", fontsize=7.6,
         color=LORA_HI, alpha=0.7)
axa.set_xlim(0, 312)
axa.set_ylim(1.95, 3.45)
axa.set_xlabel("step within the first domain (US government documents)")
axa.set_ylabel("loss on held-out windows (nats)")
axa.set_title("the first domain, three learning rates", fontsize=10.5, loc="left")
axa.legend(frameon=False, fontsize=8.0, loc="upper left")

# (b) collateral after those 300 steps: every OTHER column of the eval matrix
oth = ["d_yoruba", "c_language", "d_news", "held_control"]
lab = [DOM_LABEL.get(d, "never-trained\ncontrol").replace("multilingual news", "multilingual\nnews") for d in oth]
d_hi = [em4["after_a_book_class"][d] - em4["base"][d] for d in oth]
d_lo = [em5["after_a_book_class"][d] - em5["base"][d] for d in oth]
x = range(4)
axb.bar([i - 0.19 for i in x], d_hi, width=0.36, color=LORA_HI, label="lr 2e-4")
axb.bar([i + 0.19 for i in x], d_lo, width=0.36, color=LORA_C, label="lr 2e-5")
axb.axhline(0, color=INK, lw=1)
axb.set_xticks(list(x))
axb.set_xticklabels(lab, fontsize=8.4)
axb.set_ylabel("loss change vs base (nats)")
axb.set_title("collateral: everything else, after those 300 steps", fontsize=10.5, loc="left")
axb.legend(frameon=False, fontsize=8.5)
axb.annotate("never-trained text\n+1.20 nats", xy=(3 - 0.19, d_hi[3]), xytext=(1.2, 1.08),
             fontsize=8.0, color=LORA_HI,
             arrowprops=dict(arrowstyle="->", color=LORA_HI, lw=1.2))

# (c) LoRA adapter norm ||B·A|| per module at domain boundaries
n5 = [t["fro_norm_mean"] for t in d3["lora_norm_trace"]]
n4 = [t["fro_norm_mean"] for t in d4["lora_norm_trace"]]
axc.plot([0, 300, 600, 900, 1200], n5, color=LORA_C, lw=2.0, marker="o", ms=4,
         label="lr 2e-5: 0.88 after four domains")
axc.plot([0, 300], n4, color=LORA_HI, lw=2.0, marker="o", ms=4,
         label="lr 2e-4: 8.83 after ONE domain")
axc.annotate("10× the rate: 10× the norm\nin a quarter of the steps",
             xy=(300, n4[1]), xytext=(340, 6.1), fontsize=8.8, color=LORA_HI,
             arrowprops=dict(arrowstyle="->", color=LORA_HI, lw=1.2))
axc.set_xlabel("continual-learning step (domain boundaries)")
axc.set_ylabel("adapter update magnitude  ‖B·A‖  (mean per module)")
axc.set_title("adapter update magnitude at the two rates", fontsize=10.5, loc="left")
axc.set_xlim(-30, 1260)
axc.legend(frameon=False, fontsize=8.5, loc="center right")

fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig7_lr_ablation.png"), dpi=180)
plt.close(fig)

LRV = {"lr_2e-4": {"learning_rate": d4["learning_rate"], "stopped": d4["stopped"], "eval_base": em4["base"],
                   "eval_after_domain1": em4["after_a_book_class"], "val_curve": va4_p,
                   "train_loss_max": max(l for _, l in tr4_l), "norm_trace_mean": n4},
       "lr_2e-5": {"eval_base": em5["base"], "eval_after_domain1": em5["after_a_book_class"], "norm_trace_mean": n5}}
NAMES = ["learner_1x", "learner_2x", "lora_r256"]
SUM = {"mean_acquisition": dict(zip(NAMES, [round(v, 6) for v in mu_acq])),
       "mean_change_earlier_domains": dict(zip(NAMES, [round(v, 6) for v in bwt_mean])),
       "worst_single_domain": dict(zip(NAMES, [round(v, 6) for v in bwt_worst]))}
ARMKEYS = dict(zip(NAMES, [A1, A2, A3]))


def vals(*ks):
    return {a: {k: A[k] for k in ks} for a, A in ARMKEYS.items()}


CURVES = {a: [[s, dm, l, at] for s, dm, l, at in rebase_val(A["va"], A["tr"])] for a, A in ARMKEYS.items()}
SIDE = {
    "fig1_stream": ("Held-out loss across the stream, one panel per condition, identical axes. The faint line is the smoothed training loss (EMA 31); diamonds are the end-of-stream re-measurement.", dict(vals("base", "own", "fin"), held_out_curves=CURVES)),
    "fig2_bwt": ("End-of-stream loss change per domain (final minus own-end; positive is forgetting).", vals("bwt")),
    "fig3_acquisition": ("Loss reduction relative to each condition's recorded base reference, per domain.", vals("acq")),
    "fig4_speed": ("Held-out loss inside each domain. The base reference is a dashed level with its value; the first measurement is at step 25. In the first domain each condition is carried back to its own base at step 0; later domains start from a model that has already trained on earlier domains, which was not measured on these windows.", dict(vals("base", "own"), held_out_curves=CURVES)),
    "fig5_control": ("The never-trained control bank: 8 windows after each domain for the Learner conditions, all 64 windows before and after for LoRA.", vals("ctrl")),
    "fig6_summary": ("Mean loss reduction and mean end-of-stream change in the three earlier domains.", SUM),
    "fig7_lr_ablation": ("LoRA at 2e-4 against LoRA at 2e-5 on the first domain, the other columns after those 300 steps, and the adapter norm.", LRV)}
bad = []
for name, (cap, v) in SIDE.items():
    png = hashlib.sha256(open(os.path.join(FIG, name + ".png"), "rb").read()).hexdigest()
    v = json.loads(json.dumps(v))
    side = {"figure": name, "caption": cap, "generator": "plots/report_figures.py",
            "style": "colours and fonts are set at the top of the generator; DejaVu Sans (bundled with matplotlib)",
            "matplotlib": matplotlib.__version__, "inputs": dict(sorted(USED.items())), "values": v, "png_sha256": png}
    ref = os.path.join(ROOT, "output", "four_domain_report", name + ".json")
    if CHECK:
        old = json.load(open(ref))
        if old["values"] != v or old["inputs"] != side["inputs"]:
            bad.append(name + ": values or inputs differ")
        elif old["matplotlib"] == matplotlib.__version__ and old["png_sha256"] != png:
            bad.append(name + ": png bytes differ")
    else:
        json.dump(side, open(ref, "w"), indent=1, ensure_ascii=False)
if CHECK:
    same = all(json.load(open(os.path.join(ROOT, "output", "four_domain_report", n + ".json")))["matplotlib"] == matplotlib.__version__ for n in SIDE)
    print("report figures check:", ("FAIL " + "; ".join(bad)) if bad else "PASS (7 figures: inputs, plotted values%s)" % (", PNG bytes" if same else "; PNG bytes not compared, matplotlib version differs"))
    sys.exit(1 if bad else 0)
print("report figures:", sorted(f for f in os.listdir(FIG) if f.endswith(".png")))
print("acq means:", [round(m, 4) for m in mu_acq], "| bwt means:", [round(b, 5) for b in bwt_mean])
