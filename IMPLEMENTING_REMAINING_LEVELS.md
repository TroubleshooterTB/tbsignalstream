# Implementing Remaining Levels 22 & 23

## 📋 **Current Status**

- ✅ **21/24 levels active** (87.5% complete)
- ⏳ **2 levels remaining**: Level 22 (TICK) and Level 23 (ML)
- 🔄 Both have placeholder implementations that return `True` (pass)

---

## 🎯 **LEVEL 22: TICK Indicator (Market Flow)**

### **What It Does:**
The TICK indicator measures market breadth - how many stocks are advancing vs. declining. It confirms whether the overall market flow supports your trade direction.

### **Why It's Important:**
- Prevents trading against market internals
- Example: NIFTY shows bullish candles but TICK is negative (more stocks declining) = distribution by smart money
- Reduces false signals during market-wide reversals

---

### **OPTION 1: Use NIFTY Advance/Decline Data (RECOMMENDED)**

**Pros:**
- ✅ Data already available from Angel One API
- ✅ No additional data source needed
- ✅ Specific to Indian markets (more relevant than NYSE TICK)

**Implementation:**

```python
def get_nifty_advance_decline(self, api_client) -> Dict:
    """
    Get advance/decline data for NIFTY 50 stocks
    
    Returns:
        {
            'advancing': int,  # Number of stocks advancing
            'declining': int,  # Number of stocks declining
            'unchanged': int,  # Number of stocks unchanged
            'tick_ratio': float,  # (Advancing - Declining) / Total
            'tick_signal': str  # 'BULLISH', 'BEARISH', 'NEUTRAL'
        }
    """
    from src.lib.angel_one_api import NIFTY_50_SYMBOLS
    
    advancing = 0
    declining = 0
    unchanged = 0
    
    # Get current prices for all NIFTY 50 stocks
    for symbol in NIFTY_50_SYMBOLS:
        try:
            # Get today's open and current price
            ltp_data = api_client.get_ltp_data('NSE', symbol)
            current_price = ltp_data.get('ltp', 0)
            open_price = ltp_data.get('open', current_price)
            
            if current_price > open_price:
                advancing += 1
            elif current_price < open_price:
                declining += 1
            else:
                unchanged += 1
        except:
            continue
    
    total = advancing + declining + unchanged
    tick_ratio = (advancing - declining) / total if total > 0 else 0
    
    # Determine signal
    if tick_ratio > 0.3:  # 30% more advancing than declining
        tick_signal = 'BULLISH'
    elif tick_ratio < -0.3:
        tick_signal = 'BEARISH'
    else:
        tick_signal = 'NEUTRAL'
    
    return {
        'advancing': advancing,
        'declining': declining,
        'unchanged': unchanged,
        'tick_ratio': tick_ratio,
        'tick_signal': tick_signal
    }
```

**Integration into Advanced Screening:**

Replace the placeholder in `advanced_screening_manager.py`:

```python
def _check_tick_indicator(self, is_long: bool) -> Tuple[bool, str]:
    """
    Level 22: TICK Indicator (Market Flow)
    
    Uses NIFTY 50 advance/decline ratio as market breadth indicator.
    """
    try:
        # Get advance/decline data (you'll need to pass this in from bot)
        # For now, we'll fetch it directly
        tick_data = self._get_nifty_advance_decline()
        
        tick_signal = tick_data.get('tick_signal', 'NEUTRAL')
        tick_ratio = tick_data.get('tick_ratio', 0)
        advancing = tick_data.get('advancing', 0)
        declining = tick_data.get('declining', 0)
        
        if is_long:
            # For long trades, we want bullish market internals
            if tick_signal == 'BEARISH':
                return False, (f"Market internals bearish: {declining} declining vs "
                              f"{advancing} advancing (ratio: {tick_ratio:.2f})")
            
            if tick_signal == 'NEUTRAL' and tick_ratio < 0:
                return False, f"Weak market internals for long: ratio {tick_ratio:.2f}"
            
            return True, f"Market internals support long: {advancing} advancing ({tick_ratio:.2%})"
        
        else:  # SELL
            if tick_signal == 'BULLISH':
                return False, (f"Market internals bullish: {advancing} advancing vs "
                              f"{declining} declining (ratio: {tick_ratio:.2f})")
            
            if tick_signal == 'NEUTRAL' and tick_ratio > 0:
                return False, f"Weak market internals for short: ratio {tick_ratio:.2f}"
            
            return True, f"Market internals support short: {declining} declining ({tick_ratio:.2%})"
        
    except Exception as e:
        logger.error(f"Error in TICK indicator check: {e}")
        return True, f"TICK check error (passed): {str(e)}"

def _get_nifty_advance_decline(self) -> Dict:
    """Cache TICK data to avoid multiple API calls per screening cycle"""
    # TODO: Implement caching mechanism
    # For now, return cached value if available
    if hasattr(self, '_cached_tick_data'):
        cache_time = getattr(self, '_tick_cache_time', datetime.min)
        if (datetime.now() - cache_time).seconds < 60:  # Cache for 60 seconds
            return self._cached_tick_data
    
    # Fetch fresh data
    tick_data = self.get_nifty_advance_decline(self.api_client)
    self._cached_tick_data = tick_data
    self._tick_cache_time = datetime.now()
    
    return tick_data
```

**To Enable:**

In `realtime_bot_engine.py`, modify initialization:

```python
def _initialize_managers(self):
    # ... existing code ...
    
    screening_config = AdvancedScreeningConfig()
    screening_config.fail_safe_mode = True
    screening_config.enable_tick_indicator = True  # ENABLE TICK
    
    self._advanced_screening = AdvancedScreeningManager(
        config=screening_config,
        portfolio_value=100000.0
    )
    # Pass API client for TICK data
    self._advanced_screening.api_client = self._order_manager  # Has API access
```

**Estimated Implementation Time:** 2-3 hours

---

### **OPTION 2: Use NSE India Market Breadth API**

**Pros:**
- Official NSE data
- More comprehensive (all NSE stocks, not just NIFTY 50)

**Cons:**
- Requires separate API integration
- May have rate limits
- Additional complexity

**API Endpoint:**
```
https://www.nseindia.com/api/market-data-pre-open?key=NIFTY
```

**Not recommended** - Option 1 is simpler and equally effective.

---

## 🤖 **LEVEL 23: ML Prediction Filter**

### **What It Does:**
Uses a trained machine learning model to predict trade success probability. Only allows trades that the ML model agrees with.

### **Why It's Important:**
- Filters out historically low-probability setups
- Learns from actual trade outcomes
- Improves signal quality over time

---

### **IMPLEMENTATION ROADMAP**

#### **PHASE 1: Data Collection (1-2 weeks)**

**Step 1: Create Trade History Logger**

Create file: `trading_bot_service/ml_data_logger.py`

```python
"""
ML Data Logger - Collects historical trade data for model training
"""

import logging
import pandas as pd
from datetime import datetime
from typing import Dict
import firebase_admin
from firebase_admin import firestore

logger = logging.getLogger(__name__)


class MLDataLogger:
    """
    Logs every trade signal (taken or not) with features and outcomes
    for ML model training.
    """
    
    def __init__(self, db_client):
        self.db = db_client
        logger.info("MLDataLogger initialized")
    
    def log_signal(self, signal_data: Dict):
        """
        Log a trading signal with all features.
        
        signal_data should contain:
        - symbol, timestamp, action (BUY/SELL)
        - entry_price, stop_loss, target
        - all technical indicators (RSI, MACD, ADX, etc.)
        - pattern details
        - confidence scores
        - was_taken (True/False)
        """
        try:
            doc_ref = self.db.collection('ml_training_data').document()
            signal_data['logged_at'] = datetime.now()
            signal_data['outcome'] = None  # Will be updated later
            signal_data['pnl'] = None
            signal_data['exit_price'] = None
            signal_data['exit_time'] = None
            
            doc_ref.set(signal_data)
            logger.debug(f"Logged signal: {signal_data['symbol']} {signal_data['action']}")
            
            return doc_ref.id
            
        except Exception as e:
            logger.error(f"Error logging signal: {e}")
            return None
    
    def update_outcome(self, signal_id: str, outcome_data: Dict):
        """
        Update signal with actual outcome after trade completes.
        
        outcome_data should contain:
        - outcome: 'WIN', 'LOSS', 'BREAKEVEN'
        - exit_price, exit_time
        - pnl (profit/loss amount)
        - pnl_percent
        - holding_duration (minutes)
        """
        try:
            doc_ref = self.db.collection('ml_training_data').document(signal_id)
            doc_ref.update(outcome_data)
            logger.info(f"Updated outcome for signal {signal_id}: {outcome_data['outcome']}")
            
        except Exception as e:
            logger.error(f"Error updating outcome: {e}")
    
    def get_training_data(self, min_samples: int = 100) -> pd.DataFrame:
        """
        Retrieve all completed trades for model training.
        
        Returns DataFrame with features and outcomes.
        """
        try:
            # Query Firestore for completed signals
            signals = self.db.collection('ml_training_data').where('outcome', '!=', None).stream()
            
            data = []
            for doc in signals:
                data.append(doc.to_dict())
            
            if len(data) < min_samples:
                logger.warning(f"Only {len(data)} samples available, need {min_samples} for training")
                return pd.DataFrame()
            
            df = pd.DataFrame(data)
            logger.info(f"Retrieved {len(df)} training samples")
            return df
            
        except Exception as e:
            logger.error(f"Error retrieving training data: {e}")
            return pd.DataFrame()
```

**Integration:**

In `realtime_bot_engine.py`:

```python
def _initialize_managers(self):
    # ... existing code ...
    from ml_data_logger import MLDataLogger
    
    self._ml_logger = MLDataLogger(self.db)  # Pass Firestore client

def _place_entry_order(self, symbol, direction, entry_price, stop_loss, target, quantity, reason):
    # ... existing order placement code ...
    
    # NEW: Log this signal for ML training
    signal_data = {
        'symbol': symbol,
        'action': 'BUY' if direction == 'up' else 'SELL',
        'entry_price': entry_price,
        'stop_loss': stop_loss,
        'target': target,
        'quantity': quantity,
        'timestamp': datetime.now(),
        'was_taken': True,
        # Add all technical indicators from df
        'rsi': df['rsi'].iloc[-1] if 'rsi' in df else None,
        'macd': df['macd'].iloc[-1] if 'macd' in df else None,
        'adx': df['adx'].iloc[-1] if 'adx' in df else None,
        'bb_width': df['bb_width'].iloc[-1] if 'bb_width' in df else None,
        'volume_ratio': df['volume'].iloc[-1] / df['volume_sma'].iloc[-1],
        # ... add more features
        'reason': reason,
    }
    
    signal_id = self._ml_logger.log_signal(signal_data)
    # Store signal_id with position for later outcome update
    position_data['ml_signal_id'] = signal_id

def _close_position(self, symbol, position, exit_price, reason):
    # ... existing close logic ...
    
    # NEW: Update ML data with outcome
    if 'ml_signal_id' in position:
        pnl = (exit_price - position['entry_price']) * position['quantity']
        pnl_percent = ((exit_price - position['entry_price']) / position['entry_price']) * 100
        
        outcome_data = {
            'outcome': 'WIN' if pnl > 0 else ('LOSS' if pnl < 0 else 'BREAKEVEN'),
            'exit_price': exit_price,
            'exit_time': datetime.now(),
            'pnl': pnl,
            'pnl_percent': pnl_percent,
            'holding_duration': (datetime.now() - position['entry_time']).seconds / 60,
            'exit_reason': reason
        }
        
        self._ml_logger.update_outcome(position['ml_signal_id'], outcome_data)
```

**Time Required:** 1-2 weeks of live trading to collect 100-200 samples

---

#### **PHASE 2: Model Training (Once you have data)**

Create file: `trading_bot_service/ml_model_trainer.py`

```python
"""
ML Model Trainer - Trains Random Forest model on historical trade data
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
import pickle
import logging

logger = logging.getLogger(__name__)


class MLModelTrainer:
    """
    Trains a Random Forest model to predict trade success probability.
    """
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = None
    
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Engineer features from raw trade data.
        """
        features = pd.DataFrame()
        
        # Technical indicators
        features['rsi'] = df['rsi']
        features['macd'] = df['macd']
        features['adx'] = df['adx']
        features['bb_width'] = df['bb_width']
        features['volume_ratio'] = df['volume_ratio']
        
        # Price action features
        features['risk_reward_ratio'] = abs(df['target'] - df['entry_price']) / abs(df['entry_price'] - df['stop_loss'])
        features['stop_distance_pct'] = abs(df['entry_price'] - df['stop_loss']) / df['entry_price'] * 100
        
        # Time features
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        features['hour'] = df['timestamp'].dt.hour
        features['day_of_week'] = df['timestamp'].dt.dayofweek
        
        # Pattern features (one-hot encode)
        if 'pattern_name' in df:
            pattern_dummies = pd.get_dummies(df['pattern_name'], prefix='pattern')
            features = pd.concat([features, pattern_dummies], axis=1)
        
        # Action (BUY=1, SELL=0)
        features['is_long'] = (df['action'] == 'BUY').astype(int)
        
        # Drop NaN rows
        features = features.fillna(0)
        
        self.feature_columns = features.columns.tolist()
        logger.info(f"Prepared {len(features)} samples with {len(self.feature_columns)} features")
        
        return features
    
    def train(self, df: pd.DataFrame):
        """
        Train the model on historical data.
        
        Args:
            df: DataFrame with trade data including 'outcome' column
        """
        if len(df) < 50:
            raise ValueError(f"Insufficient data: {len(df)} samples (need at least 50)")
        
        # Prepare features
        X = self.prepare_features(df)
        
        # Target: WIN = 1, LOSS/BREAKEVEN = 0
        y = (df['outcome'] == 'WIN').astype(int)
        
        logger.info(f"Training on {len(X)} samples | Win rate: {y.mean():.2%}")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train Random Forest
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            class_weight='balanced'  # Handle imbalanced data
        )
        
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        train_score = self.model.score(X_train_scaled, y_train)
        test_score = self.model.score(X_test_scaled, y_test)
        cv_scores = cross_val_score(self.model, X_train_scaled, y_train, cv=5)
        
        logger.info(f"Training accuracy: {train_score:.2%}")
        logger.info(f"Test accuracy: {test_score:.2%}")
        logger.info(f"Cross-validation: {cv_scores.mean():.2%} (+/- {cv_scores.std():.2%})")
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        logger.info(f"Top 5 features:\n{feature_importance.head()}")
        
        return {
            'train_score': train_score,
            'test_score': test_score,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'feature_importance': feature_importance
        }
    
    def predict_probability(self, signal_data: Dict) -> float:
        """
        Predict success probability for a new signal.
        
        Returns:
            Probability between 0 and 1
        """
        if self.model is None:
            raise ValueError("Model not trained yet")
        
        # Convert signal to DataFrame
        df = pd.DataFrame([signal_data])
        
        # Prepare features
        X = self.prepare_features(df)
        
        # Ensure all expected columns are present
        for col in self.feature_columns:
            if col not in X.columns:
                X[col] = 0
        
        X = X[self.feature_columns]  # Ensure correct order
        
        # Scale and predict
        X_scaled = self.scaler.transform(X)
        prob = self.model.predict_proba(X_scaled)[0][1]  # Probability of WIN
        
        return prob
    
    def save_model(self, filepath: str):
        """Save trained model to disk"""
        if self.model is None:
            raise ValueError("No model to save")
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_columns': self.feature_columns
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load trained model from disk"""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_columns = model_data['feature_columns']
        
        logger.info(f"Model loaded from {filepath}")
```

**Training Script** (run manually after collecting data):

```python
# train_ml_model.py
from ml_data_logger import MLDataLogger
from ml_model_trainer import MLModelTrainer
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
cred = credentials.Certificate('path/to/serviceAccountKey.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

# Get training data
logger = MLDataLogger(db)
df = logger.get_training_data(min_samples=100)

if df.empty:
    print("Not enough training data yet. Keep trading!")
else:
    # Train model
    trainer = MLModelTrainer()
    results = trainer.train(df)
    
    print(f"Model trained successfully!")
    print(f"Test accuracy: {results['test_score']:.2%}")
    
    # Save model
    trainer.save_model('trading_bot_service/ml_model.pkl')
    print("Model saved!")
```

---

#### **PHASE 3: Integration into Screening**

Update `advanced_screening_manager.py`:

```python
def __init__(self, config: Optional[AdvancedScreeningConfig] = None, 
             portfolio_value: float = 1000000.0):
    # ... existing code ...
    
    # ML model
    self.ml_model = None
    self._load_ml_model()  # Load if available

def _load_ml_model(self):
    """Load trained ML model if available"""
    try:
        from ml_model_trainer import MLModelTrainer
        import os
        
        model_path = 'ml_model.pkl'
        if os.path.exists(model_path):
            trainer = MLModelTrainer()
            trainer.load_model(model_path)
            self.ml_model = trainer
            logger.info("✅ ML model loaded successfully")
        else:
            logger.info("ML model not found - will skip ML filtering")
    except Exception as e:
        logger.error(f"Error loading ML model: {e}")
        self.ml_model = None

def _check_ml_prediction(self, symbol: str, df: pd.DataFrame, 
                        signal_data: Dict, is_long: bool) -> Tuple[bool, str]:
    """
    Level 23: ML Prediction Filter
    
    Uses trained Random Forest model to predict trade success probability.
    """
    try:
        if self.ml_model is None:
            return True, "ML model not available (passed)"
        
        # Prepare signal data for prediction
        prediction_data = {
            'symbol': symbol,
            'action': 'BUY' if is_long else 'SELL',
            'entry_price': signal_data.get('entry_price'),
            'stop_loss': signal_data.get('stop_loss'),
            'target': signal_data.get('target'),
            'timestamp': datetime.now(),
            # Add technical indicators from DataFrame
            'rsi': df['rsi'].iloc[-1] if 'rsi' in df.columns else 50,
            'macd': df['macd'].iloc[-1] if 'macd' in df.columns else 0,
            'adx': df['adx'].iloc[-1] if 'adx' in df.columns else 20,
            'bb_width': df['bb_width'].iloc[-1] if 'bb_width' in df.columns else 0,
            'volume_ratio': df['volume'].iloc[-1] / df['volume_sma'].iloc[-1] if 'volume_sma' in df.columns else 1,
            'pattern_name': signal_data.get('pattern_name', 'Unknown'),
        }
        
        # Get probability prediction
        win_probability = self.ml_model.predict_probability(prediction_data)
        
        # Threshold: Only allow trades with >50% predicted success
        min_probability = 0.50  # Can be adjusted
        
        if win_probability < min_probability:
            return False, f"ML model predicts low success: {win_probability:.1%} < {min_probability:.1%}"
        
        logger.info(f"✅ ML prediction favorable: {win_probability:.1%} success probability")
        return True, f"ML model confident: {win_probability:.1%} success probability"
        
    except Exception as e:
        logger.error(f"Error in ML prediction: {e}")
        return True, f"ML prediction error (passed): {str(e)}"
```

**Enable in Config:**

```python
screening_config.enable_ml_filter = True  # After model is trained and loaded
```

---

## 📊 **IMPLEMENTATION TIMELINE**

### **Quick Implementation (This Week):**

**Level 22 (TICK):**
- ✅ Can implement TODAY using NIFTY 50 advance/decline
- ✅ Implementation time: 2-3 hours
- ✅ No external dependencies
- ✅ Immediate value

**Recommended**: Implement TICK now!

### **Long-term Implementation (2-4 weeks):**

**Level 23 (ML):**
- Week 1: Implement data logging (2-3 hours)
- Week 2-3: Collect data (100+ trades needed)
- Week 4: Train model & integrate (4-5 hours)

**Recommended**: Start data collection now, enable model in 3-4 weeks

---

## 🚀 **RECOMMENDED APPROACH**

### **Phase 1 (TODAY):**
1. Implement Level 22 (TICK with NIFTY advance/decline)
2. Enable in config
3. Deploy and test

### **Phase 2 (START IMMEDIATELY):**
1. Implement ML data logging
2. Deploy and start collecting data
3. Log every signal (taken or not)

### **Phase 3 (IN 3-4 WEEKS):**
1. Extract training data (should have 100+ samples)
2. Train Random Forest model
3. Evaluate performance
4. Deploy model and enable Level 23

---

## ✅ **ACTION ITEMS FOR YOU**

**To implement Level 22 (TICK) now:**
1. I can provide the complete code
2. You just need to deploy

**To implement Level 23 (ML) properly:**
1. I'll create the ML data logger code
2. You deploy it and let it collect data for 2-3 weeks
3. Then we train the model

**Would you like me to:**
- [ ] Implement Level 22 (TICK) now? (2-3 hours work)
- [ ] Implement ML data logging now? (start collecting data)
- [ ] Both?

Let me know and I'll proceed with the implementation!
