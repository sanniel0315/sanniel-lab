from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd


def clean(value):
    if pd.isna(value):
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def records(df: pd.DataFrame) -> list[dict]:
    return [
        {str(key): clean(value) for key, value in row.items()}
        for row in df.to_dict(orient="records")
    ]


def write_parts(rows: list[dict], output_dir: Path, prefix: str, chunk_size: int) -> list[str]:
    names = []
    for index in range(0, len(rows), chunk_size):
        name = f"{prefix}-{index // chunk_size + 1}.json"
        (output_dir / name).write_text(
            json.dumps(rows[index:index + chunk_size], ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        names.append(name)
    return names


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("workbook", type=Path)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()

    tests = pd.read_excel(args.workbook, sheet_name="1_SIT主表", dtype=object)
    tests = tests[tests["編號"].astype(str).str.match(r"^SIT-", na=False)].copy()
    tests["判定"] = tests["判定"].fillna("未執行").replace("", "未執行")

    questions = pd.read_excel(args.workbook, sheet_name="3_待釐清事項", dtype=object)
    questions = questions[questions["編號"].astype(str).str.match(r"^Q-", na=False)].copy()
    questions["狀態"] = questions["狀態"].fillna("Open").replace("", "Open")

    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    test_rows = records(tests)
    question_rows = records(questions)
    test_parts = write_parts(test_rows, args.manifest.parent, "tests", 13)
    question_parts = write_parts(question_rows, args.manifest.parent, "questions", 9)

    payload = {
        "meta": {
            "title": "Whale-700 視覺化雷達軟體 SIT",
            "source": args.workbook.name,
            "test_count": len(test_rows),
            "question_count": len(question_rows),
        },
        "test_parts": test_parts,
        "question_parts": question_parts,
    }
    args.manifest.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
