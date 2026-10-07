# Netherdivers · Helldivers 2 Lua Mod Workspace

This workspace follows the `hd2-lua-mod` workflow: offline data first, read-only reconnaissance second, runtime writes last.

## Quick start

```powershell
. .\env.ps1
python tools\doctor.py
python -m unittest discover -s tests -v
python tools\build_addon.py --name mods/netherdivers/probe --entry mods/netherdivers/probe.lua --guid 11111111-1111-4111-8111-111111111111 --output build/probe.zip --display-name "Netherdivers Probe"
```

`env.ps1` prepends the workspace Go toolchain and Python helper paths without changing the machine-wide environment.

## Layout

- `tools/`: archive, addon packaging, patch inspection, data and environment utilities.
- `references/`: offline LDLD and community JSON readers.
- `vendor/HelldiversData/`: community-decoded JSON snapshots.
- `vendor/filediver-src-archive/filediver-master/`: FileDiver source and embedded datalibrary snapshot.
- `vendor/BingusSharedLoader/`: loader source, packaging scripts and compatibility tests.
- `mods/`: plaintext addon sources. Every entry starts with an `HD2-Addon` declaration.
- `fixtures/`: synthetic/real memory dumps and offline test inputs; never commit live dumps by accident.
- `_baseline/`: build-specific runtime baselines.

## Safety boundary

The workspace does not open another process or call `OpenProcess`, `ReadProcessMemory`, `WriteProcessMemory`, or `VirtualProtect` from Python. Runtime memory access belongs inside a game-loaded addon, and development starts with read-only reconnaissance. Do not launch the game or deploy a patch without a build/hash check and a backup plan.

## Typelib export

```powershell
python tools\dump_typelib.py
```

The wrapper writes UTF-8 JSON to `data/typelib_all.json` and uses the embedded
`dl_library.dl_typelib` from FileDiver's source snapshot.

Generate the compact lookup index with:

```powershell
python tools\make_typelib_names.py
```
