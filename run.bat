@echo off
setlocal EnableDelayedExpansion

set "ROOT=%~dp0"
cd /d "%ROOT%"

set "VENV=%ROOT%.venv"
set "VENV_PY=%VENV%\Scripts\python.exe"
set "VENV_PIP=%VENV%\Scripts\pip.exe"
set "REQ=%ROOT%\requirements.txt"
set "PIP_USTC=https://mirrors.ustc.edu.cn/pypi/simple"
set "PIP_TUNA=https://pypi.tuna.tsinghua.edu.cn/simple"
set "PIP_ALIYUN=https://mirrors.aliyun.com/pypi/simple"

set "PYEXE="
where py >nul 2>&1
if !errorlevel! equ 0 (
    for /f "delims=" %%i in ('py -3 -c "import sys; print(sys.executable)" 2^>nul') do set "PYEXE=%%i"
)
if not defined PYEXE (
    where python >nul 2>&1
    if !errorlevel! equ 0 (
        for /f "delims=" %%i in ('python -c "import sys; print(sys.executable)" 2^>nul') do set "PYEXE=%%i"
    )
)
if not defined PYEXE (
    where python3 >nul 2>&1
    if !errorlevel! equ 0 (
        for /f "delims=" %%i in ('python3 -c "import sys; print(sys.executable)" 2^>nul') do set "PYEXE=%%i"
    )
)
if not defined PYEXE (
    echo [ERROR] Python not found. Install Python 3.8+ and add to PATH.
    pause
    exit /b 1
)

if not exist "%VENV_PY%" (
    echo [1/3] Creating .venv ...
    "%PYEXE%" -m venv "%VENV%"
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to create venv.
        pause
        exit /b 1
    )
    set "NEED_INSTALL=1"
) else (
    echo [1/3] .venv exists, skip.
)

if not defined NEED_INSTALL (
    "%VENV_PY%" -c "import customtkinter" >nul 2>&1
    if !errorlevel! neq 0 set "NEED_INSTALL=1"
)
if defined NEED_INSTALL (
    if not exist "%REQ%" (
        echo [ERROR] requirements.txt not found.
        pause
        exit /b 1
    )
    echo [2/3] Installing deps - USTC mirror ...
    "%VENV_PIP%" install -r "%REQ%" -i "%PIP_USTC%" --trusted-host mirrors.ustc.edu.cn
    if !errorlevel! neq 0 (
        echo USTC failed, try TUNA ...
        "%VENV_PIP%" install -r "%REQ%" -i "%PIP_TUNA%" --trusted-host pypi.tuna.tsinghua.edu.cn
    )
    if !errorlevel! neq 0 (
        echo TUNA failed, try Aliyun ...
        "%VENV_PIP%" install -r "%REQ%" -i "%PIP_ALIYUN%" --trusted-host mirrors.aliyun.com
    )
    if !errorlevel! neq 0 (
        echo [ERROR] pip install failed.
        pause
        exit /b 1
    )
) else (
    echo [2/3] Deps OK, skip.
)

if not exist "%ROOT%.env" if exist "%ROOT%.env.example" copy "%ROOT%.env.example" "%ROOT%.env" >nul
if not exist "%ROOT%config.json" if exist "%ROOT%config.json.example" copy "%ROOT%config.json.example" "%ROOT%config.json" >nul

echo [3/3] Starting main.py ...
"%VENV_PY%" "%ROOT%main.py"
set "EXIT_CODE=!errorlevel!"
if !EXIT_CODE! neq 0 (
    echo Exit code: !EXIT_CODE!
    pause
)
endlocal
exit /b %EXIT_CODE%
