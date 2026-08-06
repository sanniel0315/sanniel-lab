from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
SITE_DIR = ROOT / "site" / "whale-700-sit"
MANIFEST_PATH = SITE_DIR / "data-manifest.json"
MARKER_RE = re.compile(r"<!--\s*SANNIEL_SIT_UPDATE\s*(\{.*?\})\s*SANNIEL_SIT_UPDATE\s*-->", re.DOTALL)
ALLOWED_TEST_FIELDS = {"判定", "V2 實測值", "缺失單號", "備註 / 待釐清"}
ALLOWED_QUESTION_FIELDS = {"狀態", "期限", "廠商回復", "需提供專案", "需提供項目"}
TEST_STATUSES = {"未執行", "Pass", "Fail", "Pending", "N/A", "Doc"}
QUESTION_STATUSES = {"Open", "In Progress", "Blocked", "Closed"}

class UpdateError(RuntimeError):
    pass

def load_event() -> dict[str, Any]:
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        raise UpdateError("GITHUB_EVENT_PATH is missing")
    return json.loads(Path(event_path).read_text(encoding="utf-8"))

def authorize(event: dict[str, Any]) -> None:
    issue = event.get("issue") or {}
    login = ((issue.get("user") or {}).get("login") or "").lower()
    association = str(issue.get("author_association") or "").upper()
    owner = os.environ.get("GITHUB_REPOSITORY_OWNER", "").lower()
    if not owner or login != owner or association != "OWNER":
        raise UpdateError(f"unauthorized issue author: login={login!r}, association={association!r}")

def extract_payload(body: str) -> dict[str, Any]:
    match = MARKER_RE.search(body or "")
    if not match:
        raise UpdateError("structured SANNIEL_SIT_UPDATE payload not found")
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise UpdateError(f"invalid JSON payload: {exc}") from exc
    if payload.get("schema") != 1:
        raise UpdateError("unsupported payload schema")
    if payload.get("type") not in {"test", "question"}:
        raise UpdateError("type must be test or question")
    if not isinstance(payload.get("id"), str) or not payload["id"].strip():
        raise UpdateError("id is required")
    if not isinstance(payload.get("changes"), dict):
        raise UpdateError("changes must be an object")
    return payload

def clean_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        return value if value else None
    return value

def validate_changes(payload: dict[str, Any]) -> dict[str, Any]:
    kind = payload["type"]
    changes = {str(k): clean_value(v) for k, v in payload["changes"].items()}
    allowed = ALLOWED_TEST_FIELDS if kind == "test" else ALLOWED_QUESTION_FIELDS
    unexpected = set(changes) - allowed
    if unexpected:
        raise UpdateError(f"unsupported fields: {sorted(unexpected)}")
    if kind == "test":
        status = changes.get("判定")
        if status not in TEST_STATUSES:
            raise UpdateError(f"invalid test status: {status!r}")
        if status == "Fail" and not changes.get("缺失單號"):
            raise UpdateError("Fail requires 缺失單號")
        if status == "Pass" and not changes.get("V2 實測值"):
            raise UpdateError("Pass requires V2 實測值 / evidence summary")
    else:
        status = changes.get("狀態")
        if status not in QUESTION_STATUSES:
            raise UpdateError(f"invalid question status: {status!r}")
        due = changes.get("期限")
        if due and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(due)):
            raise UpdateError("期限 must be YYYY-MM-DD")
    return changes

def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))

def save_json(path: Path, data: Any, *, compact: bool = False) -> None:
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":")) if compact else json.dumps(data, ensure_ascii=False, indent=2)
    path.write_text(text + ("" if compact else "\n"), encoding="utf-8")

def apply_update(payload: dict[str, Any], issue_number: int) -> tuple[Path, str]:
    manifest = load_json(MANIFEST_PATH)
    kind = payload["type"]
    record_id = payload["id"].strip()
    changes = validate_changes(payload)
    part_key = "test_parts" if kind == "test" else "question_parts"
    for filename in manifest[part_key]:
        path = SITE_DIR / filename
        rows = load_json(path)
        for row in rows:
            if row.get("編號") == record_id:
                before = {key: row.get(key) for key in changes}
                row.update(changes)
                save_json(path, rows, compact=True)
                meta = manifest.setdefault("meta", {})
                meta["updated_at"] = datetime.now(timezone.utc).isoformat()
                meta["last_update"] = {"issue": issue_number, "type": kind, "id": record_id, "fields": sorted(changes)}
                save_json(MANIFEST_PATH, manifest)
                changed = [key for key, value in changes.items() if before.get(key) != value]
                return path, f"{record_id}: " + ", ".join(changed or ["no value changes"])
    raise UpdateError(f"record not found: {record_id}")

def write_output(name: str, value: str) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if output_path:
        with Path(output_path).open("a", encoding="utf-8") as handle:
            handle.write(f"{name}={value}\n")

def main() -> int:
    try:
        event = load_event()
        authorize(event)
        issue = event["issue"]
        payload = extract_payload(issue.get("body") or "")
        changed_path, summary = apply_update(payload, int(issue["number"]))
        write_output("changed_file", str(changed_path.relative_to(ROOT)))
        write_output("summary", summary)
        print(summary)
        return 0
    except UpdateError as exc:
        print(f"::error::{exc}")
        return 2

if __name__ == "__main__":
    sys.exit(main())
