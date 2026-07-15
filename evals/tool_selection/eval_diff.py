"""Compare two eval_run.py result files and flag regressions.

Usage: python eval_diff.py old.json new.json
A regression = a case whose pass-rate DROPPED old->new (the trim removed something the
model relied on). A case already failing on OLD is not a regression from the trim.
Exit code 1 if any regression, else 0.
"""
import json
import sys


def diff(old_path, new_path):
    old = json.load(open(old_path))
    new = json.load(open(new_path))
    o, n = old["results"], new["results"]

    print(f"A/B  old_src={old['src']}  new_src={new['src']}  model={new['model']}  k={new['k']}\n")
    regress, improved, unchanged, preexisting = [], [], [], []
    for cid, nr in n.items():
        if cid not in o:
            continue
        ro, rn = o[cid]["rate"], nr["rate"]
        if rn < ro:
            regress.append((cid, ro, rn, nr["probes"]))
        elif rn > ro:
            improved.append((cid, ro, rn))
        else:
            (preexisting if rn < 1.0 else unchanged).append(cid)

    for cid, ro, rn, probes in regress:
        print(f"  REGRESSION  {cid:16} {int(ro*100):3d}% -> {int(rn*100):3d}%   {probes}")
    for cid, ro, rn in improved:
        print(f"  improved    {cid:16} {int(ro*100):3d}% -> {int(rn*100):3d}%")
    if preexisting:
        print(f"  (pre-existing <100% on both, not trim-caused: {', '.join(preexisting)})")

    print(f"\n  {len(regress)} regression(s), {len(improved)} improved, "
          f"{len(unchanged)+len(preexisting)} unchanged")
    print("  VERDICT:", "TRIM SAFE — no regressions" if not regress
          else "REVIEW — the trim changed behavior on the cases above")
    return regress


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: python eval_diff.py old.json new.json")
    sys.exit(1 if diff(sys.argv[1], sys.argv[2]) else 0)
