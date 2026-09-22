"""Check Learning API input files locally before you upload them. Standard library only; sends nothing; costs nothing.

It applies the same format rules the service applies, plus a size check that is guaranteed safe:

  * training JSONL: one JSON object per line with exactly `row_id`, `prompt` and `answer`, each a non-empty string, `row_id`
    unique, at most MAX_ROWS rows;
  * monitor panels JSON: {"schema": "pumod_monitor_v1", "panels": {name: [{id, prompt, answer}, ...]}}, at most MAX_PANELS
    panels of 1..MAX_PANEL_ROWS rows;
  * evaluation JSONL: one object per line with exactly `id`, `prompt`, `expected`, non-empty strings, unique ids, at most
    MAX_EVAL_ROWS rows; no evaluation prompt may equal a training or monitor prompt after lower-casing, collapsing whitespace
    and removing trailing punctuation (the service refuses such an evaluation with 409 eval_overlap).

TOKEN LIMITS. The service counts tokens with its tokenizer when a training session starts. Every token covers at least one
byte of UTF-8 text, so a prompt of at most MAX_PROMPT_TOKENS bytes can never exceed MAX_PROMPT_TOKENS tokens, and the same
holds for answers and totals. This script therefore reports each row as SAFE (passes by bytes, so it passes for certain) or
CHECK (over the byte bound: it may still pass, because typical text is 3 to 4 bytes per token, but only the service can say).
A session refused for a token limit ends with status failed and error limits_exceeded before any training.

Usage:
    python3 validate_learning_inputs.py --train train.jsonl [--panels panels.json] [--eval eval.jsonl]
Exit status 0 = no format errors (CHECK rows are warnings); 1 = at least one error.
"""
import argparse, json, re, sys

# The limits of the service at https://api.learnerlabs.ai/learning/v1 (also stated in its OpenAPI document).
MAX_ROWS = 24000
MAX_PROMPT_TOKENS = 1024
MAX_ANSWER_TOKENS = 1024          # includes the end-of-sequence token the service appends
MAX_PRESENTED_TOKENS = 2000000    # prompt + answer tokens over the whole file
MAX_SUPERVISED_TOKENS = 1200000   # answer tokens (with end tokens) over the whole file
MAX_PANELS = 12
MAX_PANEL_ROWS = 256
MAX_EVAL_ROWS = 4000

_WS = re.compile(r"\s+")


def normalize(s):
    s = _WS.sub(" ", str(s or "").strip().lower())
    return s.rstrip(" .!?,;:")


def _nb(s):
    return len(s.encode("utf-8"))


def read_jsonl(path, keys, idkey, errors, label):
    rows, ids = [], set()
    with open(path, "rb") as f:
        raw = f.read()
    for n, line in enumerate(raw.decode("utf-8", "strict").splitlines(), 1):
        if not line.strip():
            continue
        try:
            o = json.loads(line)
        except ValueError as e:
            errors.append("%s line %d: not JSON (%s)" % (label, n, e)); continue
        if not isinstance(o, dict) or set(o) != set(keys):
            got = sorted(o) if isinstance(o, dict) else type(o).__name__
            errors.append("%s line %d: must have exactly %s, got %s" % (label, n, sorted(keys), got)); continue
        if not all(isinstance(o[k], str) and o[k] for k in keys):
            errors.append("%s line %d: %s must be non-empty strings" % (label, n, ", ".join(keys))); continue
        if o[idkey] in ids:
            errors.append("%s line %d: duplicate %s %r" % (label, n, idkey, o[idkey])); continue
        ids.add(o[idkey]); rows.append(o)
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--train"); ap.add_argument("--panels"); ap.add_argument("--eval")
    a = ap.parse_args(argv)
    if not (a.train or a.panels or a.eval):
        ap.error("give at least one of --train, --panels, --eval")
    errors, warn = [], []
    train, monitor = [], []
    if a.train:
        train = read_jsonl(a.train, ("row_id", "prompt", "answer"), "row_id", errors, "train")
        if len(train) > MAX_ROWS:
            errors.append("train: %d rows > %d" % (len(train), MAX_ROWS))
        pres = sup = 0
        for r in train:
            pb, ab = _nb(r["prompt"]), _nb(r["answer"]) + 1
            pres += pb + ab - 1; sup += ab
            if pb > MAX_PROMPT_TOKENS:
                warn.append("train %r: prompt is %d bytes (> %d): CHECK" % (r["row_id"], pb, MAX_PROMPT_TOKENS))
            if ab > MAX_ANSWER_TOKENS:
                warn.append("train %r: answer is %d bytes + end token (> %d): CHECK" % (r["row_id"], ab - 1, MAX_ANSWER_TOKENS))
        if pres > MAX_PRESENTED_TOKENS:
            warn.append("train: %d total bytes (> %d tokens allowed): CHECK" % (pres, MAX_PRESENTED_TOKENS))
        if sup > MAX_SUPERVISED_TOKENS:
            warn.append("train: %d answer bytes (> %d tokens allowed): CHECK" % (sup, MAX_SUPERVISED_TOKENS))
        print("train: %d rows, %d prompt+answer bytes, %d answer bytes" % (len(train), pres, sup))
    if a.panels:
        try:
            m = json.load(open(a.panels, encoding="utf-8"))
        except ValueError as e:
            m = None; errors.append("panels: not JSON (%s)" % e)
        if m is not None:
            if not isinstance(m, dict) or m.get("schema") != "pumod_monitor_v1" or not isinstance(m.get("panels"), dict) or set(m) - {"schema", "panels"}:
                errors.append('panels: must be {"schema": "pumod_monitor_v1", "panels": {name: [rows]}}')
            else:
                if len(m["panels"]) > MAX_PANELS:
                    errors.append("panels: %d panels > %d" % (len(m["panels"]), MAX_PANELS))
                for name, rows in m["panels"].items():
                    if not isinstance(rows, list) or not rows or len(rows) > MAX_PANEL_ROWS:
                        errors.append("panel %r: must carry 1..%d rows" % (name, MAX_PANEL_ROWS)); continue
                    for r in rows:
                        if not isinstance(r, dict) or set(r) != {"id", "prompt", "answer"} or not all(isinstance(r[k], str) and r[k] for k in r):
                            errors.append("panel %r: rows must be {id, prompt, answer} non-empty strings" % name); break
                        monitor.append(r["prompt"])
                print("panels: %d panels, %d rows" % (len(m["panels"]), len(monitor)))
    if a.eval:
        ev = read_jsonl(a.eval, ("id", "prompt", "expected"), "id", errors, "eval")
        if len(ev) > MAX_EVAL_ROWS:
            errors.append("eval: %d rows > %d" % (len(ev), MAX_EVAL_ROWS))
        tr = {normalize(r["prompt"]) for r in train}; mo = {normalize(p) for p in monitor}
        for r in ev:
            k = normalize(r["prompt"])
            if k in tr:
                errors.append("eval %r: prompt equals a training prompt (eval_overlap)" % r["id"])
            if k in mo:
                errors.append("eval %r: prompt equals a monitor prompt (eval_overlap)" % r["id"])
        print("eval: %d rows%s" % (len(ev), "" if a.train or a.panels else " (overlap not checked: pass --train and --panels too)"))
    for w in warn:
        print("WARNING " + w)
    for e in errors:
        print("ERROR " + e)
    print("OK: no format errors" if not errors else "FAILED: %d error(s)" % len(errors))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
