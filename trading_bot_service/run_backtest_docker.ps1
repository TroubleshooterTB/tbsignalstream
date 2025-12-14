# Run backtesting in Docker container
# This allows running the backtest without installing Python locally

Write-Host "Building Docker image for backtesting..." -ForegroundColor Cyan
docker build -t trading-bot-backtest .

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to build Docker image" -ForegroundColor Red
    exit 1
}

Write-Host "`nRunning backtesting container..." -ForegroundColor Cyan
Write-Host "You will be prompted for your Angel One credentials.`n" -ForegroundColor Yellow

docker run -it --rm trading-bot-backtest python run_backtest.py
