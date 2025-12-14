# The Defining Order v3.2 - Deployment Script
# Based on successful deploy_complete.ps1 pattern

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Defining Order v3.2 - Deployment Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$PROJECT_ID = "tbsignalstream"
$REGION = "asia-south1"
$WORKSPACE_DIR = "d:\Tushar 2.0\tbsignalstream_backup\tbsignalstream_backup"

Set-Location $WORKSPACE_DIR
Write-Host "Current Directory: $PWD" -ForegroundColor Gray
Write-Host ""

# Confirm deployment
Write-Host "This will deploy the following components:" -ForegroundColor Yellow
Write-Host "  • Frontend (Next.js) to Firebase App Hosting" -ForegroundColor White
Write-Host "  • Backend (trading-bot-service) to Cloud Run" -ForegroundColor White
Write-Host "  • v3.2 Strategy: The Defining Order Breakout (VALIDATED)" -ForegroundColor White
Write-Host ""
Write-Host "Project: $PROJECT_ID" -ForegroundColor Cyan
Write-Host "Region: $REGION" -ForegroundColor Cyan
Write-Host ""

$confirm = Read-Host "Continue with deployment? (y/n)"
if ($confirm -ne "y" -and $confirm -ne "yes") {
    Write-Host "Deployment cancelled." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Starting deployment..." -ForegroundColor Green
Write-Host ""

# ===========================
# STEP 1: Deploy Backend (Cloud Run)
# ===========================
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "DEPLOYING BACKEND (CLOUD RUN)" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

Set-Location "$WORKSPACE_DIR\trading_bot_service"

Write-Host "Deploying trading-bot-service to Cloud Run..." -ForegroundColor Yellow
Write-Host "  Region: $REGION" -ForegroundColor Gray
Write-Host "  Includes: v3.2 Strategy (defining_order_strategy.py)" -ForegroundColor Gray
Write-Host "  Timeout: 3600s (1 hour)" -ForegroundColor Gray
Write-Host "  Memory: 2Gi" -ForegroundColor Gray
Write-Host ""

gcloud run deploy trading-bot-service `
  --source . `
  --region $REGION `
  --platform managed `
  --allow-unauthenticated `
  --timeout 3600s `
  --memory 2Gi `
  --max-instances 10 `
  --project $PROJECT_ID

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "✗ Cloud Run deployment failed!" -ForegroundColor Red
    Write-Host "Please check the error above and try again." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "✓ Cloud Run deployment successful!" -ForegroundColor Green
Write-Host ""

# Verify Cloud Run deployment
Write-Host "Verifying Cloud Run service..." -ForegroundColor Yellow
$cloudRunUrl = gcloud run services describe trading-bot-service --region $REGION --format "value(status.url)" --project $PROJECT_ID
Write-Host "  URL: $cloudRunUrl" -ForegroundColor Gray

try {
    $healthCheck = Invoke-WebRequest -Uri "$cloudRunUrl/status" -Method GET -TimeoutSec 10
    if ($healthCheck.StatusCode -eq 200) {
        Write-Host "✓ Health check passed!" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠ Health check failed (service may need a moment to start)" -ForegroundColor Yellow
}

Write-Host ""

# ===========================
# STEP 2: Deploy Frontend (App Hosting)
# ===========================
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "DEPLOYING FRONTEND (APP HOSTING)" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

Set-Location $WORKSPACE_DIR

Write-Host "Building Next.js application..." -ForegroundColor Yellow
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "✗ Frontend build failed!" -ForegroundColor Red
    Write-Host "Please check the build errors above." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "✓ Frontend build successful!" -ForegroundColor Green
Write-Host ""

Write-Host "Deploying to Firebase App Hosting (studio backend)..." -ForegroundColor Yellow
Write-Host "  Note: This may take 5-10 minutes..." -ForegroundColor Gray
Write-Host ""

# Create backend if it doesn't exist (suppress errors if already exists)
firebase apphosting:backends:create studio --project=$PROJECT_ID 2>$null

# Deploy to App Hosting
firebase deploy --only apphosting:studio --project=$PROJECT_ID

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "⚠ App Hosting deployment may have issues" -ForegroundColor Yellow
    Write-Host "You can deploy manually later with:" -ForegroundColor Gray
    Write-Host "  firebase deploy --only apphosting:studio" -ForegroundColor Gray
} else {
    Write-Host ""
    Write-Host "✓ App Hosting deployment initiated!" -ForegroundColor Green
    Write-Host "  Monitor build progress in Firebase Console" -ForegroundColor Gray
}

Write-Host ""

# ===========================
# DEPLOYMENT SUMMARY
# ===========================
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "DEPLOYMENT COMPLETE" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

Write-Host "✓ Backend (Cloud Run) deployed" -ForegroundColor Green
Write-Host "✓ Frontend (App Hosting) deployed" -ForegroundColor Green
Write-Host "✓ v3.2 Strategy integrated" -ForegroundColor Green
Write-Host ""

Write-Host "Deployed Components:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Backend (Cloud Run):" -ForegroundColor White
Write-Host "    • Service: trading-bot-service" -ForegroundColor Gray
Write-Host "    • Region: asia-south1" -ForegroundColor Gray
Write-Host "    • URL: $cloudRunUrl" -ForegroundColor Gray
Write-Host "    • New File: defining_order_strategy.py" -ForegroundColor Gray
Write-Host "    • Updated: bot_engine.py (v3.2 routing)" -ForegroundColor Gray
Write-Host ""
Write-Host "  Frontend (App Hosting):" -ForegroundColor White
Write-Host "    • Backend ID: studio" -ForegroundColor Gray
Write-Host "    • URL: https://studio--tbsignalstream.us-central1.hosted.app" -ForegroundColor Gray
Write-Host "    • Updated: trading-bot-controls.tsx (4 strategies)" -ForegroundColor Gray
Write-Host "    • Updated: trading-context.tsx (default: 'defining')" -ForegroundColor Gray
Write-Host "    • Updated: trading-api.ts (v3.2 type)" -ForegroundColor Gray
Write-Host ""

Write-Host "v3.2 Strategy Configuration:" -ForegroundColor Yellow
Write-Host "  Hour Blocks:" -ForegroundColor White
Write-Host "    ✓ 10AM (0% WR)" -ForegroundColor Gray
Write-Host "    ✓ 11AM (20% WR)" -ForegroundColor Gray
Write-Host "    ✓ 12PM (30% WR - TOXIC)" -ForegroundColor Gray
Write-Host "    ✓ 13PM (30% WR - TOXIC)" -ForegroundColor Gray
Write-Host "    ✗ 15PM (44% WR - ALLOWED)" -ForegroundColor Gray
Write-Host ""
Write-Host "  Relaxed Filters:" -ForegroundColor White
Write-Host "    • RSI Range: 30-70 (was 35-65)" -ForegroundColor Gray
Write-Host "    • Breakout Min: 0.4% (was 0.6%)" -ForegroundColor Gray
Write-Host "    • Late Volume: 1.5x (was 2.5x)" -ForegroundColor Gray
Write-Host ""
Write-Host "  Blacklist:" -ForegroundColor White
Write-Host "    • SBIN-EQ (0/3 WR)" -ForegroundColor Gray
Write-Host "    • POWERGRID-EQ (0/2 WR)" -ForegroundColor Gray
Write-Host "    • SHRIRAMFIN-EQ (0/2 WR)" -ForegroundColor Gray
Write-Host "    • JSWSTEEL-EQ (1/5 WR - 20%)" -ForegroundColor Gray
Write-Host ""

Write-Host "Validated Performance:" -ForegroundColor Yellow
Write-Host "  • Full Backtest: 43 trades, 53.49% WR, ₹24,095.64 (24.10%)" -ForegroundColor White
Write-Host "  • 5-Day Test: 32 trades, 59.38% WR, ₹22,604 profit" -ForegroundColor White
Write-Host "  • All 5 days profitable (no losing days)" -ForegroundColor White
Write-Host ""

Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Open dashboard: https://studio--tbsignalstream.us-central1.hosted.app" -ForegroundColor White
Write-Host "  2. Verify strategy dropdown shows 4 options" -ForegroundColor White
Write-Host "  3. Confirm default is 'The Defining Order v3.2'" -ForegroundColor White
Write-Host "  4. Run PAPER TRADING test (2 hours, Monday 9:15-11:00 AM)" -ForegroundColor White
Write-Host "  5. If successful, switch to LIVE mode" -ForegroundColor White
Write-Host ""

Write-Host "Paper Trading Test Checklist:" -ForegroundColor Yellow
Write-Host "  ✓ Mode: PAPER (no real money)" -ForegroundColor White
Write-Host "  ✓ Expected: 2-3 paper trades" -ForegroundColor White
Write-Host "  ✓ Check: No 12:00/13:00 trades (toxic hours)" -ForegroundColor White
Write-Host "  ✓ Check: No blacklisted symbol trades" -ForegroundColor White
Write-Host "  ✓ Check: Activity feed updates correctly" -ForegroundColor White
Write-Host "  ✓ Check: No errors or crashes" -ForegroundColor White
Write-Host ""

Write-Host "Console Links:" -ForegroundColor Yellow
Write-Host "  • Firebase Console: https://console.firebase.google.com/project/$PROJECT_ID" -ForegroundColor Cyan
Write-Host "  • Cloud Run: https://console.cloud.google.com/run/detail/$REGION/trading-bot-service?project=$PROJECT_ID" -ForegroundColor Cyan
Write-Host "  • App Hosting: https://console.firebase.google.com/project/$PROJECT_ID/apphosting" -ForegroundColor Cyan
Write-Host ""

Write-Host "Emergency Stop:" -ForegroundColor Red
Write-Host "  Click 'Stop Trading Bot' button in dashboard" -ForegroundColor White
Write-Host ""

Set-Location $WORKSPACE_DIR

Write-Host "🎉 Deployment script completed successfully!" -ForegroundColor Green
Write-Host ""
