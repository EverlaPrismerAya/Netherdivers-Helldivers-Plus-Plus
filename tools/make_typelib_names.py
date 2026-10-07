"""Create the hash/name/size index used during offline table analysis."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path, nargs='?', default=Path('data/typelib_all.json'))
    parser.add_argument('output', type=Path, nargs='?', default=Path('data/typelib_names.tsv'))
    args = parser.parse_args()
    document = json.loads(args.input.read_text(encoding='utf-8'))
    rows = ['hash\tname\tsize\talignment\tmembers']
    for key, value in sorted(document['types'].items()):
        rows.append(f"{key}\t{value.get('name', key)}\t{value.get('size', '')}\t{value.get('alignment', '')}\t{len(value.get('members', []))}")
    args.output.write_text('\n'.join(rows) + '\n', encoding='utf-8', newline='\n')
    print(f'Wrote {args.output} ({len(rows) - 1} types)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
