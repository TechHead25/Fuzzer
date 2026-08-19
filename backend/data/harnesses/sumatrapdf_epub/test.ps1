$ErrorActionPreference = 'Stop'

Write-Host "Creating dummy input file..."
Set-Content -Path "test.epub" -Value "MOCK_EPUB_CONTENT_FOR_FUZZING"

$HarnessPath = ""
if (Test-Path "harness.exe") {
    $HarnessPath = ".\harness.exe"
} else {
    Write-Error "Could not find harness.exe. Did it compile?"
}

Write-Host "Executing harness: $HarnessPath test.epub"
& $HarnessPath test.epub

if ($LASTEXITCODE -eq 0) {
    Write-Host "VALIDATION SUCCESS: Harness executed cleanly." -ForegroundColor Green
} else {
    Write-Host "VALIDATION FAILED: Harness exited with code $LASTEXITCODE." -ForegroundColor Red
}
