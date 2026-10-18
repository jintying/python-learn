@echo off
rem ============================================================
rem  run.bat  --  run the Python lessons
rem
rem  How to use:
rem    1) Double-click this file            -> runs all lessons in order
rem    2) Double-click and type a number    -> see below
rem    3) In terminal:  run.bat 05          -> only runs lesson 05
rem                     run.bat --list      -> list all lessons
rem
rem  This file is intentionally written in plain ASCII so that
rem  Windows cmd.exe never garbles it.
rem ============================================================

chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

set "PY=%~dp0..\.venv\Scripts\python.exe"

if not exist "%PY%" (
    echo.
    echo [ERROR] Python not found at:
    echo     %PY%
    echo.
    echo Please make sure the .venv folder exists inside python-learn.
    echo.
    pause
    exit /b 1
)

if "%~1"=="" (
    echo.
    echo Which lesson do you want to run?
    echo   - Press ENTER to run ALL lessons in order
    echo   - Or type a number like 05 and press ENTER
    echo.
    set /p CHOICE=Your choice: 
    if not "%CHOICE%"=="" (
        "%PY%" "%~dp0run_lessons.py" %CHOICE%
    ) else (
        "%PY%" "%~dp0run_lessons.py"
    )
) else (
    "%PY%" "%~dp0run_lessons.py" %*
)

echo.
pause
