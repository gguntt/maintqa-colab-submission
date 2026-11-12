@echo off
cd /d "%~dp0"
python -m venv .venv
if errorlevel 1 goto failure
.venv\Scripts\python.exe -m pip install --no-index --find-links=wheels -r requirements.txt
if errorlevel 1 goto failure
echo Installation complete. Run Start-MaintQA.cmd.
pause
exit /b 0
:failure
echo Offline installation failed. Check README and wheels folder.
pause
exit /b 1
