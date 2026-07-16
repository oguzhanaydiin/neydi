# Prod stack: native backend + frontend + Cloudflare tunnel (Supabase DB).
# Ports 3000/8000 — do not change (Cloudflare tunnel points here).
# Local Docker uses 3001/8001 — see docker-compose.yml.

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$Be = Join-Path $Root "neydi-be"
$Fe = Join-Path $Root "neydi-fe"
$TunnelId = "015ec0ba-78b6-41d0-a5df-5ca24aed2c62"

. (Join-Path $PSScriptRoot "native-common.ps1")

Set-LauncherTitle "neydi | prod"

if (-not (Test-Path (Join-Path $Be ".env"))) {
    Write-Error "Missing neydi-be\.env - copy .env.example and configure."
}

$venv = Join-Path $Be ".venv"
if (-not (Test-Path $venv)) {
    Write-Host "Creating Python venv..."
    python -m venv $venv
    & (Join-Path $venv "Scripts\pip.exe") install -r (Join-Path $Be "requirements.txt")
}

if (-not (Test-Path (Join-Path $Fe "node_modules"))) {
    Write-Host "Installing frontend dependencies..."
    Push-Location $Fe
    pnpm install
    Pop-Location
}

Write-Host "Building frontend (production)..."
Push-Location $Fe
$env:NUXT_PUBLIC_API_BASE = "/api"
$env:NUXT_API_PROXY_TARGET = "http://127.0.0.1:8000"
$env:NODE_ENV = "production"
pnpm build
Pop-Location

$uvicorn = Join-Path $venv "Scripts\uvicorn.exe"
$nodeDir = Split-Path (Get-Command node -ErrorAction Stop).Source
$pnpm = Join-Path $nodeDir "pnpm.cmd"
if (-not (Test-Path $pnpm)) {
    Write-Error "pnpm.cmd not found next to node.exe"
}
$cloudflared = (Get-Command cloudflared -ErrorAction Stop).Source
$processes = @()

function Stop-AllProcesses {
    foreach ($p in $processes) {
        if ($null -ne $p -and -not $p.HasExited) {
            Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
        }
    }
}

$env:HOST = "127.0.0.1"
$env:PORT = "3000"
$env:DB_MODE = "supabase"

Write-Host ""
Write-Host "[neydi | prod] backend  -> http://127.0.0.1:8000"
Write-Host "[neydi | prod] frontend -> http://127.0.0.1:3000"
Write-Host "[neydi | prod] tunnel   -> https://neydi.aydinoguzhan.com"
Write-Host "[neydi | prod] database -> Supabase"
Write-Host "Ctrl+C stops all."
Write-Host ""

Assert-PortFree -Port 8000
Assert-PortFree -Port 3000

try {
    $processes += Start-Process -FilePath $uvicorn `
        -ArgumentList @("main:app", "--host", "127.0.0.1", "--port", "8000") `
        -WorkingDirectory $Be -NoNewWindow -PassThru

    Start-Sleep -Seconds 2

    $processes += Start-Process -FilePath $pnpm `
        -ArgumentList @("start") `
        -WorkingDirectory $Fe -NoNewWindow -PassThru

    Start-Sleep -Seconds 2

    $processes += Start-Process -FilePath $cloudflared `
        -ArgumentList @("tunnel", "run", $TunnelId) `
        -NoNewWindow -PassThru

    Wait-AllProcesses -Processes $processes
}
finally {
    Write-Host ""
    Write-Host "Stopping all processes..."
    Stop-AllProcesses
}
