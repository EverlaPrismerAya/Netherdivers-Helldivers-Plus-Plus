"""Small, dependency-free LDLD header inspector for offline work."""
from __future__ import annotations

import argparse
from pathlib import Path


def inspect(path: str | Path) -> dict:
    data = Path(path).read_bytes()
    if data[:4] != b'LDLD':
        raise ValueError('input does not start with LDLD')
    return {'path': str(path), 'bytes': len(data), 'magic': data[:4].decode('ascii'), 'prefix_hex': data[:64].hex()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', type=Path)
    args = parser.parse_args()
    print(inspect(args.path))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
