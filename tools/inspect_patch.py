"""Inspect a patch_N archive and validate its structural round-trip."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hd2_archive import entries, load, make_archive, sha256


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--round-trip', action='store_true')
    args = parser.parse_args()
    data = load(args.archive)
    found = entries(data)
    print(f'archive={args.archive}')
    print(f'bytes={len(data)} sha256={sha256(data)} resources={len(found)}')
    for index, entry in enumerate(found):
        print(f'{index}: name_hash=0x{entry.name_hash:016X} type=0x{entry.type_hash:016X} offset={entry.offset} length={entry.length}')
    if args.round_trip:
        rebuilt = make_archive({entry.name_hash: data[entry.offset:entry.offset + entry.length] for entry in found})
        if rebuilt != data:
            raise SystemExit('round-trip mismatch: archive is valid but not canonical')
        print('round_trip=ok')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
