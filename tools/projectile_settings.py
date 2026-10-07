"""Inspect a decoded generated_projectile_settings JSON snapshot."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', type=Path)
    parser.add_argument('--find', help='case-insensitive substring matched against serialized records')
    args = parser.parse_args()
    value = json.loads(args.path.read_text(encoding='utf-8'))
    if args.find:
        needle = args.find.casefold()
        records = value if isinstance(value, list) else value.get('entries', value.get('records', []))
        for index, record in enumerate(records):
            if needle in json.dumps(record, ensure_ascii=False).casefold():
                print(json.dumps({'index': index, 'record': record}, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({'path': str(args.path), 'type': type(value).__name__, 'records': len(value) if isinstance(value, list) else None}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
