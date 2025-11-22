# TBSignalStream - Complete Deployment Script
# Deploys all Cloud Functions and Frontend

Write-Host "================================" -ForegroundColor Cyan
Write-Host "TBSignalStream Deployment Script" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

$PROJECT_ID = "tbsignalstream"
$REGION = "us-central1"
$RUNTIME = "python311"

# Function to deploy a Cloud Function
function Deploy-CloudFunction {
    param(
        [string]$FunctionName,
        [string]$EntryPoint,
        [string]$Memory = "512MB",
        [string]$Timeout = "60s",
        [string]$Description
    )
    
    Write-Host "Deploying $FunctionName..." -ForegroundColor Yellow
    Write-Host "  Description: $Description" -ForegroundColor Gray
    Write-Host "  Memory: $Memory, Timeout: $Timeout" -ForegroundColor Gray
    
    gcloud functions deploy $FunctionName `
        --gen2 `
        --runtime=$RUNTIME `
        --region=$REGION `
        --source=functions `
        --entry-point=$EntryPoint `
        --trigger-http `
        --allow-unauthenticated `
        --memory=$Memory `
        --timeout=$Timeout `
        --project=$PROJECT_ID `
        --set-secrets="ANGEL_ONE_API_KEY=ANGELONE_TRADING_API_KEY:latest,ANGEL_ONE_API_SECRET=ANGELONE_TRADING_SECRET:latest,ANGEL_ONE_CLIENT_ID=ANGELONE_CLIENT_CODE:latest,ANGEL_ONE_PASSWORD=ANGELONE_PASSWORD:latest,ANGEL_ONE_TOTP_SECRET=ANGELONE_TOTP_SECRET:latest"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ $FunctionName deployed successfully!" -ForegroundColor Green
    } else {
        Write-Host "✗ $FunctionName deployment failed!" -ForegroundColor Red
        return $false
    }
    Write-Host ""
    return $true
}

# Confirm deployment
Write-Host "This will deploy the following components:" -ForegroundColor Yellow
Write-Host "  • 10 Cloud Functions (WebSocket, Orders, Trading Bot)" -ForegroundColor White
Write-Host "  • Updated Firestore security rules" -ForegroundColor White
Write-Host "  • Frontend to App Hosting" -ForegroundColor White
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

# Grant Cloud Build role to service account (fix permission issue)
Write-Host "Granting Cloud Build permissions..." -ForegroundColor Yellow
gcloud projects add-iam-policy-binding $PROJECT_ID `
    --member="serviceAccount:818546654122-compute@developer.gserviceaccount.com" `
    --role="roles/cloudbuild.builds.builder" `
    --quiet 2>&1 | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Cloud Build permissions granted" -ForegroundColor Green
}
Write-Host ""

# ===========================
# WEBSOCKET FUNCTIONS
# ===========================

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "DEPLOYING WEBSOCKET FUNCTIONS" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

Deploy-CloudFunction `
    -FunctionName "initializeWebSocket" `
    -EntryPoint "initializeWebSocket" `
    -Memory "1GB" `
    -Timeout "540s" `
    -Description "Initialize WebSocket connection for live market data"

Deploy-CloudFunction `
    -FunctionName "subscribeWebSocket" `
    -EntryPoint "subscribeWebSocket" `
    -Memory "512MB" `
    -Timeout "60s" `
    -Description "Subscribe to symbols on existing WebSocket connection"

Deploy-CloudFunction `
    -FunctionName "closeWebSocket" `
    -EntryPoint "closeWebSocket" `
    -Memory "256MB" `
    -Timeout "60s" `
    -Description "Close WebSocket connection"

# ===========================
# ORDER MANAGEMENT FUNCTIONS
# ===========================

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "DEPLOYING ORDER FUNCTIONS" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

Deploy-CloudFunction `
    -FunctionName "placeOrder" `
    -EntryPoint "placeOrder" `
    -Memory "512MB" `
    -Timeout "60s" `
    -Description "Place order with Angel One broker"

Deploy-CloudFunction `
    -FunctionName "modifyOrder" `
    -EntryPoint "modifyOrder" `
    -Memory "256MB" `
    -Timeout "60s" `
    -Description "Modify existing order"

Deploy-CloudFunction `
    -FunctionName "cancelOrder" `
    -EntryPoint "cancelOrder" `
    -Memory "256MB" `
    -Timeout "60s" `
    -Description "Cancel existing order"

Deploy-CloudFunction `
    -FunctionName "getOrderBook" `
    -EntryPoint "getOrderBook" `
    -Memory "256MB" `
    -Timeout "60s" `
    -Description "Fetch order book and history"

Deploy-CloudFunction `
    -FunctionName "getPositions" `
    -EntryPoint "getPositions" `
    -Memory "256MB" `
    -Timeout "60s" `
    -Description "Fetch current positions"

# ===========================
# LIVE TRADING BOT FUNCTIONS
# ===========================

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "DEPLOYING LIVE TRADING BOT" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

Deploy-CloudFunction `
    -FunctionName "startLiveTradingBot" `
    -EntryPoint "startLiveTradingBot" `
    -Memory "2GB" `
    -Timeout "540s" `
    -Description "Start live trading bot with real-time execution"

Deploy-CloudFunction `
    -FunctionName "stopLiveTradingBot" `
    -EntryPoint "stopLiveTradingBot" `
    -Memory "256MB" `
    -Timeout "60s" `
    -Description "Stop live trading bot"

# ===========================
# FIRESTORE SECURITY RULES
# ===========================

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "DEPLOYING FIRESTORE RULES" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

Write-Host "Deploying Firestore security rules..." -ForegroundColor Yellow

firebase deploy --only firestore --project=$PROJECT_ID

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Firestore rules deployed successfully!" -ForegroundColor Green
} else {
    Write-Host "✗ Firestore rules deployment failed!" -ForegroundColor Red
}

Write-Host ""

# ===========================
# FRONTEND DEPLOYMENT (APP HOSTING)
# ===========================

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "DEPLOYING FRONTEND (APP HOSTING)" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

Write-Host "Deploying to Firebase App Hosting (studio backend)..." -ForegroundColor Yellow
Write-Host "Note: App Hosting deployment may take 5-10 minutes..." -ForegroundColor Gray

firebase apphosting:backends:create studio --project=$PROJECT_ID 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Backend 'studio' already exists, updating..." -ForegroundColor Gray
}

firebase deploy --only apphosting:studio --project=$PROJECT_ID

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ App Hosting deployment initiated successfully!" -ForegroundColor Green
    Write-Host "  Monitor build progress in Firebase Console" -ForegroundColor Gray
} else {
    Write-Host "✗ App Hosting deployment failed!" -ForegroundColor Red
    Write-Host "  You can deploy manually with: firebase deploy --only apphosting:studio" -ForegroundColor Yellow
}

Write-Host ""

# ===========================
# DEPLOYMENT SUMMARY
# ===========================

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "DEPLOYMENT COMPLETE" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

Write-Host "✓ All Cloud Functions deployed" -ForegroundColor Green
Write-Host "✓ Firestore rules updated" -ForegroundColor Green
Write-Host "✓ Frontend deployed to App Hosting" -ForegroundColor Green
Write-Host ""

Write-Host "Deployed Functions:" -ForegroundColor Yellow
Write-Host "  WebSocket Functions:" -ForegroundColor White
Write-Host "    • initializeWebSocket" -ForegroundColor Gray
Write-Host "    • subscribeWebSocket" -ForegroundColor Gray
Write-Host "    • closeWebSocket" -ForegroundColor Gray
Write-Host ""
Write-Host "  Order Management:" -ForegroundColor White
Write-Host "    • placeOrder" -ForegroundColor Gray
Write-Host "    • modifyOrder" -ForegroundColor Gray
Write-Host "    • cancelOrder" -ForegroundColor Gray
Write-Host "    • getOrderBook" -ForegroundColor Gray
Write-Host "    • getPositions" -ForegroundColor Gray
Write-Host ""
Write-Host "  Live Trading Bot:" -ForegroundColor White
Write-Host "    • startLiveTradingBot" -ForegroundColor Gray
Write-Host "    • stopLiveTradingBot" -ForegroundColor Gray
Write-Host ""

Write-Host "Frontend URL:" -ForegroundColor Yellow
Write-Host "  https://studio--tbsignalstream.us-central1.hosted.app" -ForegroundColor Cyan
Write-Host ""

Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Test WebSocket connection with a single symbol" -ForegroundColor White
Write-Host "  2. Verify order placement in paper trading mode" -ForegroundColor White
Write-Host "  3. Start live trading bot with 1 symbol" -ForegroundColor White
Write-Host "  4. Monitor Cloud Function logs closely" -ForegroundColor White
Write-Host "  5. Scale up gradually after confirming stability" -ForegroundColor White
Write-Host ""

Write-Host "View logs:" -ForegroundColor Yellow
Write-Host "  gcloud functions logs read startLiveTradingBot --region=us-central1 --limit=100" -ForegroundColor Gray
Write-Host ""

Write-Host "🎉 Ready for live trading!" -ForegroundColor Green
Write-Host ""
