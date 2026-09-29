# AI Meeting Action-Item Extractor

Turns meeting transcripts into structured action items (task, owner, deadline, status, confidence), with validation rules and a Streamlit upload interface.

## Pipeline
1. `generate_data.py`: synthetic transcripts with known answer keys
2. `preprocess.py`: clean text, split by speaker and sentence
3. `extract.py`: LLM extraction (Gemini) to JSON
4. `schema.py`: Pydantic schema (task, owner, deadline, status, confidence)
5. `validate.py`: date checks, missing-owner flags, duplicate merging, confidence penalties
6. `evaluate.py` and `app.py`: accuracy evaluation and Streamlit interface

## Setup
```
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:GEMINI_API_KEY="your-key"
```

## Run
```
python src/generate_data.py
python src/preprocess.py
python src/extract.py 30
python src/schema.py
python src/validate.py
python src/evaluate.py
streamlit run app.py
```

## Results (30 synthetic meetings, 91 action items)
- Task detection: precision 1.00, recall 0.99, F1 0.99
- Full match (task + owner + deadline): F1 0.95
- Owner accuracy 90/91, deadline accuracy 88/91

## Limitations
## Limitations
- Data is synthetic and templated, so scores are optimistic; real meetings are messier.
- Small sample (30 meetings, 91 items): one error moves the numbers noticeably.
- Of 5 errors, 3 are date-label ambiguities ("next Monday", or "by Friday" when the meeting is held on a Friday), where the model's reading is defensible. 2 are genuine: one missed "We need to..." item with no owner, and one owner wrongly inferred from "We need to...".
- The prompt was updated partway through, so the first 14 meetings used an earlier prompt.
- LLM confidence is overconfident (often 1.0). Lower scores come from the validation rules (missing owner, unresolved date), so treat confidence as a ranking signal, not a probability.
- Free-tier API limits meant the dataset was extracted over several runs.