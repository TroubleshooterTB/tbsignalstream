# 🚀 DEPLOYMENT SCRIPT - Phase 0 Emergency Fixes

# Deploy trading bot service to Cloud Run
cd trading_bot_service

Write-Host "="*80
Write-Host "🚀 DEPLOYING SIGNALSTREAM - PHASE 0 EMERGENCY FIXES"
Write-Host "="*80
Write-Host ""
Write-Host "Changes deployed:"
Write-Host "  ✅ Liquidity filter DISABLED (testing mode)"
Write-Host "  ✅ Screening set to RELAXED (only VaR check)"
Write-Host "  ✅ Alpha-Ensemble parameters relaxed"
Write-Host "  ✅ Test signal injector added"
Write-Host "  ✅ Bypass screening support added"
Write-Host "  ✅ Test endpoint added (/api/test/inject-signal)"
Write-Host ""
Write-Host "="*80
Write-Host ""

# Confirm deployment
$confirm = Read-Host "Deploy to Cloud Run? (y/n)"

if ($confirm -ne "y") {
    Write-Host "❌ Deployment cancelled"
    exit 1
}

Write-Host ""
Write-Host "📦 Building and deploying..."
Write-Host ""

# Deploy to Cloud Run (using existing configuration)
gcloud run deploy trading-bot-service `
    --source . `
    --region us-central1 `
    --platform managed `
    --allow-unauthenticated `
    --memory 2Gi `
    --cpu 2 `
    --timeout 3600 `
    --concurrency 80 `
    --min-instances 0 `
    --max-instances 10

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "="*80
    Write-Host "✅ DEPLOYMENT SUCCESSFUL"
    Write-Host "="*80
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "  1. Run validation test: python test_first_trade.py"
    Write-Host "  2. Start bot from dashboard (PAPER mode)"
    Write-Host "  3. Inject test signal via API"
    Write-Host "  4. Monitor Cloud Run logs"
    Write-Host ""
    Write-Host "="*80
    Write-Host ""
    
    # Show service URL
    Write-Host "Service URL:"
    gcloud run services describe trading-bot-service --region us-central1 --format="value(status.url)"
    
} else {
    Write-Host ""
    Write-Host "="*80
    Write-Host "❌ DEPLOYMENT FAILED"
    Write-Host "="*80
    Write-Host ""
    Write-Host "Check errors above and fix before retrying"
    Write-Host ""
    exit 1
}
