#!/usr/bin/env python3
"""Pairing + statistics for the capability battery -- stdlib only.

Runs on the shipped per-item sample logs (answers/) and reproduces the published numbers
bit-for-bit. Implements the four pre-registered legs:

  1. Question-level paired differences   (Miller, arXiv:2411.00640 §4.2)
  2. Exact McNemar on discordant pairs   (binomial exact, two-sided)
  3. Cluster-robust SE for MMLU          (subject-clustered — the pre-registered primary form;
     on the published data the clustered SE was ~0.9x the naive paired SE, and it is used regardless)
  4. Paired Bayesian interval, small n   (Bowyer, arXiv:2503.01747; Dirichlet(1,1,1) over
                                          win/loss/tie, Monte-Carlo posterior, fixed seed)

PASS PREDICATE (pre-registered before the battery ran):
  a task PASSES iff (a) the 95% CI on the paired delta does NOT sit entirely below zero
  (no statistically significant negative delta), AND (b) the CI lower bound clears the
  non-inferiority margin  delta >= -1.0 pp  (MARGIN = -0.010).
Both legs use the CLUSTERED CI when clusters are given, else the plain paired CI.

Input row shape (one per item, per arm-pair): {"correct_a": 0|1, "correct_b": 0|1, "cluster": str|None}
where a = the learner arm, b = the base arm; delta per item = correct_a - correct_b.
"""
import json
import math
import re
import os
import random
import sys

MARGIN = -0.010          # the pre-registered non-inferiority bound: -1.0 percentage points
Z95 = 1.959963985        # two-sided 95%
BAYES_N_THRESHOLD = 500  # below this, the Bayesian interval is REPORTED alongside (Bowyer regime)
BAYES_DRAWS = 20000
BAYES_SEED = 0           # PYTHONHASHSEED=0 discipline: the posterior is reproducible byte-for-byte


# ---------------------------------------------------------------- 1. paired deltas (Miller §4.2)
def paired_delta(rows):
    """Mean per-item delta + naive paired SE + 95% CI."""
    n = len(rows)
    if n == 0:
        raise ValueError("no rows")
    d = [r["correct_a"] - r["correct_b"] for r in rows]
    mean = sum(d) / n
    if n == 1:
        return {"n": n, "mean": mean, "se": float("nan"), "ci95": (float("nan"), float("nan"))}
    var = sum((x - mean) ** 2 for x in d) / (n - 1)
    se = math.sqrt(var / n)
    return {"n": n, "mean": mean, "se": se, "ci95": (mean - Z95 * se, mean + Z95 * se)}


# ---------------------------------------------------------------- 2. exact McNemar
def mcnemar_exact(rows):
    """Two-sided exact binomial test on the discordant pairs (b01 = learner-only-right,
    b10 = base-only-right).  Returns p and the counts; p=1.0 when there are no discordants."""
    b01 = sum(1 for r in rows if r["correct_a"] == 1 and r["correct_b"] == 0)
    b10 = sum(1 for r in rows if r["correct_a"] == 0 and r["correct_b"] == 1)
    m = b01 + b10
    if m == 0:
        return {"b01": b01, "b10": b10, "p": 1.0}
    k = min(b01, b10)
    # two-sided exact: 2 * P(X <= k) under Binomial(m, 0.5), capped at 1
    tail = sum(math.comb(m, i) for i in range(0, k + 1)) / (2 ** m)
    return {"b01": b01, "b10": b10, "p": min(1.0, 2.0 * tail)}


# ---------------------------------------------------------------- 3. cluster-robust SE (MMLU subjects)
def clustered_delta(rows):
    """Cluster-robust variance of the mean paired delta, clustering by rows[i]['cluster'].
    var_hat = (1/n^2) * sum_g ( sum_{i in g} (d_i - mean) )^2  -- the standard CR0 sandwich for
    a mean.  Falls back to the naive SE when every cluster is a singleton or clusters are absent."""
    base = paired_delta(rows)
    groups = {}
    for r in rows:
        groups.setdefault(r.get("cluster") or "__none__", []).append(r["correct_a"] - r["correct_b"])
    if len(groups) <= 1 or all(len(v) == 1 for v in groups.values()):
        return {**base, "clusters": len(groups), "clustered": False}
    n, mean = base["n"], base["mean"]
    var = sum((sum(x - mean for x in g)) ** 2 for g in groups.values()) / (n * n)
    g = len(groups)
    var *= g / (g - 1)  # small-cluster correction
    se = math.sqrt(var)
    return {"n": n, "mean": mean, "se": se, "ci95": (mean - Z95 * se, mean + Z95 * se),
            "clusters": g, "clustered": True}


# ---------------------------------------------------------------- 4. paired Bayesian interval (small n)
def bayes_interval(rows, draws=BAYES_DRAWS, seed=BAYES_SEED):
    """Dirichlet(1,1,1) posterior over (win, loss, tie) item categories; the quantity is
    E[delta] = p_win - p_loss.  Monte-Carlo credible interval, seeded, reproducible."""
    w = sum(1 for r in rows if r["correct_a"] > r["correct_b"])
    l = sum(1 for r in rows if r["correct_a"] < r["correct_b"])
    t = len(rows) - w - l
    rng = random.Random(seed)
    xs = []
    for _ in range(draws):
        gw = rng.gammavariate(w + 1, 1.0)
        gl = rng.gammavariate(l + 1, 1.0)
        gt = rng.gammavariate(t + 1, 1.0)
        s = gw + gl + gt
        xs.append((gw - gl) / s)
    xs.sort()
    lo, hi = xs[int(0.025 * draws)], xs[int(0.975 * draws) - 1]
    return {"win": w, "loss": l, "tie": t, "ci95": (lo, hi), "draws": draws, "seed": seed}


# ---------------------------------------------------------------- the pre-registered predicate
def pass_predicate(ci_lo, ci_hi, margin=MARGIN):
    """PASS iff no significant negative delta (CI not entirely below 0) AND non-inferior
    (CI lower bound >= margin).  This REPLACES the old `mean > 0` clause -- a preservation
    claim never requires improvement."""
    no_sig_negative = ci_hi >= 0.0
    non_inferior = ci_lo >= margin
    # Three-way label for the publication: a task can show NO evidence of harm and still be too
    # noisy to certify the margin (CI half-width > |margin|).  That is "underpowered_for_margin",
    # NOT a fail -- the predicate refuses to rubber-stamp an underpowered non-inferiority claim,
    # and the report says so in words rather than hiding it in a boolean.
    if no_sig_negative and non_inferior:
        label = "pass"
    elif not no_sig_negative:
        label = "significant_negative"
    else:
        label = "underpowered_for_margin"
    return {"pass": bool(no_sig_negative and non_inferior), "label": label,
            "no_sig_negative": bool(no_sig_negative), "non_inferior": bool(non_inferior),
            "margin": margin, "ci95": (ci_lo, ci_hi)}


# ---------------------------------------------------------------- per-task report
def task_report(task, rows, use_clusters=False):
    """One task, one (model, baseline) pairing -> the full stats block."""
    stats = clustered_delta(rows) if use_clusters else paired_delta(rows)
    rep = {"task": task, "n": stats["n"], "mean_delta": stats["mean"], "se": stats["se"],
           "ci95": list(stats["ci95"]), "clustered": bool(stats.get("clustered", False)),
           "clusters": stats.get("clusters"), "mcnemar": mcnemar_exact(rows)}
    if stats["n"] < BAYES_N_THRESHOLD:
        rep["bayes"] = {k: (list(v) if isinstance(v, tuple) else v)
                        for k, v in bayes_interval(rows).items()}
    rep["verdict"] = pass_predicate(*stats["ci95"])
    return rep


# ---------------------------------------------------------------- selftest ($0, offline, seeded)
def _mk(n, both, a_only, b_only, cluster=None):
    rows = ([{"correct_a": 1, "correct_b": 1}] * both + [{"correct_a": 1, "correct_b": 0}] * a_only
            + [{"correct_a": 0, "correct_b": 1}] * b_only)
    rows += [{"correct_a": 0, "correct_b": 0}] * (n - len(rows))
    for r in rows:
        r["cluster"] = cluster
    return rows


def _selftest():
    ok = 0

    # T1: identical arms -> delta 0, CI touches 0, PASS (the old mean>0 clause would FAIL this)
    r = _mk(1000, both=600, a_only=0, b_only=0)
    t = task_report("t1", r)
    assert t["mean_delta"] == 0.0 and t["verdict"]["pass"], t
    assert t["mcnemar"]["p"] == 1.0
    ok += 1; print("  ok  T1 identical arms PASS at delta 0 (mean>0 clause corrected)")

    # T2: clear negative (5pp drop, n=2000) -> significant negative AND inferior -> FAIL both legs
    r = _mk(2000, both=1000, a_only=50, b_only=150)
    t = task_report("t2", r)
    assert not t["verdict"]["pass"] and not t["verdict"]["no_sig_negative"] \
        and not t["verdict"]["non_inferior"], t
    assert t["mcnemar"]["p"] < 0.001
    ok += 1; print("  ok  T2 5pp drop FAILS (both legs) with McNemar p<0.001")

    # T3: tiny wobble at LOW discordance (-0.08pp on 1.7% discordants, n=1250 -- the regime a
    # genuinely-preserving learner produces) -> not significant, CI inside the margin -> PASS
    r = _mk(1250, both=700, a_only=10, b_only=11)
    t = task_report("t3", r)
    assert t["verdict"]["pass"] and t["verdict"]["label"] == "pass", t
    ok += 1; print("  ok  T3 -0.08pp wobble @1.7%% discordance PASSES (the preserving regime)")

    # T3b: SAME wobble at HIGH discordance (10%, n=1000) -> CI wider than the margin -> the
    # verdict is 'underpowered_for_margin', NOT pass and NOT significant_negative.  This is the
    # power property caught at selftest time: a noisy small task cannot certify non-inferiority,
    # and the predicate says so instead of rubber-stamping it.
    r = _mk(1000, both=500, a_only=49, b_only=51)
    t = task_report("t3b", r)
    assert not t["verdict"]["pass"] and t["verdict"]["label"] == "underpowered_for_margin", t
    ok += 1; print("  ok  T3b 10%% discordance -> 'underpowered_for_margin' (honest three-way label)")

    # T4: significant but tiny negative (-0.55pp, n=14000, MMLU-scale) -> sig-negative leg FAILS
    r = _mk(14000, both=7000, a_only=100, b_only=177)
    t = task_report("t4", r)
    assert not t["verdict"]["no_sig_negative"] and t["verdict"]["non_inferior"], t
    assert not t["verdict"]["pass"]
    ok += 1; print("  ok  T4 significant -0.55pp FAILS leg (a) though inside the margin -- strict by design")

    # T5: McNemar exact value check -- b01=0, b10=5 -> p = 2*(1/32) = 0.0625
    r = _mk(100, both=50, a_only=0, b_only=5)
    m = mcnemar_exact(r)
    assert abs(m["p"] - 0.0625) < 1e-12, m
    ok += 1; print("  ok  T5 McNemar exact p = 0.0625 on 0-vs-5 discordants")

    # T6: clustering inflates SE when deltas are cluster-correlated
    rows = []
    for ci in range(10):  # 10 clusters, deltas perfectly correlated within cluster
        d = 1 if ci < 5 else -1
        for _ in range(50):
            rows.append({"correct_a": 1 if d == 1 else 0, "correct_b": 0 if d == 1 else 1,
                         "cluster": "c%d" % ci})
    naive = paired_delta(rows)["se"]
    clus = clustered_delta(rows)
    assert clus["clustered"] and clus["se"] > 2.5 * naive, (naive, clus["se"])
    ok += 1; print("  ok  T6 cluster-robust SE %.4f > 2.5x naive %.4f on correlated clusters"
                   % (clus["se"], naive))

    # T7: Bayesian interval reproducible + sane on small n (Winogrande-ish shape)
    r = _mk(300, both=150, a_only=10, b_only=12)
    b1, b2 = bayes_interval(r), bayes_interval(r)
    assert b1 == b2, "posterior not reproducible"
    assert b1["ci95"][0] < 0 < b1["ci95"][1], b1
    ok += 1; print("  ok  T7 Bayesian interval reproducible (seed %d) + spans 0 on a null draw" % BAYES_SEED)

    # T8: predicate truth table, directly
    assert pass_predicate(-0.005, 0.004)["pass"]            # wobble
    assert not pass_predicate(-0.02, -0.001)["pass"]        # significant negative
    assert not pass_predicate(-0.02, 0.01)["pass"]          # non-inferiority breach
    assert pass_predicate(0.001, 0.02)["pass"]              # positive
    ok += 1; print("  ok  T8 predicate truth table 4/4")

    print("bp1_stats selftest: %d/9 PASSED ($0, offline, seeded)" % ok)
    return 0




# ---------------------------------------------------------------- public pairing front-end
# Pair two directories of lm-eval sample JSONLs (files named *_<task>.jsonl with per-item
# rows carrying doc_id + acc), compute per-task paired stats + the subject-clustered MMLU
# aggregate, and print a JSON report.  Usage:
#   python3 pair_and_stats.py --model-dir A/ --baseline-dir B/
import argparse, glob, gzip, os

def _load(path):
    rows = {}
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt") as fh:
        for i, ln in enumerate(l for l in fh if l.strip()):
            d = json.loads(ln)
            did = d.get("doc_id", i)
            if did in rows:
                raise SystemExit("duplicate doc_id %r in %s" % (did, path))
            rows[did] = float(d.get("acc", d.get("exact_match", 0.0)))
    return rows

def _task_of(path):
    b = os.path.basename(path)
    for suf in (".jsonl.gz", ".jsonl"):
        if b.endswith(suf):
            b = b[:-len(suf)]
    if b.startswith("bp1_samples_") and b.count("_") >= 3:   # raw-log naming
        b = b.split("_", 3)[-1]
    return re.sub(r"^s\d+_", "", b)          # strip a leading seed tag (s0_, s1_, ...)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-dir", required=True)
    ap.add_argument("--baseline-dir", required=True)
    a = ap.parse_args()
    def _find(d):
        hits = glob.glob(os.path.join(d, "*.jsonl")) + glob.glob(os.path.join(d, "*.jsonl.gz"))
        return {_task_of(p): p for p in hits}
    fa, fb = _find(a.model_dir), _find(a.baseline_dir)
    shared = sorted(set(fa) & set(fb))
    if not shared:
        raise SystemExit("no shared task files")
    report, agg_rows = {}, []
    for t in shared:
        ra, rb = _load(fa[t]), _load(fb[t])
        if set(ra) != set(rb):
            raise SystemExit("doc_id sets differ on %s" % t)
        rows = [{"correct_a": ra[d], "correct_b": rb[d], "cluster": None} for d in sorted(ra)]
        report[t] = task_report(t, rows)
        if t.startswith("mmlu_"):
            agg_rows += [{"correct_a": ra[d], "correct_b": rb[d], "cluster": t} for d in sorted(ra)]
    if agg_rows:
        report["mmlu_AGGREGATE_clustered"] = task_report("mmlu_AGGREGATE_clustered", agg_rows,
                                                         use_clusters=True)
    print(json.dumps(report, indent=1, sort_keys=True))

if __name__ == "__main__" and os.environ.get("PAS_MAIN", "1") == "1":
    main()
