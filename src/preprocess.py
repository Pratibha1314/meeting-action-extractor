import json, re
from pathlib import Path

FILLERS = re.compile(r"\b(um+|uh+|erm|you know|i mean)\b,?\s*", re.I)
TIMESTAMP = re.compile(r"[\[\(]\d{1,2}:\d{2}(:\d{2})?[\]\)]\s*")  # only bracketed, so "10:30" survives
SENT_SPLIT = re.compile(r'(?<=[.!?])\s+(?=[A-Z"])')

def clean_text(text):
    text = TIMESTAMP.sub("", text)
    text = FILLERS.sub("", text)
    return re.sub(r"\s+", " ", text).strip()

def split_sentences(text):
    return [s.strip() for s in SENT_SPLIT.split(text) if s.strip()]

def process_meeting(m):
    segments = []
    for turn_id, turn in enumerate(m["transcript"]):
        speaker = turn["speaker"].strip().title()
        for sent_id, sent in enumerate(split_sentences(clean_text(turn["text"]))):
            segments.append({"turn": turn_id, "sent": sent_id,
                             "speaker": speaker, "text": sent})
    return {"id": m["id"], "date": m["date"],
            "segments": segments, "action_items": m["action_items"]}

def to_text(meeting):
    """Flatten segments into 'Speaker: sentence' lines (used for the LLM prompt in Step 3)."""
    return "\n".join(f"{s['speaker']}: {s['text']}" for s in meeting["segments"])

if __name__ == "__main__":
    # quick sanity check on a messy line
    print(split_sentences(clean_text(
        "[00:12:03] Um, I'll, you know, send the file by 10:30. Thanks everyone!")))

    src = Path("data/raw/transcripts.jsonl")
    dst = Path("data/processed/segments.jsonl")
    dst.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with src.open() as fin, dst.open("w") as fout:
        for line in fin:
            fout.write(json.dumps(process_meeting(json.loads(line))) + "\n")
            n += 1
    print(f"Processed {n} meetings -> {dst}")