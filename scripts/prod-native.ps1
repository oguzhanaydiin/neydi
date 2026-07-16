# Prod: native stack + Supabase + Cloudflare tunnel (ports 3000/8000).
# Local: docker compose up (ports 3001/8001) — both can run together.
#
# Usage:
#   .\scripts\prod-native.ps1              # visible terminal (taskbar: neydi | prod)
#   .\scripts\prod-native.ps1 -Background  # hidden background

param([switch]$Background)

$ErrorActionPreference = "Stop"
$host.UI.RawUI.WindowTitle = "NEYDI_PROD"

. (Join-Path $PSScriptRoot "native-common.ps1")

$runStack = Join-Path $PSScriptRoot "run-stack.ps1"
Start-ExternalStackTerminal -RunStackScript $runStack -Background:$Background | Out-Null

if ($Background) {
    Write-Host "neydi prod running in background. Stop with: .\scripts\stop-native.ps1"
} else {
    Write-Host "neydi prod started in external terminal (taskbar: neydi | prod)"
}
