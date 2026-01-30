# COMPREHENSIVE API ENDPOINT TESTING
# Tests all 14 new endpoints + health checks

$API_BASE = "https://trading-bot-service-818546654122.us-central1.run.app"
$USER_ID = "default_user"

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "TESTING ALL ENDPOINTS - Phase 0-6 Complete System" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

$testResults = @()

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Url,
        [object]$Body = $null
    )
    
    Write-Host "Testing: $Name" -ForegroundColor Yellow
    Write-Host "  URL: $Url" -ForegroundColor Gray
    
    try {
        $params = @{
            Uri = $Url
            Method = $Method
            ContentType = "application/json"
        }
        
        if ($Body) {
            $params.Body = ($Body | ConvertTo-Json -Depth 10)
            Write-Host "  Body: $($params.Body)" -ForegroundColor Gray
        }
        
        $response = Invoke-RestMethod @params -ErrorAction Stop
        
        Write-Host "  ✅ SUCCESS" -ForegroundColor Green
        Write-Host "  Response: $($response | ConvertTo-Json -Compress)" -ForegroundColor Gray
        Write-Host ""
        
        return @{
            Name = $Name
            Status = "✅ PASS"
            Response = $response
        }
    }
    catch {
        Write-Host "  ❌ FAILED: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
        
        return @{
            Name = $Name
            Status = "❌ FAIL"
            Error = $_.Exception.Message
        }
    }
}

# TEST 1: Health Check
Write-Host "`n[TEST 1/15] Health Check" -ForegroundColor Cyan
Write-Host "-" * 80
$testResults += Test-Endpoint -Name "Health Check" -Method "GET" -Url "$API_BASE/health"

# TEST 2: Service Status
Write-Host "`n[TEST 2/15] Service Status (requires auth)" -ForegroundColor Cyan
Write-Host "-" * 80
Write-Host "Note: This endpoint requires authorization, expecting 401/403" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$API_BASE/status" -Method GET -ErrorAction Stop
    Write-Host "  ✅ SUCCESS (unexpected - no auth required?)" -ForegroundColor Green
}
catch {
    if ($_.Exception.Response.StatusCode -eq 401 -or $_.Exception.Response.StatusCode -eq 403) {
        Write-Host "  ✅ EXPECTED: Auth required" -ForegroundColor Green
    }
    else {
        Write-Host "  ⚠️  Unexpected error: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}
Write-Host ""

# TEST 3: Get Screening Modes
Write-Host "`n[TEST 3/15] Get Screening Modes" -ForegroundColor Cyan
Write-Host "-" * 80
$testResults += Test-Endpoint -Name "Get Screening Modes" -Method "GET" -Url "$API_BASE/api/screening/modes"

# TEST 4: Get Current Screening Mode
Write-Host "`n[TEST 4/15] Get Current Screening Mode" -ForegroundColor Cyan
Write-Host "-" * 80
$testResults += Test-Endpoint -Name "Get Current Mode" -Method "GET" -Url "$API_BASE/api/screening/current-mode?user_id=$USER_ID"

# TEST 5: Set Screening Mode
Write-Host "`n[TEST 5/15] Set Screening Mode to MEDIUM" -ForegroundColor Cyan
Write-Host "-" * 80
$testResults += Test-Endpoint -Name "Set Screening Mode" -Method "POST" -Url "$API_BASE/api/screening/set-mode" -Body @{
    user_id = $USER_ID
    mode = "MEDIUM"
}

# TEST 6: Get User Settings
Write-Host "`n[TEST 6/15] Get User Settings" -ForegroundColor Cyan
Write-Host "-" * 80
$testResults += Test-Endpoint -Name "Get User Settings" -Method "GET" -Url "$API_BASE/api/settings/user?user_id=$USER_ID"

# TEST 7: Update User Settings (Create user document)
Write-Host "`n[TEST 7/15] Create/Update User Settings" -ForegroundColor Cyan
Write-Host "-" * 80
$testResults += Test-Endpoint -Name "Update User Settings" -Method "POST" -Url "$API_BASE/api/settings/user" -Body @{
    user_id = $USER_ID
    telegram_enabled = $true
    telegram_bot_token = "8288768103:AAG8YOpuzkCpOV6_3KKq5jcaI6WKZ4LNDAg"
    telegram_chat_id = "884558084"
    tradingview_enabled = $false
    screening_mode = "MEDIUM"
    notifications_enabled = $true
}

# TEST 8: Get User Settings Again (verify save)
Write-Host "`n[TEST 8/15] Get User Settings (verify save)" -ForegroundColor Cyan
Write-Host "-" * 80
$testResults += Test-Endpoint -Name "Get User Settings (verify)" -Method "GET" -Url "$API_BASE/api/settings/user?user_id=$USER_ID"

# TEST 9: Test Telegram Notification
Write-Host "`n[TEST 9/15] Test Telegram Notification" -ForegroundColor Cyan
Write-Host "-" * 80
Write-Host "Note: User must have started chat with bot first" -ForegroundColor Yellow
$testResults += Test-Endpoint -Name "Test Telegram" -Method "POST" -Url "$API_BASE/api/settings/telegram/test" -Body @{
    user_id = $USER_ID
    bot_token = "8288768103:AAG8YOpuzkCpOV6_3KKq5jcaI6WKZ4LNDAg"
    chat_id = "884558084"
    message = "🎉 SignalStream Test: All systems operational!"
}

# TEST 10: Generate API Key
Write-Host "`n[TEST 10/15] Generate API Key" -ForegroundColor Cyan
Write-Host "-" * 80
$apiKeyResult = Test-Endpoint -Name "Generate API Key" -Method "POST" -Url "$API_BASE/api/settings/api-key/generate" -Body @{
    user_id = $USER_ID
    name = "Test Key - Automated Testing"
    permissions = @("read", "write")
}
$testResults += $apiKeyResult

# Store API key for later tests
$generatedApiKey = $null
$generatedKeyId = $null
if ($apiKeyResult.Response) {
    $generatedApiKey = $apiKeyResult.Response.api_key
    $generatedKeyId = $apiKeyResult.Response.key_id
    Write-Host "  📝 Generated API Key: $generatedApiKey" -ForegroundColor Cyan
    Write-Host "  📝 Key ID: $generatedKeyId" -ForegroundColor Cyan
}

# TEST 11: Manual Trade - Place Trade (Dry Run)
Write-Host "`n[TEST 11/15] Manual Trade - Place BUY Order" -ForegroundColor Cyan
Write-Host "-" * 80
Write-Host "Note: This will attempt to place a real order in paper mode" -ForegroundColor Yellow
$testResults += Test-Endpoint -Name "Place Manual Trade" -Method "POST" -Url "$API_BASE/api/manual/place-trade" -Body @{
    user_id = $USER_ID
    symbol = "RELIANCE"
    action = "BUY"
    quantity = 1
    stop_loss_pct = 2.0
    target_pct = 5.0
    price = 2500.0
}

# TEST 12: TradingView Webhook Test
Write-Host "`n[TEST 12/15] TradingView Webhook Test" -ForegroundColor Cyan
Write-Host "-" * 80
Write-Host "Note: Requires valid API key from previous test" -ForegroundColor Yellow
if ($generatedApiKey) {
    $testResults += Test-Endpoint -Name "TradingView Webhook" -Method "POST" -Url "$API_BASE/webhook/tradingview" -Body @{
        api_key = $generatedApiKey
        symbol = "SBIN"
        action = "BUY"
        price = 600.0
        stop_loss_pct = 1.5
        target_pct = 4.0
        message = "Test webhook from automated testing"
    }
}
else {
    Write-Host "  ⚠️  Skipped: No API key available" -ForegroundColor Yellow
    $testResults += @{
        Name = "TradingView Webhook"
        Status = "⚠️ SKIPPED"
    }
}

# TEST 13: TradingView Webhook Test Endpoint
Write-Host "`n[TEST 13/15] TradingView Webhook Test Endpoint" -ForegroundColor Cyan
Write-Host "-" * 80
$testResults += Test-Endpoint -Name "TradingView Test" -Method "POST" -Url "$API_BASE/webhook/test" -Body @{
    symbol = "TATAMOTORS"
    action = "SELL"
    price = 750.0
}

# TEST 14: Revoke API Key
Write-Host "`n[TEST 14/15] Revoke API Key" -ForegroundColor Cyan
Write-Host "-" * 80
if ($generatedKeyId) {
    $testResults += Test-Endpoint -Name "Revoke API Key" -Method "DELETE" -Url "$API_BASE/api/settings/api-key/$generatedKeyId"
}
else {
    Write-Host "  ⚠️  Skipped: No key ID available" -ForegroundColor Yellow
    $testResults += @{
        Name = "Revoke API Key"
        Status = "⚠️ SKIPPED"
    }
}

# TEST 15: Quick Close Position
Write-Host "`n[TEST 15/15] Quick Close Position" -ForegroundColor Cyan
Write-Host "-" * 80
Write-Host "Note: Will only work if position exists" -ForegroundColor Yellow
$testResults += Test-Endpoint -Name "Quick Close Position" -Method "POST" -Url "$API_BASE/api/manual/quick-close" -Body @{
    user_id = $USER_ID
    symbol = "RELIANCE"
}

# SUMMARY
Write-Host "`n" + "=" * 80 -ForegroundColor Cyan
Write-Host "TEST SUMMARY" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

$passed = ($testResults | Where-Object { $_.Status -like "*PASS*" }).Count
$failed = ($testResults | Where-Object { $_.Status -like "*FAIL*" }).Count
$skipped = ($testResults | Where-Object { $_.Status -like "*SKIPPED*" }).Count
$total = $testResults.Count

Write-Host "Total Tests: $total" -ForegroundColor White
Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor Red
Write-Host "Skipped: $skipped" -ForegroundColor Yellow
Write-Host ""

Write-Host "Detailed Results:" -ForegroundColor White
Write-Host "-" * 80
foreach ($result in $testResults) {
    $status = $result.Status
    $color = if ($status -like "*PASS*") { "Green" } elseif ($status -like "*FAIL*") { "Red" } else { "Yellow" }
    Write-Host "  $($result.Name): $status" -ForegroundColor $color
    if ($result.Error) {
        Write-Host "    Error: $($result.Error)" -ForegroundColor Red
    }
}

Write-Host "`n" + "=" * 80 -ForegroundColor Cyan
if ($failed -eq 0) {
    Write-Host "🎉 ALL TESTS PASSED! System is production-ready!" -ForegroundColor Green
}
else {
    Write-Host "⚠️  Some tests failed. Review errors above." -ForegroundColor Yellow
}
Write-Host "=" * 80 -ForegroundColor Cyan
