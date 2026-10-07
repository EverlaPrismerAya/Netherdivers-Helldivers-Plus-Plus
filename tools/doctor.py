"""Validate the local HD2 Lua mod development environment."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def command_version(command: str) -> str | None:
    path = shutil.which(command)
    if not path:
        return None
    try:
        result = subprocess.run([path, '--version'], capture_output=True, text=True, check=False)
        return result.stdout.strip() or path
    except OSError:
        return path


def workspace_go() -> str | None:
    bundled = ROOT / 'tools' / 'go' / 'sdk' / 'bin' / 'go.exe'
    return str(bundled) if bundled.is_file() else command_version('go')


def main() -> int:
    checks = {
        'python': sys.version.split()[0],
        'git': command_version('git'),
        'go': workspace_go(),
        'lupa': bool(importlib.util.find_spec('lupa')),
        'filediver_checkout': any(path.is_file() for path in (
            ROOT / 'vendor' / 'filediver-src' / 'go.mod',
            ROOT / 'vendor' / 'filediver-src-archive' / 'go.mod',
            ROOT / 'vendor' / 'filediver-src-archive' / 'filediver-master' / 'go.mod',
        )),
        'typelib_dumper': (ROOT / 'tools' / 'dump_typelib.py').is_file(),
        'community_data': (ROOT / 'vendor' / 'HelldiversData' / 'data').exists(),
        'shared_loader': (ROOT / 'vendor' / 'BingusSharedLoader' / 'scripts' / 'build_addon.py').exists(),
        'ljd': (ROOT / 'tools' / 'ljd' / 'main.py').exists(),
    }
    print(json.dumps(checks, indent=2, ensure_ascii=False))
    required = ('git', 'go', 'lupa', 'filediver_checkout', 'community_data', 'shared_loader', 'ljd', 'typelib_dumper')
    missing = [key for key in required if not checks.get(key)]
    if missing:
        print('missing=' + ','.join(missing), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
