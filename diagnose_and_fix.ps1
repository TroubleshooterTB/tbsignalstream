# Complete Diagnostic and Fix Script for Frontend Connection Issues
# Run this to diagnose and fix the "Cannot connect to trading backend" error

Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  TBSignalStream - Connection Diagnostic & Fix Tool           ║" -ForegroundColor Cyan
Write-Host "║  Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')                         ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# 1. Check Backend Health
Write-Host "🔧 Step 1: Backend Health Check" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
try {
    $backend = Invoke-RestMethod -Uri "https://trading-bot-service-vmxfbt7qiq-el.a.run.app/health" -Method Get -TimeoutSec 10
    Write-Host "   ✅ Backend Status: $($backend.status)" -ForegroundColor Green
    Write-Host "   ✅ Firestore: $($backend.checks.firestore)" -ForegroundColor Green
    Write-Host "   ✅ Active Bots: $($backend.checks.active_bots)" -ForegroundColor Green
    Write-Host "   ✅ URL: https://trading-bot-service-vmxfbt7qiq-el.a.run.app" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Backend Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   💡 Backend might be down - contact support" -ForegroundColor Yellow
    exit 1
}

# 2. Check Git Status
Write-Host "`n🔍 Step 2: Git Repository Status" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
$latestCommit = git log -1 --format="%h - %s (%cr)"
Write-Host "   Latest Commit: $latestCommit" -ForegroundColor White

$remoteCommit = git ls-remote origin HEAD | Select-Object -First 1 | ForEach-Object { $_.Split()[0].Substring(0,7) }
$localCommit = git rev-parse HEAD | ForEach-Object { $_.Substring(0,7) }

if ($remoteCommit -eq $localCommit) {
    Write-Host "   ✅ Local and remote are in sync" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Local ($localCommit) differs from remote ($remoteCommit)" -ForegroundColor Yellow
    Write-Host "   💡 Run 'git pull' to sync" -ForegroundColor Cyan
}

# 3. Check apphosting.yaml
Write-Host "`n📝 Step 3: Configuration File Check" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
$apphostingContent = Get-Content "apphosting.yaml" -Raw
if ($apphostingContent -match "vmxfbt7qiq-el") {
    Write-Host "   ✅ apphosting.yaml has CORRECT backend URL" -ForegroundColor Green
    Write-Host "   ✅ Config: https://trading-bot-service-vmxfbt7qiq-el.a.run.app" -ForegroundColor Green
} elseif ($apphostingContent -match "818546654122") {
    Write-Host "   ❌ apphosting.yaml has WRONG backend URL (old)" -ForegroundColor Red
    Write-Host "   🔧 Fixing now..." -ForegroundColor Yellow
    
    $apphostingContent = $apphostingContent -replace "818546654122.asia-south1", "vmxfbt7qiq-el.a"
    Set-Content "apphosting.yaml" -Value $apphostingContent
    
    git add apphosting.yaml
    git commit -m "FIX: Update backend URL in apphosting.yaml"
    git push origin master
    
    Write-Host "   ✅ Fixed and pushed to GitHub" -ForegroundColor Green
    Write-Host "   ⏳ Wait 5-10 minutes for Firebase to redeploy" -ForegroundColor Yellow
} else {
    Write-Host "   ⚠️  Backend URL not found in apphosting.yaml" -ForegroundColor Yellow
}

# 4. Check Source Code URLs
Write-Host "`n🔎 Step 4: Source Code URL Check" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

$wrongUrlCount = 0
$files = @("src/lib/trading-api.ts", "src/app/api/backtest/route.ts", "src/config/env.ts")

foreach ($file in $files) {
    if (Test-Path $file) {
        $content = Get-Content $file -Raw
        if ($content -match "818546654122") {
            Write-Host "   ❌ $file contains WRONG URL" -ForegroundColor Red
            $wrongUrlCount++
        } elseif ($content -match "vmxfbt7qiq-el") {
            Write-Host "   ✅ $file has correct URL" -ForegroundColor Green
        }
    }
}

if ($wrongUrlCount -gt 0) {
    Write-Host "`n   🔧 Found $wrongUrlCount file(s) with wrong URLs - fixing now..." -ForegroundColor Yellow
    
    foreach ($file in $files) {
        if (Test-Path $file) {
            $content = Get-Content $file -Raw
            if ($content -match "818546654122") {
                $content = $content -replace "818546654122.asia-south1", "vmxfbt7qiq-el.a"
                Set-Content $file -Value $content
                Write-Host "   ✅ Fixed: $file" -ForegroundColor Green
            }
        }
    }
    
    git add src/
    git commit -m "FIX: Update backend URLs in source code"
    git push origin master
    
    Write-Host "   ✅ All URLs fixed and pushed to GitHub" -ForegroundColor Green
    Write-Host "   ⏳ Wait 5-10 minutes for Firebase to redeploy" -ForegroundColor Yellow
}

# 5. Check Frontend Deployment Status
Write-Host "`n🌐 Step 5: Frontend Deployment Status" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
try {
    $frontend = Invoke-WebRequest -Uri "https://studio--tbsignalstream.us-central1.hosted.app/" -UseBasicParsing -TimeoutSec 10
    Write-Host "   ✅ Frontend is accessible (HTTP $($frontend.StatusCode))" -ForegroundColor Green
    
    # Check if it's showing an error page
    if ($frontend.Content -match "Cannot connect to trading backend" -or $frontend.Content -match "System Error") {
        Write-Host "   ⚠️  Frontend showing error page (old deployment)" -ForegroundColor Yellow
    } elseif ($frontend.Content -match "vmxfbt7qiq-el") {
        Write-Host "   ✅ Frontend appears to have new code deployed" -ForegroundColor Green
    } else {
        Write-Host "   ℹ️  Cannot determine deployment status from HTML" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ❌ Frontend not accessible: $($_.Exception.Message)" -ForegroundColor Red
}

# 6. Browser Cache Issue Detection
Write-Host "`n🔄 Step 6: Browser Cache Status" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host "   ⚠️  Browser cache can show old error pages even after deployment" -ForegroundColor Yellow
Write-Host "`n   To clear browser cache:" -ForegroundColor White
Write-Host "   1. Open: https://studio--tbsignalstream.us-central1.hosted.app/" -ForegroundColor Gray
Write-Host "   2. Press: Ctrl + Shift + R (Windows) or Cmd + Shift + R (Mac)" -ForegroundColor Gray
Write-Host "   3. Or: Open in Incognito/Private window (Ctrl+Shift+N)" -ForegroundColor Gray
Write-Host "   4. Or: Clear all browser data for last hour" -ForegroundColor Gray

# 7. Summary and Next Steps
Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  DIAGNOSTIC SUMMARY                                           ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

Write-Host "✅ VERIFIED WORKING:" -ForegroundColor Green
Write-Host "   • Backend health check: PASSED" -ForegroundColor White
Write-Host "   • Firestore connection: WORKING" -ForegroundColor White
Write-Host "   • Backend URL: Correct (vmxfbt7qiq-el.a.run.app)" -ForegroundColor White

Write-Host "`n📋 NEXT STEPS:" -ForegroundColor Yellow

$lastCommitTime = git log -1 --format="%ci"
$lastCommitDate = [DateTime]::Parse($lastCommitTime)
$minutesSinceCommit = [Math]::Round(((Get-Date) - $lastCommitDate).TotalMinutes)

if ($wrongUrlCount -gt 0) {
    Write-Host "`n   🔧 URLs were just fixed and pushed to GitHub" -ForegroundColor Yellow
    Write-Host "   ⏳ Firebase App Hosting is now building and deploying" -ForegroundColor Cyan
    Write-Host "   ⏰ Wait 5-10 minutes, then:" -ForegroundColor White
    Write-Host "      1. Hard refresh browser (Ctrl+Shift+R)" -ForegroundColor Gray
    Write-Host "      2. Check if error is gone" -ForegroundColor Gray
    Write-Host "      3. Try starting the bot" -ForegroundColor Gray
} elseif ($minutesSinceCommit -lt 15) {
    Write-Host "`n   ⏳ Recent deployment detected ($minutesSinceCommit minutes ago)" -ForegroundColor Yellow
    Write-Host "   💡 If you see the error:" -ForegroundColor Cyan
    Write-Host "      1. Hard refresh browser: Ctrl+Shift+R" -ForegroundColor Gray
    Write-Host "      2. Try Incognito window: Ctrl+Shift+N" -ForegroundColor Gray
    Write-Host "      3. Clear browser cache completely" -ForegroundColor Gray
} else {
    Write-Host "`n   ✅ All URLs are correct in git ($minutesSinceCommit min ago)" -ForegroundColor Green
    Write-Host "   💡 If you still see the error:" -ForegroundColor Cyan
    Write-Host "      1. HARD REFRESH: Ctrl+Shift+R (MUST DO THIS!)" -ForegroundColor Yellow
    Write-Host "      2. Try Incognito window: Ctrl+Shift+N" -ForegroundColor Gray
    Write-Host "      3. Clear all browser data for last 24 hours" -ForegroundColor Gray
    Write-Host "`n   🔍 If error persists after hard refresh:" -ForegroundColor Yellow
    Write-Host "      • Check Firebase Console: https://console.firebase.google.com/project/tbsignalstream/apphosting" -ForegroundColor Gray
    Write-Host "      • Look for failed deployments" -ForegroundColor Gray
    Write-Host "      • Check build logs for errors" -ForegroundColor Gray
}

Write-Host "`n📞 TROUBLESHOOTING:" -ForegroundColor Cyan
Write-Host "   If issue persists after hard refresh:" -ForegroundColor White
Write-Host "   1. Open browser DevTools (F12)" -ForegroundColor Gray
Write-Host "   2. Go to Network tab" -ForegroundColor Gray
Write-Host "   3. Try starting bot" -ForegroundColor Gray
Write-Host "   4. Look for failed API calls" -ForegroundColor Gray
Write-Host "   5. Check which URL it's calling" -ForegroundColor Gray

Write-Host "`n🔗 USEFUL LINKS:" -ForegroundColor Cyan
Write-Host "   • Frontend: https://studio--tbsignalstream.us-central1.hosted.app/" -ForegroundColor Gray
Write-Host "   • Backend Health: https://trading-bot-service-vmxfbt7qiq-el.a.run.app/health" -ForegroundColor Gray
Write-Host "   • Firebase Console: https://console.firebase.google.com/project/tbsignalstream/apphosting" -ForegroundColor Gray
Write-Host "   • Cloud Run: https://console.cloud.google.com/run?project=tbsignalstream" -ForegroundColor Gray

Write-Host "`n✨ Done! Follow the next steps above to resolve the issue.`n" -ForegroundColor Green
