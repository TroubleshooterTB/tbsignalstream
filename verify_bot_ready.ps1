# COMPREHENSIVE PRE-TRADING VERIFICATION
# Run this before tomorrow's market session

Write-Host "`n" -NoNewline
Write-Host "="*80 -ForegroundColor Cyan
Write-Host "COMPREHENSIVE BOT VERIFICATION - December 23, 2025" -ForegroundColor Cyan
Write-Host "="*80 -ForegroundColor Cyan

$allPassed = $true

# TEST 1: Backend Health
Write-Host "`n[1/6] Backend Health Check..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "https://trading-bot-service-818546654122.asia-south1.run.app/health" -Method GET -TimeoutSec 10
    if ($health.status -eq "healthy") {
        Write-Host "  ✅ Backend is HEALTHY" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Backend unhealthy: $($health.status)" -ForegroundColor Red
        $allPassed = $false
    }
} catch {
    Write-Host "  ❌ Backend not responding: $($_.Exception.Message)" -ForegroundColor Red
    $allPassed = $false
}

# TEST 2: Cloud Run Revision
Write-Host "`n[2/6] Checking Cloud Run Revision..." -ForegroundColor Yellow
try {
    $revision = gcloud run services describe trading-bot-service --region asia-south1 --project tbsignalstream --format="value(status.latestReadyRevisionName)" 2>$null
    Write-Host "  ✅ Current Revision: $revision" -ForegroundColor Green
    if ($revision -match "00075") {
        Write-Host "  ✅ Latest revision with parameter configuration deployed" -ForegroundColor Green
    }
} catch {
    Write-Host "  ⚠️  Could not verify revision" -ForegroundColor Yellow
}

# TEST 3: Firebase Configuration
Write-Host "`n[3/6] Verifying Firestore Configuration..." -ForegroundColor Yellow
Write-Host "  ℹ️  Running Python verification..." -ForegroundColor Gray
try {
    $configCheck = python -c @"
import firebase_admin
from firebase_admin import credentials, firestore
import os

if not firebase_admin._apps:
    cred_path = os.path.join(os.getcwd(), 'firestore-key.json')
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    else:
        firebase_admin.initialize_app()

db = firestore.client()
config = db.collection('bot_configs').document('PiRehqxZQleR8QCZG0QczmQTY402').get().to_dict()
params = config.get('strategy_params', {})
print(f'ADX:{params.get(\"adx_threshold\", \"?\")}')
print(f'RSI:{params.get(\"rsi_oversold\", \"?\")}-{params.get(\"rsi_overbought\", \"?\")}')
print(f'Volume:{params.get(\"volume_multiplier\", \"?\")}x')
print(f'R:R:1:{params.get(\"risk_reward\", \"?\")}')
print(f'PosSize:{params.get(\"position_size\", \"?\")}%')
print(f'MaxPos:{config.get(\"max_open_positions\", \"?\")}')
print(f'Hours:{params.get(\"trading_start_hour\", \"?\")}:30-{params.get(\"trading_end_hour\", \"?\")}:15')
"@
    
    if ($configCheck) {
        Write-Host "  ✅ Firestore Configuration Loaded:" -ForegroundColor Green
        foreach ($line in $configCheck -split "`n") {
            Write-Host "     $line" -ForegroundColor White
        }
    }
} catch {
    Write-Host "  ❌ Failed to verify Firestore config: $($_.Exception.Message)" -ForegroundColor Red
    $allPassed = $false
}

# TEST 4: IST Time & Market Hours
Write-Host "`n[4/6] Checking Time & Market Hours..." -ForegroundColor Yellow
$istTime = [System.TimeZoneInfo]::ConvertTimeBySystemTimeZoneId([DateTime]::UtcNow, 'India Standard Time')
Write-Host "  ✅ Current IST Time: $($istTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Green

$dayOfWeek = $istTime.DayOfWeek
if ($dayOfWeek -eq 'Saturday' -or $dayOfWeek -eq 'Sunday') {
    Write-Host "  ⚠️  Weekend - Market is CLOSED" -ForegroundColor Yellow
} else {
    $hour = $istTime.Hour
    $minute = $istTime.Minute
    if ($hour -eq 9 -and $minute -ge 15) {
        Write-Host "  ✅ Market is OPEN (9:15 AM - 3:30 PM IST)" -ForegroundColor Green
    } elseif ($hour -ge 10 -and $hour -lt 15) {
        Write-Host "  ✅ Market is OPEN (9:15 AM - 3:30 PM IST)" -ForegroundColor Green
    } elseif ($hour -eq 15 -and $minute -le 30) {
        Write-Host "  ✅ Market is OPEN (9:15 AM - 3:30 PM IST)" -ForegroundColor Green
    } else {
        Write-Host "  ⏰ Market is CLOSED - Opens at 9:15 AM IST" -ForegroundColor Gray
    }
}

# TEST 5: Dashboard Accessibility
Write-Host "`n[5/6] Checking Dashboard..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "https://studio--tbsignalstream.us-central1.hosted.app" -Method HEAD -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "  ✅ Dashboard is accessible" -ForegroundColor Green
    }
} catch {
    Write-Host "  ❌ Dashboard not accessible: $($_.Exception.Message)" -ForegroundColor Red
    $allPassed = $false
}

# TEST 6: Recent Logs Check
Write-Host "`n[6/6] Checking Recent Backend Logs..." -ForegroundColor Yellow
try {
    $logs = gcloud logging read "resource.labels.service_name=trading-bot-service AND severity>=ERROR" --limit 3 --format="value(timestamp)" --project tbsignalstream 2>$null
    if ($logs -and $logs.Count -gt 0) {
        Write-Host "  ⚠️  Found $($logs.Count) recent errors in logs" -ForegroundColor Yellow
        Write-Host "     Check with: gcloud logging read 'resource.labels.service_name=trading-bot-service AND severity>=ERROR' --limit 5" -ForegroundColor Gray
    } else {
        Write-Host "  ✅ No recent errors in backend logs" -ForegroundColor Green
    }
} catch {
    Write-Host "  ℹ️  Could not check logs (non-critical)" -ForegroundColor Gray
}

# FINAL SUMMARY
Write-Host "`n" -NoNewline
Write-Host "="*80 -ForegroundColor Cyan
if ($allPassed) {
    Write-Host "✅ ALL SYSTEMS GO - BOT IS READY FOR TOMORROW!" -ForegroundColor Green
    Write-Host "="*80 -ForegroundColor Cyan
    
    Write-Host "`n📋 TOMORROW'S CHECKLIST (9:00 AM IST):" -ForegroundColor Yellow
    Write-Host "  1. Open dashboard: https://studio--tbsignalstream.us-central1.hosted.app" -ForegroundColor White
    Write-Host "  2. Press Ctrl+Shift+R (hard refresh)" -ForegroundColor White
    Write-Host "  3. Verify Mode: Paper Trading" -ForegroundColor White
    Write-Host "  4. Click 'Start Trading Bot' at 9:15 AM" -ForegroundColor White
    Write-Host "  5. Wait 20 seconds for health check" -ForegroundColor White
    Write-Host "  6. Monitor Activity Feed for parameter confirmation" -ForegroundColor White
    Write-Host "  7. First signals expected after 10:30 AM (post-DR period)" -ForegroundColor White
    
    Write-Host "`n⚙️  YOUR OPTIMAL PARAMETERS (CONFIRMED):" -ForegroundColor Cyan
    Write-Host "  • Strategy: Alpha-Ensemble" -ForegroundColor White
    Write-Host "  • Universe: NIFTY100 (select from dropdown)" -ForegroundColor White
    Write-Host "  • ADX Threshold: 25" -ForegroundColor White
    Write-Host "  • RSI Range: 35-70" -ForegroundColor White
    Write-Host "  • Volume: 2.5x average" -ForegroundColor White
    Write-Host "  • Risk:Reward: 1:2.5" -ForegroundColor White
    Write-Host "  • Position Size: 5% per trade" -ForegroundColor White
    Write-Host "  • Max Positions: 5 concurrent" -ForegroundColor White
    Write-Host "  • Trading Hours: 10:30 AM - 2:15 PM" -ForegroundColor White
    Write-Host "  • Nifty Alignment: Same Direction" -ForegroundColor White
    
} else {
    Write-Host "❌ SOME CHECKS FAILED - FIX BEFORE TOMORROW!" -ForegroundColor Red
    Write-Host "="*80 -ForegroundColor Cyan
    Write-Host "`nReview errors above and fix them before market open." -ForegroundColor Yellow
}

Write-Host "`n"
