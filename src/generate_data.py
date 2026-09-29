import json, random
import datetime as dt
from pathlib import Path

random.seed(42)

PEOPLE = ["Priya", "Rahul", "Ananya", "Karthik", "Meera", "Arjun"]
TASKS = [
    "send the revised budget to finance", "update the project roadmap",
    "fix the login bug", "schedule the client demo",
    "prepare the Q4 slides", "review the vendor contract",
    "write the test cases for the API", "share the meeting notes",
]
FILLER = [
    "Good morning everyone, let's get started.",
    "The client seemed happy with the last release.",
    "We finished the onboarding module last week.",
    "Traffic was terrible today, sorry I'm late.",
    "Sales numbers look stable this month.",
    "Thanks, that's a helpful update.",
]

def next_weekday(d, weekday):  # Mon=0 ... Sun=6
    return d + dt.timedelta(days=(weekday - d.weekday()) % 7 or 7)

def pick_deadline(d):
    far = d + dt.timedelta(days=random.randint(8, 20))
    options = [
        ("tomorrow", d + dt.timedelta(days=1)),
        ("by Friday", next_weekday(d, 4)),
        ("next Monday", next_weekday(d, 0)),
        (f"by {far.strftime('%B')} {far.day}", far),
        (None, None),
    ]
    return random.choice(options)

def make_action(speakers, meeting_date, task):   # add the task parameter
    dl_text, dl_date = pick_deadline(meeting_date)   # delete the old "task = random.choice(TASKS)" line
    dl = f" {dl_text}" if dl_text else ""
    speaker = random.choice(speakers)
    style = random.choice(["ask", "self", "assign", "nobody"])
    if style == "ask":
        owner = random.choice([p for p in speakers if p != speaker])
        text = f"{owner}, can you {task}{dl}?"
    elif style == "self":
        owner, text = speaker, f"I'll {task}{dl}."
    elif style == "assign":
        owner = random.choice([p for p in speakers if p != speaker])
        text = f"{owner} will {task}{dl}."
    else:
        owner, text = None, f"We need to {task}{dl}."
    item = {
        "task": task,
        "owner": owner,
        "deadline": dl_date.isoformat() if dl_date else None,
        "deadline_text": dl_text,
    }
    return {"speaker": speaker, "text": text}, item

def make_meeting(i):
    date = dt.date(2026, 9, 1) + dt.timedelta(days=random.randint(0, 40))
    speakers = random.sample(PEOPLE, k=random.randint(3, 4))
    turns = [{"speaker": random.choice(speakers), "text": t}
             for t in random.sample(FILLER, k=4)]
    items = []
    tasks = random.sample(TASKS, k=random.randint(2, 4))   # unique tasks
    for task in tasks:
        turn, item = make_action(speakers, date, task)
        turns.insert(random.randint(1, len(turns)), turn)
        items.append(item)
    return {"id": f"meeting_{i:03d}", "date": date.isoformat(),
            "transcript": turns, "action_items": items}

if __name__ == "__main__":
    out = Path("data/raw/transcripts.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as f:
        for i in range(60):
            f.write(json.dumps(make_meeting(i)) + "\n")
    print(f"Wrote 60 meetings to {out}")