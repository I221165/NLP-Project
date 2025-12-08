# CourseMaster AI - Quick Start Script
# Run this to start the application locally

Write-Host "🚀 Starting CourseMaster AI Platform..." -ForegroundColor Green
Write-Host ""

# Check if Docker is running
$dockerRunning = docker info 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Docker is running" -ForegroundColor Green
Write-Host ""

# Build and start services
Write-Host "📦 Building and starting services..." -ForegroundColor Cyan
docker-compose up -d --build

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Services started successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Application URLs:" -ForegroundColor Yellow
    Write-Host "   Frontend:    http://localhost:5173" -ForegroundColor White
    Write-Host "   Backend API: http://localhost:8000" -ForegroundColor White
    Write-Host "   API Docs:    http://localhost:8000/docs" -ForegroundColor White
    Write-Host "   ChromaDB:    http://localhost:8001" -ForegroundColor White
    Write-Host ""
    Write-Host "📝 To view logs:" -ForegroundColor Yellow
    Write-Host "   docker-compose logs -f" -ForegroundColor White
    Write-Host ""
    Write-Host "🛑 To stop services:" -ForegroundColor Yellow
    Write-Host "   docker-compose down" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "❌ Failed to start services. Check docker-compose.yml" -ForegroundColor Red
    exit 1
}
