"""Export FileDiver's embedded typelib as UTF-8 JSON."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'vendor' / 'filediver-src-archive' / 'filediver-master'
TYPELIB = SOURCE / 'datalibrary' / 'dl_library.dl_typelib'
TOOL = './cmd/tools/components/typelib-json-dumper'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-o', '--output', type=Path, default=ROOT / 'data' / 'typelib_all.json')
    args = parser.parse_args()
    go = ROOT / 'tools' / 'go' / 'sdk' / 'bin' / 'go.exe'
    if not go.is_file():
        go_path = shutil.which('go')
        if not go_path:
            raise SystemExit('Go SDK not found; activate env.ps1 or place it under tools/go/sdk.')
        go = Path(go_path)
    if not SOURCE.joinpath('go.mod').is_file() or not TYPELIB.is_file():
        raise SystemExit(f'FileDiver source snapshot missing: {SOURCE}')
    environment = os.environ.copy()
    environment.setdefault('GOPROXY', 'https://goproxy.cn,direct')
    result = subprocess.run([str(go), 'run', TOOL, str(TYPELIB)], cwd=SOURCE, capture_output=True, text=True, check=False, env=environment)
    if result.returncode:
        sys.stderr.write(result.stderr)
        return result.returncode
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(result.stdout, encoding='utf-8', newline='\n')
    print(f'Wrote {args.output}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
