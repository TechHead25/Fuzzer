param (
    [switch]$SkipCheck = $false,
    [switch]$MockWorker = $false
)

$ErrorActionPreference = "Stop"

if (-not $SkipCheck) {
    Write-Host "Running environment checks..." -ForegroundColor Cyan
    & .\check-environment.ps1
    # We do not block if checks fail, because user might just want to start the API/UI.
    Write-Host ""
}

$pids = @()

# Set required environment variables
$env:FUZZ_API_KEY = "test_key"
$env:PYTHONPATH = ".." # Help scripts resolve paths if necessary

Write-Host "[*] Starting FastAPI Backend..." -ForegroundColor Cyan
$backendProc = Start-Process -FilePath "..\backend\venv\Scripts\python.exe" -ArgumentList "-m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -WorkingDirectory "..\backend" -PassThru -WindowStyle Minimized -RedirectStandardOutput "..\scripts\backend.log" -RedirectStandardError "..\scripts\backend_error.log"
$pids += $backendProc.Id
Write-Host "    -> Backend running on http://localhost:8000 (PID: $($backendProc.Id))"

Write-Host "[*] Starting Next.js Frontend..." -ForegroundColor Cyan
$frontendProc = Start-Process -FilePath "npm.cmd" -ArgumentList "run dev" -WorkingDirectory "..\frontend" -PassThru -WindowStyle Minimized -RedirectStandardOutput "..\scripts\frontend.log" -RedirectStandardError "..\scripts\frontend_error.log"
$pids += $frontendProc.Id
Write-Host "    -> Frontend running on http://localhost:3000 (PID: $($frontendProc.Id))"

Write-Host "[*] Starting Fuzz Worker..." -ForegroundColor Cyan
$workerArgs = "main.py"
if ($MockWorker) {
    $workerArgs += " --mock-worker"
}
# Start worker
$workerPy = "python.exe"
if (Test-Path "..\worker\venv\Scripts\python.exe") {
    $workerPy = "..\worker\venv\Scripts\python.exe"
}
$workerProc = Start-Process -FilePath $workerPy -ArgumentList $workerArgs -WorkingDirectory "..\worker" -PassThru -WindowStyle Minimized -RedirectStandardOutput "..\scripts\worker.log" -RedirectStandardError "..\scripts\worker_error.log"
$pids += $workerProc.Id
Write-Host "    -> Worker running (PID: $($workerProc.Id))"

# Save PIDs for graceful stop
$pids | Out-File -FilePath ".\.dev-pids" -Encoding utf8

Write-Host ""
Write-Host "[+] Local development environment started successfully!" -ForegroundColor Green
Write-Host "    - Frontend: http://localhost:3000"
Write-Host "    - Backend API: http://localhost:8000/docs"
Write-Host "    - Worker logs are in separate terminal windows."
Write-Host ""
Write-Host "Run '.\stop-dev.ps1' to stop all services." -ForegroundColor Yellow
