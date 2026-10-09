# HeatShield ML Service — Test Runner
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ML Service - HeatShield Pipeline Tests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if (-Not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

Write-Host "Activating virtual environment..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1

python -m pip install --upgrade pip -q
pip install -r requirements.txt -q

Write-Host "`nRunning tests..." -ForegroundColor Cyan
pytest tests/ -v --tb=short

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✓ All tests passed!" -ForegroundColor Green
} else {
    Write-Host "`n✗ Some tests failed." -ForegroundColor Red
    exit $LASTEXITCODE
}
