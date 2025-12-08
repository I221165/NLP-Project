# CourseMaster AI - Development Start Script
# Run frontend and backend in development mode (without Docker)

Write-Host "🚀 Starting CourseMaster AI in Development Mode..." -ForegroundColor Green
Write-Host ""

# Check for Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.9+" -ForegroundColor Red
    exit 1
}

# Check for Node.js
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✅ Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js not found. Please install Node.js 18+" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "📋 Setup Instructions:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1️⃣  Start ChromaDB (in a separate terminal):" -ForegroundColor Cyan
Write-Host "   cd backend" -ForegroundColor White
Write-Host "   chroma run --path ./chroma_data --port 8001" -ForegroundColor White
Write-Host ""
Write-Host "2️⃣  Start Backend (in another terminal):" -ForegroundColor Cyan
Write-Host "   cd backend" -ForegroundColor White
Write-Host "   python -m venv venv" -ForegroundColor White
Write-Host "   venv\Scripts\activate" -ForegroundColor White
Write-Host "   pip install -r requirements.txt" -ForegroundColor White
Write-Host "   uvicorn main:app --reload" -ForegroundColor White
Write-Host ""
Write-Host "3️⃣  Start Frontend (in this terminal):" -ForegroundColor Cyan
Write-Host "   cd frontend" -ForegroundColor White
Write-Host "   npm run dev" -ForegroundColor White
Write-Host ""
Write-Host "🌐 After starting all services:" -ForegroundColor Yellow
Write-Host "   Frontend will be at: http://localhost:5173" -ForegroundColor White
Write-Host "   Backend will be at:  http://localhost:8000" -ForegroundColor White
Write-Host ""

$response = Read-Host "Start Frontend now? (y/n)"
if ($response -eq "y" -or $response -eq "Y") {
    Set-Location frontend
    npm run dev
}
