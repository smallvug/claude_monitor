@echo off
cd /d "%~dp0"

REM venv가 없거나 python이 실행 안 되면 재설정
if not exist ".venv\Scripts\pythonw.exe" goto setup
.venv\Scripts\python.exe -c "import requests, pystray, PIL, win32api" 2>nul
if errorlevel 1 goto fix
goto run

:setup
echo venv 생성 중...
python -m venv .venv
goto install

:fix
echo pip 및 패키지 재설치 중...
.venv\Scripts\python.exe -m ensurepip --upgrade 2>nul

:install
.venv\Scripts\python.exe -m pip install requests pystray Pillow pywin32 --quiet
echo 설치 완료.

:run
start "" .venv\Scripts\pythonw.exe monitor.pyw
