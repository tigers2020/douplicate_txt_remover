@echo off
REM Change to the directory where this script is located
cd /d "%~dp0"

REM Check if the documents folder is passed as an argument
set "documents_folder=%~1"
if "%documents_folder%"=="" (
    set "documents_folder=Documents"  REM Default path
)

REM Activate the virtual environment
call .venv\Scripts\activate.bat

REM Run the Python script with the documents folder argument
python file_manager.py "%documents_folder%"

REM Pause at the end
pause
