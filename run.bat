@echo off
echo Installing dependencies...
python -m pip install -r requirements.txt

echo.
echo Starting SecureAttend Server...
echo Access the app at: http://localhost:8000
echo.
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
pause
