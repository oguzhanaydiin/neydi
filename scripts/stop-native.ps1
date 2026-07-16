# Stop native prod stack (backend, frontend, tunnel).
# Does not affect Docker.
# Usage: .\scripts\stop-native.ps1

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "native-common.ps1")

$count = Stop-NativeStack
Write-Host "Stopped $count process(es)."
