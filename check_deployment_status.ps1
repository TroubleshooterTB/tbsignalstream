# Frontend Deployment Verification Script
# Checks if the new frontend code with fixed URLs is deployed

Write-Host "`n🔍 CHECKING FRONTEND DEPLOYMENT STATUS`n" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Gray

# Get the commit that should be deployed
Write-Host "`n📦 Expected Deployment:" -ForegroundColor Yellow
$latestCommit = git log -1 --format="%h - %s"
Write-Host "   $latestCommit" -ForegroundColor White

# Check backend health (should always work)
Write-Host "`n🔧 Backend Health Check:" -ForegroundColor Yellow
try {
    $backendResponse = Invoke-RestMethod -Uri "https://trading-bot-service-vmxfbt7qiq-el.a.run.app/health" -Method Get -ErrorAction Stop
    Write-Host "   ✅ Backend Status: $($backendResponse.status)" -ForegroundColor Green
    Write-Host "   ✅ Firestore Connected: $($backendResponse.checks.firestore)" -ForegroundColor Green
    Write-Host "   ✅ Backend URL: https://trading-bot-service-vmxfbt7qiq-el.a.run.app" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Backend Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Check if frontend is serving new code
Write-Host "`n🌐 Frontend Deployment Check:" -ForegroundColor Yellow
Write-Host "   Fetching: https://studio--tbsignalstream.us-central1.hosted.app/" -ForegroundColor Gray

try {
    # Try to access the frontend
    $frontendHtml = Invoke-WebRequest -Uri "https://studio--tbsignalstream.us-central1.hosted.app/" -UseBasicParsing -ErrorAction Stop
    
    if ($frontendHtml.StatusCode -eq 200) {
        Write-Host "   ✅ Frontend is loading (HTTP 200)" -ForegroundColor Green
        
        # Check if it's showing the old code or new code
        # Old code would show the error, new code should load properly
        if ($frontendHtml.Content -like "*Cannot connect to trading backend*") {
            Write-Host "   ⚠️  Frontend still showing old code (connection error)" -ForegroundColor Yellow
            Write-Host "   💡 This means Firebase is still deploying..." -ForegroundColor Cyan
        } else {
            Write-Host "   ✅ Frontend appears to be updated!" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "   ❌ Frontend Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Check frontend API proxy (this should work when new code is deployed)
Write-Host "`n🔌 Frontend API Proxy Check:" -ForegroundColor Yellow
try {
    $apiResponse = Invoke-RestMethod -Uri "https://studio--tbsignalstream.us-central1.hosted.app/api/bot/health" -Method Get -ErrorAction Stop
    Write-Host "   ✅ API Proxy Working!" -ForegroundColor Green
    Write-Host "   ✅ Frontend can reach backend" -ForegroundColor Green
    Write-Host "`n   🎉 NEW CODE IS DEPLOYED AND WORKING!" -ForegroundColor Green -BackgroundColor Black
} catch {
    if ($_.Exception.Response.StatusCode -eq 404) {
        Write-Host "   ⏳ API routes not found (old code still deployed)" -ForegroundColor Yellow
        Write-Host "   💡 Waiting for Firebase deployment to complete..." -ForegroundColor Cyan
    } else {
        Write-Host "   ❌ API Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Deployment timeline
Write-Host "`n⏰ Deployment Timeline:" -ForegroundColor Yellow
$pushTime = git log -1 --format="%ai"
$currentTime = Get-Date
$pushDateTime = [DateTime]::Parse($pushTime)
$elapsed = ($currentTime - $pushDateTime).TotalMinutes

Write-Host "   Push Time: $pushTime" -ForegroundColor Gray
Write-Host "   Current Time: $($currentTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Gray
Write-Host "   Elapsed: $([Math]::Round($elapsed, 1)) minutes" -ForegroundColor Gray

if ($elapsed -lt 5) {
    Write-Host "   ⏳ Typical wait: 5-15 minutes" -ForegroundColor Yellow
    Write-Host "   💡 Please wait a few more minutes..." -ForegroundColor Cyan
} elseif ($elapsed -lt 15) {
    Write-Host "   ⏳ Should deploy soon (typical: 5-15 min)" -ForegroundColor Yellow
} else {
    Write-Host "   ⚠️  Deployment taking longer than usual" -ForegroundColor Yellow
    Write-Host "   💡 Check Firebase Console: https://console.firebase.google.com/project/tbsignalstream/apphosting" -ForegroundColor Cyan
}

Write-Host "`n" -NoNewline
Write-Host "=" * 60 -ForegroundColor Gray
Write-Host "`n📋 NEXT STEPS:`n" -ForegroundColor Cyan

if ($elapsed -lt 15) {
    Write-Host "1. Wait for Firebase deployment to complete (5-15 minutes)" -ForegroundColor White
    Write-Host "2. Refresh your browser at: https://studio--tbsignalstream.us-central1.hosted.app/" -ForegroundColor White
    Write-Host "3. Hard refresh to clear cache: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)" -ForegroundColor White
    Write-Host "4. Run this script again in 2-3 minutes to check status" -ForegroundColor White
    Write-Host "`nℹ️  Firebase is building and deploying your code right now." -ForegroundColor Gray
} else {
    Write-Host "1. Check Firebase Console: https://console.firebase.google.com/project/tbsignalstream/apphosting" -ForegroundColor White
    Write-Host "2. Look for build logs or errors" -ForegroundColor White
    Write-Host "3. Verify the latest commit is being deployed" -ForegroundColor White
}

Write-Host "`n✨ To run this check again, use:" -ForegroundColor Cyan
Write-Host "   .\check_deployment_status.ps1`n" -ForegroundColor White
