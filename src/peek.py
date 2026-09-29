import json, sys

mid = sys.argv[1] if len(sys.argv) > 1 else "meeting_000"
truth = {}
for line in open("data/processed/segments.jsonl"):
    m = json.loads(line)
    truth[m["id"]] = m
for line in open("data/predictions.jsonl"):
    p = json.loads(line)
    if p["id"] == mid:
        print("TRANSCRIPT:")
        for s in truth[mid]["segments"]:
            print(f"  {s['speaker']}: {s['text']}")
        print("\nANSWER KEY:")
        for a in truth[mid]["action_items"]:
            print(" ", a)
        print("\nPREDICTED:")
        for a in p["predicted"]:
            print(" ", a)