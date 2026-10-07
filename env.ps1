$workspace = Split-Path -Parent $MyInvocation.MyCommand.Path
$goRoot = Join-Path $workspace 'tools\go\sdk'
$ljdRoot = Join-Path $workspace 'tools\ljd'
$env:HD2_WORKSPACE = $workspace
$env:HD2_GO_ROOT = $goRoot
$env:HD2_LJD_ROOT = $ljdRoot
$env:PATH = "$goRoot\bin;$workspace\tools;$env:PATH"
$env:PYTHONPATH = "$workspace;$ljdRoot;$env:PYTHONPATH"
if (-not $env:GOPROXY) { $env:GOPROXY = 'https://goproxy.cn,direct' }
Write-Host "HD2 workspace activated: $workspace"
Write-Host "Go: $goRoot"
Write-Host "Python: $((Get-Command python).Source)"
