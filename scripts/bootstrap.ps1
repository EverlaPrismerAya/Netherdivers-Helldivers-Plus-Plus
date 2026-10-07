$ErrorActionPreference = 'Stop'
$workspace = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $workspace
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { throw 'Python 3 is required.' }
python -m pip install --user --upgrade -r requirements.txt
if (-not (Test-Path -LiteralPath 'tools\go\sdk\bin\go.exe')) {
    Write-Warning 'Workspace Go is missing. Place a Go SDK under tools\go\sdk.'
}
python tools\doctor.py
