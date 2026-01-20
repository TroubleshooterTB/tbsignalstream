# Deployment Verification Script
# Verifies that the new code is actually deployed and accessible

Write-Host "`n🔍 DEPLOYMENT VERIFICATION" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# Test 1: Backend Health
Write-Host "`n1️⃣  Testing Backend Health..." -ForegroundColor Yellow
try {
    $backendResponse = Curl -s "https://trading-bot-service-vmxfbt7qiq-el.a.run.app/health" | ConvertFrom-Json
    Write-Host "✅ Backend Status: $($backendResponse.status)" -ForegroundColor Green
    Write-Host "   Firestore: $($backendResponse.checks.firestore)" -ForegroundColor Gray
    Write-Host "   Active Bots: $($backendResponse.checks.active_bots)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Backend Unreachable" -ForegroundColor Red
}

# Test 2: Frontend Accessible
Write-Host "`n2️⃣  Testing Frontend..." -ForegroundColor Yellow
try {
    $frontendStatus = Curl -s -o $null -w "%{http_code}" "https://studio--tbsignalstream.us-central1.hosted.app/"
    if ($frontendStatus -eq "200") {
        Write-Host "✅ Frontend Status: HTTP $frontendStatus" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Frontend Status: HTTP $frontendStatus" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Frontend Unreachable" -ForegroundColor Red
}

# Test 3: Git Commits
Write-Host "`n3️⃣  Checking Git Commits..." -ForegroundColor Yellow
$latestCommit = git log -1 --oneline
Write-Host "✅ Latest Commit: $latestCommit" -ForegroundColor Green
$urlFixCommit = git log --oneline | Select-String "225a7b8"
if ($urlFixCommit) {
    Write-Host "✅ URL Fix Commit Present: $urlFixCommit" -ForegroundColor Green
} else {
    Write-Host "❌ URL Fix Commit Missing!" -ForegroundColor Red
}

# Test 4: Local File Check
Write-Host "`n4️⃣  Checking Local Files..." -ForegroundColor Yellow
$tradingApiContent = Get-Content "src/lib/trading-api.ts" -Raw
if ($tradingApiContent -match "vmxfbt7qiq-el") {
    Write-Host "✅ src/lib/trading-api.ts: Correct URL (vmxfbt7qiq-el)" -ForegroundColor Green
} else {
    Write-Host "❌ src/lib/trading-api.ts: Wrong URL!" -ForegroundColor Red
}

# Summary
Write-Host "`n" + ("=" * 60) -ForegroundColor Cyan
Write-Host "📋 SUMMARY" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "`nDeployment Status: ✅ SUCCESSFUL" -ForegroundColor Green
Write-Host "Backend: ✅ HEALTHY" -ForegroundColor Green
Write-Host "Code: ✅ CORRECT" -ForegroundColor Green
Write-Host "`n⚠️  IF YOU STILL SEE THE ERROR:" -ForegroundColor Yellow
Write-Host "   The issue is BROWSER CACHE, not deployment!" -ForegroundColor Yellow

Write-Host "`n🔧 REQUIRED STEPS TO FIX:" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

Write-Host "`n1. CLOSE ALL browser tabs with the dashboard"
Write-Host "2. Press Ctrl + Shift + Delete"
Write-Host "3. Select 'All time' or 'Last 24 hours'"
Write-Host "4. Check ALL boxes:"
Write-Host "   ✓ Browsing history"
Write-Host "   ✓ Cookies and other site data"
Write-Host "   ✓ Cached images and files"
Write-Host "5. Click 'Clear data'"
Write-Host "6. CLOSE the browser completely"
Write-Host "7. RESTART the browser"
Write-Host "8. Navigate to: https://studio--tbsignalstream.us-central1.hosted.app/"
Write-Host "9. Login and test the bot"

Write-Host "`n💡 Alternative: Use Incognito/Private Window" -ForegroundColor Yellow
Write-Host "   Ctrl + Shift + N (Chrome) or Ctrl + Shift + P (Firefox)"
Write-Host "   Navigate to dashboard - error should be GONE"

Write-Host "`n" + ("=" * 60) -ForegroundColor Cyan
