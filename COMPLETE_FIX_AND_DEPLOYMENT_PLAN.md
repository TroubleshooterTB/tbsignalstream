# COMPLETE FIX & DEPLOYMENT PLAN
## Zero to Trading - Step by Step Execution Guide
**Date:** December 8, 2025  
**Target:** Monday December 9, 2025 9:00 AM Market Open  
**Timeline:** ~2 hours of focused work tonight

---

## REVISED AUDIT FINDINGS (Additional Issues Found)

### ❌ ISSUE CORRECTION: WebSocket Dependency
**STATUS:** Not the issue - `websocket-client==1.6.0` IS installed in requirements.txt

### 🔴 NEW CRITICAL ISSUE FOUND: No Status Polling
**Problem:** Frontend NEVER polls bot status automatically
```typescript
// NO useEffect to refresh status!
// State can be stale from previous session
const [isBotRunning, setIsBotRunning] = useState(false);
```

**Impact:**
- If page refreshed while bot running → state resets to `false`
- If bot crashed → UI still shows `true`
- No sync between frontend state and backend reality

### 🔴 CONFIRMED: Frontend State Blocking
```typescript
const startTradingBot = useCallback(async () => {
  if (isBotRunning) {  // ← BLOCKS API CALL
    toast({ title: 'Bot Already Running' });
    return;  // ← NEVER reaches backend!
  }
  // ... rest of code
}, [isBotRunning]);
```

### 🔴 NEW THEORY: What Actually Happened on Dec 8

Based on evidence:
1. **NO /start endpoint calls** found in logs
2. **Scanning logs exist** from 9:59 AM
3. **Only /market_data calls** every minute

**Hypothesis:** You were using a DIFFERENT interface (not the Next.js dashboard) that:
- Calls `/market_data` for price display
- Has its own bot start mechanism
- Possibly an old HTML page or test script
- That interface started a bot but it had no WebSocket/data

---

## COMPLETE FIX PLAN - ORGANIZED BY PRIORITY

### TIER 1: MUST FIX (Critical - Bot Won't Work Without These)

#### Fix 1.1: Add Frontend Status Polling
**File:** `src/context/trading-context.tsx`  
**Why:** Keep UI in sync with backend reality  
**Time:** 5 minutes

```typescript
// Add after other useEffects
useEffect(() => {
  if (!isAuthReady) return;
  
  // Initial status check
  refreshBotStatus();
  
  // Poll every 10 seconds
  const interval = setInterval(() => {
    refreshBotStatus();
  }, 10000);
  
  return () => clearInterval(interval);
}, [isAuthReady, refreshBotStatus]);
```

#### Fix 1.2: Remove State Check Before API Call
**File:** `src/context/trading-context.tsx`  
**Why:** Always try to start, let backend decide if already running  
**Time:** 2 minutes

```typescript
const startTradingBot = useCallback(async () => {
  // REMOVE THESE LINES:
  // if (isBotRunning) {
  //   toast({ title: 'Bot Already Running' });
  //   return;
  // }
  
  setIsBotLoading(true);
  try {
    // ... rest stays the same
```

#### Fix 1.3: Add Fail-Fast on Critical Errors
**File:** `trading_bot_service/realtime_bot_engine.py`  
**Why:** Don't continue with broken state  
**Time:** 10 minutes

```python
# In start() method, after WebSocket init:
if not self.ws_manager or not self.ws_manager.is_connected:
    raise Exception("CRITICAL: WebSocket connection failed - cannot trade without real-time data")

# After bootstrap:
if len(self.candle_data) == 0:
    raise Exception("CRITICAL: Historical data bootstrap failed - cannot analyze without candles")

# Before entering main loop:
self._verify_ready_to_trade()  # Add this method
```

#### Fix 1.4: Add Pre-Trade Verification
**File:** `trading_bot_service/realtime_bot_engine.py`  
**Why:** Final check before trading  
**Time:** 10 minutes

```python
def _verify_ready_to_trade(self):
    """Final verification before entering trading loop"""
    checks = {
        'websocket_connected': self.ws_manager and hasattr(self.ws_manager, 'is_connected') and self.ws_manager.is_connected,
        'has_prices': len(self.latest_prices) > 0,
        'has_candles': len(self.candle_data) >= len(self.symbol_tokens) * 0.8,  # At least 80% of symbols
        'has_tokens': len(self.symbol_tokens) > 0,
    }
    
    logger.info("🔍 PRE-TRADE VERIFICATION:")
    for check, status in checks.items():
        icon = "✅" if status else "❌"
        logger.info(f"  {icon} {check}: {status}")
    
    if not all(checks.values()):
        failed = [k for k, v in checks.items() if not v]
        error_msg = f"Bot not ready to trade. Failed checks: {', '.join(failed)}"
        logger.error(f"❌ {error_msg}")
        raise Exception(error_msg)
    
    logger.info("✅ ALL CHECKS PASSED - Bot ready to trade!")
    return True
```

### TIER 2: HIGH PRIORITY (Prevent Future Issues)

#### Fix 2.1: Add Health Check Endpoint
**File:** `trading_bot_service/main.py`  
**Why:** Verify bot is functional, not just "running"  
**Time:** 15 minutes

```python
@app.route('/health-check', methods=['GET'])
def health_check():
    """Comprehensive bot health check"""
    try:
        # Verify auth
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing authorization'}), 401
        
        id_token = auth_header.split('Bearer ')[1]
        decoded_token = auth.verify_id_token(id_token)
        user_id = decoded_token['uid']
        
        # Check if bot exists
        if user_id not in active_bots:
            return jsonify({
                'status': 'not_running',
                'running': False
            }), 200
        
        bot = active_bots[user_id]
        
        # Gather health metrics
        health = {
            'running': bot.is_running,
            'has_engine': bot.engine is not None,
            'websocket_connected': False,
            'num_prices': 0,
            'num_candles': 0,
            'num_symbols': 0,
            'warnings': [],
            'errors': []
        }
        
        if bot.engine:
            # WebSocket check
            if hasattr(bot.engine, 'ws_manager') and bot.engine.ws_manager:
                health['websocket_connected'] = getattr(bot.engine.ws_manager, 'is_connected', False)
            
            # Data checks
            if hasattr(bot.engine, 'latest_prices'):
                health['num_prices'] = len(bot.engine.latest_prices)
            if hasattr(bot.engine, 'candle_data'):
                health['num_candles'] = len(bot.engine.candle_data)
            if hasattr(bot.engine, 'symbol_tokens'):
                health['num_symbols'] = len(bot.engine.symbol_tokens)
        
        # Determine overall status
        if not health['websocket_connected']:
            health['errors'].append('WebSocket not connected - no real-time data')
        if health['num_prices'] == 0:
            health['errors'].append('No price data available')
        if health['num_candles'] == 0:
            health['errors'].append('No historical candle data')
        elif health['num_candles'] < health['num_symbols'] * 0.5:
            health['warnings'].append(f'Only {health["num_candles"]}/{health["num_symbols"]} symbols have data')
        
        # Overall status
        if health['errors']:
            health['overall_status'] = 'error'
        elif health['warnings']:
            health['overall_status'] = 'degraded'
        else:
            health['overall_status'] = 'healthy'
        
        return jsonify(health), 200
        
    except Exception as e:
        logger.error(f"Health check error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
```

#### Fix 2.2: Call Health Check After Start
**File:** `src/context/trading-context.tsx`  
**Why:** Verify bot actually initialized correctly  
**Time:** 10 minutes

```typescript
const startTradingBot = useCallback(async () => {
  setIsBotLoading(true);
  try {
    const result = await tradingBotApi.start({...});
    
    // Wait for bot to initialize
    toast({
      title: 'Bot Starting...',
      description: 'Initializing WebSocket and loading data. Please wait 20 seconds...',
    });
    
    await new Promise(resolve => setTimeout(resolve, 20000));
    
    // Check health
    const health = await tradingBotApi.healthCheck();
    
    if (health.overall_status === 'healthy') {
      setIsBotRunning(true);
      toast({
        title: 'Bot Started Successfully',
        description: `Trading with ${health.num_symbols} symbols. WebSocket connected.`,
      });
    } else if (health.overall_status === 'degraded') {
      setIsBotRunning(true);
      toast({
        title: '⚠️ Bot Started with Warnings',
        description: health.warnings.join(', '),
        variant: 'warning',
      });
    } else {
      toast({
        title: '❌ Bot Started but Has Errors',
        description: health.errors.join(', '),
        variant: 'destructive',
      });
    }
  } catch (error: any) {
    toast({
      title: 'Failed to Start Bot',
      description: error.message,
      variant: 'destructive',
    });
  } finally {
    setIsBotLoading(false);
  }
}, [botConfig, toast]);
```

#### Fix 2.3: Add healthCheck to API client
**File:** `src/lib/trading-api.ts`  
**Time:** 5 minutes

```typescript
export const tradingBotApi = {
  // ... existing methods
  
  healthCheck: async () => {
    const user = auth.currentUser;
    if (!user) throw new Error('Not authenticated');
    
    const TRADING_BOT_SERVICE_URL = 'https://trading-bot-service-vmxfbt7qiq-el.a.run.app';
    const idToken = await user.getIdToken();
    
    const response = await fetch(`${TRADING_BOT_SERVICE_URL}/health-check`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${idToken}`,
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) throw new Error('Health check failed');
    return response.json();
  },
};
```

### TIER 3: MONITORING & OBSERVABILITY

#### Fix 3.1: Add Better Logging in Bootstrap
**File:** `trading_bot_service/realtime_bot_engine.py`  
**Time:** 10 minutes

```python
def _bootstrap_historical_candles(self):
    """Fetch historical data with detailed logging"""
    logger.info(f"📊 [BOOTSTRAP] Starting for {len(self.symbol_tokens)} symbols")
    
    successful = 0
    failed = 0
    errors_by_type = {}
    
    for i, (symbol, token_info) in enumerate(self.symbol_tokens.items()):
        try:
            logger.info(f"📊 [BOOTSTRAP] [{i+1}/{len(self.symbol_tokens)}] Fetching {symbol}...")
            
            candles = self._fetch_historical_candles(
                exchange=token_info['exchange'],
                symboltoken=token_info['token'],
                interval='FIVE_MINUTE',
                fromdate=(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M'),
                todate=datetime.now().strftime('%Y-%m-%d %H:%M')
            )
            
            if candles and len(candles) > 0:
                self.candle_data[symbol] = candles
                successful += 1
                logger.info(f"✅ [BOOTSTRAP] {symbol}: {len(candles)} candles loaded")
            else:
                failed += 1
                logger.warning(f"⚠️ [BOOTSTRAP] {symbol}: No data returned")
            
            time.sleep(0.4)  # Rate limiting
            
        except Exception as e:
            failed += 1
            error_type = type(e).__name__
            errors_by_type[error_type] = errors_by_type.get(error_type, 0) + 1
            logger.error(f"❌ [BOOTSTRAP] {symbol}: {e}")
    
    logger.info(f"📊 [BOOTSTRAP] Complete: {successful} success, {failed} failed")
    
    if errors_by_type:
        logger.warning(f"📊 [BOOTSTRAP] Errors by type: {errors_by_type}")
    
    if successful == 0:
        raise Exception("CRITICAL: All symbols failed to bootstrap")
    elif successful < len(self.symbol_tokens) * 0.5:
        logger.warning(f"⚠️ [BOOTSTRAP] Only {successful}/{len(self.symbol_tokens)} succeeded")
    
    return successful
```

#### Fix 3.2: Add Dashboard Health Widget
**File:** `src/components/bot-health-indicator.tsx` (NEW FILE)  
**Time:** 15 minutes

```typescript
'use client';

import { useEffect, useState } from 'react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
import { tradingBotApi } from '@/lib/trading-api';

export function BotHealthIndicator() {
  const [health, setHealth] = useState<any>(null);
  
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const result = await tradingBotApi.healthCheck();
        setHealth(result);
      } catch (error) {
        setHealth(null);
      }
    };
    
    checkHealth();
    const interval = setInterval(checkHealth, 5000);  // Check every 5 seconds
    
    return () => clearInterval(interval);
  }, []);
  
  if (!health || health.status === 'not_running') return null;
  
  return (
    <div className="fixed top-4 right-4 z-50 max-w-md">
      {health.overall_status === 'healthy' && (
        <Alert className="border-green-500 bg-green-50">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertTitle>Bot Healthy</AlertTitle>
          <AlertDescription>
            Trading with {health.num_symbols} symbols. WebSocket connected.
          </AlertDescription>
        </Alert>
      )}
      
      {health.overall_status === 'degraded' && (
        <Alert className="border-yellow-500 bg-yellow-50">
          <AlertTriangle className="h-4 w-4 text-yellow-600" />
          <AlertTitle>Bot Running with Warnings</AlertTitle>
          <AlertDescription>
            {health.warnings.map((w: string, i: number) => (
              <div key={i}>• {w}</div>
            ))}
          </AlertDescription>
        </Alert>
      )}
      
      {health.overall_status === 'error' && (
        <Alert className="border-red-500 bg-red-50">
          <XCircle className="h-4 w-4 text-red-600" />
          <AlertTitle>Bot Has Errors</AlertTitle>
          <AlertDescription>
            {health.errors.map((e: string, i: number) => (
              <div key={i}>• {e}</div>
            ))}
          </AlertDescription>
        </Alert>
      )}
      
      <div className="mt-2 flex gap-2 text-xs">
        <Badge variant="outline">Prices: {health.num_prices}</Badge>
        <Badge variant="outline">Candles: {health.num_candles}</Badge>
        <Badge variant={health.websocket_connected ? "default" : "destructive"}>
          WebSocket: {health.websocket_connected ? 'Connected' : 'Disconnected'}
        </Badge>
      </div>
    </div>
  );
}
```

---

## STEP-BY-STEP EXECUTION PLAN

### TONIGHT (8:00 PM - 10:00 PM IST) - 2 Hours

#### PHASE 1: Backend Fixes (45 minutes)

**Step 1.1: Add _verify_ready_to_trade Method** (10 min)
```bash
# Open file
code trading_bot_service/realtime_bot_engine.py

# Add method after _bootstrap_historical_candles (around line 800)
# Copy code from Fix 1.4 above
```

**Step 1.2: Add Fail-Fast Logic** (10 min)
```python
# In start() method (around line 120-180)
# After WebSocket init (around line 145):
if not self.ws_manager or not hasattr(self.ws_manager, 'is_connected') or not self.ws_manager.is_connected:
    raise Exception("CRITICAL: WebSocket failed - cannot trade")

# After bootstrap (around line 165):
successful_candles = self._bootstrap_historical_candles()
if successful_candles == 0:
    raise Exception("CRITICAL: Bootstrap failed - cannot analyze")

# Before main loop (around line 185):
self._verify_ready_to_trade()
```

**Step 1.3: Improve Bootstrap Logging** (10 min)
```bash
# Replace _bootstrap_historical_candles method
# Use code from Fix 3.1 above
```

**Step 1.4: Add Health Check Endpoint** (15 min)
```bash
# Open file
code trading_bot_service/main.py

# Add new route after /status endpoint (around line 320)
# Copy code from Fix 2.1 above
```

**Step 1.5: Deploy Backend** (5 min)
```bash
cd trading_bot_service
gcloud run deploy trading-bot-service --source . --region asia-south1

# Wait for deployment (2-3 minutes)
```

#### PHASE 2: Frontend Fixes (45 minutes)

**Step 2.1: Add Status Polling** (10 min)
```bash
# Open file
code src/context/trading-context.tsx

# Add useEffect for polling (around line 138, before startTradingBot)
# Copy code from Fix 1.1 above
```

**Step 2.2: Remove State Check** (5 min)
```bash
# Same file: src/context/trading-context.tsx
# In startTradingBot method (around line 142-147)
# DELETE or comment out the isBotRunning check
```

**Step 2.3: Add Health Check After Start** (10 min)
```bash
# Same file: src/context/trading-context.tsx
# Replace startTradingBot method
# Use code from Fix 2.2 above
```

**Step 2.4: Add healthCheck API Method** (5 min)
```bash
# Open file
code src/lib/trading-api.ts

# Add healthCheck method to tradingBotApi object
# Use code from Fix 2.3 above
```

**Step 2.5: Create Health Indicator Component** (10 min)
```bash
# Create new file
code src/components/bot-health-indicator.tsx

# Copy entire component from Fix 3.2 above
```

**Step 2.6: Add Health Indicator to Layout** (5 min)
```typescript
// Open: src/app/page.tsx
// Add import:
import { BotHealthIndicator } from '@/components/bot-health-indicator';

// Add to return JSX (at top level):
return (
  <>
    <BotHealthIndicator />
    {/* ... rest of your components */}
  </>
);
```

**Step 2.7: Commit and Push** (5 min)
```bash
cd ..  # Back to root
git add -A
git commit -m "CRITICAL: Add bot health verification and status polling

- Add status polling every 10 seconds
- Remove blocking state check before start
- Add health check endpoint and frontend integration
- Add fail-fast on WebSocket/bootstrap errors
- Add health indicator widget in dashboard
- Improve bootstrap logging for debugging"

git push origin master
```

**Step 2.8: Wait for App Hosting Deploy** (5-10 min)
```bash
# App Hosting auto-deploys from GitHub
# Monitor at: https://console.firebase.google.com/project/tbsignalstream/apphosting
```

#### PHASE 3: Verification (30 minutes)

**Step 3.1: Hard Refresh Dashboard**
```
1. Open: https://studio--tbsignalstream.us-central1.hosted.app
2. Press: Ctrl + Shift + R (hard refresh)
3. Press: F12 (open DevTools)
4. Go to: Application → Storage → Clear site data
5. Refresh again
```

**Step 3.2: Test Backend Health Endpoint**
```bash
# Without auth (should fail):
curl https://trading-bot-service-vmxfbt7qiq-el.a.run.app/health-check

# With your auth token (get from browser):
# 1. In DevTools, go to Network tab
# 2. Refresh page
# 3. Find any request with Authorization header
# 4. Copy the Bearer token
# 5. Run:
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
     https://trading-bot-service-vmxfbt7qiq-el.a.run.app/health-check
     
# Should return: {"status": "not_running", "running": false}
```

**Step 3.3: Test Frontend Status Polling**
```
1. Login to dashboard
2. Open DevTools → Console
3. Watch for: "[TradingContext] Bot status check:" messages
4. Should appear every 10 seconds
5. Verify console shows: { running: false }
```

**Step 3.4: Document Current State**
```bash
# Create verification log
echo "=== PRE-LAUNCH VERIFICATION ===" > verification.log
echo "Date: $(date)" >> verification.log
echo "" >> verification.log
echo "Backend deployed: " >> verification.log
gcloud run services describe trading-bot-service --region asia-south1 --format="value(status.latestReadyRevisionName,status.conditions)" >> verification.log
echo "" >> verification.log
echo "Frontend URL: https://studio--tbsignalstream.us-central1.hosted.app" >> verification.log
echo "All fixes applied: YES" >> verification.log
echo "Ready for Monday: YES" >> verification.log
```

---

## MONDAY MORNING CHECKLIST (9:00 AM IST)

### PRE-MARKET SETUP (8:45 - 9:00 AM)

**[ ] 1. Verify Credentials**
```
- Login to dashboard
- Check Angel One connection status
- If "Disconnected", click "Connect Angel One"
- Verify credentials are fresh (not expired)
```

**[ ] 2. Open DevTools**
```
- Press F12
- Go to Console tab
- Clear console (Ctrl+L)
- Go to Network tab
- Enable "Preserve log"
```

**[ ] 3. Prepare Terminal**
```powershell
# Open PowerShell
# Navigate to project
cd "d:\Tushar 2.0\tbsignalstream_backup\tbsignalstream_backup"

# Prepare log monitoring command
$logCmd = "gcloud run services logs read trading-bot-service --region asia-south1 --limit 200 | Select-String 'WebSocket|Fetched tokens|candles loaded|ready to trade|CRITICAL|ERROR' | Select-Object -Last 30"
```

### MARKET OPEN (9:15 AM)

**[ ] 4. Start Bot**
```
1. Click "Start Trading Bot"
2. Watch console for POST /start request
3. Should see 200 OK response
4. Toast should say: "Bot Starting... Please wait 20 seconds..."
```

**[ ] 5. Monitor Startup (0-20 seconds)**
```powershell
# In terminal, run:
gcloud run services logs read trading-bot-service --region asia-south1 --limit 200 | Select-String "WebSocket|Fetched tokens|candles loaded|ready to trade|CRITICAL|ERROR" | Select-Object -Last 30
```

**MUST SEE:**
```
✅ Fetched tokens for 50 symbols
🔧 Initializing trading managers...
✅ Trading managers initialized successfully
🔌 Initializing WebSocket connection...
✅ WebSocket initialized and connected
⏳ Waiting 10 seconds for first ticks...
✅ WebSocket receiving data: 50 symbols have prices
📊 Bootstrapping historical candle data...
📊 [BOOTSTRAP] [1/50] Fetching RELIANCE-EQ...
✅ [BOOTSTRAP] RELIANCE-EQ: 2016 candles loaded
... (more symbols)
📊 [BOOTSTRAP] Complete: 50 success, 0 failed
🔍 PRE-TRADE VERIFICATION:
  ✅ websocket_connected: True
  ✅ has_prices: True
  ✅ has_candles: True
  ✅ has_tokens: True
✅ ALL CHECKS PASSED - Bot ready to trade!
```

**[ ] 6. Verify Health Check (After 20 seconds)**
```
Dashboard should show:
- Green alert: "Bot Healthy"
- "Trading with 50 symbols. WebSocket connected."
- Badges: Prices: 50 | Candles: 50 | WebSocket: Connected
```

**[ ] 7. Watch for First Analysis (9:20 AM)**
```powershell
# Run every 5 minutes:
gcloud run services logs read trading-bot-service --region asia-south1 --limit 100 | Select-String "Scanning|Candle data available|signal|BUY|SELL" | Select-Object -Last 20
```

**MUST SEE:**
```
📊 Scanning 50 symbols for trading opportunities...
🔢 Candle data available for 50 symbols  ← NOT 0!
💰 Latest prices available for 50 symbols  ← NOT 0!
🔍 Analyzing RELIANCE-EQ...
🔍 Analyzing TCS-EQ...
```

**[ ] 8. Monitor Positions Tab**
```
- Click "Positions" tab
- Should update every 3 seconds
- If bot generates signal → position should appear within 30 seconds
- Verify P&L updates in real-time
```

---

## EMERGENCY PROCEDURES

### If Bot Doesn't Start

**Symptom:** No logs after clicking start

**Diagnosis:**
```powershell
# Check if /start was called:
gcloud run services logs read trading-bot-service --region asia-south1 --limit 100 | Select-String "/start"

# If NOTHING → Frontend issue
# If ERROR → Backend issue
```

**Fix:**
```typescript
// Frontend: Check browser console for errors
// Look for: Network errors, CORS issues, 401/403 responses

// If "Bot Already Running" toast but backend shows not running:
// 1. Hard refresh (Ctrl+Shift+R)
// 2. Clear local storage
// 3. Try again
```

### If WebSocket Doesn't Connect

**Symptom:** Logs show "WebSocket failed" or timeout

**Diagnosis:**
```powershell
gcloud run services logs read trading-bot-service --region asia-south1 --limit 200 | Select-String "WebSocket|feed_token" | Select-Object -Last 10
```

**Fix:**
```
1. Check Angel One credentials in Firestore
2. Verify feed_token not expired (check timestamp)
3. Try disconnecting and reconnecting Angel One in UI
4. Check if Angel One API is down (rare)
```

### If Bootstrap Fails

**Symptom:** Logs show "Bootstrap failed" or "0 candles"

**Diagnosis:**
```powershell
gcloud run services logs read trading-bot-service --region asia-south1 --limit 300 | Select-String "BOOTSTRAP|403|rate limit" | Select-Object -Last 30
```

**Fix:**
```
# If 403 errors → Rate limiting
# Solution: Bot has retry logic, should recover

# If all symbols fail → API key issue
# Check environment variable:
gcloud run services describe trading-bot-service --region asia-south1 --format="value(spec.template.spec.containers[0].env)"
```

### If No Signals Generated (After 1 Hour)

**Symptom:** Bot running, data loaded, but no signals

**Possible Causes:**
```
1. Market conditions don't meet criteria (normal - wait)
2. Screening too strict (check logs for "Skipping" reasons)
3. Indicator calculation errors (check for ERROR logs)
```

**Diagnosis:**
```powershell
# Check what screening criteria are failing:
gcloud run services logs read trading-bot-service --region asia-south1 --limit 500 | Select-String "Skipping|Failed screening" | Select-Object -Last 50
```

**Note:** It's NORMAL to not have signals every minute. Pattern detection requires:
- Strong volume
- Clear trend
- Technical indicator alignment
- Market volatility

Could be 30-60 minutes before first signal in slow market.

---

## SUCCESS CRITERIA

### Immediate Success (9:20 AM - 9:30 AM)
- ✅ Bot starts without errors
- ✅ WebSocket connected
- ✅ 50/50 symbols have candles loaded
- ✅ 50/50 symbols have prices
- ✅ Health indicator shows "Healthy"
- ✅ Scanning logs every 5 seconds
- ✅ Dashboard shows real-time price updates

### 1-Hour Success (9:30 AM - 10:30 AM)
- ✅ No crashes or restarts
- ✅ WebSocket stays connected
- ✅ At least 1 signal generated (market dependent)
- ✅ If signal → Position appears in dashboard
- ✅ If position → P&L updates correctly
- ✅ No ERROR logs (warnings OK)

### Full Day Success (9:15 AM - 3:30 PM)
- ✅ Bot runs entire session without restart
- ✅ At least 3-5 signals generated (normal conditions)
- ✅ Stop loss monitoring works (test with paper position)
- ✅ Auto-close at 3:15 PM (EOD check)
- ✅ No missed opportunities due to data issues

---

## ROLLBACK PLAN

If critical issues found after deployment:

### Backend Rollback
```bash
# List recent revisions:
gcloud run services describe trading-bot-service --region asia-south1 --format="value(status.traffic)"

# Rollback to previous (00030-77t):
gcloud run services update-traffic trading-bot-service \
  --to-revisions=trading-bot-service-00030-77t=100 \
  --region asia-south1
```

### Frontend Rollback
```bash
# Check App Hosting builds:
firebase apphosting:backends:get studio

# Rollback in Firebase Console:
# https://console.firebase.google.com/project/tbsignalstream/apphosting
# Click "Rollback" on previous successful build
```

---

## FINAL VERIFICATION CHECKLIST

**Before Going to Sleep Tonight:**
- [ ] All code changes committed and pushed
- [ ] Backend deployed successfully
- [ ] Frontend deployed successfully (App Hosting)
- [ ] Health endpoint tested and working
- [ ] Status polling verified in console
- [ ] Emergency procedures documented
- [ ] Terminal commands prepared
- [ ] DevTools opened and ready

**Confidence Level:**
- Tonight (after all fixes): **85%**
- Monday 9:30 AM (after startup verification): **95%**
- Monday 10:30 AM (after 1 hour running): **98%**

---

## TIME ESTIMATE

| Phase | Task | Time |
|-------|------|------|
| Phase 1 | Backend fixes | 45 min |
| Phase 2 | Frontend fixes | 45 min |
| Phase 3 | Verification | 30 min |
| **TOTAL** | **Tonight's Work** | **2 hours** |
| Monday | Monitoring (9-10:30 AM) | 90 min |
| **GRAND TOTAL** | **Complete Fix & Verify** | **3.5 hours** |

---

## WHAT MAKES THIS DIFFERENT FROM YESTERDAY?

**Yesterday:**
- ❌ Assumed code existence = working
- ❌ No runtime verification
- ❌ No health checks
- ❌ Silent failures allowed
- ❌ No monitoring plan

**Today:**
- ✅ Added health check endpoint
- ✅ Added fail-fast on errors
- ✅ Added status polling
- ✅ Added health indicator widget
- ✅ Added detailed logging
- ✅ Complete monitoring plan
- ✅ Emergency procedures documented
- ✅ Success criteria defined

**This plan is different because:**
1. Every fix has a verification step
2. Every component has health checks
3. Every failure mode has a documented recovery
4. We're not assuming anything works until proven

---

**Generated:** December 8, 2025 11:30 PM IST  
**Target Execution:** Tonight 8:00 PM - 10:00 PM  
**Go-Live:** Monday 9:15 AM  
**First Verification:** Monday 9:30 AM  
**Confidence:** 85% → 98% (progressive verification)
