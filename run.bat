@echo off
echo Starting SQL Optimizer Pro...

IF NOT EXIST venv (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating environment...
call venv\Scripts\activate

echo Installing dependencies...
pip install -r requirements.txt

echo Running application...
python app.py

pause
