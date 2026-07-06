@echo off
REM ============================================================================
REM  AICluster - one-command build entry point
REM
REM  Usage:
REM     build-all.bat                   full build
REM     build-all.bat clean             wipe release/ first
REM     build-all.bat verify            only verify the environment
REM     build-all.bat skip-tauri        skip Tauri desktop apps
REM     build-all.bat skip-installer    only emit installer scripts
REM     build-all.bat sign              enable Authenticode signing
REM ============================================================================

setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

REM Move into the repo root (one level up from this script).
pushd "%~dp0\.."

echo.
echo  AICluster v2.0.0 - Production Build
echo  =====================================
echo  Repo root: %CD%
echo.

REM --- Locate a working Python -------------------------------------------------
set "PY_CMD="
for %%P in (python py python3) do (
    if not defined PY_CMD (
        where %%P >nul 2>&1 && set "PY_CMD=%%P"
    )
)
if not defined PY_CMD (
    echo [ERROR] Python is not on PATH. Install Python 3.12+.
    popd
    exit /b 1
)

echo  Using Python: !PY_CMD!
!PY_CMD! --version
echo.

REM --- Compose the arguments ---------------------------------------------------
set "ARGS=build.build"
:loop
if "%~1"=="" goto :run
set "ARGS=!ARGS! %1"
shift
goto :loop

:run
echo  Running: !PY_CMD! -m !ARGS!
echo.
!PY_CMD! -m %ARGS%
set "RC=%ERRORLEVEL%"

echo.
if "%RC%"=="0" (
    echo  Build SUCCEEDED. Artifacts in release\
) else (
    echo  Build FAILED with code %RC%.
)

popd
endlocal & exit /b %RC%
