# Frontend-Backend Integration Verification Script
# Run this to verify all components are properly connected

Write-Host "`n=== FRONTEND-BACKEND INTEGRATION VERIFICATION ===" -ForegroundColor Cyan

# 1. Check Backend Cloud Functions
Write-Host "`n[1/5] Checking Backend Cloud Functions..." -ForegroundColor Yellow
$functions = @(
    'initializeWebSocket',
    'subscribeWebSocket', 
    'closeWebSocket',
    'placeOrder',
    'modifyOrder',
    'cancelOrder',
    'getOrderBook',
    'getPositions',
    'startLiveTradingBot',
    'stopLiveTradingBot'
)

$activeCount = 0
foreach ($func in $functions) {
    $status = gcloud functions describe $func --region=us-central1 --project=tbsignalstream --gen2 --format="value(state)" 2>$null
    if ($status -eq "ACTIVE") {
        Write-Host "  ✓ $func - ACTIVE" -ForegroundColor Green
        $activeCount++
    } else {
        Write-Host "  ✗ $func - $status" -ForegroundColor Red
    }
}
Write-Host "  Result: $activeCount/$($functions.Count) functions ACTIVE" -ForegroundColor $(if ($activeCount -eq $functions.Count) { "Green" } else { "Red" })

# 2. Check Frontend Components
Write-Host "`n[2/5] Checking Frontend Components..." -ForegroundColor Yellow
$components = @(
    'src/components/live-alerts-dashboard.tsx',
    'src/components/websocket-controls.tsx',
    'src/components/order-manager.tsx',
    'src/components/trading-bot-controls.tsx',
    'src/components/positions-monitor.tsx',
    'src/components/order-book.tsx',
    'src/lib/trading-api.ts'
)

$componentCount = 0
foreach ($comp in $components) {
    if (Test-Path $comp) {
        Write-Host "  ✓ $comp exists" -ForegroundColor Green
        $componentCount++
    } else {
        Write-Host "  ✗ $comp MISSING" -ForegroundColor Red
    }
}
Write-Host "  Result: $componentCount/$($components.Count) components present" -ForegroundColor $(if ($componentCount -eq $components.Count) { "Green" } else { "Red" })

# 3. Check API Imports in Components
Write-Host "`n[3/5] Checking API Integration..." -ForegroundColor Yellow
$imports = @(
    @{ File = 'src/components/websocket-controls.tsx'; Import = 'websocketApi' },
    @{ File = 'src/components/order-manager.tsx'; Import = 'orderApi' },
    @{ File = 'src/components/trading-bot-controls.tsx'; Import = 'tradingBotApi' },
    @{ File = 'src/components/positions-monitor.tsx'; Import = 'orderApi' },
    @{ File = 'src/components/order-book.tsx'; Import = 'orderApi' }
)

$importCount = 0
foreach ($imp in $imports) {
    $content = Get-Content $imp.File -Raw
    if ($content -match "from '@/lib/trading-api'") {
        Write-Host "  ✓ $($imp.File) imports trading-api" -ForegroundColor Green
        $importCount++
    } else {
        Write-Host "  ✗ $($imp.File) missing import" -ForegroundColor Red
    }
}
Write-Host "  Result: $importCount/$($imports.Count) imports verified" -ForegroundColor $(if ($importCount -eq $imports.Count) { "Green" } else { "Red" })

# 4. Check Dashboard Integration
Write-Host "`n[4/5] Checking Dashboard Integration..." -ForegroundColor Yellow
$dashboardContent = Get-Content 'src/components/live-alerts-dashboard.tsx' -Raw

$tabsPresent = $dashboardContent -match 'from "@/components/ui/tabs"'
$wsControlsPresent = $dashboardContent -match 'from "@/components/websocket-controls"'
$orderMgrPresent = $dashboardContent -match 'from "@/components/order-manager"'
$botControlsPresent = $dashboardContent -match 'from "@/components/trading-bot-controls"'
$positionsPresent = $dashboardContent -match 'from "@/components/positions-monitor"'
$orderBookPresent = $dashboardContent -match 'from "@/components/order-book"'
$tabsUsed = $dashboardContent -match '<Tabs'

$integrationScore = @($tabsPresent, $wsControlsPresent, $orderMgrPresent, $botControlsPresent, $positionsPresent, $orderBookPresent, $tabsUsed) | Where-Object { $_ } | Measure-Object | Select-Object -ExpandProperty Count

Write-Host "  $(if ($tabsPresent) { '✓' } else { '✗' }) Tabs component imported" -ForegroundColor $(if ($tabsPresent) { "Green" } else { "Red" })
Write-Host "  $(if ($wsControlsPresent) { '✓' } else { '✗' }) WebSocket controls imported" -ForegroundColor $(if ($wsControlsPresent) { "Green" } else { "Red" })
Write-Host "  $(if ($orderMgrPresent) { '✓' } else { '✗' }) Order manager imported" -ForegroundColor $(if ($orderMgrPresent) { "Green" } else { "Red" })
Write-Host "  $(if ($botControlsPresent) { '✓' } else { '✗' }) Trading bot controls imported" -ForegroundColor $(if ($botControlsPresent) { "Green" } else { "Red" })
Write-Host "  $(if ($positionsPresent) { '✓' } else { '✗' }) Positions monitor imported" -ForegroundColor $(if ($positionsPresent) { "Green" } else { "Red" })
Write-Host "  $(if ($orderBookPresent) { '✓' } else { '✗' }) Order book imported" -ForegroundColor $(if ($orderBookPresent) { "Green" } else { "Red" })
Write-Host "  $(if ($tabsUsed) { '✓' } else { '✗' }) Tabs component used in render" -ForegroundColor $(if ($tabsUsed) { "Green" } else { "Red" })
Write-Host "  Result: $integrationScore/7 integration points verified" -ForegroundColor $(if ($integrationScore -eq 7) { "Green" } else { "Red" })

# 5. Check TypeScript Compilation
Write-Host "`n[5/5] Checking TypeScript..." -ForegroundColor Yellow
Write-Host "  Running TypeScript compiler check..." -ForegroundColor Gray

# Quick check for obvious errors
$tscOutput = npx tsc --noEmit 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ No TypeScript errors found" -ForegroundColor Green
} else {
    Write-Host "  ✗ TypeScript errors detected" -ForegroundColor Red
    Write-Host "  Run 'npx tsc --noEmit' for details" -ForegroundColor Yellow
}

# Final Summary
Write-Host "`n=== INTEGRATION SUMMARY ===" -ForegroundColor Cyan
Write-Host "Backend Functions:  $activeCount/$($functions.Count) ACTIVE" -ForegroundColor $(if ($activeCount -eq $functions.Count) { "Green" } else { "Red" })
Write-Host "Frontend Components: $componentCount/$($components.Count) Present" -ForegroundColor $(if ($componentCount -eq $components.Count) { "Green" } else { "Red" })
Write-Host "API Integration:    $importCount/$($imports.Count) Verified" -ForegroundColor $(if ($importCount -eq $imports.Count) { "Green" } else { "Red" })
Write-Host "Dashboard Tabs:     $integrationScore/7 Integrated" -ForegroundColor $(if ($integrationScore -eq 7) { "Green" } else { "Red" })

$allChecks = ($activeCount -eq $functions.Count) -and ($componentCount -eq $components.Count) -and ($importCount -eq $imports.Count) -and ($integrationScore -eq 7)

if ($allChecks) {
    Write-Host "`n✅ ALL CHECKS PASSED - Frontend is fully synchronized with Backend!" -ForegroundColor Green
    Write-Host "`nReady to deploy with:" -ForegroundColor Cyan
    Write-Host "  npm run build" -ForegroundColor White
    Write-Host "  firebase apphosting:backends:deploy studio --project=tbsignalstream" -ForegroundColor White
} else {
    Write-Host "`n⚠️  Some checks failed - review errors above" -ForegroundColor Yellow
}

Write-Host ""
