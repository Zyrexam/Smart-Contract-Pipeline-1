# Build custom Docker images for Stage 3 security tools (Windows PowerShell)

Write-Host "🐳 Building Custom Docker Images for Stage 3" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

Write-Host "📦 Pulling base images..." -ForegroundColor Yellow
docker pull smartbugs/slither:0.11.3
docker pull smartbugs/mythril:0.24.7

Write-Host ""
Write-Host "🔨 Building custom Slither image..." -ForegroundColor Yellow
docker build -f Dockerfile.slither -t custom-slither:latest .
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ custom-slither:latest built successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to build custom-slither" -ForegroundColor Red
}

Write-Host ""
Write-Host "🔨 Building custom Mythril image..." -ForegroundColor Yellow
docker build -f Dockerfile.mythril -t custom-mythril:latest .
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ custom-mythril:latest built successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to build custom-mythril" -ForegroundColor Red
}

Write-Host ""
Write-Host "==============================================" -ForegroundColor Green
Write-Host "🎉 Build Complete!" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Available custom images:"
docker images | Select-String -Pattern "REPOSITORY|custom-"

Write-Host ""
Write-Host "🧪 Testing images..." -ForegroundColor Yellow

# Test Slither
Write-Host "Testing custom-slither..."
docker run --rm custom-slither:latest solc --version 2>&1 | Select-Object -First 1

# Test Mythril
Write-Host "Testing custom-mythril..."
docker run --rm custom-mythril:latest myth version

Write-Host ""
Write-Host "✅ All done!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Update tool configs to use custom images"
Write-Host "  2. Run: cd .. && python -m stage_3.test"
