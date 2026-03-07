@echo off
cd /d "%~dp0"

set VENV_DIR=%USERPROFILE%\.venvs\claude_monitor

REM venv가 없거나 python이 실행 안 되면 재설정
if not exist "%VENV_DIR%\Scripts\pythonw.exe" goto setup
"%VENV_DIR%\Scripts\python.exe" -c "import requests, pystray, PIL, win32api" 2>nul
if errorlevel 1 goto fix
goto run

:setup
echo venv 생성 중 (%VENV_DIR%)...
if not exist "%USERPROFILE%\.venvs" mkdir "%USERPROFILE%\.venvs"
python -m venv "%VENV_DIR%"
goto install

:fix
echo pip 및 패키지 재설치 중...
"%VENV_DIR%\Scripts\python.exe" -m ensurepip --upgrade 2>nul

:install
"%VENV_DIR%\Scripts\python.exe" -m pip install requests pystray Pillow pywin32 --quiet
echo 설치 완료.

:run
start "" "%VENV_DIR%\Scripts\pythonw.exe" monitor.pyw
