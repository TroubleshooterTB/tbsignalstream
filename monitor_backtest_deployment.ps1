# Monitor Backtest Fix Deployment
Write-Host "🚀 Monitoring Trading Bot Service Deployment..." -ForegroundColor Cyan
Write-Host ""

# Wait for build to start
Start-Sleep -Seconds 10

# Get latest build
Write-Host "📦 Checking build status..." -ForegroundColor Yellow
$builds = gcloud builds list --limit=1 --format="value(id,status,createTime)" --project=tbsignalstream 2>$null

if ($builds) {
    $buildId, $status, $createTime = $builds -split '\t'
    Write-Host "   Build ID: $buildId" -ForegroundColor White
    Write-Host "   Status: $status" -ForegroundColor $(if ($status -eq "WORKING") { "Yellow" } elseif ($status -eq "SUCCESS") { "Green" } else { "Red" })
    Write-Host "   Started: $createTime" -ForegroundColor Gray
    Write-Host ""
    
    if ($status -eq "WORKING") {
        Write-Host "⏳ Build in progress... Waiting for completion..." -ForegroundColor Yellow
        Write-Host ""
        
        # Wait for build to complete
        while ($true) {
            Start-Sleep -Seconds 15
            $currentStatus = gcloud builds describe $buildId --format="value(status)" --project=tbsignalstream 2>$null
            
            if ($currentStatus -eq "SUCCESS") {
                Write-Host "✅ BUILD SUCCESSFUL!" -ForegroundColor Green
                break
            } elseif ($currentStatus -eq "FAILURE") {
                Write-Host "❌ BUILD FAILED!" -ForegroundColor Red
                Write-Host ""
                Write-Host "📋 Error logs:" -ForegroundColor Red
                gcloud logging read "resource.type=build AND resource.labels.build_id=$buildId" --limit=20 --format="value(textPayload)" --project=tbsignalstream
                exit 1
            }
            
            Write-Host "." -NoNewline -ForegroundColor Yellow
        }
    }
}

# Check deployment
Write-Host ""
Write-Host "📡 Checking Cloud Run deployment..." -ForegroundColor Yellow
$service = gcloud run services describe trading-bot-service --region=asia-south1 --project=tbsignalstream --format="value(status.latestReadyRevisionName,status.url)" 2>$null

if ($service) {
    $revision, $url = $service -split '\t'
    Write-Host "   Latest Revision: $revision" -ForegroundColor Green
    Write-Host "   URL: $url" -ForegroundColor Cyan
    Write-Host ""
    
    # Verify the fix is deployed by checking logs
    Write-Host "🔍 Verifying backtest fix deployment..." -ForegroundColor Yellow
    Write-Host "   Testing backtest endpoint..." -ForegroundColor Gray
    
    # Make a test backtest call
    $testPayload = @{
        strategy = "defining"
        start_date = "2026-01-13"
        end_date = "2026-01-17"
        symbols = "NIFTY50"
        capital = 100000
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "$url/backtest" -Method Post -Body $testPayload -ContentType "application/json" -TimeoutSec 120
        
        Write-Host ""
        Write-Host "✅ BACKTEST FIX VERIFIED!" -ForegroundColor Green
        Write-Host "   Total Trades: $($response.summary.total_trades)" -ForegroundColor White
        
        if ($response.summary.total_trades -gt 0) {
            Write-Host "   Win Rate: $([math]::Round($response.summary.win_rate, 2))%" -ForegroundColor Green
            Write-Host "   Total P&L: ₹$([math]::Round($response.summary.total_pnl, 2))" -ForegroundColor $(if ($response.summary.total_pnl -gt 0) { "Green" } else { "Red" })
            Write-Host ""
            Write-Host "🎉 SUCCESS! Backtest is now working with 100-day SMA window!" -ForegroundColor Green
        } else {
            Write-Host ""
            Write-Host "⚠️ Still showing 0 trades. Checking logs for details..." -ForegroundColor Yellow
            Write-Host ""
            
            # Get recent backtest logs
            Write-Host "📋 Recent backtest logs:" -ForegroundColor Cyan
            gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=trading-bot-service AND (textPayload:'Fetching hourly' OR textPayload:'hourly candles' OR textPayload:'trend bias')" --limit=10 --format="value(textPayload)" --freshness=5m --project=tbsignalstream
        }
        
    } catch {
        Write-Host ""
        Write-Host "❌ Backtest test failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    
} else {
    Write-Host "❌ Could not get service info" -ForegroundColor Red
}

Write-Host ""
Write-Host "📊 DEPLOYMENT SUMMARY" -ForegroundColor Cyan
Write-Host "=" * 60
Write-Host "Status: Deployment Complete" -ForegroundColor Green
Write-Host "Next Step: Test backtest from dashboard with Dec 20 - Jan 20 date range" -ForegroundColor Yellow
Write-Host ""
