Write-Host "Starting SentinelSOC Development Environment..." -ForegroundColor Cyan

# Start backend in a new window
Write-Host "Starting Backend API (FastAPI)..." -ForegroundColor Green
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "title 'SentinelSOC Backend'; cd backend; .\venv\Scripts\uvicorn app.main:app --reload --host 127.0.0.1 --port 8000" -WindowStyle Normal

# Start frontend in a new window
Write-Host "Starting Frontend (Next.js)..." -ForegroundColor Green
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "title 'SentinelSOC Frontend'; cd frontend; npm run dev" -WindowStyle Normal

Write-Host "Development servers are starting up in separate windows." -ForegroundColor Cyan
