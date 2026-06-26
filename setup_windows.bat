@echo off
echo Installing FFmpeg via winget...
winget install Gyan.FFmpeg
echo.
echo Installing Python dependencies...
pip install -r requirements.txt
echo.
echo Setup complete.
