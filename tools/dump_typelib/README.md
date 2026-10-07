# `dump_typelib`

The current FileDiver source exposes the exporter as
`cmd/tools/components/typelib-json-dumper`. The workspace wrapper is:

```powershell
python tools\dump_typelib.py
```

Do not use PowerShell `>` redirection for JSON output; it can produce UTF-16
text that Python cannot read as UTF-8.
