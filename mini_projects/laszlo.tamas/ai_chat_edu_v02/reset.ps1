# ===========================
# AI Chat Education v02 - Reset Script (PowerShell)
# ===========================
# This script completely resets the local environment:
# - Stops all containers
# - Removes containers and volumes
# - Starts fresh containers with clean databases

# UTF-8 encoding for console
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['*:Encoding'] = 'utf8'
chcp 65001 > $null

Write-Host "🔄 AI Chat Education v02 - Environment Reset" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Load ports from .env
$envContent = Get-Content .env -ErrorAction SilentlyContinue
$FRONTEND_PORT = if ($envContent | Select-String "FRONTEND_EXTERNAL_PORT=(\d+)") { ($envContent | Select-String "FRONTEND_EXTERNAL_PORT=(\d+)" | ForEach-Object { $_.Matches.Groups[1].Value }) } else { "13000" }
$BACKEND_PORT = if ($envContent | Select-String "BACKEND_EXTERNAL_PORT=(\d+)") { ($envContent | Select-String "BACKEND_EXTERNAL_PORT=(\d+)" | ForEach-Object { $_.Matches.Groups[1].Value }) } else { "18000" }
$QDRANT_PORT = if ($envContent | Select-String "QDRANT_HTTP_EXTERNAL_PORT=(\d+)") { ($envContent | Select-String "QDRANT_HTTP_EXTERNAL_PORT=(\d+)" | ForEach-Object { $_.Matches.Groups[1].Value }) } else { "16333" }

# Step 1: Stop and remove containers
Write-Host "🛑 Stopping containers..." -ForegroundColor Yellow
docker-compose down

# Step 2: Remove volumes (clean slate)
Write-Host "🗑️  Removing data (this will DELETE all data)..." -ForegroundColor Yellow
Remove-Item -Path "data/postgres/*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "data/qdrant/*" -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "✅ Local database files cleared" -ForegroundColor Green

# Step 3: Start fresh
Write-Host ""
Write-Host "✨ Starting fresh environment..." -ForegroundColor Green
docker-compose up -d

# Step 4: Wait for services
Write-Host ""
Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

# Step 5: Show status
Write-Host ""
Write-Host "✅ Reset complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Container Status:" -ForegroundColor Cyan
docker-compose ps

Write-Host ""
Write-Host "🌐 Access the application:" -ForegroundColor Cyan
Write-Host "   Frontend: http://localhost:$FRONTEND_PORT" -ForegroundColor White
Write-Host "   Backend:  http://localhost:$BACKEND_PORT" -ForegroundColor White
Write-Host "   Qdrant:   http://localhost:${QDRANT_PORT}/dashboard" -ForegroundColor White
Write-Host ""
Write-Host "📝 Seed data (4 tenants, 3 users) auto-loaded on backend startup" -ForegroundColor Yellow
