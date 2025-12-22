# Quick Backend Health Check
# Run this before starting the bot to ensure backend is working

Write-Host "`n=== TRADING BOT BACKEND HEALTH CHECK ===" -ForegroundColor Cyan
Write-Host "Checking: https://trading-bot-service-818546654122.asia-south1.run.app" -ForegroundColor Gray

try {
    $response = Invoke-RestMethod -Uri "https://trading-bot-service-818546654122.asia-south1.run.app/health" -Method GET -TimeoutSec 10
    
    if ($response.status -eq "healthy") {
        Write-Host "`n✅ BACKEND IS HEALTHY" -ForegroundColor Green
        Write-Host "   Status: $($response.status)" -ForegroundColor Green
        Write-Host "   Active Bots: $($response.active_bots)" -ForegroundColor Green
        Write-Host "`n✅ SAFE TO START BOT" -ForegroundColor Green
        exit 0
    } else {
        Write-Host "`n❌ BACKEND UNHEALTHY" -ForegroundColor Red
        Write-Host "   Status: $($response.status)" -ForegroundColor Red
        Write-Host "`n❌ DO NOT START BOT - CONTACT SUPPORT" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "`n❌ BACKEND NOT RESPONDING" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`n❌ DO NOT START BOT - BACKEND IS DOWN" -ForegroundColor Red
    Write-Host "`nTroubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Check Cloud Run logs: gcloud logging read 'resource.labels.service_name=trading-bot-service' --limit 5" -ForegroundColor Yellow
    Write-Host "2. Verify revision: gcloud run services describe trading-bot-service --region asia-south1" -ForegroundColor Yellow
    exit 1
}
