function Assert-PortFree {
    param([int]$Port)

    $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -First 1

    if ($listener) {
        $msg = "Port $Port is already in use (PID $($listener.OwningProcess)). " +
               "Stop it first: Stop-Process -Id $($listener.OwningProcess) -Force"
        Write-Error $msg
    }
}

function Wait-AllProcesses {
    param([System.Diagnostics.Process[]]$Processes)

    while ($true) {
        foreach ($p in $Processes) {
            if ($p.HasExited -and $p.ExitCode -ne 0 -and $null -ne $p.ExitCode) {
                throw "Process exited unexpectedly (PID $($p.Id), exit code $($p.ExitCode))"
            }
        }

        $running = @($Processes | Where-Object { -not $_.HasExited })
        if ($running.Count -eq 0) {
            return
        }

        Start-Sleep -Seconds 1
    }
}

function Set-LauncherTitle {
    param([string]$Title)

    $Host.UI.RawUI.WindowTitle = $Title
}

function Start-ExternalStackTerminal {
    param(
        [string]$RunStackScript,
        [switch]$Background
    )

    $args = @("-File", $RunStackScript)
    if ($Background) {
        $args = @("-WindowStyle", "Hidden") + $args
    } else {
        $args = @("-NoExit") + $args
    }

    $params = @{
        FilePath     = "powershell"
        ArgumentList = $args
        PassThru     = $true
    }
    if ($Background) {
        $params.WindowStyle = "Hidden"
    }

    return Start-Process @params
}

function Stop-NativeStack {
    $stopped = @()

    foreach ($port in 8000, 3000) {
        $listeners = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
        foreach ($listener in $listeners) {
            $pid = $listener.OwningProcess
            if ($pid -and $stopped -notcontains $pid) {
                Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                $stopped += $pid
            }
        }
    }

    Get-Process cloudflared -ErrorAction SilentlyContinue | ForEach-Object {
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
        $stopped += $_.Id
    }

    return $stopped.Count
}
