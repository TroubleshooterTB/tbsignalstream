# 🚀 TOMORROW MORNING - QUICK START GUIDE
**Date**: December 11, 2025 | **Market Open**: 9:15 AM IST

**✅ FIXES DEPLOYED TONIGHT**:
- Bot candle requirement: 50 → 30 (trades 20 mins earlier!)
- Dashboard: Market Heatmap, Bot Performance Stats, Pattern Tooltips
- Backend revision: 00037-k8v (deployed 1:45 PM Dec 10)
- Frontend: Auto-deploying from GitHub (check in 5 mins)

---

## ⏰ 9:00 AM - SETUP (Do this FIRST)

### 1. Open Terminal
```powershell
cd "D:\Tushar 2.0\tbsignalstream_backup\tbsignalstream_backup"
```

### 2. Open Browser
- Go to: `https://studio--tbsignalstream.us-central1.hosted.app`
- Press: **Ctrl + Shift + R** (hard refresh)
- Press: **F12** (open DevTools)

### 3. Verify Settings
- ✅ Mode: Paper/Live/Simulation (your choice)
- ✅ Portfolio: ₹100,000
- ✅ Symbols: 49 stocks

---

## ⏰ 9:15 AM SHARP - START BOT

### Click "Start Trading Bot" Button

### IMMEDIATELY Copy-Paste This Command:
```powershell
$startTime = (Get-Date).AddMinutes(-1).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

while ($true) {
    Clear-Host
    Write-Host "=== BOT STARTUP - $(Get-Date -Format 'HH:mm:ss') ===" -ForegroundColor Cyan
    
    gcloud run services logs read trading-bot-service --region asia-south1 --limit 5000 --format "value(timestamp,textPayload)" --log-filter "timestamp>=\"$startTime\"" | Select-String -Pattern "Fetching tokens|Trading managers|WebSocket|Subscribed|PRE-TRADE|ALL CHECKS|Real-time trading|ERROR|CRITICAL" | Select-Object -Last 40 | ForEach-Object {
        if ($_ -match "ERROR|CRITICAL") { Write-Host $_ -ForegroundColor Red }
        elseif ($_ -match "✅|ALL CHECKS PASSED") { Write-Host $_ -ForegroundColor Green }
        else { Write-Host $_ }
    }
    
    Start-Sleep -Seconds 5
}
```

---

## ✅ WATCH FOR THIS SEQUENCE (15 minutes):

```
9:15:00 → ✅ Fetching tokens for 49 symbols...
9:16:00 → ✅ Trading managers initialized
9:18:00 → ✅ WebSocket connected
9:18:10 → ✅ Subscribed to 48 symbols
9:18:15 → ✅ After subscription wait: 48 symbols have prices
9:20:00 → ✅ Bootstrapping historical candles...
9:25:00 → ✅ 🔍 PRE-TRADE VERIFICATION:
          ✅   websocket_connected: True
          ✅   has_prices: True
          ✅   has_candles: True
          ✅   has_tokens: True
9:25:01 → ✅ ALL CHECKS PASSED - Bot ready to trade! ← SUCCESS!
9:25:02 → ✅ Real-time trading bot started successfully!
```

---

## 🎯 IF YOU SEE "ALL CHECKS PASSED" → SUCCESS!

Press **Ctrl + C** to stop monitoring, then run:
```powershell
curl -s "https://trading-bot-service-818546654122.asia-south1.run.app/bot-health-check" | ConvertFrom-Json | Format-List
```

**Expected**: `overall_status : healthy`

**You're done! Bot is trading!** ✅

---

## 🚨 IF YOU SEE "❌" IN PRE-TRADE VERIFICATION:

### STOP THE BOT IMMEDIATELY!
1. Click "Stop Trading Bot" button
2. Take screenshot
3. Copy error logs
4. Contact developer

### DO NOT TRADE until issue is fixed!

---

## 📊 EVERY 15 MINUTES - QUICK CHECK

```powershell
$h = curl -s "https://trading-bot-service-818546654122.asia-south1.run.app/bot-health-check" | ConvertFrom-Json
Write-Host "Status: $($h.overall_status) | Symbols: $($h.num_symbols) | Prices: $($h.num_prices)" -ForegroundColor $(if ($h.overall_status -eq 'healthy') {'Green'} else {'Red'})
```

---

## 📈 CHECK FOR TRADES (Every 30 min)

```powershell
gcloud run services logs read trading-bot-service --region asia-south1 --limit 2000 --format "value(timestamp,textPayload)" | Select-String -Pattern "SIGNAL|Opening position|Closing position|Target hit|Stop loss" | Select-Object -Last 20
```

---

## ⏰ 3:15 PM - WATCH FOR AUTO-CLOSE

Bot automatically closes all INTRADAY positions at 3:15 PM.

Look for:
```
⏰ EOD AUTO-CLOSE: 3:15 PM reached - Closing all INTRADAY positions
```

---

## 🛑 EMERGENCY STOP

**Dashboard**: Click "Stop Trading Bot" button

**OR Firestore** (instant):
1. Go to: https://console.firebase.google.com/u/0/project/tbsignalstream/firestore
2. Navigate: `bot_configs/{your_user_id}`
3. Set: `emergency_stop = true`
4. Bot stops in 5 seconds

---

## 📞 TROUBLESHOOTING

| Issue | Action |
|-------|--------|
| Startup takes >15 min | Stop and restart |
| Pre-trade verification fails | STOP, don't trade, contact dev |
| No signals after 1 hour | Normal if market is slow |
| Health check returns "degraded" | Check logs for errors |
| Bot stops spontaneously | Check logs, restart if clean |

---

## 🎯 THAT'S IT! 

**Main thing**: Watch for **"ALL CHECKS PASSED"** message.

If you see it → **Bot is working perfectly** ✅

If you don't see it after 15 minutes → **Something is wrong** ❌

**Good luck tomorrow! 🚀**

---

**Full Audit Report**: See `PRODUCTION_READY_AUDIT_DEC_9_2025.md`
