import json
from collections import Counter
from datetime import date, timedelta
from difflib import SequenceMatcher
from pathlib import Path

PENALTY = 0.8  # confidence multiplier per flag

def norm(t):
    return " ".join(t.lower().split())

def similar(a, b, threshold=0.85):
    return SequenceMatcher(None, norm(a), norm(b)).ratio() >= threshold

def merge_duplicates(items):
    merged = []
    for it in items:
        for kept in merged:
            if similar(kept["task"], it["task"]):
                for f in ("owner", "deadline", "deadline_text"):
                    if kept[f] is None and it[f] is not None:
                        kept[f] = it[f]
                kept["confidence"] = max(kept["confidence"], it["confidence"])
                kept["flags"].append("merged_duplicate")
                break
        else:
            merged.append({**it, "flags": []})
    return merged

def check(item, meeting_date, transcript_text):
    flags = item["flags"]
    if item["owner"] is None:
        flags.append("missing_owner")
    elif item["owner"].lower() not in transcript_text:
        flags.append("unknown_owner")

    d = date.fromisoformat(item["deadline"]) if item["deadline"] else None
    if item["deadline_text"] and d is None:
        flags.append("unresolved_deadline")
    if d and d < meeting_date:
        flags.append("deadline_in_past")
    if d and d > meeting_date + timedelta(days=180):
        flags.append("deadline_far")

    problems = [f for f in flags if f != "merged_duplicate"]
    item["confidence"] = round(item["confidence"] * PENALTY ** len(problems), 2)
    item["needs_review"] = bool(problems)
    return item

if __name__ == "__main__":
    meetings = {}
    for line in open("data/processed/segments.jsonl"):
        m = json.loads(line)
        text = " ".join(f"{s['speaker']} {s['text']}" for s in m["segments"]).lower()
        meetings[m["id"]] = (date.fromisoformat(m["date"]), text)

    counts, out = Counter(), []
    for line in open("data/validated.jsonl"):
        v = json.loads(line)
        md, text = meetings[v["id"]]
        items = [check(i, md, text) for i in merge_duplicates(v["items"])]
        for i in items:
            counts.update(i["flags"])
        out.append({"id": v["id"], "date": md.isoformat(), "items": items})

    Path("data/final.jsonl").write_text("".join(json.dumps(o) + "\n" for o in out))
    print(f"{len(out)} meetings, {sum(len(o['items']) for o in out)} items")
    print("Flags:", dict(counts))

    # quick duplicate self-test
    demo = merge_duplicates([
        {"task": "send the budget to finance", "owner": None, "deadline": None,
         "deadline_text": None, "confidence": 0.7},
        {"task": "Send the budget to finance.", "owner": "Priya", "deadline": "2026-10-03",
         "deadline_text": "by Friday", "confidence": 0.9},
    ])
    print("Duplicate test (expect 1 item, owner Priya):", demo)