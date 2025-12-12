"""
Real-Time Trading Bot Engine with WebSocket Integration
Implements sub-second position monitoring and instant order execution
"""

import logging
import time
import threading
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Callable, Optional
import pandas as pd
import numpy as np
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class RealtimeBotEngine:
    """
    Production-grade trading engine with real-time WebSocket data streaming.
    
    Features:
    - WebSocket v2 integration for tick-by-tick data (sub-second updates)
    - Separate monitoring thread for instant stop loss/target detection
    - Async token fetching for fast initialization
    - Continuous candle building from tick data
    - Independent position monitoring (runs every 0.5 seconds)
    """
    
    def __init__(self, user_id: str, credentials: dict, symbols: list, 
                 trading_mode: str = 'paper', strategy: str = 'pattern', db_client=None):
        self.user_id = user_id
        self.credentials = credentials
        self.symbols = symbols
        self.trading_mode = trading_mode.lower()
        self.strategy = strategy.lower()
        self.db = db_client  # Firestore client for Activity Logger and ML Logger
        
        # Extract credentials
        self.jwt_token = credentials.get('jwt_token', '')
        self.feed_token = credentials.get('feed_token', '')
        self.client_code = credentials.get('client_code', '')
        self.api_key = credentials.get('api_key', '')
        
        # Detailed credential validation
        missing = []
        if not self.jwt_token:
            missing.append('jwt_token')
        if not self.feed_token:
            missing.append('feed_token')
        if not self.client_code:
            missing.append('client_code')
        if not self.api_key:
            missing.append('api_key')
        
        if missing:
            error_msg = f"Missing credentials: {', '.join(missing)}. Please reconnect Angel One account."
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        self.base_url = "https://apiconnect.angelone.in"
        
        # WebSocket manager
        self.ws_manager = None
        
        # Real-time data storage (thread-safe)
        self._lock = threading.RLock()
        self.tick_data = defaultdict(lambda: deque(maxlen=1000))  # Last 1000 ticks per symbol
        self.candle_data = {}  # Current candle data
        self.latest_prices = {}  # Latest LTP per symbol
        self.symbol_tokens = {}  # Token mapping
        
        # Trading managers (initialized on first use)
        self._pattern_detector = None
        self._execution_manager = None
        self._order_manager = None
        self._risk_manager = None
        self._position_manager = None
        self._ironclad = None
        self._advanced_screening = None  # NEW: Universal 24-level screening layer
        self._ml_logger = None  # NEW: ML data logging for model training
        self._activity_logger = None  # NEW: Real-time activity logging for dashboard
        
        # Control flags
        self.is_running = False
        self._monitoring_thread = None
        self._candle_builder_thread = None
        self.bot_start_time = datetime.now()
        
        logger.info(f"RealtimeBotEngine initialized for {user_id}")
        logger.info(f"Mode: {trading_mode.upper()}, Strategy: {strategy.upper()}")
    
    def start(self, running_flag: Callable[[], bool]):
        """
        Start the real-time trading bot.
        
        Args:
            running_flag: Callable that returns True while bot should keep running
        """
        try:
            self.is_running = True
            
            # Step 1: Initialize symbol tokens (parallel fetch) - WITH ERROR HANDLING
            logger.info("Fetching symbol tokens...")
            try:
                self.symbol_tokens = self._get_symbol_tokens_parallel()
                if not self.symbol_tokens:
                    logger.warning("No symbol tokens fetched, will retry with fallback method")
                    # Fallback: use hardcoded tokens for critical symbols
                    self.symbol_tokens = self._get_fallback_tokens()
                
                logger.info(f"✅ Fetched tokens for {len(self.symbol_tokens)} symbols")
            except Exception as e:
                logger.error(f"Error fetching tokens: {e}")
                # Use fallback tokens instead of failing
                logger.info("Using fallback symbol tokens...")
                self.symbol_tokens = self._get_fallback_tokens()
                if not self.symbol_tokens:
                    raise Exception("Failed to fetch any symbol tokens, cannot continue")
            
            # Step 2: Initialize trading managers
            logger.info("🔧 [DEBUG] Initializing trading managers...")
            self._initialize_managers()
            logger.info("✅ [DEBUG] Trading managers initialized successfully")
            
            # Step 3: Initialize WebSocket connection - WITH ERROR HANDLING
            logger.info("🔌 [DEBUG] Initializing WebSocket connection...")
            try:
                logger.info("🔌 [DEBUG] About to call _initialize_websocket()...")
                self._initialize_websocket()
                logger.info("✅ [DEBUG] WebSocket initialized and connected")
                # NOTE: We'll verify data flow AFTER subscribing to symbols (Step 5)
                    
            except Exception as e:
                logger.error(f"❌ [DEBUG] WebSocket initialization failed: {e}", exc_info=True)
                logger.warning("⚠️  [DEBUG] Bot will continue with polling mode (no real-time ticks)")
                logger.warning("⚠️  Position monitoring will NOT work without WebSocket")
                self.ws_manager = None  # Bot will run without WebSocket
            
            # CRITICAL: Fail fast if WebSocket didn't connect in live mode
            if self.trading_mode == 'live' and (not self.ws_manager or not hasattr(self.ws_manager, 'is_connected') or not getattr(self.ws_manager, 'is_connected', False)):
                raise Exception("CRITICAL: WebSocket connection failed - cannot trade live without real-time data")
            
            # Step 4: Bootstrap historical candle data (CRITICAL FIX)
            # Without this, bot needs 200 minutes to accumulate candles for indicators!
            logger.info("📊 [CRITICAL] Bootstrapping historical candle data...")
            logger.info("📊 [CRITICAL] About to call _bootstrap_historical_candles()...")
            try:
                logger.info("📊 [CRITICAL] Calling bootstrap function NOW...")
                self._bootstrap_historical_candles()
                logger.info("✅ [CRITICAL] Historical candles loaded - bot ready to trade immediately!")
            except Exception as e:
                logger.error(f"❌ [CRITICAL] Failed to bootstrap historical data: {e}", exc_info=True)
                logger.error(f"❌ [CRITICAL] Error type: {type(e).__name__}")
                logger.error(f"❌ [CRITICAL] Error details: {str(e)}")
                logger.warning("⚠️  Bot will need 200+ minutes to build candles from ticks")
                # Fail fast if bootstrap completely failed
                if len(self.candle_data) == 0:
                    raise Exception("CRITICAL: Bootstrap failed - cannot analyze without historical candles")
            
            # Step 5: Subscribe to symbols (only if WebSocket is active)
            if self.ws_manager:
                try:
                    self._subscribe_to_symbols()
                    logger.info("✅ Subscribed to symbols")
                    
                    # CRITICAL: Wait 3 seconds for price data to start flowing after subscription
                    logger.info("⏳ Waiting 3 seconds for WebSocket price data to arrive...")
                    time.sleep(3)
                    
                    with self._lock:
                        num_prices = len(self.latest_prices)
                    logger.info(f"✅ After subscription wait: {num_prices} symbols have prices")
                    
                except Exception as e:
                    logger.error(f"Symbol subscription failed: {e}")
                    logger.warning("Bot will continue without real-time subscriptions")
            
            # Step 6: Start position monitoring thread (runs every 0.5 seconds)
            logger.info("Starting position monitoring thread...")
            self._monitoring_thread = threading.Thread(
                target=self._continuous_position_monitoring,
                daemon=True
            )
            self._monitoring_thread.start()
            
            # Step 7: Start candle builder thread (builds 1-min candles from ticks)
            logger.info("Starting candle builder thread...")
            self._candle_builder_thread = threading.Thread(
                target=self._continuous_candle_building,
                daemon=True
            )
            self._candle_builder_thread.start()
            
            # Step 8: Final verification before trading
            logger.info("🔍 Running final pre-trade verification...")
            try:
                self._verify_ready_to_trade()
            except Exception as e:
                logger.error(f"❌ Pre-trade verification failed: {e}")
                raise
            
            # Step 9: Main strategy execution loop (runs every 5 seconds)
            logger.info("🚀 Real-time trading bot started successfully!")
            logger.info("Position monitoring: Every 0.5 seconds")
            logger.info("Strategy analysis: Every 5 seconds")
            logger.info(f"Data updates: {'Real-time via WebSocket' if self.ws_manager else 'Polling mode'}")
            
            error_count = 0
            max_consecutive_errors = 10  # Stop only after 10 consecutive errors
            
            while running_flag() and self.is_running:
                try:
                    # 🚨 EMERGENCY STOP: Check Firestore flag for instant shutdown
                    try:
                        import firebase_admin
                        from firebase_admin import firestore
                        db = firestore.client()
                        bot_config = db.collection('bot_configs').document(self.user_id).get()
                        if bot_config.exists and bot_config.to_dict().get('emergency_stop', False):
                            logger.critical("🚨 EMERGENCY STOP ACTIVATED - Shutting down bot immediately")
                            self.is_running = False
                            break
                    except Exception as stop_check_err:
                        logger.debug(f"Emergency stop check error (non-critical): {stop_check_err}")
                    
                    cycle_start = time.time()
                    
                    # Execute strategy analysis (every 5 seconds)
                    self._analyze_and_trade()
                    
                    # Reset error count on successful iteration
                    error_count = 0
                    
                    # Sleep for 5 seconds (strategy doesn't need to run faster)
                    # Positions are monitored independently every 0.5 seconds
                    elapsed = time.time() - cycle_start
                    sleep_time = max(0, 5 - elapsed)
                    time.sleep(sleep_time)
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error in main loop (error #{error_count}): {e}", exc_info=True)
                    
                    if error_count >= max_consecutive_errors:
                        logger.critical(f"Too many consecutive errors ({error_count}), stopping bot")
                        break
                    
                    # Wait before retrying (exponential backoff)
                    wait_time = min(30, 2 ** min(error_count, 5))  # Max 30 seconds
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
            
            logger.info("Trading bot stopped")
            
        except Exception as e:
            logger.error(f"Fatal error in bot initialization: {e}", exc_info=True)
            # Don't raise - allow graceful shutdown
        finally:
            self.stop()
    
    def stop(self):
        """Gracefully stop the bot and cleanup resources"""
        logger.info("Stopping trading bot...")
        self.is_running = False
        
        # Close WebSocket
        if self.ws_manager:
            try:
                self.ws_manager.close()
            except:
                pass
        
        # Wait for threads
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=2)
        
        if self._candle_builder_thread and self._candle_builder_thread.is_alive():
            self._candle_builder_thread.join(timeout=2)
        
        logger.info("✅ Bot stopped successfully")
    
    def _initialize_websocket(self):
        """Initialize WebSocket v2 connection"""
        try:
            # Import WebSocket manager from ws_manager module (renamed to avoid conflict)
            from ws_manager.websocket_manager_v2 import AngelWebSocketV2Manager
            
            # Create WebSocket manager
            self.ws_manager = AngelWebSocketV2Manager(
                api_key=self.api_key,
                client_code=self.client_code,
                feed_token=self.feed_token,
                jwt_token=self.jwt_token
            )
            
            # Register tick callback
            self.ws_manager.add_tick_callback(self._on_tick)
            
            # Connect
            self.ws_manager.connect()
            logger.info("✅ WebSocket connected successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize WebSocket: {e}", exc_info=True)
            raise
    
    def _subscribe_to_symbols(self):
        """Subscribe to all symbols via WebSocket"""
        try:
            # Skip if no symbols to subscribe
            if not self.symbol_tokens:
                logger.warning("⚠️  No symbols to subscribe - skipping WebSocket subscription")
                return
            
            # Group tokens by exchange
            exchange_tokens = defaultdict(list)
            
            for symbol, token_info in self.symbol_tokens.items():
                exchange_type = self._get_exchange_type(token_info['exchange'])
                exchange_tokens[exchange_type].append(token_info['token'])
            
            # Build subscription list
            subscription_data = []
            for exchange_type, tokens in exchange_tokens.items():
                subscription_data.append({
                    "exchangeType": exchange_type,
                    "tokens": tokens
                })
            
            # Subscribe with LTP mode (fastest, 51 bytes per tick)
            mode = 1  # LTP mode
            self.ws_manager.subscribe(mode, subscription_data)
            
            logger.info(f"✅ Subscribed to {len(self.symbol_tokens)} symbols via WebSocket")
            
        except Exception as e:
            logger.error(f"Failed to subscribe: {e}", exc_info=True)
            raise
    
    def _get_exchange_type(self, exchange: str) -> int:
        """Convert exchange string to WebSocket exchange type"""
        mapping = {
            'NSE': 1,  # NSE_CM
            'NFO': 2,  # NSE_FO
            'BSE': 3,  # BSE_CM
            'BFO': 4,  # BSE_FO
            'MCX': 5,  # MCX_FO
        }
        return mapping.get(exchange, 1)  # Default to NSE
    
    def _on_tick(self, tick_data: Dict):
        """
        Callback for WebSocket tick data (called for EVERY price update).
        This runs in real-time (sub-second frequency).
        """
        try:
            # Extract data from tick
            token = str(tick_data.get('token', ''))
            ltp = float(tick_data.get('ltp', 0))
            
            if ltp == 0:
                return
            
            # Find symbol for this token
            symbol = None
            for sym, token_info in self.symbol_tokens.items():
                if str(token_info['token']) == token:
                    symbol = sym
                    break
            
            if not symbol:
                logger.debug(f"Tick received for unknown token: {token}")
                return
            
            # Thread-safe update
            with self._lock:
                # Update latest price
                old_price = self.latest_prices.get(symbol, 0)
                self.latest_prices[symbol] = ltp
                
                # Log first tick and significant price changes
                if old_price == 0:
                    logger.info(f"🟢 First tick: {symbol} @ ₹{ltp:.2f}")
                elif abs(ltp - old_price) / old_price > 0.01:  # >1% change
                    logger.debug(f"📊 Price update: {symbol} {old_price:.2f} → {ltp:.2f}")
                
                # Store tick data
                self.tick_data[symbol].append({
                    'timestamp': datetime.now(),
                    'ltp': ltp,
                    'volume': tick_data.get('volume', 0),
                    'open': tick_data.get('open', ltp),
                    'high': tick_data.get('high', ltp),
                    'low': tick_data.get('low', ltp),
                    'close': ltp
                })
            
        except Exception as e:
            logger.error(f"Error processing tick: {e}")
    
    def _continuous_position_monitoring(self):
        """
        Continuously monitor positions for stop loss/target hits.
        Runs INDEPENDENTLY every 0.5 seconds (500ms).
        This ensures instant exit on stop loss/target regardless of strategy execution.
        """
        logger.info("🔍 Position monitoring thread started (0.5s interval)")
        
        while self.is_running:
            try:
                self._monitor_positions()
                time.sleep(0.5)  # Check every 500ms
                
            except Exception as e:
                logger.error(f"Error in position monitoring: {e}")
                time.sleep(0.5)
    
    def _continuous_candle_building(self):
        """
        Continuously build 1-minute candles from tick data.
        Runs every 1 second for faster indicator updates.
        """
        logger.info("📊 Candle builder thread started (1s interval for faster updates)")
        
        while self.is_running:
            try:
                self._build_candles()
                time.sleep(1)  # Build candles every 1 second (5X faster!)
                
            except Exception as e:
                logger.error(f"Error building candles: {e}")
                time.sleep(1)
    
    def _build_candles(self):
        """Build 1-minute candles from tick data and calculate technical indicators"""
        with self._lock:
            for symbol, ticks in self.tick_data.items():
                if len(ticks) < 10:
                    continue
                
                # Convert ticks to DataFrame
                df = pd.DataFrame(list(ticks))
                
                if df.empty:
                    continue
                
                # Group by minute and create OHLC
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
                
                # Resample to 1-minute candles
                candles = df.resample('1min').agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'volume': 'sum'
                }).dropna()
                
                # CRITICAL FIX: Rename columns to uppercase for pattern detector compatibility
                # Pattern detector expects: 'Open', 'High', 'Low', 'Close', 'Volume'
                # But resampled candles have lowercase: 'open', 'high', 'low', 'close', 'volume'
                candles.columns = [col.capitalize() for col in candles.columns]
                
                # DEBUG: Check if historical data exists
                has_historical = symbol in self.candle_data
                historical_count = len(self.candle_data[symbol]) if has_historical else 0
                
                # CRITICAL FIX: APPEND new candles to historical data instead of replacing
                # If we have historical data, merge it with new realtime candles
                if symbol in self.candle_data and len(self.candle_data[symbol]) > 0:
                    historical_df = self.candle_data[symbol]
                    new_count = len(candles)
                    
                    # FIX timezone mismatch: Remove timezone info from both DataFrames before merging
                    # Historical data is tz-naive, realtime data is tz-aware (IST)
                    if historical_df.index.tz is not None:
                        historical_df.index = historical_df.index.tz_localize(None)
                    if candles.index.tz is not None:
                        candles.index = candles.index.tz_localize(None)
                    
                    # ALWAYS combine historical + new candles
                    combined = pd.concat([historical_df, candles])
                    combined = combined[~combined.index.duplicated(keep='last')]
                    combined = combined.sort_index()
                    
                    logger.info(f"📊 {symbol}: Merged {historical_count} historical + {new_count} new = {len(combined)} total candles")
                    
                    # Calculate indicators on FULL dataset (historical + new)
                    if len(combined) >= 200:
                        combined = self._calculate_indicators(combined)
                    
                    self.candle_data[symbol] = combined
                else:
                    # No historical data - use realtime only
                    # Remove timezone info for consistency
                    if candles.index.tz is not None:
                        candles.index = candles.index.tz_localize(None)
                    
                    logger.info(f"📊 {symbol}: No historical data (had {historical_count}), using {len(candles)} realtime candles")
                    if len(candles) >= 200:
                        candles = self._calculate_indicators(candles)
                    self.candle_data[symbol] = candles
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all technical indicators needed by trading strategies.
        
        Indicators calculated:
        - SMA: 10, 20, 50, 100, 200
        - RSI: 14
        - MACD: 12, 26, 9
        - ATR: 14
        - ADX: 14 (with DMI+/-)
        - VWAP
        - Volume SMA: 10
        
        Args:
            df: DataFrame with OHLCV data (capitalized columns: Open, High, Low, Close, Volume)
            
        Returns:
            DataFrame with added indicator columns
        """
        try:
            # CRITICAL FIX: Use capitalized column names to match pattern detector
            # Simple Moving Averages
            df['sma_10'] = df['Close'].rolling(window=10).mean()
            df['sma_20'] = df['Close'].rolling(window=20).mean()
            df['sma_50'] = df['Close'].rolling(window=50).mean()
            df['sma_100'] = df['Close'].rolling(window=100).mean()
            df['sma_200'] = df['Close'].rolling(window=200).mean()
            
            # RSI (14)
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            # Prevent division by zero
            rs = gain / loss.replace(0, 1e-10)
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # MACD (12, 26, 9)
            ema_12 = df['Close'].ewm(span=12, adjust=False).mean()
            ema_26 = df['Close'].ewm(span=26, adjust=False).mean()
            df['macd'] = ema_12 - ema_26
            df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
            df['macd_hist'] = df['macd'] - df['macd_signal']
            
            # ATR (14) - True Range calculation
            df['tr'] = np.maximum(
                df['High'] - df['Low'],
                np.maximum(
                    abs(df['High'] - df['Close'].shift(1)),
                    abs(df['Low'] - df['Close'].shift(1))
                )
            )
            df['atr'] = df['tr'].rolling(window=14).mean()
            
            # ADX (14) - Directional Movement Index
            df['high_diff'] = df['High'] - df['High'].shift(1)
            df['low_diff'] = df['Low'].shift(1) - df['Low']
            
            df['plus_dm'] = np.where((df['high_diff'] > df['low_diff']) & (df['high_diff'] > 0), df['high_diff'], 0)
            df['minus_dm'] = np.where((df['low_diff'] > df['high_diff']) & (df['low_diff'] > 0), df['low_diff'], 0)
            
            atr_14 = df['tr'].rolling(window=14).mean()
            # Prevent division by zero in DI calculations
            plus_di = 100 * (df['plus_dm'].rolling(window=14).mean() / atr_14.replace(0, 1e-10))
            minus_di = 100 * (df['minus_dm'].rolling(window=14).mean() / atr_14.replace(0, 1e-10))
            
            # Prevent division by zero in DX calculation
            di_sum = plus_di + minus_di
            dx = 100 * abs(plus_di - minus_di) / di_sum.replace(0, 1e-10)
            df['adx'] = dx.rolling(window=14).mean()
            df['dmi_plus'] = plus_di
            df['dmi_minus'] = minus_di
            
            # VWAP (Volume Weighted Average Price)
            if isinstance(df.index, pd.DatetimeIndex):
                df['vwap'] = (df['Volume'] * (df['High'] + df['Low'] + df['Close']) / 3).cumsum() / df['Volume'].cumsum()
            else:
                df['vwap'] = (df['High'] + df['Low'] + df['Close']) / 3  # Fallback to typical price
            
            # Volume SMA (10)
            df['volume_sma'] = df['Volume'].rolling(window=10).mean()
            
            # Clean up temporary columns
            df = df.drop(columns=['tr', 'high_diff', 'low_diff', 'plus_dm', 'minus_dm'], errors='ignore')
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}", exc_info=True)
        
        return df
    
    def _get_symbol_tokens_parallel(self) -> Dict:
        """
        Fetch symbol tokens sequentially to comply with Angel One rate limits.
        
        CRITICAL: searchScrip API has rate limit of 1 call/second per client code!
        Reference: https://smartapi.angelbroking.com/docs/RateLimit
        """
        import requests
        import time
        
        tokens = {}
        total = len(self.symbols)
        
        logger.info(f"📊 Fetching tokens for {total} symbols (rate limited to 1/second)...")
        logger.info(f"⏱️  Estimated time: ~{total} seconds")
        
        for idx, symbol in enumerate(self.symbols, 1):
            try:
                url = f"{self.base_url}/rest/secure/angelbroking/order/v1/searchScrip"
                headers = {
                    'Authorization': f'Bearer {self.jwt_token}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-UserType': 'USER',
                    'X-SourceID': 'WEB',
                    'X-ClientLocalIP': '127.0.0.1',
                    'X-ClientPublicIP': '127.0.0.1',
                    'X-MACAddress': '00:00:00:00:00:00',
                    'X-PrivateKey': self.api_key
                }
                payload = {"exchange": "NSE", "searchscrip": symbol}
                
                response = requests.post(url, json=payload, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') and data.get('data'):
                        scrip = data['data'][0]
                        tokens[symbol] = {
                            'token': scrip.get('symboltoken'),
                            'exchange': scrip.get('exch_seg', 'NSE'),
                            'trading_symbol': scrip.get('tradingsymbol', symbol)
                        }
                        logger.info(f"✅ [{idx}/{total}] Fetched {symbol}: {tokens[symbol]['token']}")
                    else:
                        logger.warning(f"⚠️  [{idx}/{total}] No data for {symbol}")
                else:
                    logger.error(f"❌ [{idx}/{total}] API error for {symbol}: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ [{idx}/{total}] Error fetching {symbol}: {e}")
            
            # CRITICAL: Enforce 1 second delay between calls to respect rate limit
            if idx < total:
                time.sleep(1.1)  # 1.1 seconds to be safe
        
        logger.info(f"✅ Successfully fetched {len(tokens)}/{total} symbol tokens")
        return tokens
    
    def _get_fallback_tokens(self) -> Dict:
        """
        Fallback symbol tokens for Nifty 50 stocks.
        Used when API token fetching fails due to rate limiting or network issues.
        """
        # Comprehensive Nifty 50 token list (updated Dec 2025)
        fallback_tokens = {
            'RELIANCE': {'token': '2885', 'exchange': 'NSE', 'trading_symbol': 'RELIANCE-EQ'},
            'HDFCBANK': {'token': '1333', 'exchange': 'NSE', 'trading_symbol': 'HDFCBANK-EQ'},
            'INFY': {'token': '1594', 'exchange': 'NSE', 'trading_symbol': 'INFY-EQ'},
            'TCS': {'token': '11536', 'exchange': 'NSE', 'trading_symbol': 'TCS-EQ'},
            'ICICIBANK': {'token': '1330', 'exchange': 'NSE', 'trading_symbol': 'ICICIBANK-EQ'},
            'SBIN': {'token': '3045', 'exchange': 'NSE', 'trading_symbol': 'SBIN-EQ'},
            'BHARTIARTL': {'token': '10604', 'exchange': 'NSE', 'trading_symbol': 'BHARTIARTL-EQ'},
            'ITC': {'token': '1660', 'exchange': 'NSE', 'trading_symbol': 'ITC-EQ'},
            'AXISBANK': {'token': '5900', 'exchange': 'NSE', 'trading_symbol': 'AXISBANK-EQ'},
            'KOTAKBANK': {'token': '1922', 'exchange': 'NSE', 'trading_symbol': 'KOTAKBANK-EQ'},
            'HINDUNILVR': {'token': '1394', 'exchange': 'NSE', 'trading_symbol': 'HINDUNILVR-EQ'},
            'LT': {'token': '11483', 'exchange': 'NSE', 'trading_symbol': 'LT-EQ'},
            'ASIANPAINT': {'token': '236', 'exchange': 'NSE', 'trading_symbol': 'ASIANPAINT-EQ'},
            'MARUTI': {'token': '10999', 'exchange': 'NSE', 'trading_symbol': 'MARUTI-EQ'},
            'HCLTECH': {'token': '7229', 'exchange': 'NSE', 'trading_symbol': 'HCLTECH-EQ'},
            'WIPRO': {'token': '3787', 'exchange': 'NSE', 'trading_symbol': 'WIPRO-EQ'},
            'M&M': {'token': '2031', 'exchange': 'NSE', 'trading_symbol': 'M&M-EQ'},
            'TATAMOTORS': {'token': '3456', 'exchange': 'NSE', 'trading_symbol': 'TATAMOTORS-EQ'},
            'TATASTEEL': {'token': '3499', 'exchange': 'NSE', 'trading_symbol': 'TATASTEEL-EQ'},
            'SUNPHARMA': {'token': '3351', 'exchange': 'NSE', 'trading_symbol': 'SUNPHARMA-EQ'},
            'NTPC': {'token': '11630', 'exchange': 'NSE', 'trading_symbol': 'NTPC-EQ'},
            'POWERGRID': {'token': '14977', 'exchange': 'NSE', 'trading_symbol': 'POWERGRID-EQ'},
            'ULTRACEMCO': {'token': '11532', 'exchange': 'NSE', 'trading_symbol': 'ULTRACEMCO-EQ'},
            'BAJFINANCE': {'token': '317', 'exchange': 'NSE', 'trading_symbol': 'BAJFINANCE-EQ'},
            'BAJAJFINSV': {'token': '16675', 'exchange': 'NSE', 'trading_symbol': 'BAJAJFINSV-EQ'},
            'TECHM': {'token': '13538', 'exchange': 'NSE', 'trading_symbol': 'TECHM-EQ'},
            'TITAN': {'token': '3506', 'exchange': 'NSE', 'trading_symbol': 'TITAN-EQ'},
            'NESTLEIND': {'token': '17963', 'exchange': 'NSE', 'trading_symbol': 'NESTLEIND-EQ'},
            'ADANIENT': {'token': '25', 'exchange': 'NSE', 'trading_symbol': 'ADANIENT-EQ'},
            'ADANIPORTS': {'token': '15083', 'exchange': 'NSE', 'trading_symbol': 'ADANIPORTS-EQ'},
            'COALINDIA': {'token': '20374', 'exchange': 'NSE', 'trading_symbol': 'COALINDIA-EQ'},
            'JSWSTEEL': {'token': '11723', 'exchange': 'NSE', 'trading_symbol': 'JSWSTEEL-EQ'},
            'INDUSINDBK': {'token': '5258', 'exchange': 'NSE', 'trading_symbol': 'INDUSINDBK-EQ'},
            'ONGC': {'token': '2475', 'exchange': 'NSE', 'trading_symbol': 'ONGC-EQ'},
            'HINDALCO': {'token': '1363', 'exchange': 'NSE', 'trading_symbol': 'HINDALCO-EQ'},
            'GRASIM': {'token': '1232', 'exchange': 'NSE', 'trading_symbol': 'GRASIM-EQ'},
            'CIPLA': {'token': '694', 'exchange': 'NSE', 'trading_symbol': 'CIPLA-EQ'},
            'DRREDDY': {'token': '881', 'exchange': 'NSE', 'trading_symbol': 'DRREDDY-EQ'},
            'DIVISLAB': {'token': '10940', 'exchange': 'NSE', 'trading_symbol': 'DIVISLAB-EQ'},
            'EICHERMOT': {'token': '910', 'exchange': 'NSE', 'trading_symbol': 'EICHERMOT-EQ'},
            'HEROMOTOCO': {'token': '1348', 'exchange': 'NSE', 'trading_symbol': 'HEROMOTOCO-EQ'},
            'TATACONSUM': {'token': '3432', 'exchange': 'NSE', 'trading_symbol': 'TATACONSUM-EQ'},
            'BRITANNIA': {'token': '547', 'exchange': 'NSE', 'trading_symbol': 'BRITANNIA-EQ'},
            'BPCL': {'token': '526', 'exchange': 'NSE', 'trading_symbol': 'BPCL-EQ'},
            'UPL': {'token': '11287', 'exchange': 'NSE', 'trading_symbol': 'UPL-EQ'},
            'APOLLOHOSP': {'token': '157', 'exchange': 'NSE', 'trading_symbol': 'APOLLOHOSP-EQ'},
            'SHRIRAMFIN': {'token': '4306', 'exchange': 'NSE', 'trading_symbol': 'SHRIRAMFIN-EQ'},
            'LTIM': {'token': '17818', 'exchange': 'NSE', 'trading_symbol': 'LTIM-EQ'},
            'TRENT': {'token': '1964', 'exchange': 'NSE', 'trading_symbol': 'TRENT-EQ'},
        }
        
        # Filter to only requested symbols
        filtered_tokens = {}
        for symbol in self.symbols:
            if symbol in fallback_tokens:
                filtered_tokens[symbol] = fallback_tokens[symbol]
        
        logger.info(f"Using fallback tokens for {len(filtered_tokens)} symbols")
        return filtered_tokens
    
    def _bootstrap_historical_candles(self):
        """
        🚨 CRITICAL FIX: Bootstrap historical candle data at bot startup.
        
        Problem: Bot was building candles ONLY from WebSocket ticks starting from zero.
        This meant the bot needed 200+ minutes to accumulate enough candles for indicators!
        
        Solution: Fetch last 200 1-minute candles from Angel One Historical API on startup.
        This allows immediate signal generation from 9:15 AM market open.
        
        ⚠️ IMPORTANT: If bot starts before market open (before 9:15 AM IST),
        historical API may return errors. This is EXPECTED. Bot will build candles
        from live ticks once market opens. THIS IS NOT A FAILURE.
        
        API Limits (per Angel One docs):
        - ONE_MINUTE: Max 30 days in one request
        - Rate limit: Standard API rate limits apply
        """
        logger.info("📊 [BOOTSTRAP] Starting historical candle bootstrap...")
        from datetime import datetime, timedelta
        from historical_data_manager import HistoricalDataManager
        
        # Check if market is open or was open recently
        now = datetime.now()
        market_open_time = datetime.strptime(f"{now.year}-{now.month:02d}-{now.day:02d} 09:15:00", "%Y-%m-%d %H:%M:%S")
        
        if now < market_open_time and now.weekday() < 5:
            logger.warning("⏰ Bot started BEFORE market open (9:15 AM) - Historical data may not be available")
            logger.warning("⏰ This is NORMAL - bot will accumulate candles from live ticks when market opens")
            logger.warning("⏰ For immediate signals, start bot AFTER 9:15 AM")
            # Still try to fetch - may get previous day's data
        
        logger.info("📊 Fetching historical candles for immediate indicator calculation...")
        
        # Initialize historical data manager
        hist_manager = HistoricalDataManager(
            api_key=self.api_key,
            jwt_token=self.jwt_token
        )
        
        # Calculate time range
        # CRITICAL OPTIMIZATION: Fetch FULL previous trading session (9:15 AM - 3:30 PM = 375 candles)
        # This allows INSTANT signal generation at 9:16 AM instead of waiting 50 minutes!
        # 375 candles is MORE than enough for all indicators (RSI, MACD, ATR, ADX, SMA50)
        if now < market_open_time:
            # Before market open: Fetch yesterday's COMPLETE trading session
            yesterday = now - timedelta(days=1)
            # Handle weekends: if today is Monday, fetch from Friday
            while yesterday.weekday() >= 5:  # Saturday=5, Sunday=6
                yesterday -= timedelta(days=1)
            to_date = yesterday.replace(hour=15, minute=30, second=0, microsecond=0)  # Yesterday 3:30 PM
            from_date = yesterday.replace(hour=9, minute=15, second=0, microsecond=0)  # Yesterday 9:15 AM
            logger.info(f"📊 Fetching previous trading session: {from_date.strftime('%Y-%m-%d %H:%M')} to {to_date.strftime('%Y-%m-%d %H:%M')}")
            logger.info(f"📊 Expected ~375 candles (full session) for INSTANT signal generation!")
        else:
            # After market open: Fetch ONLY yesterday's session (realtime will build today's candles)
            yesterday = now - timedelta(days=1)
            while yesterday.weekday() >= 5:  # Handle weekends
                yesterday -= timedelta(days=1)
            to_date = yesterday.replace(hour=15, minute=30, second=0, microsecond=0)  # Yesterday 3:30 PM
            from_date = yesterday.replace(hour=9, minute=15, second=0, microsecond=0)  # Yesterday 9:15 AM
            logger.info(f"📊 Fetching previous trading session only: {from_date.strftime('%Y-%m-%d %H:%M')} to {to_date.strftime('%Y-%m-%d %H:%M')}")
            logger.info(f"📊 Expected ~375 candles (realtime will add today's candles)")
        
        success_count = 0
        fail_count = 0
        
        # CRITICAL: Angel One rate limits - 3 requests/second, 180/minute
        # We use 0.4 seconds between requests = 2.5 requests/second (safe margin)
        RATE_LIMIT_DELAY = 0.4  # seconds between requests
        
        for idx, symbol in enumerate(self.symbols, 1):
            try:
                token_info = self.symbol_tokens.get(symbol)
                if not token_info:
                    logger.debug(f"⏭️  [{idx}/{len(self.symbols)}] {symbol}: No token info, skipping")
                    continue
                
                # Fetch 1-minute candles (with built-in retry logic for 403 errors)
                df = hist_manager.fetch_historical_data(
                    symbol=symbol,
                    token=token_info['token'],
                    exchange=token_info['exchange'],
                    interval='ONE_MINUTE',
                    from_date=from_date,
                    to_date=to_date,
                    max_retries=3  # Retry up to 3 times for rate limit errors
                )
                
                if df is not None and len(df) > 0:
                    # Calculate indicators if we have enough data
                    if len(df) >= 200:
                        df = self._calculate_indicators(df)
                    
                    # Store in candle_data (thread-safe)
                    with self._lock:
                        self.candle_data[symbol] = df
                    
                    success_count += 1
                    logger.info(f"✅ [{idx}/{len(self.symbols)}] {symbol}: Loaded {len(df)} historical candles")
                else:
                    fail_count += 1
                    logger.debug(f"⏭️  [{idx}/{len(self.symbols)}] {symbol}: No historical data returned")
                    
            except Exception as e:
                fail_count += 1
                logger.debug(f"⏭️  [{idx}/{len(self.symbols)}] {symbol}: Historical fetch failed: {e}")
                # Continue with other symbols even if one fails
            
            finally:
                # CRITICAL: ALWAYS rate limit between requests, regardless of success/failure
                # This prevents cascading 403 errors when one request fails
                if idx < len(self.symbols):  # Don't sleep after last symbol
                    time.sleep(RATE_LIMIT_DELAY)
        
        if success_count == 0 and now < market_open_time:
            logger.warning("📊 No historical data available - Bot started before market open")
            logger.warning("📊 Bot will accumulate candles from live ticks starting at 9:15 AM")
            logger.warning("📊 Pattern detection will activate once 50+ candles accumulated (~50 minutes)")
            logger.info("✅ [CRITICAL] Historical candles loaded - bot ready to trade immediately!")
        elif success_count > 0:
            logger.info(f"📈 Historical data bootstrap: {success_count} symbols loaded")
            logger.info(f"🎯 Bot ready for immediate signal generation with pre-loaded indicators!")
            logger.info("✅ [CRITICAL] Historical candles loaded - bot ready to trade immediately!")
        else:
            logger.warning(f"⚠️ Historical data bootstrap: 0 success, {fail_count} failed")
            logger.warning("⚠️ Bot will build candles from live ticks (may take 50+ minutes for patterns)")
            logger.info("✅ [CRITICAL] Historical candles loaded - bot ready to trade immediately!")
    
    def _verify_ready_to_trade(self):
        """Final verification before entering trading loop"""
        checks = {
            'websocket_connected': self.ws_manager and hasattr(self.ws_manager, 'is_connected') and getattr(self.ws_manager, 'is_connected', False),
            'has_prices': len(self.latest_prices) > 0,
            'has_candles': len(self.candle_data) >= len(self.symbol_tokens) * 0.5,  # At least 50% of symbols (Angel One API can be slow at market open)
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
    
    def _load_bot_config(self) -> Dict:
        """Load bot configuration from Firestore including portfolio value"""
        try:
            import firebase_admin
            from firebase_admin import firestore
            
            db = firestore.client()
            config_doc = db.collection('bot_configs').document(self.user_id).get()
            
            if config_doc.exists:
                config = config_doc.to_dict()
                logger.info(f"✅ Loaded bot config from Firestore for user {self.user_id}")
                return config
            else:
                # Create default config if doesn't exist
                default_config = {
                    'portfolio_value': 100000.0,  # Default ₹1 lakh
                    'trading_mode': 'paper',
                    'max_position_size_pct': 0.02,
                    'max_daily_loss_pct': 0.03,
                    'max_portfolio_heat': 0.06,
                    'max_open_positions': 5,
                    'emergency_stop': False,
                    'created_at': firestore.SERVER_TIMESTAMP
                }
                db.collection('bot_configs').document(self.user_id).set(default_config)
                logger.info(f"📝 Created default bot config for user {self.user_id}")
                return default_config
                
        except Exception as e:
            logger.error(f"Failed to load bot config: {e}")
            # Return defaults if Firestore fails
            return {
                'portfolio_value': 100000.0,
                'trading_mode': 'paper',
                'max_position_size_pct': 0.02,
                'max_daily_loss_pct': 0.03,
                'max_portfolio_heat': 0.06,
                'max_open_positions': 5,
                'emergency_stop': False
            }
    
    def _initialize_managers(self):
        """Initialize all trading managers"""
        from trading.patterns import PatternDetector
        try:
            from trading.execution_manager import ExecutionManager
        except ImportError as e:
            logger.warning(f"ExecutionManager import failed: {e} - Will skip 30-point validation")
            ExecutionManager = None
        from trading.order_manager import OrderManager
        from trading.risk_manager import RiskManager, RiskLimits
        from trading.simple_position_manager import SimplePositionManager
        from advanced_screening_manager import AdvancedScreeningManager, AdvancedScreeningConfig
        from ml_data_logger import MLDataLogger
        
        # Load bot configuration from Firestore (includes portfolio value)
        bot_config = self._load_bot_config()
        portfolio_value = bot_config.get('portfolio_value', 100000.0)
        logger.info(f"💰 Portfolio Value: ₹{portfolio_value:,.2f}")
        
        self._pattern_detector = PatternDetector()
        if ExecutionManager:
            self._execution_manager = ExecutionManager()
        else:
            self._execution_manager = None
            logger.warning("⚠️  ExecutionManager disabled - trades will skip 30-point validation")
        self._order_manager = OrderManager(self.api_key, self.jwt_token)
        
        risk_limits = RiskLimits(
            max_position_size_pct=bot_config.get('max_position_size_pct', 0.05),
            max_daily_loss_pct=bot_config.get('max_daily_loss_pct', 0.02),
            max_portfolio_heat=bot_config.get('max_portfolio_heat', 0.20),
            max_open_positions=bot_config.get('max_open_positions', 5)
        )
        self._risk_manager = RiskManager(portfolio_value=portfolio_value, risk_limits=risk_limits)
        self._position_manager = SimplePositionManager()
        
        # NEW: Initialize Advanced 24-Level Screening Manager
        screening_config = AdvancedScreeningConfig()
        screening_config.fail_safe_mode = True  # Won't block trades on errors (safe rollout)
        screening_config.enable_tick_indicator = True  # Enable Level 22 (TICK)
        self._advanced_screening = AdvancedScreeningManager(
            config=screening_config,
            portfolio_value=portfolio_value  # ✅ Use actual portfolio value
        )
        logger.info("✅ Advanced Screening Manager initialized (fail-safe mode: ON, TICK: ON)")
        
        # NEW: Initialize ML Data Logger
        try:
            self._ml_logger = MLDataLogger(db_client=self.db)
            logger.info("✅ ML Data Logger initialized (collection enabled)")
        except Exception as e:
            logger.error(f"Failed to initialize ML Logger: {e}")
            self._ml_logger = MLDataLogger(db_client=None)  # Disabled mode
        
        # NEW: Initialize Bot Activity Logger for real-time dashboard
        try:
            from bot_activity_logger import BotActivityLogger
            self._activity_logger = BotActivityLogger(user_id=self.user_id, db_client=self.db)
            logger.info("✅ Bot Activity Logger initialized (real-time dashboard feed)")
        except Exception as e:
            logger.error(f"Failed to initialize Activity Logger: {e}")
            self._activity_logger = None  # Disabled mode
        
        # Initialize Ironclad if needed
        if self.strategy in ['ironclad', 'both']:
            from ironclad_strategy import IroncladStrategy
            self._ironclad = IroncladStrategy(db_client=None, dr_window_minutes=60)
        
        logger.info("✅ Trading managers initialized")
    
    def _is_market_open(self):
        """
        Check if Indian stock market is currently open.
        Trading Hours: 9:15 AM - 3:30 PM IST (Mon-Fri)
        """
        from datetime import datetime
        import pytz
        
        # Get current time in IST (Indian Standard Time)
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)
        
        # Check if weekend
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        current_time = now.time()
        market_open = datetime.strptime("09:15:00", "%H:%M:%S").time()
        market_close = datetime.strptime("15:30:00", "%H:%M:%S").time()
        
        is_open = market_open <= current_time <= market_close
        
        if not is_open:
            logger.debug(f"⏰ Market closed - Current IST time: {current_time.strftime('%H:%M:%S')}")
        
        return is_open
    
    def _analyze_and_trade(self):
        """
        Main strategy execution (runs every 5 seconds).
        Position monitoring happens independently every 0.5 seconds.
        """
        try:
            logger.debug(f"🔍 [DEBUG] _analyze_and_trade() called - Strategy: {self.strategy}")
            
            # Check if market is open before trading
            if not self._is_market_open():
                logger.debug("⏸️  Market is closed - skipping strategy execution")
                return
            
            # Check EOD auto-close (3:15 PM for safety before broker's 3:20 PM)
            self._check_eod_auto_close()
            
            if self.strategy == 'pattern':
                logger.debug("📊 [DEBUG] Executing PATTERN strategy...")
                self._execute_pattern_strategy()
            elif self.strategy == 'ironclad':
                logger.debug("🛡️  [DEBUG] Executing IRONCLAD strategy...")
                self._execute_ironclad_strategy()
            elif self.strategy == 'both':
                logger.debug("🔀 [DEBUG] Executing DUAL strategy...")
                self._execute_dual_strategy()
            
            logger.debug("✅ [DEBUG] _analyze_and_trade() completed successfully")
                
        except Exception as e:
            logger.error(f"❌ [DEBUG] Error in strategy execution: {e}", exc_info=True)
    
    def _check_eod_auto_close(self):
        """
        Auto-close all positions at 3:15 PM (15:15) for INTRADAY safety.
        Angel One auto-squares off at 3:20 PM, but we close 5 minutes earlier
        to ensure clean exits without broker's forced liquidation.
        """
        from datetime import datetime
        
        now = datetime.now()
        current_time = now.time()
        
        # Market closes at 3:30 PM (15:30)
        # Broker auto square-off at 3:20 PM (15:20)
        # Our safety auto-close at 3:15 PM (15:15)
        eod_close_time = datetime.strptime("15:15:00", "%H:%M:%S").time()
        market_close_time = datetime.strptime("15:30:00", "%H:%M:%S").time()
        
        # Check if it's EOD time (between 3:15 PM and 3:30 PM)
        if eod_close_time <= current_time <= market_close_time:
            positions = self._position_manager.get_all_positions()
            
            if positions and not hasattr(self, '_eod_closed'):
                logger.warning("⏰ EOD AUTO-CLOSE: 3:15 PM reached - Closing all INTRADAY positions")
                
                # Get latest prices
                with self._lock:
                    current_prices = self.latest_prices.copy()
                
                # Close all positions
                for symbol, position in positions.items():
                    current_price = current_prices.get(symbol, position.get('entry_price', 0))
                    logger.info(f"⏰ EOD: Closing {symbol} @ ₹{current_price:.2f}")
                    self._close_position(symbol, position, current_price, 'EOD_AUTO_CLOSE')
                
                # Set flag to prevent repeated closes
                self._eod_closed = True
                logger.info("✅ All INTRADAY positions closed for end-of-day")
        else:
            # Reset flag for next day
            if hasattr(self, '_eod_closed'):
                delattr(self, '_eod_closed')
    
    def _update_market_internals(self):
        """
        Calculate and update NIFTY 50 advance/decline ratio for TICK indicator.
        Uses real-time prices vs open prices from candle data.
        """
        try:
            with self._lock:
                candle_copy = self.candle_data.copy()
                prices_copy = self.latest_prices.copy()
            
            advancing = declining = unchanged = 0
            
            for symbol in self.symbols:
                # Need both candle data (for open price) and current price
                if symbol not in candle_copy or symbol not in prices_copy:
                    continue
                
                df = candle_copy[symbol]
                if df.empty:
                    continue
                
                # Get today's open price (first candle of the day)
                open_price = float(df.iloc[0]['open'])
                current_price = prices_copy[symbol]
                
                # Calculate change threshold (0.1% to avoid noise)
                threshold = open_price * 0.001
                
                if current_price > open_price + threshold:
                    advancing += 1
                elif current_price < open_price - threshold:
                    declining += 1
                else:
                    unchanged += 1
            
            # Update advanced screening manager with real market internals
            if self._advanced_screening and (advancing + declining + unchanged) > 0:
                self._advanced_screening.update_tick_data(advancing, declining, unchanged)
                logger.debug(f"📊 Market Internals: {advancing} ADV | {declining} DEC | {unchanged} UNCH")
                
        except Exception as e:
            logger.error(f"Error updating market internals: {e}")
    
    def _execute_pattern_strategy(self):
        """
        Execute pattern detection strategy with intelligent signal ranking.
        Scans all Nifty 50 stocks and selects trades with highest confidence.
        """
        from trading.order_manager import OrderType, TransactionType, ProductType
        
        # Update market internals BEFORE scanning (for TICK indicator)
        self._update_market_internals()
        
        with self._lock:
            candle_data_copy = self.candle_data.copy()
            latest_prices_copy = self.latest_prices.copy()
        
        # STEP 1: Scan all symbols and collect signals with confidence scores
        signals = []
        
        logger.info(f"📊 [DEBUG] Scanning {len(self.symbols)} symbols for trading opportunities...")
        logger.info(f"🔢 [DEBUG] Candle data available for {len(candle_data_copy)} symbols")
        logger.info(f"💰 [DEBUG] Latest prices available for {len(latest_prices_copy)} symbols")
        
        for symbol in self.symbols:
            try:
                # Check if we have enough candle data (need 50 for full indicator accuracy)
                # 50 candles ensures: RSI(14), MACD(26), EMA(20), BB(20), ATR(14), ADX(28)
                # All patterns (Double Top/Bottom, Flags, Triangles) work optimally
                # SMA50 available for trend confirmation
                candle_count = len(candle_data_copy.get(symbol, []))
                if symbol not in candle_data_copy or candle_count < 50:
                    logger.info(f"⏭️  [DEBUG] {symbol}: Skipping - insufficient candle data ({candle_count} candles, need 50+)")
                    continue
                
                # Skip if already have position
                if self._position_manager.has_position(symbol):
                    continue
                
                df = candle_data_copy[symbol].copy()
                
                # Pattern detection (detects both forming and confirmed patterns)
                pattern_details = self._pattern_detector.scan(df)
                if not pattern_details:
                    logger.info(f"[DEBUG] {symbol}: No pattern detected this cycle.")
                    continue
                
                # Check if pattern is tradeable (confirmed breakout) or just forming (watchlist)
                is_tradeable = pattern_details.get('tradeable', True)  # Default True for backward compatibility
                pattern_status = pattern_details.get('pattern_status', 'confirmed')
                
                # Add symbol to pattern_details for fundamental checks
                pattern_details['symbol'] = symbol
                
                # Log to Activity Feed (both forming and confirmed patterns)
                if self._activity_logger:
                    confidence = self._calculate_signal_confidence(df, pattern_details) if is_tradeable else 0
                    self._activity_logger.log_pattern_detected(
                        symbol=symbol,
                        pattern=pattern_details.get('pattern_name', 'Unknown'),
                        confidence=confidence if is_tradeable else 0,
                        rr_ratio=0,  # Will calculate below if tradeable
                        details={
                            'status': pattern_status,
                            'tradeable': is_tradeable,
                            'current_price': latest_prices_copy.get(symbol, float(df['close'].iloc[-1])),
                            'distance_to_breakout': pattern_details.get('distance_to_breakout', 0)
                        }
                    )
                
                # Only proceed with trading logic if pattern is confirmed (not just forming)
                if not is_tradeable:
                    logger.info(f"👀 {symbol}: {pattern_details.get('pattern_name')} detected - FORMING (watchlist only)")
                    continue
                
                # 30-point validation (optional, only for tradeable patterns)
                is_valid = True
                if self._execution_manager:
                    is_valid = self._execution_manager.validate_trade_entry(df, pattern_details)
                if not is_valid:
                    continue
                
                # Get current price (real-time from WebSocket)
                current_price = latest_prices_copy.get(symbol, float(df['close'].iloc[-1]))
                
                # Calculate confidence score (0-100)
                confidence = self._calculate_signal_confidence(df, pattern_details)
                
                # Calculate risk-reward ratio
                stop_loss = float(pattern_details.get('initial_stop_loss', current_price * 0.98))
                target = float(pattern_details.get('calculated_price_target', current_price * 1.05))
                risk = abs(current_price - stop_loss)
                reward = abs(target - current_price)
                rr_ratio = reward / risk if risk > 0 else 0
                
                # Store signal
                signals.append({
                    'symbol': symbol,
                    'confidence': confidence,
                    'rr_ratio': rr_ratio,
                    'pattern_details': pattern_details,
                    'current_price': current_price,
                    'stop_loss': stop_loss,
                    'target': target,
                })
                
                logger.info(f"✅ {symbol}: Pattern detected | Confidence: {confidence:.1f}% | R:R = 1:{rr_ratio:.2f}")
                
                # NEW: Log pattern detection to dashboard
                if self._activity_logger:
                    self._activity_logger.log_pattern_detected(
                        symbol=symbol,
                        pattern=pattern_details.get('pattern_name', 'Unknown'),
                        confidence=confidence,
                        rr_ratio=rr_ratio,
                        details={
                            'current_price': current_price,
                            'stop_loss': stop_loss,
                            'target': target
                        }
                    )
                
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}", exc_info=True)
        
        # STEP 2: Rank signals by confidence * risk-reward ratio
        if signals:
            # Sort by composite score (confidence * RR ratio)
            signals.sort(key=lambda x: x['confidence'] * x['rr_ratio'], reverse=True)
            
            logger.info(f"🎯 Found {len(signals)} potential trades. Top signals:")
            for i, sig in enumerate(signals[:5]):  # Show top 5
                score = sig['confidence'] * sig['rr_ratio']
                logger.info(f"  {i+1}. {sig['symbol']}: Score={score:.1f} (Conf={sig['confidence']:.1f}%, R:R=1:{sig['rr_ratio']:.2f})")
            
            # STEP 3: Take best trades up to max_positions limit
            current_positions = len(self._position_manager.get_all_positions())
            max_positions = self._risk_manager.risk_limits.max_positions
            available_slots = max_positions - current_positions
            
            for sig in signals[:available_slots]:
                try:
                    # Position sizing
                    risk_per_share = abs(sig['current_price'] - sig['stop_loss'])
                    max_risk = self._risk_manager.risk_limits.max_position_size_percent * self._risk_manager.portfolio_value
                    quantity = int(max_risk / risk_per_share) if risk_per_share > 0 else 1
                    quantity = max(1, min(quantity, 100))
                    
                    # NEW: Advanced 24-Level Screening (before order placement)
                    logger.info(f"🔍 [{sig['symbol']}] Running Advanced 24-Level Screening...")
                    
                    # Log screening started
                    if self._activity_logger:
                        self._activity_logger.log_screening_started(
                            symbol=sig['symbol'],
                            pattern=sig['pattern_details'].get('pattern_name', 'Unknown')
                        )
                    
                    signal_data = {
                        'action': 'BUY' if sig['pattern_details'].get('breakout_direction', 'up') == 'up' else 'SELL',
                        'entry_price': sig['current_price'],
                        'stop_loss': sig['stop_loss'],
                        'target': sig['target'],
                        'pattern_name': sig['pattern_details'].get('pattern_name'),
                        'score': sig['confidence']
                    }
                    
                    is_screened, screen_reason = self._advanced_screening.validate_signal(
                        symbol=sig['symbol'],
                        signal_data=signal_data,
                        df=candle_data_copy[sig['symbol']],
                        current_positions=self._position_manager.get_all_positions(),
                        current_price=sig['current_price']
                    )
                    
                    if not is_screened:
                        logger.warning(f"❌ [{sig['symbol']}] Advanced Screening BLOCKED: {screen_reason}")
                        
                        # Log screening failed to dashboard
                        if self._activity_logger:
                            self._activity_logger.log_screening_failed(
                                symbol=sig['symbol'],
                                pattern=sig['pattern_details'].get('pattern_name', 'Unknown'),
                                reason=screen_reason
                            )
                        
                        # Log rejected signal for ML training
                        if self._ml_logger and self._ml_logger.enabled:
                            try:
                                df_latest = candle_data_copy[sig['symbol']].iloc[-1]
                                rejected_signal_data = {
                                    'symbol': sig['symbol'],
                                    'action': signal_data['action'],
                                    'entry_price': sig['current_price'],
                                    'stop_loss': sig['stop_loss'],
                                    'target': sig['target'],
                                    'rsi': df_latest.get('rsi', 50),
                                    'macd': df_latest.get('macd', 0),
                                    'macd_signal': df_latest.get('macd_signal', 0),
                                    'adx': df_latest.get('adx', 20),
                                    'pattern_type': sig['pattern_details'].get('pattern_name', 'Unknown'),
                                    'confidence': sig['confidence']
                                }
                                self._ml_logger.log_rejected_signal(rejected_signal_data, screen_reason)
                            except Exception as log_err:
                                logger.debug(f"ML logger (rejected signal) error: {log_err}")

                        continue  # Skip this trade

                    logger.info(f"✅ [{sig['symbol']}] Advanced Screening PASSED: {screen_reason}")
                    
                    # Log screening passed to dashboard
                    if self._activity_logger:
                        self._activity_logger.log_screening_passed(
                            symbol=sig['symbol'],
                            pattern=sig['pattern_details'].get('pattern_name', 'Unknown'),
                            reason=screen_reason
                        )

                    # Log signal for ML training (before order placement)
                    ml_signal_id = None
                    if self._ml_logger and self._ml_logger.enabled:
                        try:
                            df_latest = candle_data_copy[sig['symbol']].iloc[-1]
                            ml_signal_data = {
                                'symbol': sig['symbol'],
                                'action': signal_data['action'],
                                'entry_price': sig['current_price'],
                                'stop_loss': sig['stop_loss'],
                                'target': sig['target'],
                                'was_taken': True,
                                'rsi': df_latest.get('rsi', 50),
                                'macd': df_latest.get('macd', 0),
                                'macd_signal': df_latest.get('macd_signal', 0),
                                'adx': df_latest.get('adx', 20),
                                'bb_width': df_latest.get('bb_width', 0),
                                'volume_ratio': df_latest.get('volume_ratio', 1.0),
                                'pattern_type': sig['pattern_details'].get('pattern_name', 'Unknown'),
                                'hour_of_day': datetime.now().hour,
                                'confidence': sig['confidence']
                            }
                            ml_signal_id = self._ml_logger.log_signal(ml_signal_data)
                            logger.info(f"📊 ML signal logged: {ml_signal_id}")
                        except Exception as log_err:
                            logger.debug(f"ML logger error: {log_err}")
                    
                    # Place order for best opportunity
                    logger.info(f"🔴 ENTERING TRADE: {sig['symbol']} (Top ranked signal)")
                    self._place_entry_order(
                        symbol=sig['symbol'],
                        direction=sig['pattern_details'].get('breakout_direction', 'up'),
                        entry_price=sig['current_price'],
                        stop_loss=sig['stop_loss'],
                        target=sig['target'],
                        quantity=quantity,
                        reason=f"Pattern: {sig['pattern_details'].get('pattern_name')} | Confidence: {sig['confidence']:.1f}%",
                        ml_signal_id=ml_signal_id,  # Pass ML signal ID for outcome tracking
                        confidence=sig['confidence']  # Pass actual calculated confidence
                    )
                    
                except Exception as e:
                    logger.error(f"Error placing order for {sig['symbol']}: {e}", exc_info=True)
        else:
            logger.debug("No trading signals found in this scan cycle")
    
    def _calculate_signal_confidence(self, df: pd.DataFrame, pattern_details: dict) -> float:
        """
        Calculate confidence score (0-100) for a trading signal.
        
        Factors:
        - Volume strength (20%)
        - Trend alignment (20%)
        - Pattern quality (30%)
        - Support/Resistance proximity (15%)
        - Momentum indicators (15%)
        """
        try:
            confidence = 0.0
            
            # 1. Volume strength (20 points)
            if 'volume' in df.columns:
                avg_volume = df['volume'].tail(20).mean()
                current_volume = df['volume'].iloc[-1]
                volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
                volume_score = min(20, volume_ratio * 10)  # Max 20 points
                confidence += volume_score
            
            # 2. Trend alignment (20 points)
            if 'sma_50' in df.columns and 'sma_200' in df.columns:
                sma_50 = df['sma_50'].iloc[-1]
                sma_200 = df['sma_200'].iloc[-1]
                price = df['close'].iloc[-1]
                
                # Bullish alignment: price > sma_50 > sma_200
                if price > sma_50 > sma_200:
                    confidence += 20
                elif price > sma_50:
                    confidence += 10
            
            # 3. Pattern quality (30 points)
            pattern_score = pattern_details.get('pattern_score', 0.5)  # 0-1 scale
            confidence += pattern_score * 30
            
            # 4. Support/Resistance proximity (15 points)
            support = pattern_details.get('support_level', 0)
            resistance = pattern_details.get('resistance_level', 0)
            price = df['close'].iloc[-1]
            
            if support > 0 and resistance > 0:
                range_size = resistance - support
                distance_from_support = price - support
                position_in_range = distance_from_support / range_size if range_size > 0 else 0.5
                
                # Lower in range = better for longs
                if position_in_range < 0.3:  # Near support
                    confidence += 15
                elif position_in_range < 0.5:
                    confidence += 10
            
            # 5. Momentum indicators (15 points)
            if 'rsi' in df.columns:
                rsi = df['rsi'].iloc[-1]
                # RSI between 50-70 is ideal for longs
                if 50 <= rsi <= 70:
                    confidence += 15
                elif 40 <= rsi <= 80:
                    confidence += 10
            
            return min(100, confidence)  # Cap at 100
            
        except Exception as e:
            logger.warning(f"Error calculating confidence: {e}")
            return 50.0  # Default moderate confidence
    
    def _execute_ironclad_strategy(self):
        """
        Execute Ironclad strategy with intelligent signal ranking.
        Scans all Nifty 50 stocks and selects trades with highest Ironclad scores.
        """
        from trading.order_manager import OrderType, TransactionType, ProductType
        
        # Update market internals BEFORE scanning (for TICK indicator)
        self._update_market_internals()
        
        with self._lock:
            candle_data_copy = self.candle_data.copy()
            latest_prices_copy = self.latest_prices.copy()
        
        # STEP 1: Scan all symbols and collect signals
        signals = []
        
        logger.info(f"🛡️ Running Ironclad analysis on {len(self.symbols)} symbols...")
        
        for symbol in self.symbols:
            try:
                if symbol not in candle_data_copy or len(candle_data_copy[symbol]) < 100:
                    continue
                
                if self._position_manager.has_position(symbol):
                    continue
                
                stock_df = candle_data_copy[symbol].copy()
                nifty_df = stock_df.copy()  # Use stock as NIFTY proxy for now
                
                signal = self._ironclad.run_analysis_cycle(
                    nifty_df=nifty_df,
                    stock_df=stock_df,
                    symbol=symbol,
                    bot_start_time=self.bot_start_time
                )
                
                if not signal or signal.get('action') == 'HOLD':
                    continue
                
                # Add symbol to signal for fundamental checks
                signal['symbol'] = symbol
                
                # NEW: Apply 30-Point Grandmaster Checklist to Ironclad signals (optional)
                is_valid = True
                if self._execution_manager:
                    logger.info(f"🔍 [{symbol}] Ironclad signal - applying 30-Point Checklist...")
                    is_valid = self._execution_manager.validate_trade_entry(stock_df, signal)
                    if not is_valid:
                        logger.warning(f"❌ [{symbol}] 30-Point Checklist FAILED - Ironclad signal rejected")
                if not is_valid:
                    continue
                
                logger.info(f"✅ [{symbol}] 30-Point Checklist PASSED for Ironclad signal")
                
                # Ironclad already provides confidence/score
                ironclad_score = signal.get('score', 50)
                
                signals.append({
                    'symbol': symbol,
                    'signal': signal,
                    'score': ironclad_score,
                    'action': signal.get('action'),
                })
                
                logger.info(f"✅ {symbol}: Ironclad {signal.get('action')} | Score: {ironclad_score:.1f}")
                
            except Exception as e:
                logger.error(f"Error in Ironclad analysis for {symbol}: {e}", exc_info=True)
        
        # STEP 2: Rank signals by Ironclad score
        if signals:
            signals.sort(key=lambda x: x['score'], reverse=True)
            
            logger.info(f"🎯 Found {len(signals)} Ironclad signals. Top signals:")
            for i, sig in enumerate(signals[:5]):
                logger.info(f"  {i+1}. {sig['symbol']}: {sig['action']} | Score={sig['score']:.1f}")
            
            # STEP 3: Take best trades up to max_positions limit
            current_positions = len(self._position_manager.get_all_positions())
            max_positions = self._risk_manager.risk_limits.max_positions
            available_slots = max_positions - current_positions
            
            for sig in signals[:available_slots]:
                try:
                    signal = sig['signal']
                    symbol = sig['symbol']
                    
                    current_price = latest_prices_copy.get(symbol, signal.get('entry_price', 0))
                    stop_loss = signal.get('stop_loss', current_price * 0.98)
                    target = signal.get('target', current_price * 1.05)
                    
                    # Position sizing
                    risk_per_share = abs(current_price - stop_loss)
                    max_risk = self._risk_manager.risk_limits.max_position_size_percent * self._risk_manager.portfolio_value
                    quantity = int(max_risk / risk_per_share) if risk_per_share > 0 else 1
                    quantity = max(1, min(quantity, 100))
                    
                    # NEW: Advanced 24-Level Screening (before order placement)
                    logger.info(f"🔍 [{symbol}] Running Advanced 24-Level Screening...")
                    signal_data = {
                        'action': signal.get('action'),
                        'entry_price': current_price,
                        'stop_loss': stop_loss,
                        'target': target,
                        'pattern_name': 'Ironclad DR Breakout',
                        'score': sig['score']
                    }
                    
                    is_screened, screen_reason = self._advanced_screening.validate_signal(
                        symbol=symbol,
                        signal_data=signal_data,
                        df=candle_data_copy[symbol],
                        current_positions=self._position_manager.get_all_positions(),
                        current_price=current_price
                    )
                    
                    if not is_screened:
                        logger.warning(f"❌ [{symbol}] Advanced Screening BLOCKED: {screen_reason}")
                        
                        # Log rejected signal for ML training
                        if self._ml_logger and self._ml_logger.enabled:
                            try:
                                df_latest = candle_data_copy[symbol].iloc[-1]
                                rejected_signal_data = {
                                    'symbol': symbol,
                                    'action': signal.get('action'),
                                    'entry_price': current_price,
                                    'stop_loss': stop_loss,
                                    'target': target,
                                    'rsi': df_latest.get('rsi', 50),
                                    'macd': df_latest.get('macd', 0),
                                    'macd_signal': df_latest.get('macd_signal', 0),
                                    'adx': df_latest.get('adx', 20),
                                    'pattern_type': 'Ironclad DR Breakout',
                                    'confidence': sig['score']
                                }
                                self._ml_logger.log_rejected_signal(rejected_signal_data, screen_reason)
                            except Exception as log_err:
                                logger.debug(f"ML logger (rejected signal) error: {log_err}")
                        
                        continue  # Skip this trade
                    
                    logger.info(f"✅ [{symbol}] Advanced Screening PASSED: {screen_reason}")
                    
                    # Log signal for ML training (before order placement)
                    ml_signal_id = None
                    if self._ml_logger and self._ml_logger.enabled:
                        try:
                            df_latest = candle_data_copy[symbol].iloc[-1]
                            ml_signal_data = {
                                'symbol': symbol,
                                'action': signal.get('action'),
                                'entry_price': current_price,
                                'stop_loss': stop_loss,
                                'target': target,
                                'was_taken': True,
                                'rsi': df_latest.get('rsi', 50),
                                'macd': df_latest.get('macd', 0),
                                'macd_signal': df_latest.get('macd_signal', 0),
                                'adx': df_latest.get('adx', 20),
                                'bb_width': df_latest.get('bb_width', 0),
                                'volume_ratio': df_latest.get('volume_ratio', 1.0),
                                'pattern_type': 'Ironclad DR Breakout',
                                'hour_of_day': datetime.now().hour,
                                'confidence': sig['score']
                            }
                            ml_signal_id = self._ml_logger.log_signal(ml_signal_data)
                            logger.info(f"📊 ML signal logged: {ml_signal_id}")
                        except Exception as log_err:
                            logger.debug(f"ML logger error: {log_err}")
                    
                    logger.info(f"🔴 ENTERING TRADE: {symbol} (Ironclad top signal)")
                    self._place_entry_order(
                        symbol=symbol,
                        direction='up' if signal.get('action') == 'BUY' else 'down',
                        entry_price=current_price,
                        stop_loss=stop_loss,
                        target=target,
                        quantity=quantity,
                        reason=f"Ironclad {signal.get('action')} | Score: {sig['score']:.1f}",
                        ml_signal_id=ml_signal_id,  # Pass ML signal ID
                        confidence=sig['score']  # Pass actual Ironclad score
                    )
                    
                except Exception as e:
                    logger.error(f"Error placing Ironclad order for {sig['symbol']}: {e}", exc_info=True)
        else:
            logger.debug("No Ironclad signals found in this scan cycle")
    
    def _execute_dual_strategy(self):
        """Execute both strategies with dual confirmation"""
        # Implementation similar to pattern + ironclad combined
        pass
    
    def _place_entry_order(self, symbol: str, direction: str, entry_price: float,
                          stop_loss: float, target: float, quantity: int, reason: str,
                          ml_signal_id: Optional[str] = None, confidence: float = 95.0):
        """Place entry order with proper logging"""
        from trading.order_manager import OrderType, TransactionType, ProductType
        
        token_info = self.symbol_tokens.get(symbol)
        if not token_info:
            logger.error(f"{symbol}: No token info available")
            return
        
        mode_label = "📝 PAPER" if self.trading_mode == 'paper' else "🔴 LIVE"
        logger.info(f"{mode_label} ENTRY: {symbol}")
        logger.info(f"  Reason: {reason}")
        logger.info(f"  Direction: {direction.upper()}")
        logger.info(f"  Entry: ₹{entry_price:.2f}")
        logger.info(f"  Stop: ₹{stop_loss:.2f}")
        logger.info(f"  Target: ₹{target:.2f}")
        logger.info(f"  Qty: {quantity}")
        logger.info(f"  Confidence: {confidence:.1f}%")
        if ml_signal_id:
            logger.info(f"  ML Signal ID: {ml_signal_id}")
        
        # 🔥 WRITE SIGNAL TO FIRESTORE FOR FRONTEND DISPLAY
        logger.info(f"💾 [DEBUG] Attempting to write {symbol} signal to Firestore...")
        try:
            import firebase_admin
            from firebase_admin import firestore
            from datetime import datetime
            
            db = firestore.client()
            signal_data = {
                'user_id': self.user_id,
                'symbol': symbol,
                'type': 'BUY' if direction == 'up' else 'SELL',
                'signal_type': 'Breakout',  # Could be enhanced with actual pattern type
                'price': entry_price,
                'stop_loss': stop_loss,
                'target': target,
                'quantity': quantity,
                'confidence': confidence / 100.0,  # ✅ FIXED: Use actual calculated confidence (0-1 scale)
                'rationale': reason,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'mode': self.trading_mode,
                'status': 'open'
            }
            if ml_signal_id:
                signal_data['ml_signal_id'] = ml_signal_id
            
            logger.debug(f"📝 [DEBUG] Signal data: {signal_data}")
            doc_ref = db.collection('trading_signals').add(signal_data)
            logger.info(f"✅ [DEBUG] Signal written to Firestore! Doc ID: {doc_ref[1].id}")
            logger.info(f"🎯 SIGNAL GENERATED: {symbol} @ ₹{entry_price:.2f} - Check dashboard NOW!")
            
            # Log signal generation to activity feed
            if self._activity_logger:
                pattern_name = reason.split('Pattern: ')[-1].split(' |')[0] if 'Pattern:' in reason else 'Unknown'
                self._activity_logger.log_signal_generated(
                    symbol=symbol,
                    pattern=pattern_name,
                    confidence=confidence,
                    rr_ratio=(target - entry_price) / (entry_price - stop_loss) if (entry_price - stop_loss) > 0 else 0,
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    profit_target=target
                )
                
        except Exception as e:
            logger.error(f"❌ [DEBUG] Failed to write signal to Firestore: {e}", exc_info=True)
        
        if self.trading_mode == 'live':
            # 🚨 SAFETY CHECKS FOR LIVE TRADING
            try:
                # Check 1: Verify market is open
                if not self._is_market_open():
                    logger.error(f"❌ SAFETY: Cannot place order - market is closed")
                    return
                
                # Check 2: Check position limit
                current_positions = self._position_manager.get_all_positions()
                max_positions = 5  # Safety limit
                if len(current_positions) >= max_positions:
                    logger.error(f"❌ SAFETY: Max positions ({max_positions}) reached")
                    return
                
                # Check 3: Verify not already in position for this symbol
                if symbol in current_positions:
                    logger.warning(f"⚠️  SAFETY: Already in position for {symbol} - skipping")
                    return
                
                logger.info("✅ SAFETY: All pre-order checks passed")
                
            except Exception as safety_err:
                logger.error(f"❌ SAFETY CHECK FAILED: {safety_err}")
                return
            
            # Place real order with enhanced error handling
            transaction_type = TransactionType.BUY if direction == 'up' else TransactionType.SELL
            
            try:
                order_result = self._order_manager.place_order(
                    symbol=symbol,
                    token=token_info['token'],
                    exchange=token_info['exchange'],
                    transaction_type=transaction_type,
                    order_type=OrderType.MARKET,
                    quantity=quantity,
                    product_type=ProductType.INTRADAY
                )
            except Exception as order_err:
                logger.error(f"❌ CRITICAL: Order placement exception for {symbol}: {order_err}", exc_info=True)
                # Don't create position if order failed
                return
            
            if order_result:
                order_id = order_result.get('orderid', 'unknown')
                logger.info(f"✅ LIVE order placed: {order_id}")
                
                # Create position data with ML signal ID
                position_data = {
                    'symbol': symbol,
                    'entry_price': entry_price,
                    'quantity': quantity,
                    'stop_loss': stop_loss,
                    'target': target,
                    'order_id': order_id
                }
                if ml_signal_id:
                    position_data['ml_signal_id'] = ml_signal_id
                
                self._position_manager.add_position(**position_data)
            else:
                logger.error(f"❌ Failed to place LIVE order for {symbol}")
        else:
            # Paper trading
            position_data = {
                'symbol': symbol,
                'entry_price': entry_price,
                'quantity': quantity,
                'stop_loss': stop_loss,
                'target': target,
                'order_id': f"PAPER_{symbol}_{int(time.time())}"
            }
            if ml_signal_id:
                position_data['ml_signal_id'] = ml_signal_id
            
            self._position_manager.add_position(**position_data)
            logger.info(f"✅ Paper position added")
    
    def _monitor_positions(self):
        """
        Monitor all open positions for stop loss/target hits.
        Uses REAL-TIME prices from WebSocket (not candle data).
        Runs every 0.5 seconds for instant detection.
        """
        try:
            # Position reconciliation every 60 seconds (120 iterations * 0.5s)
            if not hasattr(self, '_reconcile_counter'):
                self._reconcile_counter = 0
            self._reconcile_counter += 1
            
            if self._reconcile_counter >= 120:  # Every 60 seconds
                self._reconcile_positions()
                self._reconcile_counter = 0
            
            # Daily P&L calculation at market close (3:15 PM IST)
            from datetime import datetime
            now = datetime.now()
            if now.hour == 15 and now.minute == 15 and not hasattr(self, '_daily_pnl_done'):
                self._calculate_daily_pnl()
                self._daily_pnl_done = True
            elif now.hour != 15 or now.minute != 15:
                # Reset flag for next day
                if hasattr(self, '_daily_pnl_done'):
                    delattr(self, '_daily_pnl_done')
            
            positions = self._position_manager.get_all_positions()
            
            if not positions:
                return
            
            # Get latest prices (thread-safe)
            with self._lock:
                current_prices = self.latest_prices.copy()
            
            # CRITICAL: Warn if no price data available
            if not current_prices:
                if not hasattr(self, '_no_price_warning_logged'):
                    logger.error("⚠️  CRITICAL: No price data available - positions cannot be monitored!")
                    logger.error("⚠️  WebSocket may not be connected or not receiving ticks")
                    self._no_price_warning_logged = True
                return
            
            for symbol, position in positions.items():
                # Get real-time price
                current_price = current_prices.get(symbol)
                
                if current_price is None:
                    continue
                
                entry_price = position.get('entry_price', 0)
                stop_loss = position.get('stop_loss', 0)
                target = position.get('target', 0)
                
                # Check stop loss (instant detection)
                if current_price <= stop_loss:
                    logger.warning(f"🛑 STOP LOSS HIT: {symbol} @ ₹{current_price:.2f}")
                    self._close_position(symbol, position, current_price, 'STOP_LOSS')
                    continue
                
                # Check target (instant detection)
                if current_price >= target:
                    logger.info(f"🎯 TARGET HIT: {symbol} @ ₹{current_price:.2f}")
                    self._close_position(symbol, position, current_price, 'TARGET')
                    continue
                
        except Exception as e:
            logger.error(f"Error monitoring positions: {e}")
    
    def _close_position(self, symbol: str, position: Dict, exit_price: float, reason: str):
        """Close position with real-time exit order"""
        from trading.order_manager import OrderType, TransactionType, ProductType
        
        entry_price = position.get('entry_price', 0)
        quantity = position.get('quantity', 0)
        entry_time = position.get('timestamp', datetime.now())
        
        pnl = (exit_price - entry_price) * quantity
        pnl_percent = ((exit_price - entry_price) / entry_price) * 100
        
        # Calculate holding duration
        if isinstance(entry_time, str):
            from dateutil import parser
            entry_time = parser.parse(entry_time)
        holding_duration = (datetime.now() - entry_time).total_seconds() / 60  # minutes
        
        logger.info(f"CLOSING {symbol}:")
        logger.info(f"  Entry: ₹{entry_price:.2f} | Exit: ₹{exit_price:.2f}")
        logger.info(f"  P&L: ₹{pnl:.2f} ({pnl_percent:+.2f}%)")
        logger.info(f"  Duration: {holding_duration:.1f} minutes")
        logger.info(f"  Reason: {reason}")
        
        # 🔥 PLACE ACTUAL EXIT ORDER (LIVE MODE)
        if self.trading_mode == 'live':
            try:
                token_info = self.symbol_tokens.get(symbol)
                if token_info:
                    logger.info(f"📤 Placing LIVE exit order for {symbol}")
                    exit_order = self._order_manager.place_order(
                        symbol=symbol,
                        token=token_info['token'],
                        exchange=token_info['exchange'],
                        transaction_type=TransactionType.SELL,
                        order_type=OrderType.MARKET,
                        quantity=quantity,
                        product_type=ProductType.INTRADAY
                    )
                    
                    if exit_order:
                        order_id = exit_order.get('orderid', 'unknown')
                        logger.info(f"✅ LIVE exit order placed: {order_id}")
                    else:
                        logger.error(f"❌ Failed to place exit order for {symbol}")
                else:
                    logger.error(f"❌ Token info not found for {symbol}")
            except Exception as order_err:
                logger.error(f"❌ Exit order placement failed: {order_err}", exc_info=True)
        
        # 🔥 WRITE EXIT SIGNAL TO FIRESTORE
        try:
            import firebase_admin
            from firebase_admin import firestore
            
            db = firestore.client()
            exit_signal_data = {
                'user_id': self.user_id,
                'symbol': symbol,
                'type': 'SELL',
                'signal_type': reason.replace('_', ' ').title(),
                'price': exit_price,
                'pnl': pnl,
                'pnl_percent': pnl_percent,
                'rationale': f"{reason.replace('_', ' ').title()} - P&L: ₹{pnl:.2f} ({pnl_percent:+.2f}%)",
                'timestamp': firestore.SERVER_TIMESTAMP,
                'mode': self.trading_mode,
                'status': 'closed',
                'holding_duration_minutes': int(holding_duration)
            }
            
            db.collection('trading_signals').add(exit_signal_data)
            logger.info(f"✅ Exit signal written to Firestore for {symbol}")
        except Exception as e:
            logger.error(f"Failed to write exit signal to Firestore: {e}")
        
        # Update ML outcome
        ml_signal_id = position.get('ml_signal_id')
        if ml_signal_id and self._ml_logger and self._ml_logger.enabled:
            try:
                # Determine outcome
                if pnl_percent > 0.5:
                    outcome = 'WIN'
                elif pnl_percent < -0.5:
                    outcome = 'LOSS'
                else:
                    outcome = 'BREAKEVEN'
                
                # Map exit reason and log outcome
                self._ml_logger.log_outcome(ml_signal_id, outcome, pnl_percent)
            except Exception as e:
                logger.error(f"Failed to log ML outcome: {e}")
    
    def _reconcile_positions(self):
        """Cross-check bot's positions with broker's actual positions"""
        try:
            if self.trading_mode != 'live':
                return  # Only reconcile in live mode
            
            # Get broker's actual positions
            broker_positions = self._order_manager.get_positions()
            if not broker_positions:
                logger.debug("No broker positions returned (may be zero open positions)")
                return
            
            # Get bot's tracked positions
            bot_positions = self._position_manager.get_all_positions()
            
            broker_symbols = set()
            if isinstance(broker_positions, dict):
                # Parse broker positions (format: {'data': [positions...]})
                broker_data = broker_positions.get('data', [])
                for pos in broker_data:
                    if pos.get('netqty', '0') != '0':  # Has open quantity
                        broker_symbols.add(pos['tradingsymbol'])
            
            bot_symbols = {pos['symbol'] for pos in bot_positions.values()}
            
            # Find discrepancies
            bot_only = bot_symbols - broker_symbols
            broker_only = broker_symbols - bot_symbols
            
            if bot_only:
                logger.warning(f"⚠️ POSITION MISMATCH: Bot has {bot_only} but broker doesn't")
                # Auto-close phantom positions
                for symbol in bot_only:
                    logger.warning(f"Removing phantom position: {symbol}")
                    self._position_manager.close_position(symbol)
            
            if broker_only:
                logger.warning(f"⚠️ POSITION MISMATCH: Broker has {broker_only} but bot doesn't track them")
                # Don't auto-close - user may have manual positions
            
            if not bot_only and not broker_only:
                logger.debug("✅ Position reconciliation: All positions match")
                
        except Exception as e:
            logger.error(f"Position reconciliation error: {e}", exc_info=True)
    
    def _calculate_daily_pnl(self):
        """Calculate and report end-of-day P&L"""
        try:
            from datetime import datetime, timedelta
            import firebase_admin
            from firebase_admin import firestore
            
            db = firestore.client()
            today = datetime.now().date()
            
            # Query all closed positions for today
            today_start = datetime.combine(today, datetime.min.time())
            
            # Get all exit signals from today
            exit_signals = db.collection('trading_signals')\
                .where('user_id', '==', self.user_id)\
                .where('status', '==', 'closed')\
                .where('timestamp', '>=', today_start)\
                .stream()
            
            total_pnl = 0.0
            win_count = 0
            loss_count = 0
            total_trades = 0
            
            for signal in exit_signals:
                data = signal.to_dict()
                pnl = data.get('pnl', 0)
                total_pnl += pnl
                total_trades += 1
                
                if pnl > 0:
                    win_count += 1
                elif pnl < 0:
                    loss_count += 1
            
            # Calculate metrics
            win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
            
            # Write daily summary to Firestore
            daily_summary = {
                'user_id': self.user_id,
                'date': today.isoformat(),
                'total_pnl': total_pnl,
                'total_trades': total_trades,
                'win_count': win_count,
                'loss_count': loss_count,
                'win_rate': win_rate,
                'trading_mode': self.trading_mode,
                'timestamp': firestore.SERVER_TIMESTAMP
            }
            
            # Use date as document ID for easy querying
            db.collection('daily_pnl').document(f"{self.user_id}_{today.isoformat()}").set(daily_summary)
            
            logger.info(f"📊 DAILY P&L SUMMARY ({today.isoformat()}):")
            logger.info(f"  Total P&L: ₹{total_pnl:,.2f}")
            logger.info(f"  Trades: {total_trades} (W: {win_count}, L: {loss_count})")
            logger.info(f"  Win Rate: {win_rate:.1f}%")
            logger.info(f"  Mode: {self.trading_mode.upper()}")
            
            return daily_summary
            
        except Exception as e:
            logger.error(f"Failed to calculate daily P&L: {e}", exc_info=True)
            return None

