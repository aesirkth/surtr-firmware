@echo off
call venv\Scripts\activate.bat

set /p port="Enter the COM port: " 

python dashboard\main.py %port%

pause