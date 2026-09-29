import json
from difflib import SequenceMatcher

def norm(t):
    return " ".join(t.lower().replace(".", "").split())

def same_task(a, b):
    return SequenceMatcher(None, norm(a), norm(b)).ratio() >= 0.85

truth = {}
for line in open("data/processed/segments.jsonl"):
    m = json.loads(line)
    truth[m["id"]] = m["action_items"]

tp = fp = fn = full = owner_ok = date_ok = skipped = 0
errors = []

for line in open("data/final.jsonl"):
    p = json.loads(line)
    if not p["items"]:          # failed extraction, not a real model miss
        skipped += 1
        continue
    gold = list(truth[p["id"]])
    for pred in p["items"]:
        hit = next((g for g in gold if same_task(g["task"], pred["task"])), None)
        if hit is None:
            fp += 1
            errors.append((p["id"], "EXTRA", pred["task"]))
            continue
        gold.remove(hit)
        tp += 1
        o = (hit["owner"] or "").lower() == (pred["owner"] or "").lower()
        d = hit["deadline"] == pred["deadline"]
        owner_ok += o
        date_ok += d
        if o and d:
            full += 1
        else:
            errors.append((p["id"], "WRONG", pred["task"],
                           f"owner {pred['owner']} vs {hit['owner']}",
                           f"date {pred['deadline']} vs {hit['deadline']}"))
    for g in gold:
        fn += 1
        errors.append((p["id"], "MISSED", g["task"]))

def f1(p, r):
    return 2 * p * r / (p + r) if p + r else 0

prec, rec = tp / max(tp + fp, 1), tp / max(tp + fn, 1)
fprec, frec = full / max(tp + fp, 1), full / max(tp + fn, 1)
print(f"Meetings skipped (failed extraction): {skipped}")
print(f"Task detection    P={prec:.2f}  R={rec:.2f}  F1={f1(prec, rec):.2f}")
print(f"Full match (task+owner+date)  P={fprec:.2f}  R={frec:.2f}  F1={f1(fprec, frec):.2f}")
print(f"Owner accuracy: {owner_ok}/{max(tp, 1)}   Deadline accuracy: {date_ok}/{max(tp, 1)}")
print("\nErrors:")
for e in errors:
    print(" ", e)
if not errors:
    print("  none")