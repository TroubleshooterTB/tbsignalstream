# Monitor Firebase Deployment Status
# Checks every 30 seconds if the new build is deployed

$startTime = Get-Date
$maxWaitMinutes = 15
$checkInterval = 30  # seconds

Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Firebase Deployment Monitor                                  ║" -ForegroundColor Cyan
Write-Host "║  Waiting for new build to go live...                         ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

Write-Host "Started: $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Gray
Write-Host "Checking every $checkInterval seconds for up to $maxWaitMinutes minutes`n" -ForegroundColor Gray

$attempt = 0
$deployed = $false

while (((Get-Date) - $startTime).TotalMinutes -lt $maxWaitMinutes -and -not $deployed) {
    $attempt++
    $elapsed = [Math]::Round(((Get-Date) - $startTime).TotalMinutes, 1)
    
    Write-Host "[$attempt] Check at $(Get-Date -Format 'HH:mm:ss') (${elapsed}min elapsed)" -ForegroundColor Yellow
    
    # Test 1: Can we reach the Next.js API proxy?
    try {
        $apiTest = Invoke-RestMethod -Uri "https://studio--tbsignalstream.us-central1.hosted.app/api/bot/health" -Method Get -TimeoutSec 10 -ErrorAction Stop
        Write-Host "   ✅ API proxy working! Backend health:" -ForegroundColor Green
        Write-Host "      Status: $($apiTest.status)" -ForegroundColor White
        Write-Host "      Service: $($apiTest.service)" -ForegroundColor White
        $deployed = $true
    } catch {
        if ($_.Exception.Response.StatusCode.value__ -eq 404) {
            Write-Host "   ⏳ Still deploying... (API returns 404)" -ForegroundColor Gray
        } else {
            Write-Host "   ⚠️  Error: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
    
    if (-not $deployed) {
        if ($attempt -lt ([Math]::Floor($maxWaitMinutes * 60 / $checkInterval))) {
            Write-Host "   💤 Waiting $checkInterval seconds...`n" -ForegroundColor Gray
            Start-Sleep -Seconds $checkInterval
        }
    }
}

Write-Host "`n" + ("═" * 64) -ForegroundColor Gray

if ($deployed) {
    Write-Host "`n🎉 DEPLOYMENT SUCCESSFUL!" -ForegroundColor Green -BackgroundColor Black
    Write-Host "`n✅ Next Steps:" -ForegroundColor Cyan
    Write-Host "   1. Open: https://studio--tbsignalstream.us-central1.hosted.app/" -ForegroundColor White
    Write-Host "   2. Hard refresh: Ctrl + Shift + R" -ForegroundColor White
    Write-Host "   3. Login and test the bot" -ForegroundColor White
    Write-Host "   4. The error should be GONE!" -ForegroundColor Green
    Write-Host "`n💡 If you still see the error:" -ForegroundColor Yellow
    Write-Host "   • Try Incognito mode (Ctrl + Shift + N)" -ForegroundColor Gray
    Write-Host "   • Clear ALL browser data (not just cached images)" -ForegroundColor Gray
    Write-Host "   • Try a different browser" -ForegroundColor Gray
} else {
    Write-Host "`n⏰ Deployment taking longer than expected ($maxWaitMinutes min)" -ForegroundColor Yellow
    Write-Host "`nPossible reasons:" -ForegroundColor White
    Write-Host "   • Firebase build queue is busy" -ForegroundColor Gray
    Write-Host "   • Build is failing (check Firebase Console)" -ForegroundColor Gray
    Write-Host "   • Larger build taking more time" -ForegroundColor Gray
    Write-Host "`n📊 Check Firebase Console:" -ForegroundColor Cyan
    Write-Host "   https://console.firebase.google.com/project/tbsignalstream/apphosting" -ForegroundColor White
    Write-Host "`n💡 You can:" -ForegroundColor Yellow
    Write-Host "   • Wait another 5-10 minutes" -ForegroundColor Gray
    Write-Host "   • Check build logs in Firebase Console" -ForegroundColor Gray
    Write-Host "   • Run this script again: .\monitor_deployment.ps1" -ForegroundColor Gray
}

Write-Host "`n" + ("═" * 64) -ForegroundColor Gray
Write-Host ""
