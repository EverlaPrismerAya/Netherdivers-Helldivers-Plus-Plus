# FileDiver entry point

The FileDiver source snapshot is available through the workspace junction
`filediver-src/`, targeting `vendor/filediver-src-archive/filediver-master/`.

Use `python tools/dump_typelib.py` for the reproducible typelib export. For
other Go tools, activate `env.ps1`, change to `filediver-src/`, and run the
desired `go run ./cmd/...` target with `GOPROXY` available.
