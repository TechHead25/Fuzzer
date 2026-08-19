param (
    [switch]$Verbose = $false
)

$ErrorActionPreference = "Stop"

function Write-Step ($msg) {
    Write-Host "[*] $msg" -ForegroundColor Cyan
}

function Write-Success ($msg) {
    Write-Host "[+] $msg" -ForegroundColor Green
}

function Write-Warning ($msg) {
    Write-Host "[!] $msg" -ForegroundColor Yellow
}

function Write-ErrorMsg ($msg) {
    Write-Host "[-] $msg" -ForegroundColor Red
}

$issues = 0

Write-Step "Checking Node.js & npm..."
if (Get-Command npm -ErrorAction SilentlyContinue) {
    $npmVer = (npm --version).Trim()
    Write-Success "npm is installed (v$npmVer)"
} else {
    Write-ErrorMsg "npm is not installed. Please install Node.js (https://nodejs.org)."
    $issues++
}

Write-Step "Checking Python..."
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pyVer = (python --version).Trim()
    Write-Success "Python is installed ($pyVer)"
} else {
    Write-ErrorMsg "Python is not installed. Please install Python 3.10+ and add it to PATH."
    $issues++
}

Write-Step "Checking Backend Environment..."
$backendVenv = "..\backend\venv\Scripts\python.exe"
if (Test-Path $backendVenv) {
    Write-Success "Backend venv exists"
} else {
    Write-ErrorMsg "Backend venv not found. Run: cd backend; python -m venv venv; .\venv\Scripts\Activate.ps1; pip install -r requirements.txt"
    $issues++
}

if (Test-Path "..\backend\fuzz_sentinel.db") {
    Write-Success "Database initialized"
} else {
    Write-Warning "Database not found (fuzz_sentinel.db). It will be created on first start, but migrations may be required."
}

Write-Step "Checking Frontend Environment..."
if (Test-Path "..\frontend\node_modules") {
    Write-Success "Frontend node_modules exists"
} else {
    Write-ErrorMsg "Frontend dependencies not found. Run: cd frontend; npm install"
    $issues++
}

Write-Step "Checking Fuzzing Worker Dependencies (WinAFL / DynamoRIO)..."
# Check if WinAFL path is passed via env, else use standard relative paths from project root
$winaflDir = $env:WINAFL_DIR
if (-not $winaflDir) {
    $winaflDir = "..\winafl"
}
$dynamorioDir = $env:DYNAMORIO_DIR
if (-not $dynamorioDir) {
    $dynamorioDir = "..\dynamorio"
}

if (Test-Path "$winaflDir\afl-fuzz.exe") {
    Write-Success "WinAFL found at $winaflDir"
} else {
    Write-ErrorMsg "WinAFL not found at $winaflDir."
    Write-Host "    -> Download/Build WinAFL: https://github.com/googleprojectzero/winafl" -ForegroundColor DarkGray
    Write-Host "    -> Or set the WINAFL_DIR environment variable to the correct path." -ForegroundColor DarkGray
    $issues++
}

if (Test-Path "$dynamorioDir\bin32\drrun.exe") {
    Write-Success "DynamoRIO found at $dynamorioDir"
} else {
    Write-ErrorMsg "DynamoRIO not found at $dynamorioDir."
    Write-Host "    -> Download DynamoRIO: https://dynamorio.org/" -ForegroundColor DarkGray
    Write-Host "    -> Or set the DYNAMORIO_DIR environment variable to the correct path." -ForegroundColor DarkGray
    $issues++
}

if ($issues -gt 0) {
    Write-ErrorMsg "Environment check failed with $issues missing dependencies."
    Write-Host "The application (frontend/backend) can still start, but the worker will fail to fuzz." -ForegroundColor Yellow
    exit $issues
} else {
    Write-Success "All dependencies satisfied!"
    exit 0
}
