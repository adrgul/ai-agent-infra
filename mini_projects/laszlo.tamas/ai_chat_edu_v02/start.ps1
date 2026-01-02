# AI Chat Education v02 - Start Script
# Quick start for the education version

# UTF-8 encoding for console
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['*:Encoding'] = 'utf8'
chcp 65001 > $null

Write-Host "🚀 Starting AI Chat Education v02..." -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found! Copying from .env.example..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "✅ .env file created. Please edit it and set your OPENAI_API_KEY" -ForegroundColor Green
    Write-Host ""
    exit 1
}

# Load ports from .env
$envContent = Get-Content .env -ErrorAction SilentlyContinue
$FRONTEND_PORT = ($envContent | Select-String "FRONTEND_EXTERNAL_PORT=(\d+)" | ForEach-Object { $_.Matches.Groups[1].Value }) ?? "13000"
$BACKEND_PORT = ($envContent | Select-String "BACKEND_EXTERNAL_PORT=(\d+)" | ForEach-Object { $_.Matches.Groups[1].Value }) ?? "18000"
$QDRANT_PORT = ($envContent | Select-String "QDRANT_HTTP_EXTERNAL_PORT=(\d+)" | ForEach-Object { $_.Matches.Groups[1].Value }) ?? "16333"

# Check Docker
Write-Host "🐳 Checking Docker..." -ForegroundColor Cyan
$dockerRunning = docker info 2>&1 | Out-Null; $?
if (-not $dockerRunning) {
    Write-Host "❌ Docker is not running! Please start Docker Desktop." -ForegroundColor Red
    exit 1
}
Write-Host "✅ Docker is running" -ForegroundColor Green
Write-Host ""

# Start services
Write-Host "📦 Building and starting services..." -ForegroundColor Cyan
docker-compose up --build -d

Write-Host ""
Write-Host "✅ Services started!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Access the application:" -ForegroundColor Cyan
Write-Host "   Frontend:  http://localhost:$FRONTEND_PORT" -ForegroundColor White
Write-Host "   Backend:   http://localhost:$BACKEND_PORT" -ForegroundColor White
Write-Host "   API Docs:  http://localhost:${BACKEND_PORT}/docs" -ForegroundColor White
Write-Host "   Qdrant:    http://localhost:${QDRANT_PORT}/dashboard" -ForegroundColor White
Write-Host ""
Write-Host "📊 View logs:" -ForegroundColor Cyan
Write-Host "   docker-compose logs -f" -ForegroundColor White
Write-Host ""
Write-Host "🛑 Stop services:" -ForegroundColor Cyan
Write-Host "   docker-compose down" -ForegroundColor White
