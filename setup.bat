@echo off
echo Starting project setup...
echo Checking for Python installation...
if not exist python (
    echo Python is not installed. Please install Python 3.8+ and try again.
    exit /b 1
)
echo Creating a virtual environment...
python -m venv venv
if %ERRORLEVEL% NEQ 0 (
    echo Failed to create a virtual environment. Please check your Python installation.
    exit /b 1
)
echo Activating the virtual environment...
call venv\Scripts\Activate.bat
if %ERRORLEVEL% NEQ 0 (
    echo Failed to activate the virtual environment. Ensure you are running this script with cmd.exe.
    exit /b 1
)
echo Upgrading pip...
python -m pip install --upgrade pip
if %ERRORLEVEL% NEQ 0 (
    echo Failed to upgrade pip.
    exit /b 1
)
echo Installing dependencies from requirements.txt...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo Failed to install dependencies. Please check the requirements file or your internet connection.
    exit /b 1
)
echo Setup completed successfully! Run 'python main.py' to start the application.
