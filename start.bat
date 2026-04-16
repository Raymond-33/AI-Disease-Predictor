@echo off
echo.
echo ============================================
echo   AI-Disease Predictor — Symptom Analysis
echo ============================================
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Starting MediSense AI server...
echo Open your browser at: http://localhost:5001
echo Press Ctrl+C to stop the server.
echo.

python app.py
