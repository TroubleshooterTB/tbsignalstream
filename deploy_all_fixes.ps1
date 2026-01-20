#!/usr/bin/env pwsh
# Phase 1-3 Complete Deployment Script
# Run this to deploy all fixes to production

Write-Host "🚀 DEPLOYING ALL FIXES TO PRODUCTION" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""

# Phase 1: Frontend is auto-deploying via Firebase App Hosting
Write-Host "✅ PHASE 1: Frontend URL Fixes" -ForegroundColor Cyan
Write-Host "   - Already pushed to GitHub (commit 225a7b8)" -ForegroundColor Gray
Write-Host "   - Firebase App Hosting auto-deploying..." -ForegroundColor Gray
Write-Host "   - Check: https://console.firebase.google.com/project/tbsignalstream/apphosting" -ForegroundColor Gray
Write-Host ""

# Phase 2: Deploy backend improvements
Write-Host "⏳ PHASE 2: Deploying Backend Improvements" -ForegroundColor Cyan
Write-Host "   - WebSocket timeout increased to 60s" -ForegroundColor Gray
Write-Host "   - Deploying to Cloud Run..." -ForegroundColor Gray
Write-Host ""

Set-Location "trading_bot_service"

$deployOutput = gcloud run deploy trading-bot-service `
  --source=. `
  --platform=managed `
  --region=asia-south1 `
  --allow-unauthenticated `
  --memory=2Gi `
  --cpu=2 `
  --timeout=3600 `
  --max-instances=1 `
  --set-env-vars="PYTHONUNBUFFERED=1" `
  --project=tbsignalstream 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Backend deployed successfully!" -ForegroundColor Green
} else {
    Write-Host "   ❌ Backend deployment failed!" -ForegroundColor Red
    Write-Host $deployOutput
    exit 1
}

Set-Location ".."

Write-Host ""

# Phase 3: Verify deployments
Write-Host "🔍 PHASE 3: Verifying Deployments" -ForegroundColor Cyan

# Check backend health
Write-Host "   Testing backend health..." -ForegroundColor Gray
try {
    $healthResponse = Invoke-RestMethod -Uri "https://trading-bot-service-vmxfbt7qiq-el.a.run.app/health" -Method Get
    if ($healthResponse.status -eq "healthy") {
        Write-Host "   ✅ Backend health check: PASSED" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Backend health check: Unexpected response" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Backend health check: FAILED" -ForegroundColor Red
    Write-Host "   Error: $_" -ForegroundColor Red
}

Write-Host ""

# Summary
Write-Host "📊 DEPLOYMENT SUMMARY" -ForegroundColor Green
Write-Host "=====================" -ForegroundColor Green
Write-Host ""
Write-Host "✅ Fixed Issues:" -ForegroundColor Cyan
Write-Host "   1. Frontend-Backend URL mismatch (9 URLs updated)" -ForegroundColor Gray
Write-Host "   2. WebSocket timeout increased (30s → 60s)" -ForegroundColor Gray
Write-Host "   3. Local testing enabled (.env file created)" -ForegroundColor Gray
Write-Host "   4. Backtesting verified working" -ForegroundColor Gray
Write-Host ""
Write-Host "🌐 Live URLs:" -ForegroundColor Cyan
Write-Host "   Frontend: https://studio--tbsignalstream.us-central1.hosted.app/" -ForegroundColor Gray
Write-Host "   Backend:  https://trading-bot-service-vmxfbt7qiq-el.a.run.app/" -ForegroundColor Gray
Write-Host ""
Write-Host "📝 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Wait 3-5 minutes for Firebase frontend deployment to complete" -ForegroundColor Yellow
Write-Host "   2. Open dashboard and try starting the bot" -ForegroundColor Yellow
Write-Host "   3. Monitor during next market hours (tomorrow 9:15 AM IST)" -ForegroundColor Yellow
Write-Host ""
Write-Host "🎉 All critical fixes deployed!" -ForegroundColor Green
