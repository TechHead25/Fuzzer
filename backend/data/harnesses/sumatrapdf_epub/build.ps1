$ErrorActionPreference = 'Stop'
Write-Host "Building SumatraPDF EPUB Harness..."

Write-Host "Compiling mupdf_mock.c and harness.cpp with g++..."
g++ mupdf_mock.c harness.cpp -o harness.exe -O2

if ($LASTEXITCODE -eq 0) {
    Write-Host "Build complete! Output is in harness.exe"
} else {
    Write-Error "Compilation failed."
}
