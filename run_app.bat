@echo off
REM ====================================================
REM TinySA Spectrum Analyzer - Launch Script
REM ====================================================

REM Check if virtual environment folder "venv" exists; if not, create it.
IF NOT EXIST venv (
    echo Creating virtual environment...
    python -m venv venv
) ELSE (
    echo Virtual environment found.
)

REM Activate the virtual environment.
call venv\Scripts\activate

REM Upgrade pip (optional).
echo Upgrading pip...
pip install --upgrade pip

REM Install required packages from requirements.txt.
echo Installing required packages...
pip install -r requirements.txt

REM Launch the Streamlit application.
echo Launching TinySA Spectrum Analyzer...
streamlit run app.py

REM Pause to keep the command window open (optional).
pause
