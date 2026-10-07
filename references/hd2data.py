"""Offline helpers for community-decoded HelldiversData JSON files."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: str | Path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def find_records(value, needle: str):
    needle = needle.casefold()
    records = value if isinstance(value, list) else value.get('entries', value.get('records', [])) if isinstance(value, dict) else []
    return [(index, record) for index, record in enumerate(records) if needle in json.dumps(record, ensure_ascii=False).casefold()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', type=Path)
    parser.add_argument('--find')
    args = parser.parse_args()
    value = load_json(args.path)
    if args.find:
        for index, record in find_records(value, args.find):
            print(json.dumps({'index': index, 'record': record}, ensure_ascii=False))
    else:
        print(json.dumps({'type': type(value).__name__, 'top_level_keys': sorted(value) if isinstance(value, dict) else None}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
