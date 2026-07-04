import csv
import json
from pathlib import Path


TEXT_FIELDS = ("text", "tweet", "full_text", "content", "body")
TIME_FIELDS = ("created_at", "published_at", "timestamp", "time")
LIKE_FIELDS = ("favorite_count", "like_count", "likes")
RETWEET_FIELDS = ("retweet_count", "retweets", "reposts")


def _first_value(record, fields, default=""):
    for field in fields:
        value = record.get(field)
        if value is not None and str(value).strip():
            return value
    return default


def _json_records(raw_text, file_name):
    if file_name.endswith(".jsonl"):
        return [
            json.loads(line)
            for line in raw_text.splitlines()
            if line.strip()
        ]
    parsed = json.loads(raw_text)
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, dict):
        for key in ("data", "tweets", "results", "items"):
            value = parsed.get(key)
            if isinstance(value, list):
                return value
        return [parsed]
    raise ValueError("Xquik export must be a JSON object or array.")


def _csv_records(raw_text):
    return list(csv.DictReader(raw_text.splitlines()))


def load_xquik_export_rows(export_path, username="xquik"):
    path = Path(export_path)
    raw_text = path.read_text(encoding="utf-8-sig")
    suffix = path.suffix.lower()

    if suffix == ".csv":
        records = _csv_records(raw_text)
    elif suffix in {".json", ".jsonl"}:
        try:
            records = _json_records(raw_text, path.name.lower())
        except json.JSONDecodeError as exc:
            raise ValueError("Xquik JSON export contains invalid JSON.") from exc
    else:
        raise ValueError("Xquik export must be a .json, .jsonl, or .csv file.")

    rows = []
    for record in records:
        if not isinstance(record, dict):
            continue
        text = str(_first_value(record, TEXT_FIELDS)).strip()
        if not text:
            continue
        rows.append(
            {
                "user": str(record.get("user") or record.get("username") or record.get("author") or username),
                "text": text,
                "favorite_count": int(_first_value(record, LIKE_FIELDS, 0) or 0),
                "retweet_count": int(_first_value(record, RETWEET_FIELDS, 0) or 0),
                "created_at": _first_value(record, TIME_FIELDS),
            }
        )
    return rows
