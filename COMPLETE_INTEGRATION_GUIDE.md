# 🎯 Complete Integration Guide - Crypto Bot

**Everything you need to connect Frontend → Backend → Firestore → Cloud Run**

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Stock Bot   │  │  Crypto Bot  │  │   Settings   │         │
│  │  Dashboard   │  │  Dashboard   │  │   Page       │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP/REST API
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND (Flask/Cloud Run)                    │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  API Endpoints:                                            │ │
│  │  • /api/crypto/status                                      │ │
│  │  • /api/crypto/start                                       │ │
│  │  • /api/crypto/stop                                        │ │
│  │  • /api/crypto/switch-pair                                 │ │
│  │  • /api/crypto/credentials (save/get)                      │ │
│  └────────────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                  FIRESTORE DATABASE                             │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Collections:                                             │  │
│  │  • coindcx_credentials/{user_id}                          │  │
│  │  • crypto_bot_config/{user_id}                            │  │
│  │  • crypto_bot_status/{user_id}                            │  │
│  │  • crypto_activity_feed (subcollection)                   │  │
│  │  • crypto_bot_sessions (history)                          │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                    TRADING BOT ENGINE                           │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  crypto_bot_engine.py                                      │ │
│  │  • Reads config from Firestore                             │ │
│  │  • Executes day/night strategies                           │ │
│  │  • Writes status/activity back to Firestore                │ │
│  └────────────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                      COINDCX EXCHANGE                           │
│  • REST API (orders, balances)                                  │
│  • WebSocket (real-time prices)                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1️⃣ Firestore Collections (Database)

### **A. coindcx_credentials**
```javascript
/coindcx_credentials/{user_id}
{
  api_key: "YOUR_API_KEY",
  api_secret_encrypted: "gAAAAA...",  // Fernet encrypted
  enabled: true,
  created_at: <timestamp>,
  last_updated: <timestamp>
}
```

**Status:** ⏳ Need to run `initialize_crypto_bot_firestore.py`

---

### **B. crypto_bot_config**
```javascript
/crypto_bot_config/{user_id}
{
  user_id: "default_user",
  active_pair: "BTC",  // or "ETH"
  trading_enabled: true,
  mode: "paper",  // or "live"
  strategy_day: "momentum_scalping",
  strategy_night: "mean_reversion",
  risk_params: {
    target_volatility: 0.25,
    max_position_weight: 2.0,
    max_daily_loss_pct: 0.05,
    rebalance_threshold: 0.20,
    fee_barrier_pct: 0.0015,
    min_daily_volume_usd: 1000000
  },
  created_at: <timestamp>,
  last_updated: <timestamp>
}
```

**Status:** ⏳ Need to run `initialize_crypto_bot_firestore.py`

---

### **C. crypto_bot_status**
```javascript
/crypto_bot_status/{user_id}
{
  user_id: "default_user",
  status: "running",  // "stopped", "running", "error"
  is_running: true,
  active_pair: "BTC",
  open_positions: 2,
  total_trades_today: 15,
  daily_pnl: 125.50,
  websocket_connected: true,
  uptime_seconds: 3600,
  last_signal: {
    type: "DAY_ENTRY",
    price: 42567.89,
    timestamp: <timestamp>
  },
  last_updated: <timestamp>
}
```

**Status:** ⏳ Need to run `initialize_crypto_bot_firestore.py`

---

### **D. crypto_activity_feed**
```javascript
/crypto_activity_feed/{auto_id}
{
  user_id: "default_user",
  timestamp: <timestamp>,
  type: "POSITION_OPENED",  // or "POSITION_CLOSED", "PAIR_SWITCHED", etc.
  message: "BUY position opened: 0.015 BTC @ $42,567",
  details: {
    pair: "BTC",
    side: "buy",
    quantity: 0.015,
    price: 42567.89,
    strategy: "day_momentum"
  }
}
```

**Status:** ⏳ Will be populated when bot runs

---

### **E. crypto_bot_sessions**
```javascript
/crypto_bot_sessions/{auto_id}
{
  user_id: "default_user",
  active_pair: "BTC",
  start_time: <timestamp>,
  end_time: <timestamp>,
  runtime_seconds: 7200,
  total_trades: 25,
  winning_trades: 15,
  losing_trades: 10,
  daily_pnl: 250.00,
  max_drawdown: -50.00
}
```

**Status:** ⏳ Will be populated when bot stops

---

## 2️⃣ Backend API Endpoints

Need to add these to your Flask API:

### **File:** `api/crypto_bot_api.py` (NEW)

```python
from flask import Blueprint, request, jsonify
from firebase_admin import firestore
from trading_bot_service.crypto_bot_engine import CryptoBotEngine
from trading_bot_service.coindcx_credentials import CoinDCXCredentials
import asyncio

crypto_api = Blueprint('crypto_api', __name__)
db = firestore.client()

# Global bot instance
crypto_bot_instance = None

@crypto_api.route('/api/crypto/status', methods=['GET'])
def get_crypto_status():
    """Get crypto bot status"""
    user_id = request.args.get('user_id', 'default_user')
    
    try:
        status_doc = db.collection('crypto_bot_status').document(user_id).get()
        
        if not status_doc.exists:
            return jsonify({'error': 'Bot not initialized'}), 404
        
        return jsonify(status_doc.to_dict()), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@crypto_api.route('/api/crypto/start', methods=['POST'])
def start_crypto_bot():
    """Start crypto bot"""
    global crypto_bot_instance
    
    data = request.json
    user_id = data.get('user_id', 'default_user')
    initial_pair = data.get('pair', 'BTC')
    
    try:
        # Get credentials
        creds = CoinDCXCredentials.get_credentials(user_id)
        if not creds:
            return jsonify({'error': 'Credentials not found'}), 404
        
        # Create bot instance
        crypto_bot_instance = CryptoBotEngine(
            user_id=user_id,
            api_key=creds['api_key'],
            api_secret=creds['api_secret'],
            initial_pair=initial_pair
        )
        
        # Start bot in background
        import threading
        running_flag = threading.Event()
        running_flag.set()
        
        def run_bot():
            asyncio.run(crypto_bot_instance.start(running_flag))
        
        thread = threading.Thread(target=run_bot, daemon=True)
        thread.start()
        
        return jsonify({
            'message': 'Crypto bot started',
            'user_id': user_id,
            'pair': initial_pair
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@crypto_api.route('/api/crypto/stop', methods=['POST'])
def stop_crypto_bot():
    """Stop crypto bot"""
    global crypto_bot_instance
    
    data = request.json
    user_id = data.get('user_id', 'default_user')
    
    try:
        if crypto_bot_instance:
            asyncio.run(crypto_bot_instance.stop())
            crypto_bot_instance = None
        
        return jsonify({'message': 'Crypto bot stopped'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@crypto_api.route('/api/crypto/switch-pair', methods=['POST'])
def switch_trading_pair():
    """Switch between BTC and ETH"""
    global crypto_bot_instance
    
    data = request.json
    pair = data.get('pair')  # "BTC" or "ETH"
    
    if not pair or pair not in ['BTC', 'ETH']:
        return jsonify({'error': 'Invalid pair'}), 400
    
    try:
        if not crypto_bot_instance:
            return jsonify({'error': 'Bot not running'}), 400
        
        crypto_bot_instance.switch_pair(pair)
        
        return jsonify({
            'message': f'Switched to {pair}',
            'new_pair': pair
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@crypto_api.route('/api/crypto/credentials', methods=['POST'])
def save_crypto_credentials():
    """Save CoinDCX credentials"""
    data = request.json
    user_id = data.get('user_id', 'default_user')
    api_key = data.get('api_key')
    api_secret = data.get('api_secret')
    
    if not api_key or not api_secret:
        return jsonify({'error': 'Missing credentials'}), 400
    
    try:
        success = CoinDCXCredentials.save_credentials(user_id, api_key, api_secret)
        
        if success:
            return jsonify({'message': 'Credentials saved'}), 200
        else:
            return jsonify({'error': 'Failed to save credentials'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@crypto_api.route('/api/crypto/activity', methods=['GET'])
def get_crypto_activity():
    """Get recent activity feed"""
    user_id = request.args.get('user_id', 'default_user')
    limit = int(request.args.get('limit', 50))
    
    try:
        activities = (
            db.collection('crypto_activity_feed')
            .where('user_id', '==', user_id)
            .order_by('timestamp', direction=firestore.Query.DESCENDING)
            .limit(limit)
            .stream()
        )
        
        activity_list = []
        for activity in activities:
            data = activity.to_dict()
            data['id'] = activity.id
            activity_list.append(data)
        
        return jsonify(activity_list), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

**Status:** ⏳ Need to create this file and register blueprint in main API

---

## 3️⃣ Frontend Components (React)

### **A. Crypto Bot Dashboard** (NEW)

**File:** `src/components/CryptoBotDashboard.jsx`

```jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const CryptoBotDashboard = ({ userId }) => {
  const [status, setStatus] = useState(null);
  const [activity, setActivity] = useState([]);
  const [selectedPair, setSelectedPair] = useState('BTC');

  useEffect(() => {
    fetchStatus();
    fetchActivity();
    
    // Poll status every 5 seconds
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchStatus = async () => {
    try {
      const response = await axios.get(`/api/crypto/status?user_id=${userId}`);
      setStatus(response.data);
    } catch (error) {
      console.error('Error fetching status:', error);
    }
  };

  const fetchActivity = async () => {
    try {
      const response = await axios.get(`/api/crypto/activity?user_id=${userId}&limit=20`);
      setActivity(response.data);
    } catch (error) {
      console.error('Error fetching activity:', error);
    }
  };

  const handleStart = async () => {
    try {
      await axios.post('/api/crypto/start', { user_id: userId, pair: selectedPair });
      alert('Crypto bot started!');
      fetchStatus();
    } catch (error) {
      alert('Failed to start bot: ' + error.message);
    }
  };

  const handleStop = async () => {
    try {
      await axios.post('/api/crypto/stop', { user_id: userId });
      alert('Crypto bot stopped!');
      fetchStatus();
    } catch (error) {
      alert('Failed to stop bot: ' + error.message);
    }
  };

  const handleSwitchPair = async (pair) => {
    try {
      await axios.post('/api/crypto/switch-pair', { pair });
      setSelectedPair(pair);
      alert(`Switched to ${pair}!`);
      fetchStatus();
    } catch (error) {
      alert('Failed to switch pair: ' + error.message);
    }
  };

  if (!status) {
    return <div>Loading...</div>;
  }

  return (
    <div className="crypto-bot-dashboard">
      <h2>🚀 Crypto Trading Bot (24/7)</h2>
      
      {/* Status Card */}
      <div className="status-card">
        <h3>Status</h3>
        <p>Status: {status.is_running ? '🟢 Running' : '🔴 Stopped'}</p>
        <p>Active Pair: {status.active_pair}</p>
        <p>Open Positions: {status.open_positions}</p>
        <p>Today's Trades: {status.total_trades_today}</p>
        <p>Daily P&L: ${status.daily_pnl?.toFixed(2)}</p>
        <p>WebSocket: {status.websocket_connected ? '🟢 Connected' : '🔴 Disconnected'}</p>
      </div>

      {/* Controls */}
      <div className="controls">
        <button onClick={handleStart} disabled={status.is_running}>
          ▶️ Start Bot
        </button>
        <button onClick={handleStop} disabled={!status.is_running}>
          ⏸️ Stop Bot
        </button>
      </div>

      {/* Pair Switcher */}
      <div className="pair-switcher">
        <h3>Trading Pair</h3>
        <button 
          onClick={() => handleSwitchPair('BTC')}
          className={status.active_pair === 'BTC' ? 'active' : ''}
          disabled={!status.is_running}
        >
          ₿ Bitcoin
        </button>
        <button 
          onClick={() => handleSwitchPair('ETH')}
          className={status.active_pair === 'ETH' ? 'active' : ''}
          disabled={!status.is_running}
        >
          Ξ Ethereum
        </button>
      </div>

      {/* Activity Feed */}
      <div className="activity-feed">
        <h3>Recent Activity</h3>
        {activity.map((item) => (
          <div key={item.id} className="activity-item">
            <span className="timestamp">{new Date(item.timestamp).toLocaleString()}</span>
            <span className="message">{item.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CryptoBotDashboard;
```

**Status:** ⏳ Need to create this component

---

### **B. Dual Bot View** (Combined Dashboard)

```jsx
<div className="dual-bot-dashboard">
  <div className="stock-bot-panel">
    <StockBotDashboard userId={userId} />
  </div>
  
  <div className="crypto-bot-panel">
    <CryptoBotDashboard userId={userId} />
  </div>
</div>
```

---

## 4️⃣ Cloud Run Deployment

### **Update:** `apphosting.yaml` or `cloudbuild.yaml`

Add crypto bot dependencies and ensure it starts:

```yaml
runtime: python39
entrypoint: gunicorn -b :$PORT main:app --workers 2 --threads 8 --timeout 0

env_variables:
  CREDENTIALS_ENCRYPTION_KEY: "your-encryption-key-here"
```

---

## ✅ Step-by-Step Integration Checklist

### **Phase 1: Database Setup** (5 minutes)
- [ ] Run `python initialize_crypto_bot_firestore.py`
- [ ] Enter your CoinDCX API key and secret
- [ ] Verify collections in Firebase Console

### **Phase 2: Local Testing** (1-2 hours)
- [ ] Test bot locally: `python start_crypto_bot_locally.py --user default_user --pair BTC`
- [ ] Verify signals appear in logs
- [ ] Check Firestore for activity updates
- [ ] Test BTC → ETH switching

### **Phase 3: Backend API** (30 minutes)
- [ ] Create `api/crypto_bot_api.py` (code above)
- [ ] Register blueprint in `main.py`:
  ```python
  from api.crypto_bot_api import crypto_api
  app.register_blueprint(crypto_api)
  ```
- [ ] Test endpoints with Postman/curl

### **Phase 4: Frontend** (1-2 hours)
- [ ] Create `CryptoBotDashboard.jsx` component
- [ ] Add to main app navigation
- [ ] Test start/stop/switch functionality
- [ ] Style to match existing UI

### **Phase 5: Production Deploy** (30 minutes)
- [ ] Deploy to Cloud Run
- [ ] Test API endpoints from frontend
- [ ] Monitor logs
- [ ] Verify bot stays running

---

## 🚀 Quick Start (Right Now!)

1. **Initialize Firestore:**
```powershell
cd "d:\Tushar 2.0\tbsignalstream_backup\tbsignalstream_backup"
python initialize_crypto_bot_firestore.py
```

2. **Enter your CoinDCX API credentials** when prompted

3. **Test locally:**
```powershell
python start_crypto_bot_locally.py --user default_user --pair BTC
```

4. **Watch it work!** You'll see signals, entries, exits in real-time

---

**Ready to initialize?** Run the script now! 🎯
