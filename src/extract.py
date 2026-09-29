import json, sys, time, datetime as dt
from pathlib import Path
from google import genai
from google.genai import types
from preprocess import to_text

client = genai.Client()  # reads GEMINI_API_KEY from the environment
MODEL = "gemini-3-flash-preview"  # if quota runs out, run src/list_models.py to find another model

SYSTEM = """You extract action items from meeting transcripts.
Return ONLY a JSON array (no prose, no code fences). Each element:
{"task": str, "owner": str|null, "deadline": "YYYY-MM-DD"|null,
 "deadline_text": str|null, "confidence": float between 0 and 1}
Rules:
- Include only real commitments or assignments, not status updates or small talk.
- owner is the person assigned, or the speaker if they say "I'll ...". Use null if nobody is named.
- deadline_text is the exact phrase used ("by Friday"); deadline is that phrase resolved to a date using the meeting date. Use null for both if no deadline is given.
- "next <weekday>" means the nearest upcoming <weekday> after the meeting date.
- confidence reflects how clearly the transcript states the task, owner and deadline.
- If there are no action items, return []."""

class DailyQuota(Exception):
    pass

def extract(meeting, retries=3):
    d = dt.date.fromisoformat(meeting["date"])
    prompt = (f"Meeting date: {d.isoformat()} ({d.strftime('%A')})\n\n"
              f"Transcript:\n{to_text(meeting)}")
    for attempt in range(retries):
        try:
            resp = client.models.generate_content(
                model=MODEL, contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM,
                    response_mime_type="application/json"),
            )
            raw = (resp.text or "").strip()
            raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            return json.loads(raw)
        except json.JSONDecodeError:
            print("  bad JSON, retrying")
        except Exception as e:
            msg = str(e)
            if "PerDay" in msg:
                raise DailyQuota()
            print(f"  retry {attempt + 1} after error: {msg[:120]}")
            time.sleep(20)
    return None  # failed after all retries

if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    src = Path("data/processed/segments.jsonl")
    dst = Path("data/predictions.jsonl")

    # keep only good earlier results, so failed meetings get retried
    good = []
    if dst.exists():
        good = [l for l in dst.open() if json.loads(l)["predicted"]]
    dst.write_text("".join(good))
    done = {json.loads(l)["id"] for l in good}

    with src.open() as fin, dst.open("a") as fout:
        for i, line in enumerate(fin):
            if i >= limit:
                break
            m = json.loads(line)
            if m["id"] in done:
                continue
            try:
                items = extract(m)
            except DailyQuota:
                print("Daily free quota reached. Run again tomorrow, or switch models.")
                break
            if items is None:
                print(f"{m['id']}: FAILED, will retry next run")
                continue
            fout.write(json.dumps({"id": m["id"], "predicted": items}) + "\n")
            fout.flush()
            print(f"{m['id']}: {len(items)} items")
            time.sleep(5)
    print("Done.")