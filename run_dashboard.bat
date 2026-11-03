@echo off
echo ==============================================================================
echo Launching Healytics (Obsidian & Gold Executive Suite) on Localhost...
echo ==============================================================================
echo.

set PORT=8080
echo Starting local web server at http://localhost:%PORT% ...

start "" http://localhost:%PORT%
python -m http.server %PORT% --directory app

pause
