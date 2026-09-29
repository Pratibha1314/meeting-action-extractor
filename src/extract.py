import json, sys, time, datetime as dt
from pathlib import Path
from google import genai
from google.genai import types
from preprocess import to_text

client = genai.Client()  # reads GEMINI_API_KEY from the environment
MODEL = "gemini-3-flash-preview"  # if "model not found", try "gemini-2.5-flash"

SYSTEM = """You extract action items from meeting transcripts.
Return ONLY a JSON array (no prose, no code fences). Each element:
{"task": str, "owner": str|null, "deadline": "YYYY-MM-DD"|null,
 "deadline_text": str|null, "confidence": float between 0 and 1}
Rules:
- Include only real commitments or assignments, not status updates or small talk.
- owner is the person assigned, or the speaker if they say "I'll ...". Use null if nobody is named.
- deadline_text is the exact phrase used ("by Friday"); deadline is that phrase resolved to a date using the meeting date. Use null for both if no deadline is given.
- confidence reflects how clearly the transcript states the task, owner and deadline.
- If there are no action items, return []."""

def extract(meeting, retries=3):
    d = dt.date.fromisoformat(meeting["date"])
    prompt = (f"Meeting date: {d.isoformat()} ({d.strftime('%A')})\n\n"
              f"Transcript:\n{to_text(meeting)}")
    raw = ""
    for attempt in range(retries):
        try:
            resp = client.models.generate_content(
                model=MODEL, contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM,
                    response_mime_type="application/json"),
            )
            raw = (resp.text or "").strip()
            break
        except Exception as e:  # usually a rate limit on the free tier
            print(f"  retry {attempt + 1} after error: {e}")
            time.sleep(20)
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(raw), None
    except json.JSONDecodeError:
        return [], raw  # keep the bad output so we can inspect it

if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 5  # test on a few first
    src = Path("data/processed/segments.jsonl")
    dst = Path("data/predictions.jsonl")
    with src.open() as fin, dst.open("w") as fout:
        for i, line in enumerate(fin):
            if i >= limit:
                break
            m = json.loads(line)
            items, bad = extract(m)
            fout.write(json.dumps({"id": m["id"], "predicted": items,
                                   "parse_error": bad}) + "\n")
            print(f"{m['id']}: {len(items)} items" + ("  (PARSE ERROR)" if bad else ""))
            time.sleep(5)  # stay under free-tier rate limits
    print(f"Saved -> {dst}")