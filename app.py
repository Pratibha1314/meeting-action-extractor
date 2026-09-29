import sys
from datetime import date
from pathlib import Path
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent / "src"))
from preprocess import clean_text, split_sentences
from extract import extract, DailyQuota
from schema import ActionItem
from validate import merge_duplicates, check

def parse(text):
    segs = []
    for i, line in enumerate(l for l in text.splitlines() if l.strip()):
        line = clean_text(line)                      # drops timestamps and fillers first
        speaker, sep, body = line.partition(":")
        if not sep or len(speaker) > 30:             # no "Name:" prefix
            speaker, body = "Unknown", line
        for s in split_sentences(body):
            segs.append({"turn": i, "sent": 0,
                         "speaker": speaker.strip().title(), "text": s})
    return segs

st.title("Meeting Action-Item Extractor")
meeting_date = st.date_input("Meeting date", value=date.today())
up = st.file_uploader("Upload a transcript (.txt), one 'Speaker: sentence' per line", type=["txt"])
text = up.read().decode("utf-8") if up else st.text_area("...or paste it here", height=200)

if st.button("Extract action items") and text.strip():
    meeting = {"id": "upload", "date": meeting_date.isoformat(), "segments": parse(text)}
    with st.spinner("Extracting..."):
        try:
            raw = extract(meeting)
        except DailyQuota:
            st.error("Free daily quota reached. Try again after it resets.")
            st.stop()
    if raw is None:
        st.error("Extraction failed. Please try again.")
        st.stop()

    valid = []
    for r in raw:
        try:
            valid.append(ActionItem(**r).model_dump(mode="json"))
        except Exception:
            st.warning(f"Skipped an invalid item: {r}")

    full_text = " ".join(f"{s['speaker']} {s['text']}" for s in meeting["segments"]).lower()
    items = [check(i, meeting_date, full_text) for i in merge_duplicates(valid)]

    if not items:
        st.info("No action items found.")
    else:
        df = pd.DataFrame(items)[["task", "owner", "deadline", "confidence", "needs_review", "flags"]]
        df["flags"] = df["flags"].apply(", ".join)
        st.dataframe(df)
        st.download_button("Download CSV", df.to_csv(index=False), "action_items.csv")