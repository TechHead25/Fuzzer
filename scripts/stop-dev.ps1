param ()

$ErrorActionPreference = "SilentlyContinue"

Write-Host "[*] Stopping Local Development Environment..." -ForegroundColor Cyan

$pidFile = ".\.dev-pids"

if (Test-Path $pidFile) {
    $pids = Get-Content $pidFile
    foreach ($p in $pids) {
        if ([string]::IsNullOrWhiteSpace($p)) { continue }
        Write-Host "    -> Stopping process $p..."
        Stop-Process -Id $p -Force
    }
    Remove-Item $pidFile -Force
    Write-Host "[+] All tracked processes stopped." -ForegroundColor Green
} else {
    Write-Host "[-] No .dev-pids file found. Searching for running node and uvicorn processes..." -ForegroundColor Yellow
}

# Catch-all for stray processes
$nodeProcs = Get-Process -Name "node" -ErrorAction SilentlyContinue
if ($nodeProcs) {
    Write-Host "    -> Force stopping stray Node processes..."
    Stop-Process -Name "node" -Force
}

$pythonProcs = Get-WmiObject Win32_Process -Filter "Name='python.exe' AND CommandLine LIKE '%uvicorn%'" -ErrorAction SilentlyContinue
if ($pythonProcs) {
    Write-Host "    -> Force stopping stray Uvicorn processes..."
    foreach ($proc in $pythonProcs) {
        Stop-Process -Id $proc.ProcessId -Force
    }
}

$workerProcs = Get-WmiObject Win32_Process -Filter "Name='python.exe' AND CommandLine LIKE '%worker/main.py%'" -ErrorAction SilentlyContinue
if ($workerProcs) {
    Write-Host "    -> Force stopping stray Worker processes..."
    foreach ($proc in $workerProcs) {
        Stop-Process -Id $proc.ProcessId -Force
    }
}

Write-Host "[+] Environment cleanup complete." -ForegroundColor Green
