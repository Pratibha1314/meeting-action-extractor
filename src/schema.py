import json
from datetime import date
from pathlib import Path
from typing import Literal, Optional
from pydantic import BaseModel, Field, ValidationError, field_validator

class ActionItem(BaseModel):
    task: str = Field(min_length=3)
    owner: Optional[str] = None
    deadline: Optional[date] = None        # "2026-10-07" is parsed into a real date
    deadline_text: Optional[str] = None
    status: Literal["open", "done"] = "open"
    confidence: float = Field(ge=0, le=1)

    @field_validator("task", "owner", "deadline_text", mode="before")
    @classmethod
    def strip_text(cls, v):
        return v.strip() if isinstance(v, str) else v

if __name__ == "__main__":
    src = Path("data/predictions.jsonl")
    dst = Path("data/validated.jsonl")
    ok = bad = 0
    with src.open() as fin, dst.open("w") as fout:
        for line in fin:
            p = json.loads(line)
            valid, errors = [], []
            for raw in p["predicted"]:
                try:
                    valid.append(ActionItem(**raw).model_dump(mode="json"))
                    ok += 1
                except ValidationError as e:
                    errors.append({"item": raw, "error": str(e)})
                    bad += 1
            fout.write(json.dumps({"id": p["id"], "items": valid,
                                   "schema_errors": errors}) + "\n")
    print(f"Valid items: {ok}, rejected: {bad} -> {dst}")