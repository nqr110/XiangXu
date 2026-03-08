@echo off
setlocal
set "ROOT=%~dp0"
cd /d "%ROOT%"

set "VENV_PY=%ROOT%.venv\Scripts\python.exe"
set "VENV_PIP=%ROOT%.venv\Scripts\pip.exe"

if not exist "%VENV_PY%" (
    echo [ERROR] .venv not found. Run run.bat once to create it.
    pause
    exit /b 1
)

echo [1/3] Ensuring PyInstaller ...
"%VENV_PIP%" install pyinstaller -q
if %errorlevel% neq 0 (
    echo [ERROR] pip install pyinstaller failed.
    pause
    exit /b 1
)

echo [2/3] Generating icon from images\logo.jpg ...
"%VENV_PY%" -c "from PIL import Image; img = Image.open('images/logo.jpg').convert('RGBA'); img.save('images/logo.ico', format='ICO', sizes=[(256,256), (128,128), (64,64), (48,48), (32,32), (16,16)])"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create logo.ico.
    pause
    exit /b 1
)
if not exist "%ROOT%images\logo.ico" (
    echo [ERROR] logo.ico not found after generation.
    pause
    exit /b 1
)
for %%I in ("%ROOT%images\logo.ico") do if %%~zI equ 0 (
    echo [ERROR] logo.ico is empty.
    pause
    exit /b 1
)

echo [3/3] Building (onedir, --clean to refresh icon) ...
"%VENV_PY%" -m PyInstaller --noconfirm --clean xiangxu.spec
if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller failed.
    pause
    exit /b 1
)

echo.
echo Done. Output: %ROOT%dist\象胥\
echo Run: dist\象胥\象胥.exe
echo.
pause
