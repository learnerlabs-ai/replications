# tools

One script. It is the gate that every file in this repository has to pass before the repository
is published or changed.

```bash
python3 tools/leak_sweep.py            # sweep the whole repository
python3 tools/leak_sweep.py --self-test # prove the gate can still go red
```

Exit status 0 means clean, 1 means it found something, 2 means the gate itself is broken.

## What it looks for

Three classes, because there are three kinds of risk and they need different matching.

| Class | Matching | Catches |
|---|---|---|
| Stems | plain substring | roots with no innocent English carrier |
| Words | alphanumeric-boundary | words ordinary English also uses, where a substring match would fire constantly |
| Patterns | regular expression | learner ids, job ids, key prefixes, host names, internal paths |

The boundary for the second class is deliberately not `\b`. Underscore and hyphen are word
characters to `\b`, and they are exactly how internal identifiers are joined, so `\b` would let
the joined forms through while still catching the innocent ones. Treating only letters and digits
as "inside a word" gets this the right way round.

## Two properties it has to keep

**It must be able to go red.** `--self-test` plants five strings that must each fail and one
clean string that must pass. A gate nobody has watched fail is not a gate. Run it before trusting
a clean sweep.

**Its allowances must be readable and justified.** Every exemption is one line with the reason it
was added, in `ALLOW` at the top of the script. There are four. Three are phrases that belong to
the taught documents rather than to us, and one is the key placeholder printed in our own install
instructions. Adding a fifth is a deliberate act, not a convenience.

## Calibration

The gate was calibrated against the published demonstrations page, on the principle that copy
already approved for publication must pass. It failed that copy twice on the first run, and both
failures were the gate's fault rather than the copy's:

| It flagged | In | Verdict |
|---|---|---|
| `gate` | "two gates were set before the run" | Over-strict. Bare `gate` is ordinary experimental English. Removed; the specific compound stays. |
| `sk-your-key` | the install command | Over-strict. The documented placeholder. Allowed by exact phrase; the pattern still catches a real key. |
| `witness` | a colour variable inside the page's figure markup | Correct catch, and worth knowing: our own figure palette names a colour this. Any figure markup copied into this repository will trip it. |

## Why this directory is not published

The script and its term list spell out the exact vocabulary the published data must never
contain. Publishing them publishes the vocabulary, which is the thing the gate exists to protect.
The gate belongs in the private mirror, or in continuous integration with the list supplied as a
secret, and this directory is removed from the public copy.

The sweep skips its own files for the same reason a term list always contains its own terms. The
exclusion is printed on every run so that it is never silent.
