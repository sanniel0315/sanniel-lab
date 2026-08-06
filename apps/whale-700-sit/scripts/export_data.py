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

    # V2 判定若尚未填寫，承接 V1(0707) 已明確標示「符合」的既有結果。
    # 「有待商榷」不視為通過，仍維持未執行，避免放寬新版驗收標準。
    status = tests["判定"].fillna("").astype(str).str.strip()
    legacy = tests["V1(0707)對應"].fillna("").astype(str).str.strip()
    inherited = status.eq("") & legacy.eq("符合")
    tests.loc[inherited, "判定"] = "Pass"
    v2_value = tests["V2 實測值"].fillna("").astype(str).str.strip()
    tests.loc[inherited & v2_value.eq(""), "V2 實測值"] = (
        "沿用 V1(0707)：符合（正式 V2 驗收仍需補齊量化佐證）"
    )
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
