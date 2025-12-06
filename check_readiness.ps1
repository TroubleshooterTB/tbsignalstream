# 🔍 Live Trading Readiness Validator
# Run this script to check if system is ready for live trading

Write-Host "`n🚀 LIVE TRADING READINESS CHECK" -ForegroundColor Cyan
Write-Host "================================`n" -ForegroundColor Cyan

$allChecksPass = $true

# Check 1: Cloud Run Service Status
Write-Host "✓ Checking Cloud Run service..." -ForegroundColor Yellow
try {
    $cloudRunStatus = gcloud run services describe trading-bot-service --region asia-south1 --format="value(status.conditions[0].status)" 2>$null
    if ($cloudRunStatus -eq "True") {
        Write-Host "  ✅ Cloud Run service is running" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Cloud Run service is NOT ready" -ForegroundColor Red
        $allChecksPass = $false
    }
} catch {
    Write-Host "  ❌ Failed to check Cloud Run status" -ForegroundColor Red
    $allChecksPass = $false
}

# Check 2: Frontend Deployment Status
Write-Host "`n✓ Checking Firebase App Hosting..." -ForegroundColor Yellow
try {
    $appHostingStatus = firebase apphosting:backends:list --json 2>$null | ConvertFrom-Json
    if ($appHostingStatus) {
        Write-Host "  ✅ App Hosting backend deployed" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Could not verify App Hosting status" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠️  Firebase CLI check skipped" -ForegroundColor Yellow
}

# Check 3: Recent Backend Logs Check
Write-Host "`n✓ Checking recent backend activity..." -ForegroundColor Yellow
try {
    $recentLogs = gcloud run services logs read trading-bot-service --region asia-south1 --limit 10 2>$null
    if ($recentLogs) {
        $errorCount = ($recentLogs | Select-String -Pattern "ERROR|CRITICAL|429|403" -CaseSensitive).Count
        
        if ($errorCount -eq 0) {
            Write-Host "  ✅ No critical errors in recent logs" -ForegroundColor Green
        } elseif ($errorCount -lt 3) {
            Write-Host "  ⚠️  Found $errorCount errors in recent logs (review recommended)" -ForegroundColor Yellow
        } else {
            Write-Host "  ❌ Found $errorCount errors in recent logs (MUST FIX)" -ForegroundColor Red
            $allChecksPass = $false
        }
        
        # Check for WebSocket errors specifically
        $wsErrors = ($recentLogs | Select-String -Pattern "429|Connection Limit").Count
        if ($wsErrors -gt 0) {
            Write-Host "  ❌ WebSocket connection errors detected (429)" -ForegroundColor Red
            Write-Host "     ACTION: Stop bot, wait 5 min, reconnect Angel One" -ForegroundColor Yellow
            $allChecksPass = $false
        }
        
        # Check for API authentication errors
        $authErrors = ($recentLogs | Select-String -Pattern "403|Forbidden").Count
        if ($authErrors -gt 0) {
            Write-Host "  ❌ API authentication errors detected (403)" -ForegroundColor Red
            Write-Host "     ACTION: Reconnect Angel One to refresh tokens" -ForegroundColor Yellow
            $allChecksPass = $false
        }
    } else {
        Write-Host "  ⚠️  No recent logs found (bot may not be running)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ❌ Failed to check logs" -ForegroundColor Red
    $allChecksPass = $false
}

# Check 4: Environment Variables
Write-Host "`n✓ Checking environment configuration..." -ForegroundColor Yellow
try {
    $envVars = gcloud run services describe trading-bot-service --region asia-south1 --format="value(spec.template.spec.containers[0].env[].name)" 2>$null
    
    $requiredVars = @(
        "ANGELONE_TRADING_API_KEY",
        "FIREBASE_PROJECT_ID",
        "FIREBASE_CLIENT_EMAIL"
    )
    
    $missingVars = @()
    foreach ($var in $requiredVars) {
        if ($envVars -notcontains $var) {
            $missingVars += $var
        }
    }
    
    if ($missingVars.Count -eq 0) {
        Write-Host "  ✅ All required environment variables configured" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Missing environment variables: $($missingVars -join ', ')" -ForegroundColor Red
        $allChecksPass = $false
    }
} catch {
    Write-Host "  ⚠️  Could not verify environment variables" -ForegroundColor Yellow
}

# Check 5: File Structure
Write-Host "`n✓ Checking critical files..." -ForegroundColor Yellow
$criticalFiles = @(
    "tbsignalstream_backup\trading_bot_service\main.py",
    "tbsignalstream_backup\trading_bot_service\realtime_bot_engine.py",
    "tbsignalstream_backup\src\lib\trading-api.ts",
    "tbsignalstream_backup\apphosting.yaml"
)

$missingFiles = @()
foreach ($file in $criticalFiles) {
    $fullPath = Join-Path "d:\Tushar 2.0\tbsignalstream_backup" $file
    if (-not (Test-Path $fullPath)) {
        $missingFiles += $file
    }
}

if ($missingFiles.Count -eq 0) {
    Write-Host "  ✅ All critical files present" -ForegroundColor Green
} else {
    Write-Host "  ❌ Missing files: $($missingFiles -join ', ')" -ForegroundColor Red
    $allChecksPass = $false
}

# Check 6: Git Status
Write-Host "`n✓ Checking git status..." -ForegroundColor Yellow
try {
    Set-Location "d:\Tushar 2.0\tbsignalstream_backup\tbsignalstream_backup"
    $gitStatus = git status --porcelain 2>$null
    
    if ($gitStatus) {
        Write-Host "  ⚠️  Uncommitted changes detected" -ForegroundColor Yellow
        Write-Host "     Files changed: $(($gitStatus | Measure-Object).Count)" -ForegroundColor Yellow
        Write-Host "     Recommend: Commit and deploy latest changes" -ForegroundColor Yellow
    } else {
        Write-Host "  ✅ Working directory clean" -ForegroundColor Green
    }
} catch {
    Write-Host "  ⚠️  Could not check git status" -ForegroundColor Yellow
}

# Summary
Write-Host "`n================================" -ForegroundColor Cyan
Write-Host "READINESS SUMMARY" -ForegroundColor Cyan
Write-Host "================================`n" -ForegroundColor Cyan

if ($allChecksPass) {
    Write-Host "✅ SYSTEM READY FOR TESTING" -ForegroundColor Green
    Write-Host "`nNext Steps:" -ForegroundColor Cyan
    Write-Host "1. Ensure Angel One credentials are fresh (< 24 hours)" -ForegroundColor White
    Write-Host "2. Start bot in PAPER mode" -ForegroundColor White
    Write-Host "3. Monitor for 30+ minutes" -ForegroundColor White
    Write-Host "4. Review LIVE_TRADING_READINESS.md checklist" -ForegroundColor White
    Write-Host "5. Wait for Monday market open (9:15 AM)" -ForegroundColor White
} else {
    Write-Host "❌ ISSUES DETECTED - NOT READY FOR LIVE TRADING" -ForegroundColor Red
    Write-Host "`nRequired Actions:" -ForegroundColor Cyan
    Write-Host "1. Fix all ❌ items listed above" -ForegroundColor White
    Write-Host "2. Run this script again to verify fixes" -ForegroundColor White
    Write-Host "3. Review LIVE_TRADING_READINESS.md for detailed steps" -ForegroundColor White
}

Write-Host "`n================================`n" -ForegroundColor Cyan

# Detailed Logs Section
Write-Host "📋 DETAILED LOGS (Last 20 entries)" -ForegroundColor Cyan
Write-Host "================================`n" -ForegroundColor Cyan

try {
    $detailedLogs = gcloud run services logs read trading-bot-service --region asia-south1 --limit 20 2>$null
    if ($detailedLogs) {
        $detailedLogs | ForEach-Object {
            if ($_ -match "ERROR|CRITICAL|429|403") {
                Write-Host $_ -ForegroundColor Red
            } elseif ($_ -match "WARNING|WARN") {
                Write-Host $_ -ForegroundColor Yellow
            } else {
                Write-Host $_ -ForegroundColor Gray
            }
        }
    } else {
        Write-Host "No recent logs available" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Could not fetch detailed logs" -ForegroundColor Red
}

Write-Host "`n✨ Check complete!`n" -ForegroundColor Cyan
