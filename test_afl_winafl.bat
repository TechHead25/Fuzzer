@echo off
setlocal

set ROOT=C:\Projects\Fuzzer
set TARGET=%ROOT%\target\sumatrapdf\out\rel64\pdf_harness.exe
set DR=%ROOT%\dynamorio\bin64
set WINAFL=%ROOT%\winafl\build64\bin\Release
set INPUT=%ROOT%\work\sumatra-pdf\input
set OUTPUT=%ROOT%\work\sumatra-pdf\output_afl_test

echo ============================================================
echo WinAFL AFL-launch diagnostic
echo ============================================================
echo.

echo [1] Cleaning processes...
taskkill /F /IM afl-fuzz.exe >nul 2>&1
taskkill /F /IM pdf_harness.exe >nul 2>&1
taskkill /F /IM drrun.exe >nul 2>&1

echo [2] Checking files...
if not exist "%TARGET%" (
    echo ERROR: Target missing:
    echo %TARGET%
    pause
    exit /b 1
)

if not exist "%WINAFL%\winafl.dll" (
    echo ERROR: winafl.dll missing:
    echo %WINAFL%\winafl.dll
    pause
    exit /b 1
)

if not exist "%WINAFL%\afl-fuzz.exe" (
    echo ERROR: afl-fuzz.exe missing
    pause
    exit /b 1
)

if not exist "%DR%\drrun.exe" (
    echo ERROR: drrun.exe missing
    pause
    exit /b 1
)

echo All required files exist.
echo.

echo [3] Cleaning diagnostic output...
rmdir /S /Q "%OUTPUT%" >nul 2>&1
mkdir "%OUTPUT%"

echo.
echo [4] Launching AFL...
echo.
echo Target:
echo %TARGET%
echo.
echo Instrumentation:
echo   coverage_module = pdf_harness.exe
echo   target_module   = pdf_harness.exe
echo   target_method   = fuzz_target
echo   nargs           = 1
echo   convention      = ms64
echo   iterations      = 5
echo.

"%WINAFL%\afl-fuzz.exe" ^
-i "%INPUT%" ^
-o "%OUTPUT%" ^
-D "%DR%" ^
-t 10000 ^
-w "%WINAFL%\winafl.dll" ^
-- ^
-coverage_module pdf_harness.exe ^
-target_module pdf_harness.exe ^
-target_method fuzz_target ^
-fuzz_iterations 5 ^
-nargs 1 ^
-call_convention ms64 ^
-- ^
"%TARGET%" @@

echo.
echo ============================================================
echo AFL EXITED
echo ============================================================
echo.

echo [5] Remaining processes:
tasklist | findstr /i "afl-fuzz pdf_harness drrun"

echo.
echo Exit code: %ERRORLEVEL%
pause