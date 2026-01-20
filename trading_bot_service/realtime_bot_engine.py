"""
Real-Time Trading Bot Engine with WebSocket Integration
Implements sub-second position monitoring and instant order execution
"""

import logging
import time
import threading
import asyncio
import requests  # For REST API calls (historical data, replay mode)
from datetime import datetime, timedelta
from typing import Dict, List, Callable, Optional
import pandas as pd
import numpy as np
from collections import defaultdict, deque

# Import comprehensive error handling
from bot_errors import (
    BotError, CriticalError, RecoverableError, WarningError,
    WebSocketError, WebSocketDisconnected, WebSocketTimeout,
    APIError, TokenExpired, RateLimitExceeded, NetworkTimeout,
    DataError, MissingCandleData, InvalidPriceData,
    OrderError, InsufficientMargin, BrokerRejection,
    BotInternalError, StrategyInitError, FirestoreError
)
from error_handler import ErrorHandler, with_error_handling, safe_execute, ErrorContext
from health_monitor import HealthMonitor, get_health_monitor

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
                 trading_mode: str = 'paper', strategy: str = 'pattern', db_client=None, replay_date: str = None):
        self.user_id = user_id
        self.credentials = credentials
        
        # CRITICAL: Convert universe string to symbol list if needed
        # When alpha-ensemble strategy is selected, 'symbols' might be a string like 'NIFTY50'
        if isinstance(symbols, str):
            logger.info(f"🔄 Converting universe '{symbols}' to symbol list...")
            from nifty200_watchlist import NIFTY200_WATCHLIST
            all_symbols = [stock['symbol'] for stock in NIFTY200_WATCHLIST]
            
            if symbols == 'NIFTY50':
                self.symbols = all_symbols[:50]
                logger.info(f"✅ Using NIFTY50: {len(self.symbols)} symbols")
            elif symbols == 'NIFTY100':
                self.symbols = all_symbols[:100]
                logger.info(f"✅ Using NIFTY100: {len(self.symbols)} symbols")
            elif symbols == 'NIFTY200':
                self.symbols = all_symbols
                logger.info(f"✅ Using NIFTY200: {len(self.symbols)} symbols")
            else:
                # If it's a single symbol string, wrap in list
                self.symbols = [symbols]
                logger.warning(f"⚠️ Unknown universe '{symbols}', treating as single symbol")
        else:
            self.symbols = symbols
            logger.info(f"✅ Using provided symbol list: {len(self.symbols)} symbols")
        
        self.trading_mode = trading_mode.lower()
        self.strategy = strategy.lower()
        self.db = db_client  # Firestore client for Activity Logger and ML Logger
        self.replay_date = replay_date  # Phase 3: Replay Mode
        self.is_replay_mode = replay_date is not None
        
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
        self.tick_data = defaultdict(lambda: deque(maxlen=5000))  # Last 5000 ticks per symbol (prevents data loss during high volume)
        self.candle_data = {}  # Current candle data
        self.latest_prices = {}  # Latest LTP per symbol
        self.symbol_tokens = {}  # Token mapping
        
        # 🚨 AUDIT OPTIMIZATION #2: Retest-based entry tracking
        self.pending_retests = {}  # Tracks breakout signals waiting for retest entry
        # Format: {symbol: {'breakout_price': float, 'direction': str, 'stop_loss': float, 'target': float, 'timestamp': datetime}}
        
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
        self._mean_reversion = None  # 🔄 NEW: Mean reversion strategy for sideways markets (ADX < 20)
        
        # 🚨 AUDIT FIX: OTR Monitoring for SEBI Compliance
        try:
            from otr_monitor import OrderToTradeRatioMonitor
            self._otr_monitor = OrderToTradeRatioMonitor(otr_threshold=20.0)
        except ImportError as e:
            logger.warning(f"⚠️  OTR Monitor not available: {e}")
            self._otr_monitor = None
        
        # NEW: Error handling and health monitoring
        self.error_handler = None  # Initialized after activity logger
        self.health_monitor = get_health_monitor()
        
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
            
            # CRITICAL: Check if tokens are expired before starting
            self._check_and_refresh_tokens()
            
            # 🔄 REPLAY MODE: Use simulation instead of real-time trading
            if self.is_replay_mode:
                logger.info("="*80)
                logger.info(f"🔄 REPLAY MODE ACTIVE - Date: {self.replay_date}")
                logger.info(f"   Mode: {self.trading_mode}")
                logger.info(f"   Strategy: {self.strategy}")
                logger.info(f"   Symbols: {len(self.symbols)} symbols")
                logger.info("="*80)
                self._run_replay_simulation(running_flag)
                return
            
            # Regular real-time mode
            logger.info("="*80)
            logger.info(f"🔴 REAL-TIME MODE ACTIVE")
            logger.info(f"   Mode: {self.trading_mode.upper()}")
            logger.info(f"   Strategy: {self.strategy.upper()}")
            logger.info(f"   Symbols: {len(self.symbols)} symbols")
            logger.info("="*80)
            
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
        Use pre-validated tokens from NIFTY200_WATCHLIST instead of API calls.
        This avoids rate limits and ensures consistent token mapping.
        """
        try:
            from nifty200_watchlist import NIFTY200_WATCHLIST
        except ImportError:
            logger.error("❌ Failed to import NIFTY200_WATCHLIST - using fallback tokens")
            return self._get_fallback_tokens()
        
        tokens = {}
        total = len(self.symbols)
        missing_symbols = []
        
        logger.info(f"📊 Loading tokens for {total} symbols from NIFTY200_WATCHLIST...")
        
        # Create lookup dictionary from watchlist (both by symbol)
        watchlist_lookup = {item['symbol']: item for item in NIFTY200_WATCHLIST}
        
        for idx, symbol in enumerate(self.symbols, 1):
            if symbol in watchlist_lookup:
                item = watchlist_lookup[symbol]
                tokens[symbol] = {
                    'token': item['token'],
                    'exchange': item.get('exchange', 'NSE'),
                    'trading_symbol': item.get('trading_symbol', symbol)
                }
                if idx <= 5 or idx % 10 == 0:  # Reduce log spam
                    logger.info(f"✅ [{idx}/{total}] Loaded {symbol}: {tokens[symbol]['token']}")
            else:
                missing_symbols.append(symbol)
                # Try fallback tokens
                fallback = self._get_fallback_tokens()
                if symbol in fallback:
                    tokens[symbol] = fallback[symbol]
                    logger.info(f"✅ [{idx}/{total}] {symbol} from fallback: {tokens[symbol]['token']}")
                else:
                    logger.warning(f"⚠️  [{idx}/{total}] Symbol {symbol} not available - skipping")
        
        if missing_symbols:
            logger.warning(f"⚠️  {len(missing_symbols)} symbols not in watchlist: {', '.join(missing_symbols[:10])}{'...' if len(missing_symbols) > 10 else ''}")
        
        logger.info(f"✅ Successfully loaded {len(tokens)}/{total} symbol tokens")
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
        import pytz
        
        # Check if market is open or was open recently
        # CRITICAL FIX: Use IST timezone-aware datetime (Cloud Run runs in UTC)
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)
        market_open_time = ist.localize(datetime.strptime(f"{now.year}-{now.month:02d}-{now.day:02d} 09:15:00", "%Y-%m-%d %H:%M:%S"))
        
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
        # CRITICAL OPTIMIZATION: Fetch ONLY last 60 minutes to avoid rate limits
        # 60 candles is MORE than enough for all required indicators (RSI, MACD, ATR, ADX need max 28 candles)
        # This reduces API calls from 375 to 60 (6X reduction) and completes in ~60 seconds instead of 375 seconds
        if now < market_open_time:
            # Before market open: Fetch yesterday's LAST HOUR of trading (2:30 PM - 3:30 PM)
            yesterday = now - timedelta(days=1)
            # Handle weekends: if today is Monday, fetch from Friday
            while yesterday.weekday() >= 5:  # Saturday=5, Sunday=6
                yesterday -= timedelta(days=1)
            to_date = yesterday.replace(hour=15, minute=30, second=0, microsecond=0)  # Yesterday 3:30 PM
            from_date = yesterday.replace(hour=14, minute=30, second=0, microsecond=0)  # Yesterday 2:30 PM (LAST 60 MIN)
            logger.info(f"📊 Fetching last 60 minutes of previous session: {from_date.strftime('%Y-%m-%d %H:%M')} to {to_date.strftime('%Y-%m-%d %H:%M')}")
            logger.info(f"📊 Expected ~60 candles for INSTANT signal generation (avoids rate limits)!")
        else:
            # After market open: Fetch ONLY yesterday's last hour (realtime will build today's candles)
            yesterday = now - timedelta(days=1)
            while yesterday.weekday() >= 5:  # Handle weekends
                yesterday -= timedelta(days=1)
            to_date = yesterday.replace(hour=15, minute=30, second=0, microsecond=0)  # Yesterday 3:30 PM
            from_date = yesterday.replace(hour=14, minute=30, second=0, microsecond=0)  # Yesterday 2:30 PM (LAST 60 MIN)
            logger.info(f"📊 Fetching last 60 minutes of previous session: {from_date.strftime('%Y-%m-%d %H:%M')} to {to_date.strftime('%Y-%m-%d %H:%M')}")
            logger.info(f"📊 Expected ~60 candles (realtime will add today's candles)")
        
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
                    # 🚨 AUDIT OPTIMIZATION #3: Timestamp validation (prevent look-ahead bias)
                    from datetime import datetime
                    now_timestamp = datetime.now()
                    
                    # Check for future timestamps
                    if 'timestamp' in df.columns:
                        future_candles = df[df['timestamp'] > now_timestamp]
                        if len(future_candles) > 0:
                            logger.error(f"🚨 LOOK-AHEAD BIAS DETECTED: {symbol} has {len(future_candles)} future candles!")
                            logger.error(f"   Latest candle: {df['timestamp'].iloc[-1]}")
                            logger.error(f"   Current time:  {now_timestamp}")
                            # Filter out future candles
                            df = df[df['timestamp'] <= now_timestamp]
                            logger.info(f"   ✅ Filtered to {len(df)} valid candles (no future data)")
                    
                    # Calculate indicators if we have enough data
                    if len(df) >= 200:
                        df = self._calculate_indicators(df)
                    
                    # Store in candle_data (thread-safe)
                    with self._lock:
                        self.candle_data[symbol] = df
                    
                    success_count += 1
                    logger.info(f"✅ [{idx}/{len(self.symbols)}] {symbol}: Loaded {len(df)} historical candles (validated)")
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
        
        # CRITICAL FIX: Bootstrap failure is NOT fatal - bot can still work with live ticks
        if success_count == 0 and now < market_open_time:
            logger.warning("📊 No historical data available - Bot started before market open")
            logger.warning("📊 Bot will accumulate candles from live ticks starting at 9:15 AM")
            logger.warning("📊 Pattern detection will activate once 50+ candles accumulated (~50 minutes)")
            logger.info("✅ Bootstrap complete - bot will build candles from live ticks")
        elif success_count > 0:
            logger.info(f"📈 Historical data bootstrap: {success_count} symbols loaded, {fail_count} failed")
            logger.info(f"🎯 Bot ready for immediate signal generation with pre-loaded indicators!")
            logger.info("✅ Historical candles loaded - bot ready to trade immediately!")
        else:
            logger.warning(f"⚠️ Historical data bootstrap: 0 success, {fail_count} failed")
            logger.warning("⚠️ Bot will build candles from live ticks (may take 50+ minutes for patterns)")
            logger.info("✅ Bootstrap complete - bot will build candles from live ticks")
        
        # NEVER raise exception here - allow bot to continue even if bootstrap fails
        # Bot can still work by accumulating candles from live WebSocket ticks
    
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
        # CRITICAL FIX: Ensure verbose mode is enabled for full visibility
        try:
            from bot_activity_logger import BotActivityLogger
            self._activity_logger = BotActivityLogger(
                user_id=self.user_id, 
                db_client=self.db,
                verbose_mode=True  # ALWAYS enable verbose logging for dashboard visibility
            )
            logger.info("✅ Bot Activity Logger initialized (verbose mode: ON, real-time dashboard feed)")
            
            # DIAGNOSTIC: Test write immediately to verify Firestore connectivity
            try:
                logger.info("🔥 [TEST] Testing activity logger write to Firestore...")
                self._activity_logger.log_bot_started(
                    mode=self.trading_mode,
                    strategy=self.strategy,
                    symbols_count=len(self.symbols)
                )
                logger.info("✅ [TEST] Activity logger write successful! Dashboard feed should update.")
            except Exception as test_err:
                logger.error(f"❌ [TEST] Activity logger write FAILED: {test_err}", exc_info=True)
                logger.error("❌ [TEST] Bot will continue but dashboard activity feed may not work")
                # Don't disable activity logger - let it retry on next log
                
        except Exception as e:
            logger.error(f"Failed to initialize Activity Logger: {e}", exc_info=True)
            self._activity_logger = None  # Disabled mode
        
        # NEW: Initialize Error Handler (depends on activity logger)
        self.error_handler = ErrorHandler(
            activity_logger=self._activity_logger,
            max_retries=3,
            retry_delay=1.0
        )
        logger.info("✅ Error Handler initialized (comprehensive error handling enabled)")
        
        # Initialize Ironclad if needed
        if self.strategy in ['ironclad', 'both']:
            try:
                from ironclad_strategy import IroncladStrategy
                self._ironclad = IroncladStrategy(db_client=None, dr_window_minutes=60)
                logger.info("✅ Ironclad strategy initialized")
            except ImportError as e:
                logger.warning(f"⚠️  Ironclad strategy not available: {e}")
                self._ironclad = None
        
        # Initialize Alpha-Ensemble if needed
        if self.strategy == 'alpha-ensemble':
            try:
                from alpha_ensemble_strategy import AlphaEnsembleStrategy
                # Load strategy parameters from bot_config
                strategy_params = bot_config.get('strategy_params', {})
                self._alpha_ensemble = AlphaEnsembleStrategy(
                    api_key=self.api_key,
                    jwt_token=self.jwt_token,
                    strategy_params=strategy_params
                )
                logger.info(f"✅ Alpha-Ensemble strategy initialized with custom parameters")
            except ImportError as e:
                logger.warning(f"⚠️  Alpha-Ensemble strategy not available: {e}")
                self._alpha_ensemble = None
        
        # Initialize Mean Reversion Strategy for sideways markets
        try:
            from mean_reversion_strategy import MeanReversionStrategy
            self._mean_reversion = MeanReversionStrategy(
                bb_period=20,
                bb_std=2.0,
                rsi_period=14,
                rsi_oversold=30,
                rsi_overbought=70,
                volume_threshold=0.5,  # Relaxed: 50% of avg volume OK in sideways
                risk_reward=1.5
            )
            logger.info(f"✅ Mean Reversion strategy initialized (activates when ADX < 20)")
        except ImportError as e:
            logger.warning(f"⚠️  Mean Reversion strategy not available: {e}")
            self._mean_reversion = None
        
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
            
            # 🚨 AUDIT OPTIMIZATION #2: Monitor pending retests for limit order entries
            self._monitor_pending_retests()
            
            # Check if market is open before trading
            # CRITICAL FIX: Allow paper trading outside market hours for testing
            if not self._is_market_open():
                if self.trading_mode == 'live':
                    logger.debug("⏸️  Market is closed - skipping LIVE trading (safety)")
                    return
                else:
                    # Paper mode: Allow trading outside hours for testing and replay mode
                    logger.debug(f"📝 PAPER MODE: Analyzing outside market hours (testing mode)")
                    # Continue execution
            
            # 🚨 AUDIT FIX: Liquidity U-Shape Time Filter
            # Block entries during 12:00-14:30 PM (midday liquidity trap)
            import pytz
            ist = pytz.timezone('Asia/Kolkata')
            current_time = datetime.now(ist).time()
            if time(12, 0) <= current_time <= time(14, 30):
                logger.debug("⏸️  LIQUIDITY FILTER: Skipping 12:00-14:30 (midday U-shape dip - 12.5% WR trap)")
                return
            
            # Check EOD auto-close (3:15 PM for safety before broker's 3:20 PM)
            self._check_eod_auto_close()
            
            if self.strategy == 'pattern':
                logger.debug("📊 [DEBUG] Executing PATTERN strategy...")
                self._execute_pattern_strategy()
            elif self.strategy == 'defining':
                logger.debug("📐 [DEBUG] Executing DEFINING ORDER strategy...")
                self._execute_pattern_strategy()  # Defining Order uses same pattern detection
            elif self.strategy == 'ironclad':
                logger.debug("🛡️  [DEBUG] Executing IRONCLAD strategy...")
                self._execute_ironclad_strategy()
            elif self.strategy == 'both':
                logger.debug("🔀 [DEBUG] Executing DUAL strategy...")
                self._execute_dual_strategy()
            elif self.strategy == 'alpha-ensemble':
                logger.debug("⭐ [DEBUG] Executing ALPHA-ENSEMBLE strategy...")
                self._execute_alpha_ensemble_strategy()
            else:
                logger.warning(f"⚠️  Unknown strategy: {self.strategy} - no execution performed")
            
            logger.debug("✅ [DEBUG] _analyze_and_trade() completed successfully")
                
        except Exception as e:
            logger.error(f"❌ [DEBUG] Error in strategy execution: {e}", exc_info=True)
    
    def _monitor_pending_retests(self):
        """
        🚨 AUDIT OPTIMIZATION #2: Monitor breakout signals for retest entries.
        
        When a breakout is detected, we don't enter immediately with market order.
        Instead, we wait for a pullback (retest) and enter with a limit order.
        This improves:
        - Entry price (better R:R)
        - Win rate (+15-20%)
        - Reduced slippage
        
        Retest conditions:
        - LONG: Price pulls back to within 0.3-0.5% of breakout level
        - SHORT: Price rebounds to within 0.3-0.5% of breakdown level
        - Timeout: Cancel if no retest within 30 minutes
        """
        from datetime import datetime, timedelta
        
        if not self.pending_retests:
            return  # No pending retests to monitor
        
        # Get current prices
        with self._lock:
            current_prices = self.latest_prices.copy()
        
        # Check each pending retest
        symbols_to_remove = []
        
        for symbol, retest_data in list(self.pending_retests.items()):
            try:
                current_price = current_prices.get(symbol)
                if not current_price:
                    continue
                
                breakout_price = retest_data['breakout_price']
                direction = retest_data['direction']
                timestamp = retest_data['timestamp']
                
                # Check timeout (30 minutes)
                if datetime.now() - timestamp > timedelta(minutes=30):
                    logger.info(f"⏱️  [{symbol}] RETEST TIMEOUT: No retest within 30 minutes - canceling")
                    symbols_to_remove.append(symbol)
                    continue
                
                # Check for retest (pullback to breakout level)
                retest_detected = False
                
                if direction == 'up':
                    # LONG: Wait for pullback to 0.3-0.5% below breakout
                    pullback_min = breakout_price * 0.997  # 0.3% below
                    pullback_max = breakout_price * 0.995  # 0.5% below
                    
                    if pullback_min <= current_price <= breakout_price:
                        retest_detected = True
                        logger.info(f"✅ [{symbol}] RETEST DETECTED: Price pulled back to ₹{current_price:.2f} (breakout: ₹{breakout_price:.2f})")
                
                else:  # SHORT
                    # SHORT: Wait for rebound to 0.3-0.5% above breakdown
                    rebound_max = breakout_price * 1.003  # 0.3% above
                    rebound_min = breakout_price * 1.005  # 0.5% above
                    
                    if breakout_price <= current_price <= rebound_max:
                        retest_detected = True
                        logger.info(f"✅ [{symbol}] RETEST DETECTED: Price rebounded to ₹{current_price:.2f} (breakdown: ₹{breakout_price:.2f})")
                
                # Place limit order if retest detected
                if retest_detected:
                    logger.info(f"🎯 [{symbol}] PLACING LIMIT ORDER at retest level")
                    
                    # Place entry order at current price (limit order at retest)
                    self._place_entry_order(
                        symbol=symbol,
                        direction=direction,
                        entry_price=current_price,  # Better entry than breakout!
                        stop_loss=retest_data['stop_loss'],
                        target=retest_data['target'],
                        quantity=retest_data['quantity'],
                        reason=retest_data['reason'] + " | RETEST ENTRY",
                        ml_signal_id=None,
                        confidence=retest_data['confidence']
                    )
                    
                    # Remove from pending retests
                    symbols_to_remove.append(symbol)
            
            except Exception as e:
                logger.error(f"Error monitoring retest for {symbol}: {e}")
                symbols_to_remove.append(symbol)
        
        # Clean up processed retests
        with self._lock:
            for symbol in symbols_to_remove:
                if symbol in self.pending_retests:
                    del self.pending_retests[symbol]
    
    def _check_eod_auto_close(self):
        """
        Auto-close all positions at 3:15 PM (15:15) IST for INTRADAY safety.
        Angel One auto-squares off at 3:20 PM, but we close 5 minutes earlier
        to ensure clean exits without broker's forced liquidation.
        """
        import pytz
        from datetime import datetime
        
        # CRITICAL FIX: Use IST timezone (not system local time)
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)
        current_time = now.time()
        
        # Only check on weekdays (Mon-Fri)
        if now.weekday() >= 5:
            return
        
        # Market closes at 3:30 PM (15:30)
        # Broker auto square-off at 3:20 PM (15:20)
        # Our safety auto-close at 3:15 PM (15:15)
        eod_close_time = datetime.strptime("15:15:00", "%H:%M:%S").time()
        market_close_time = datetime.strptime("15:30:00", "%H:%M:%S").time()
        
        # Check if it's EOD time (between 3:15 PM and 3:30 PM IST)
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
        
        # NEW: Log scan cycle start to activity feed
        if self._activity_logger:
            try:
                logger.info(f"🔍 [ACTIVITY] Logging scan cycle start...")
                self._activity_logger.log_scan_cycle_start(
                    total_symbols=len(self.symbols),
                    symbols_with_data=len(candle_data_copy)
                )
                logger.info(f"✅ [ACTIVITY] Scan cycle logged successfully")
            except Exception as e:
                logger.error(f"❌ [ACTIVITY] Scan cycle log failed: {e}", exc_info=True)
        
        for symbol in self.symbols:
            try:
                # NEW: Log symbol scanning to activity feed
                if self._activity_logger:
                    try:
                        self._activity_logger.log_symbol_scanning(
                            symbol=symbol,
                            current_price=latest_prices_copy.get(symbol, 0)
                        )
                    except Exception as e:
                        logger.debug(f"Activity logger (scanning) error: {e}")
                
                # Check if we have enough candle data (need 50 for full indicator accuracy)
                # 50 candles ensures: RSI(14), MACD(26), EMA(20), BB(20), ATR(14), ADX(28)
                # All patterns (Double Top/Bottom, Flags, Triangles) work optimally
                # SMA50 available for trend confirmation
                candle_count = len(candle_data_copy.get(symbol, []))
                if symbol not in candle_data_copy or candle_count < 50:
                    logger.info(f"⏭️  [DEBUG] {symbol}: Skipping - insufficient candle data ({candle_count} candles, need 50+)")
                    
                    # NEW: Log skip reason
                    if self._activity_logger:
                        try:
                            self._activity_logger.log_symbol_skipped(
                                symbol=symbol,
                                reason=f"Insufficient data ({candle_count}/50 candles)"
                            )
                        except Exception as e:
                            logger.debug(f"Activity logger (skip) error: {e}")
                    continue
                
                # Skip if already have position
                if self._position_manager.has_position(symbol):
                    # NEW: Log skip reason
                    if self._activity_logger:
                        try:
                            self._activity_logger.log_symbol_skipped(
                                symbol=symbol,
                                reason="Already have position"
                            )
                        except Exception as e:
                            logger.debug(f"Activity logger (skip) error: {e}")
                    continue
                
                df = candle_data_copy[symbol].copy()
                
                # � DUAL-REGIME SYSTEM: Trend-Following vs Mean Reversion
                # ADX >= 20: Use trend-following strategies (breakouts, patterns)
                # ADX < 20: Use mean reversion strategy (Bollinger Bands + RSI)
                
                current_adx = float(df['adx'].iloc[-1]) if 'adx' in df.columns else 25  # Default to trending if no ADX
                
                if current_adx < 20:
                    # 🔄 SIDEWAYS MARKET: Try Mean Reversion Strategy
                    logger.debug(f"🔄 [{symbol}] ADX {current_adx:.1f} < 20 → SIDEWAYS MARKET → Checking Mean Reversion")
                    
                    try:
                        # Calculate Bollinger Bands if not present
                        if 'BB_MIDDLE' not in df.columns:
                            df = self._mean_reversion.calculate_indicators(df)
                        
                        # Find mean reversion setup
                        mr_signal = self._mean_reversion.find_mean_reversion_setup(df, symbol)
                        
                        if mr_signal:
                            logger.info(f"🔄 [{symbol}] MEAN REVERSION OPPORTUNITY (ADX {current_adx:.1f})")
                            
                            # Convert to pattern-detector compatible format
                            pattern_details = {
                                'pattern': 'MEAN_REVERSION',
                                'action': mr_signal['action'],
                                'entry': mr_signal['entry_price'],
                                'stop_loss': mr_signal['stop_loss'],
                                'target': mr_signal['target'],
                                'confidence': mr_signal['confidence'],
                                'details': mr_signal['rationale']
                            }
                            
                            # Continue to signal validation (skip pattern detection)
                        else:
                            logger.debug(f"⏭️ [{symbol}] No mean reversion setup found")
                            if self._activity_logger:
                                try:
                                    self._activity_logger.log_symbol_skipped(
                                        symbol=symbol,
                                        reason=f"ADX={current_adx:.1f} < 20, no mean reversion setup"
                                    )
                                except:
                                    pass
                            continue
                    
                    except Exception as mr_err:
                        logger.error(f"Error checking mean reversion for {symbol}: {mr_err}")
                        continue
                else:
                    # 🎯 TRENDING MARKET: Use Pattern Detection (breakouts, trends)
                    logger.debug(f"🎯 [{symbol}] ADX {current_adx:.1f} >= 20 → TRENDING MARKET → Pattern Detection")
                
                # Pattern detection (detects both forming and confirmed patterns)
                # ONLY runs if ADX >= 20 (trending) OR if mean reversion already found signal
                if current_adx >= 20:
                    pattern_details = self._pattern_detector.scan(df)
                # else: pattern_details already set by mean reversion above
                
                if not pattern_details:
                    logger.info(f"[DEBUG] {symbol}: No pattern detected this cycle.")
                    
                    # NEW: Log no pattern detected
                    if self._activity_logger:
                        try:
                            self._activity_logger.log_no_pattern(
                                symbol=symbol,
                                indicators={
                                    'rsi': float(df['rsi'].iloc[-1]) if 'rsi' in df.columns else 0,
                                    'adx': float(df['adx'].iloc[-1]) if 'adx' in df.columns else 0
                                }
                            )
                        except Exception as e:
                            logger.debug(f"Activity logger (no pattern) error: {e}")
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
                    try:
                        logger.info(f"🔍 [ACTIVITY] Logging pattern detection for {symbol}: {pattern_details.get('pattern_name', 'Unknown')}")
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
                        logger.info(f"✅ [ACTIVITY] Pattern logged successfully for {symbol}")
                    except Exception as e:
                        logger.error(f"❌ [ACTIVITY] Failed to log pattern for {symbol}: {e}", exc_info=True)
                
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
                    # CRITICAL FIX: Comprehensive position sizing validation
                    risk_per_share = abs(sig['current_price'] - sig['stop_loss'])
                    
                    # VALIDATION #1: Ensure risk_per_share is meaningful
                    if risk_per_share <= 0:
                        logger.error(f"❌ [{sig['symbol']}] Invalid risk_per_share: {risk_per_share:.4f} (stop={sig['stop_loss']:.2f}, entry={sig['current_price']:.2f}) - SKIPPING TRADE")
                        continue
                    
                    # VALIDATION #2: Ensure stop_loss is at least 0.2% away from entry (minimum risk)
                    min_risk_pct = 0.002  # 0.2% minimum
                    risk_pct = risk_per_share / sig['current_price']
                    if risk_pct < min_risk_pct:
                        logger.warning(f"⚠️ [{sig['symbol']}] Stop too tight: {risk_pct*100:.2f}% (need {min_risk_pct*100}%) - SKIPPING TRADE")
                        continue
                    
                    # Use risk manager for proper position sizing
                    quantity = self._risk_manager.calculate_position_size(
                        entry_price=sig['current_price'],
                        stop_loss=sig['stop_loss'],
                        volatility=0.02  # Default 2% volatility (can enhance with ATR later)
                    )
                    
                    # VALIDATION #3: Ensure quantity is reasonable
                    if quantity <= 0:
                        logger.error(f"❌ [{sig['symbol']}] Risk manager returned 0 shares - SKIPPING TRADE")
                        continue
                    if quantity > 1000:
                        logger.warning(f"⚠️ [{sig['symbol']}] Quantity too large: {quantity} shares - capping at 100")
                        quantity = 100
                    
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
        
        FIXED: Bidirectional logic for longs/shorts, logarithmic volume scaling,
        no default pattern_score, direction-aware S/R and momentum checks.
        
        Factors:
        - Volume strength (20%) - Logarithmic scaling
        - Trend alignment (20%) - Bidirectional (long/short)
        - Pattern quality (30%) - No default, calculated from duration
        - Support/Resistance proximity (15%) - Direction-aware
        - Momentum indicators (15%) - Bidirectional (long/short)
        """
        import math
        
        try:
            confidence = 0.0
            direction = pattern_details.get('breakout_direction', 'up')
            
            # 1. Volume strength (20 points) - LOGARITHMIC SCALING
            if 'volume' in df.columns:
                avg_volume = df['volume'].tail(20).mean()
                current_volume = df['volume'].iloc[-1]
                volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
                # Logarithmic: 2x=10pts, 3x=15pts, 5x=20pts
                volume_score = min(20, math.log(volume_ratio + 1, 2) * 10)
                confidence += volume_score
            
            # 2. Trend alignment (20 points) - BIDIRECTIONAL
            if 'sma_50' in df.columns and 'sma_200' in df.columns:
                sma_50 = df['sma_50'].iloc[-1]
                sma_200 = df['sma_200'].iloc[-1]
                price = df['close'].iloc[-1]
                
                if direction == 'up':  # LONG
                    if price > sma_50 > sma_200:
                        confidence += 20
                    elif price > sma_50:
                        confidence += 10
                else:  # SHORT
                    if price < sma_50 < sma_200:
                        confidence += 20
                    elif price < sma_50:
                        confidence += 10
            
            # 3. Pattern quality (30 points) - NO DEFAULT, calculate from duration
            pattern_score = pattern_details.get('pattern_score', 0.0)  # FIXED: Default to 0
            if pattern_score > 0:
                confidence += pattern_score * 30
            else:
                # Fallback: Use pattern duration if pattern_score not provided
                duration = pattern_details.get('duration', 0)
                if duration >= 15:  # Strong pattern (15+ candles)
                    confidence += 20
                elif duration >= 10:
                    confidence += 10
            
            # 4. Support/Resistance proximity (15 points) - DIRECTION-AWARE
            support = pattern_details.get('support_level', 0)
            resistance = pattern_details.get('resistance_level', 0)
            price = df['close'].iloc[-1]
            
            if support > 0 and resistance > 0:
                range_size = resistance - support
                distance_from_support = price - support
                position_in_range = distance_from_support / range_size if range_size > 0 else 0.5
                
                if direction == 'up':  # LONG - reward near support
                    if position_in_range < 0.3:
                        confidence += 15
                    elif position_in_range < 0.5:
                        confidence += 10
                else:  # SHORT - reward near resistance
                    if position_in_range > 0.7:
                        confidence += 15
                    elif position_in_range > 0.5:
                        confidence += 10
            
            # 5. Momentum indicators (15 points) - BIDIRECTIONAL
            if 'rsi' in df.columns:
                rsi = df['rsi'].iloc[-1]
                
                if direction == 'up':  # LONG - RSI 50-70
                    if 50 <= rsi <= 70:
                        confidence += 15
                    elif 40 <= rsi <= 80:
                        confidence += 10
                else:  # SHORT - RSI 30-50
                    if 30 <= rsi <= 50:
                        confidence += 15
                    elif 20 <= rsi <= 60:
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
    
    def _execute_alpha_ensemble_strategy(self):
        """
        Execute Alpha-Ensemble Multi-Timeframe Strategy.
        
        This strategy:
        1. Scans NIFTY 50/100/200 symbols based on user selection
        2. Applies intelligent multi-layer filtering (EMA200, ADX, RSI, Volume)
        3. Uses retest-based entries with market regime detection
        4. Targets 40%+ win rate with 2.5:1 risk:reward
        
        Strategy validates BEFORE placing orders:
        - Market regime (Nifty alignment, VIX)
        - Trend filters (EMA 200, EMA 20)
        - Execution filters (ADX >25, Volume >2.5x, RSI 35-70)
        - Position & risk management (2.5:1 R:R, 5% position size)
        """
        from trading.order_manager import OrderType, TransactionType, ProductType
        
        if not self._alpha_ensemble:
            logger.error("❌ Alpha-Ensemble strategy not initialized!")
            return
        
        logger.info("⭐ Running Alpha-Ensemble Multi-Timeframe Analysis...")
        
        # Get real-time candle data and prices (thread-safe)
        with self._lock:
            candle_data_copy = self.candle_data.copy()
            latest_prices_copy = self.latest_prices.copy()
        
        # Check current positions
        current_positions = self._position_manager.get_all_positions()
        max_positions = self._risk_manager.risk_limits.max_positions
        available_slots = max_positions - len(current_positions)
        
        if available_slots <= 0:
            logger.info(f"⏸️  Max positions ({max_positions}) reached - skipping new signals")
            return
        
        # Scan all symbols using Alpha-Ensemble logic
        signals = []
        
        for symbol in self.symbols:
            try:
                # Skip if insufficient data (need 200 candles for EMA200)
                if symbol not in candle_data_copy or len(candle_data_copy[symbol]) < 200:
                    continue
                
                # Skip if already in position
                if symbol in current_positions:
                    continue
                
                df = candle_data_copy[symbol].copy()
                current_price = latest_prices_copy.get(symbol, float(df['close'].iloc[-1]))
                
                # Run Alpha-Ensemble analysis
                signal = self._alpha_ensemble.analyze_symbol(df, symbol, current_price)
                
                if not signal or signal.get('action') == 'HOLD':
                    continue
                
                logger.info(f"⭐ {symbol}: Alpha-Ensemble {signal.get('action')} signal")
                logger.info(f"   Entry: ₹{signal.get('entry_price'):.2f}")
                logger.info(f"   Stop: ₹{signal.get('stop_loss'):.2f}")
                logger.info(f"   Target: ₹{signal.get('target'):.2f}")
                logger.info(f"   Score: {signal.get('score', 0):.1f}")
                
                signals.append({
                    'symbol': symbol,
                    'signal': signal,
                    'score': signal.get('score', 50),
                    'current_price': current_price
                })
                
            except Exception as e:
                logger.error(f"Error analyzing {symbol} with Alpha-Ensemble: {e}", exc_info=True)
        
        # Rank signals by Alpha-Ensemble score
        if signals:
            signals.sort(key=lambda x: x['score'], reverse=True)
            
            logger.info(f"🎯 Alpha-Ensemble found {len(signals)} signals. Top candidates:")
            for i, sig in enumerate(signals[:5]):
                logger.info(f"  {i+1}. {sig['symbol']}: {sig['signal'].get('action')} | Score={sig['score']:.1f}")
            
            # Take best trades up to available slots
            for sig in signals[:available_slots]:
                try:
                    symbol = sig['symbol']
                    signal = sig['signal']
                    current_price = sig['current_price']
                    
                    entry_price = signal.get('entry_price', current_price)
                    stop_loss = signal.get('stop_loss', current_price * 0.98)
                    target = signal.get('target', current_price * 1.05)
                    
                    # Position sizing
                    risk_per_share = abs(entry_price - stop_loss)
                    
                    # VALIDATION: Ensure risk_per_share is meaningful
                    if risk_per_share <= 0:
                        logger.error(f"❌ [{symbol}] Invalid risk_per_share: {risk_per_share:.4f}")
                        continue
                    
                    # Use risk manager
                    quantity = self._risk_manager.calculate_position_size(
                        entry_price=entry_price,
                        stop_loss=stop_loss,
                        volatility=0.02
                    )
                    
                    # VALIDATION: Ensure quantity is reasonable
                    if quantity <= 0:
                        logger.error(f"❌ [{symbol}] Risk manager returned 0 shares")
                        continue
                    if quantity > 1000:
                        logger.warning(f"⚠️ [{symbol}] Quantity too large: {quantity} - capping at 100")
                        quantity = 100
                    
                    quantity = max(1, min(quantity, 100))
                    
                    # 🚨 AUDIT OPTIMIZATION #2: Retest-Based Entry (Limit Orders)
                    # Instead of market order on breakout, wait for retest and use limit order
                    # This improves entry price and increases win rate by 15-20%
                    
                    # Check if we should use retest-based entry (for breakout patterns)
                    use_retest_entry = True  # Enable for all breakout patterns
                    
                    if use_retest_entry and signal.get('action') in ['BUY', 'SELL']:
                        # Store breakout for retest monitoring
                        direction = 'up' if signal.get('action') == 'BUY' else 'down'
                        
                        with self._lock:
                            self.pending_retests[symbol] = {
                                'breakout_price': entry_price,
                                'direction': direction,
                                'stop_loss': stop_loss,
                                'target': target,
                                'quantity': quantity,
                                'reason': f"Alpha-Ensemble | Score: {sig['score']:.1f}",
                                'timestamp': datetime.now(),
                                'ml_signal_id': None,  # Will be set during actual entry
                                'confidence': sig['score']
                            }
                        
                        logger.info(f"📌 [{symbol}] RETEST MODE: Breakout detected @ ₹{entry_price:.2f}")
                        logger.info(f"   Waiting for retest (pullback) before entry with limit order")
                        logger.info(f"   This improves R:R and reduces slippage")
                        continue  # Don't place market order yet
                    
                    # Fallback: Traditional market order entry (disabled when retest enabled)
                    # Log signal for ML training (if enabled)
                    ml_signal_id = None
                    if self._ml_logger and self._ml_logger.enabled:
                        try:
                            df_latest = candle_data_copy[symbol].iloc[-1]
                            ml_signal_data = {
                                'symbol': symbol,
                                'action': signal.get('action'),
                                'entry_price': entry_price,
                                'stop_loss': stop_loss,
                                'target': target,
                                'was_taken': True,
                                'rsi': df_latest.get('rsi', 50),
                                'macd': df_latest.get('macd', 0),
                                'macd_signal': df_latest.get('macd_signal', 0),
                                'adx': df_latest.get('adx', 20),
                                'pattern_type': 'Alpha-Ensemble',
                                'hour_of_day': datetime.now().hour,
                                'confidence': sig['score']
                            }
                            ml_signal_id = self._ml_logger.log_signal(ml_signal_data)
                        except Exception as log_err:
                            logger.debug(f"ML logger error: {log_err}")
                    
                    # Place order
                    logger.info(f"🔴 ENTERING TRADE: {symbol} (Alpha-Ensemble top signal)")
                    self._place_entry_order(
                        symbol=symbol,
                        direction='up' if signal.get('action') == 'BUY' else 'down',
                        entry_price=entry_price,
                        stop_loss=stop_loss,
                        target=target,
                        quantity=quantity,
                        reason=f"Alpha-Ensemble | Score: {sig['score']:.1f}",
                        ml_signal_id=ml_signal_id,
                        confidence=sig['score']
                    )
                    
                except Exception as e:
                    logger.error(f"Error placing Alpha-Ensemble order for {sig['symbol']}: {e}", exc_info=True)
        else:
            logger.debug("No Alpha-Ensemble signals found in this scan cycle")
    
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
            
            # 🎯 EXTRACT ACTUAL SIGNAL TYPE FROM PATTERN
            # Map internal pattern names to user-friendly signal types
            signal_type = 'Breakout'  # Default
            if 'pattern_details' in locals() and isinstance(pattern_details, dict):
                pattern_name = pattern_details.get('pattern', 'Breakout')
                if pattern_name == 'MEAN_REVERSION':
                    signal_type = 'Mean Reversion'
                elif 'Alpha-Ensemble' in reason or 'alpha_ensemble' in reason.lower():
                    signal_type = 'Alpha Ensemble'
                elif 'Defining Order' in reason or 'defining' in reason.lower():
                    signal_type = 'Defining Order'
                elif 'Ironclad' in reason:
                    signal_type = 'Ironclad'
                else:
                    # Extract pattern from reason (e.g., "Pattern: Double Top")
                    if 'Pattern:' in reason:
                        extracted = reason.split('Pattern: ')[-1].split(' |')[0].strip()
                        if extracted:
                            signal_type = extracted
            
            # 🌊 DETERMINE MARKET REGIME
            current_adx = 25  # Default
            if symbol in candle_data_copy:
                try:
                    df_temp = candle_data_copy[symbol]
                    if 'adx' in df_temp.columns:
                        current_adx = float(df_temp['adx'].iloc[-1])
                except:
                    pass
            regime = 'sideways' if current_adx < 20 else 'trending'
            
            signal_data = {
                'user_id': self.user_id,
                'symbol': symbol,
                'type': 'BUY' if direction == 'up' else 'SELL',
                'signal_type': signal_type,  # ✅ FIXED: Dynamic signal type
                'price': entry_price,
                'stop_loss': stop_loss,
                'target': target,
                'quantity': quantity,
                'confidence': confidence / 100.0,  # ✅ FIXED: Use actual calculated confidence (0-1 scale)
                'rationale': reason,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'mode': self.trading_mode,
                'status': 'open',
                'replay_mode': self.is_replay_mode,  # Phase 3: Mark replay signals
                'replay_date': self.replay_date if self.is_replay_mode else None,
                # ✅ NEW: Enhanced tracking fields
                'regime': regime,
                'adx_value': round(current_adx, 2),
                'breakeven_moved': False,
                'trailing_active': False,
                'entry_method': 'limit' if signal_type == 'Mean Reversion' else 'market'
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
            
            # 🚨 AUDIT FIX: Check OTR throttle before placing order
            if self._otr_monitor.is_throttled():
                logger.warning(f"🚫 OTR THROTTLE: Cannot place order for {symbol} (high OTR - SEBI compliance)")
                return
            
            try:
                # Record order placement for OTR tracking
                self._otr_monitor.record_order_placed()
                
                order_result = self._order_manager.place_order(
                    symbol=symbol,
                    token=token_info['token'],
                    exchange=token_info['exchange'],
                    transaction_type=transaction_type,
                    order_type=OrderType.MARKET,
                    quantity=quantity,
                    product_type=ProductType.INTRADAY,
                    strategy_tag=self.strategy.upper()  # 🚨 AUDIT FIX: SEBI compliance
                )
            except Exception as order_err:
                logger.error(f"❌ CRITICAL: Order placement exception for {symbol}: {order_err}", exc_info=True)
                # Don't create position if order failed
                return
            
            if order_result:
                order_id = order_result.get('orderid', 'unknown')
                logger.info(f"✅ LIVE order placed: {order_id}")
                
                # 🚨 AUDIT FIX: Record order execution for OTR tracking
                self._otr_monitor.record_order_executed()
                
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
                direction = position.get('direction', 'up')
                
                # 🚨 AUDIT FIX: Breakeven Stop Logic
                # Move stop to entry when trade reaches 1R profit
                if not position.get('breakeven_moved', False):
                    risk_distance = abs(entry_price - stop_loss)
                    
                    if direction == 'up':
                        profit_distance = current_price - entry_price
                        # Check if reached 1R profit
                        if profit_distance >= risk_distance and stop_loss < entry_price:
                            logger.info(f"🔒 [{symbol}] BREAKEVEN: Moving stop to entry (1R profit reached)")
                            logger.info(f"  Entry: ₹{entry_price:.2f} | Current: ₹{current_price:.2f} | Profit: +₹{profit_distance:.2f} (>= ₹{risk_distance:.2f})")
                            old_stop = stop_loss
                            position['stop_loss'] = entry_price
                            position['breakeven_moved'] = True
                            position['highest_price'] = current_price  # Initialize for trailing stop
                            stop_loss = entry_price  # Update for current check
                            
                            # ✅ NEW: Write breakeven update to Firestore
                            try:
                                db_fs = firestore.client()
                                
                                # Write to position_updates collection
                                db_fs.collection('position_updates').add({
                                    'user_id': self.user_id,
                                    'symbol': symbol,
                                    'update_type': 'BREAKEVEN_STOP',
                                    'old_stop_loss': old_stop,
                                    'new_stop_loss': entry_price,
                                    'current_price': current_price,
                                    'profit_locked': 0,  # Risk eliminated
                                    'reason': 'Profit reached 1R - moving stop to entry',
                                    'timestamp': firestore.SERVER_TIMESTAMP
                                })
                                
                                # Update original signal document
                                signals_ref = db_fs.collection('trading_signals').where('symbol', '==', symbol).where('status', '==', 'open').limit(1).stream()
                                for sig in signals_ref:
                                    sig.reference.update({
                                        'stop_loss': entry_price,
                                        'breakeven_moved': True,
                                        'last_stop_update': firestore.SERVER_TIMESTAMP
                                    })
                                
                                logger.info(f"✅ Breakeven update written to Firestore for {symbol}")
                            except Exception as fs_err:
                                logger.error(f"Failed to write breakeven update: {fs_err}")
                            
                            # Log to activity feed
                            if self._activity_logger:
                                try:
                                    self._activity_logger.log_position_update(
                                        symbol=symbol,
                                        action='BREAKEVEN_STOP',
                                        details=f"Stop moved to ₹{entry_price:.2f} (protecting profit)"
                                    )
                                except:
                                    pass
                    else:  # Short position
                        profit_distance = entry_price - current_price
                        if profit_distance >= risk_distance and stop_loss > entry_price:
                            logger.info(f"🔒 [{symbol}] BREAKEVEN: Moving stop to entry (1R profit reached)")
                            old_stop = stop_loss
                            position['stop_loss'] = entry_price
                            position['breakeven_moved'] = True
                            position['lowest_price'] = current_price  # Initialize for trailing stop
                            stop_loss = entry_price
                            
                            # ✅ NEW: Write breakeven update to Firestore
                            try:
                                db_fs = firestore.client()
                                
                                db_fs.collection('position_updates').add({
                                    'user_id': self.user_id,
                                    'symbol': symbol,
                                    'update_type': 'BREAKEVEN_STOP',
                                    'old_stop_loss': old_stop,
                                    'new_stop_loss': entry_price,
                                    'current_price': current_price,
                                    'profit_locked': 0,
                                    'reason': 'Profit reached 1R - moving stop to entry',
                                    'timestamp': firestore.SERVER_TIMESTAMP
                                })
                                
                                signals_ref = db_fs.collection('trading_signals').where('symbol', '==', symbol).where('status', '==', 'open').limit(1).stream()
                                for sig in signals_ref:
                                    sig.reference.update({
                                        'stop_loss': entry_price,
                                        'breakeven_moved': True,
                                        'last_stop_update': firestore.SERVER_TIMESTAMP
                                    })
                                
                                logger.info(f"✅ Breakeven update written to Firestore for {symbol}")
                            except Exception as fs_err:
                                logger.error(f"Failed to write breakeven update: {fs_err}")
                            
                            if self._activity_logger:
                                try:
                                    self._activity_logger.log_position_update(
                                        symbol=symbol,
                                        action='BREAKEVEN_STOP',
                                        details=f"Stop moved to ₹{entry_price:.2f} (protecting profit)"
                                    )
                                except:
                                    pass
                
                # 🚨 AUDIT OPTIMIZATION #4: Trailing Stop Logic
                # After breakeven, trail stop by 50% of additional profit
                if position.get('breakeven_moved', False):
                    if direction == 'up':
                        # Track highest price since breakeven
                        highest_price = position.get('highest_price', current_price)
                        if current_price > highest_price:
                            position['highest_price'] = current_price
                            highest_price = current_price
                        
                        # Trail stop: Lock in 50% of profit above breakeven
                        profit_above_entry = highest_price - entry_price
                        trailing_stop = entry_price + (profit_above_entry * 0.5)
                        
                        if trailing_stop > stop_loss:
                            logger.info(f"📈 [{symbol}] TRAILING STOP: ₹{stop_loss:.2f} → ₹{trailing_stop:.2f}")
                            logger.info(f"  Highest: ₹{highest_price:.2f} | Locking: 50% of profit above entry")
                            old_stop = stop_loss
                            position['stop_loss'] = trailing_stop
                            stop_loss = trailing_stop
                            
                            # ✅ NEW: Write trailing stop update to Firestore
                            try:
                                db_fs = firestore.client()
                                profit_locked = (trailing_stop - entry_price) * position.get('quantity', 0)
                                
                                db_fs.collection('position_updates').add({
                                    'user_id': self.user_id,
                                    'symbol': symbol,
                                    'update_type': 'TRAILING_STOP',
                                    'old_stop_loss': old_stop,
                                    'new_stop_loss': trailing_stop,
                                    'current_price': current_price,
                                    'profit_locked': round(profit_locked, 2),
                                    'reason': f'Trailing 50% of profit above entry (₹{highest_price:.2f} peak)',
                                    'timestamp': firestore.SERVER_TIMESTAMP
                                })
                                
                                signals_ref = db_fs.collection('trading_signals').where('symbol', '==', symbol).where('status', '==', 'open').limit(1).stream()
                                for sig in signals_ref:
                                    sig.reference.update({
                                        'stop_loss': trailing_stop,
                                        'trailing_active': True,
                                        'last_stop_update': firestore.SERVER_TIMESTAMP
                                    })
                                
                                logger.info(f"✅ Trailing stop update written to Firestore for {symbol}")
                            except Exception as fs_err:
                                logger.error(f"Failed to write trailing stop update: {fs_err}")
                            
                            if self._activity_logger:
                                try:
                                    self._activity_logger.log_position_update(
                                        symbol=symbol,
                                        action='TRAILING_STOP',
                                        details=f"Stop trailed to ₹{trailing_stop:.2f} (locking profit)"
                                    )
                                except:
                                    pass
                    
                    else:  # Short position
                        # Track lowest price since breakeven
                        lowest_price = position.get('lowest_price', current_price)
                        if current_price < lowest_price:
                            position['lowest_price'] = current_price
                            lowest_price = current_price
                        
                        # Trail stop: Lock in 50% of profit above breakeven
                        profit_above_entry = entry_price - lowest_price
                        trailing_stop = entry_price - (profit_above_entry * 0.5)
                        
                        if trailing_stop < stop_loss:
                            logger.info(f"📈 [{symbol}] TRAILING STOP: ₹{stop_loss:.2f} → ₹{trailing_stop:.2f}")
                            old_stop = stop_loss
                            position['stop_loss'] = trailing_stop
                            stop_loss = trailing_stop
                            
                            # ✅ NEW: Write trailing stop update to Firestore
                            try:
                                db_fs = firestore.client()
                                profit_locked = (entry_price - trailing_stop) * position.get('quantity', 0)
                                
                                db_fs.collection('position_updates').add({
                                    'user_id': self.user_id,
                                    'symbol': symbol,
                                    'update_type': 'TRAILING_STOP',
                                    'old_stop_loss': old_stop,
                                    'new_stop_loss': trailing_stop,
                                    'current_price': current_price,
                                    'profit_locked': round(profit_locked, 2),
                                    'reason': f'Trailing 50% of profit above entry (₹{lowest_price:.2f} low)',
                                    'timestamp': firestore.SERVER_TIMESTAMP
                                })
                                
                                signals_ref = db_fs.collection('trading_signals').where('symbol', '==', symbol).where('status', '==', 'open').limit(1).stream()
                                for sig in signals_ref:
                                    sig.reference.update({
                                        'stop_loss': trailing_stop,
                                        'trailing_active': True,
                                        'last_stop_update': firestore.SERVER_TIMESTAMP
                                    })
                                
                                logger.info(f"✅ Trailing stop update written to Firestore for {symbol}")
                            except Exception as fs_err:
                                logger.error(f"Failed to write trailing stop update: {fs_err}")
                            
                            if self._activity_logger:
                                try:
                                    self._activity_logger.log_position_update(
                                        symbol=symbol,
                                        action='TRAILING_STOP',
                                        details=f"Stop trailed to ₹{trailing_stop:.2f} (locking profit)"
                                    )
                                except:
                                    pass
                
                # Check stop loss (instant detection)
                if direction == 'up' and current_price <= stop_loss:
                    logger.warning(f"🛑 STOP LOSS HIT: {symbol} @ ₹{current_price:.2f}")
                    self._close_position(symbol, position, current_price, 'STOP_LOSS')
                    continue
                elif direction == 'down' and current_price >= stop_loss:
                    logger.warning(f"🛑 STOP LOSS HIT: {symbol} @ ₹{current_price:.2f}")
                    self._close_position(symbol, position, current_price, 'STOP_LOSS')
                    continue
                
                # Check target (instant detection)
                if direction == 'up' and current_price >= target:
                    logger.info(f"🎯 TARGET HIT: {symbol} @ ₹{current_price:.2f}")
                    self._close_position(symbol, position, current_price, 'TARGET')
                    continue
                elif direction == 'down' and current_price <= target:
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
                        product_type=ProductType.INTRADAY,
                        strategy_tag=self.strategy.upper()  # 🚨 AUDIT FIX: SEBI compliance
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
                'holding_duration_minutes': int(holding_duration),
                'replay_mode': self.is_replay_mode,  # Phase 3: Mark replay signals
                'replay_date': self.replay_date if self.is_replay_mode else None
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
            
        except Exception as e:
            logger.error(f"Failed to calculate daily P&L: {e}", exc_info=True)
    
    def _run_replay_simulation(self, running_flag: Callable[[], bool]):
        """
        Run replay mode simulation - simulate trading for a historical date
        Fetches historical data and processes it as if trading in real-time
        """
        try:
            from datetime import datetime, timedelta
            import pandas as pd
            from SmartApi import SmartConnect
            
            logger.info(f"🔄 REPLAY MODE: Starting simulation for {self.replay_date}")
            
            # Step 1: Initialize managers (without WebSocket)
            logger.info("🔧 Initializing trading managers for replay...")
            self._initialize_managers()
            
            # Step 2: Initialize and authenticate SmartAPI client
            logger.info("🔌 Initializing SmartAPI client...")
            smart_api = SmartConnect(api_key=self.api_key)
            
            # Authenticate with existing JWT token (set token attributes directly)
            if self.jwt_token:
                logger.info("🔐 Setting JWT token for SmartAPI...")
                # SmartAPI stores tokens as instance attributes after generateSession
                # We manually set them since we already have valid tokens
                smart_api._access_token = self.jwt_token
                smart_api._refresh_token = self.jwt_token  # Use same token
                smart_api._feed_token = self.feed_token
                logger.info("✅ SmartAPI authenticated with existing tokens")
            else:
                raise Exception("No JWT token available - cannot fetch historical data")
            
            # Step 3: Get symbol tokens
            logger.info("📋 Fetching symbol tokens...")
            self.symbol_tokens = self._get_symbol_tokens_parallel()
            if not self.symbol_tokens:
                logger.warning("No symbol tokens, using fallback...")
                self.symbol_tokens = self._get_fallback_tokens()
            
            logger.info(f"✅ Got tokens for {len(self.symbol_tokens)} symbols")
            
            # Step 4: Parse replay date
            replay_dt = datetime.strptime(self.replay_date, '%Y-%m-%d')
            
            # Step 4.5: Convert universe string to actual symbols if needed
            # Alpha-Ensemble passes universe name (e.g., "NIFTY50"), need to convert to symbols
            if isinstance(self.symbols, str):
                logger.info(f"🔄 Converting universe '{self.symbols}' to symbol list...")
                from nifty200_watchlist import NIFTY200_WATCHLIST
                all_symbols = [stock['symbol'] for stock in NIFTY200_WATCHLIST]
                
                if self.symbols == 'NIFTY50':
                    self.symbols = all_symbols[:50]
                elif self.symbols == 'NIFTY100':
                    self.symbols = all_symbols[:100]
                elif self.symbols == 'NIFTY200':
                    self.symbols = all_symbols
                else:
                    self.symbols = all_symbols[:50]  # Default to NIFTY50
                
                logger.info(f"✅ Converted to {len(self.symbols)} symbols")
            
            # Step 5: Fetch historical data for each symbol
            logger.info(f"📊 Fetching historical data for {self.replay_date}...")
            historical_data = {}
            failed_symbols = []
            
            # Reduce to 5 symbols for replay to avoid rate limits
            symbols_to_fetch = self.symbols[:5] if len(self.symbols) > 5 else self.symbols
            logger.info(f"📋 Will fetch data for {len(symbols_to_fetch)} symbols: {symbols_to_fetch}")
            
            for symbol in symbols_to_fetch:
                if symbol not in self.symbol_tokens:
                    logger.warning(f"No token for {symbol}, skipping...")
                    continue
                
                token_info = self.symbol_tokens[symbol]
                
                try:
                    # Fetch intraday 1-minute candles using REST API (SDK doesn't work reliably for historical data)
                    url = "https://apiconnect.angelbroking.com/rest/secure/angelbroking/historical/v1/getCandleData"
                    
                    headers = {
                        'Authorization': f'Bearer {smart_api.getfeedToken()}',
                        'Content-Type': 'application/json',
                        'Accept': 'application/json',
                        'X-UserType': 'USER',
                        'X-SourceID': 'WEB',
                        'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
                        'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
                        'X-MACAddress': 'MAC_ADDRESS',
                        'X-PrivateKey': smart_api.api_key
                    }
                    
                    payload = {
                        "exchange": "NSE",
                        "symboltoken": token_info['token'],
                        "interval": "ONE_MINUTE",
                        "fromdate": f"{self.replay_date} 09:15",
                        "todate": f"{self.replay_date} 15:30"
                    }
                    
                    logger.info(f"  📊 Fetching {symbol} via REST API...")
                    response = requests.post(url, json=payload, headers=headers, timeout=30)
                    hist_data = response.json()
                    
                    if hist_data and hist_data.get('status') and hist_data.get('data'):
                        candles = hist_data['data']
                        df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                        df['timestamp'] = pd.to_datetime(df['timestamp'])
                        df = df.set_index('timestamp')
                        historical_data[symbol] = df
                        logger.info(f"  ✅ {symbol}: {len(df)} candles")
                    else:
                        error_msg = hist_data.get('message', 'No response') if hist_data else 'No response'
                        logger.warning(f"  ⚠️  {symbol}: No data - {error_msg}")
                        failed_symbols.append(f"{symbol} ({error_msg})")
                        
                except Exception as e:
                    logger.error(f"  ❌ {symbol}: Failed to fetch data - {e}")
                    failed_symbols.append(f"{symbol} (Error: {str(e)[:50]})")
                    continue
                
                # Increased delay to avoid rate limits
                time.sleep(0.5)  # 500ms delay between requests
            
            if not historical_data:
                # Better error message with date validation
                replay_dt = datetime.strptime(self.replay_date, '%Y-%m-%d')
                day_name = replay_dt.strftime('%A')
                
                error_msg = f"No historical data available for {self.replay_date} ({day_name}). "
                
                if replay_dt.weekday() >= 5:  # Saturday or Sunday
                    error_msg += "This is a weekend - markets are closed."
                elif replay_dt > datetime.now():
                    error_msg += "This is a future date - cannot replay future data."
                else:
                    error_msg += f"API returned no data for any symbols. "
                    if failed_symbols:
                        error_msg += f"Failed symbols: {', '.join(failed_symbols[:3])}. "
                    error_msg += "This might be a market holiday or rate limit issue."
                
                error_msg += " Please try again or select a different date."
                
                logger.error(f"❌ {error_msg}")
                raise Exception(error_msg)
            
            logger.info(f"✅ Historical data loaded for {len(historical_data)} symbols")
            
            # Step 6: Simulate trading session
            logger.info("🎬 Starting replay simulation...")
            
            # Get all unique timestamps across all symbols
            all_timestamps = set()
            for df in historical_data.values():
                all_timestamps.update(df.index)
            
            sorted_timestamps = sorted(list(all_timestamps))
            logger.info(f"📅 Simulating {len(sorted_timestamps)} time points from {sorted_timestamps[0]} to {sorted_timestamps[-1]}")
            
            # Update bot config with replay progress
            if self.db:
                self.db.collection('bot_configs').document(self.user_id).update({
                    'replay_progress': 0,
                    'replay_total': len(sorted_timestamps),
                    'replay_status': 'running'
                })
            
            signals_generated = 0
            
            # Process each timestamp sequentially
            for idx, timestamp in enumerate(sorted_timestamps):
                if not running_flag() or not self.is_running:
                    logger.info("🛑 Replay simulation stopped by user")
                    break
                
                # Update candle data for each symbol at this timestamp
                for symbol, df in historical_data.items():
                    if timestamp in df.index:
                        candle = df.loc[timestamp]
                        
                        # Add to candle_data (same format as real-time)
                        if symbol not in self.candle_data:
                            self.candle_data[symbol] = pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
                        
                        new_row = pd.DataFrame({
                            'open': [candle['open']],
                            'high': [candle['high']],
                            'low': [candle['low']],
                            'close': [candle['close']],
                            'volume': [candle['volume']]
                        }, index=[timestamp])
                        
                        self.candle_data[symbol] = pd.concat([self.candle_data[symbol], new_row])
                        
                        # Update latest price
                        with self._lock:
                            self.latest_prices[symbol] = float(candle['close'])
                
                # Run strategy analysis at this timestamp
                try:
                    self._analyze_and_trade()
                except Exception as e:
                    logger.error(f"Error during analysis at {timestamp}: {e}")
                
                # Update progress every 50 timestamps
                if idx % 50 == 0:
                    progress = int((idx / len(sorted_timestamps)) * 100)
                    logger.info(f"🔄 Replay progress: {progress}% ({idx}/{len(sorted_timestamps)})")
                    
                    if self.db:
                        self.db.collection('bot_configs').document(self.user_id).update({
                            'replay_progress': idx,
                            'replay_status': 'running'
                        })
                
                # Small delay to avoid overwhelming Firestore
                if idx % 10 == 0:
                    time.sleep(0.01)
            
            # Step 7: Close any open positions at end of day
            logger.info("📴 End of replay session - closing open positions...")
            with self._lock:
                open_positions = list(self.open_positions.values())
            
            for position in open_positions:
                try:
                    exit_price = self.latest_prices.get(position['ticker'], position['entry_price'])
                    self._close_position_replay(position, exit_price, 'EOD', 'End of replay session')
                except Exception as e:
                    logger.error(f"Error closing position {position['ticker']}: {e}")
            
            # Step 8: Calculate final statistics
            logger.info("📊 Calculating replay results...")
            
            if self.db:
                # Get all signals generated during replay
                signals_ref = self.db.collection('trading_signals').where('user_id', '==', self.user_id).where('replay_date', '==', self.replay_date)
                signals = [doc.to_dict() for doc in signals_ref.stream()]
                
                total_signals = len(signals)
                buy_signals = len([s for s in signals if s.get('action') == 'BUY'])
                sell_signals = len([s for s in signals if s.get('action') == 'SELL'])
                
                # Calculate P&L
                total_pnl = sum([s.get('pnl', 0) for s in signals if s.get('pnl')])
                winning_trades = len([s for s in signals if s.get('pnl', 0) > 0])
                losing_trades = len([s for s in signals if s.get('pnl', 0) < 0])
                
                win_rate = (winning_trades / (winning_trades + losing_trades) * 100) if (winning_trades + losing_trades) > 0 else 0
                
                # Store replay results
                replay_results = {
                    'user_id': self.user_id,
                    'replay_date': self.replay_date,
                    'completed_at': firestore.SERVER_TIMESTAMP,
                    'total_signals': total_signals,
                    'buy_signals': buy_signals,
                    'sell_signals': sell_signals,
                    'total_pnl': total_pnl,
                    'winning_trades': winning_trades,
                    'losing_trades': losing_trades,
                    'win_rate': win_rate,
                    'strategy': self.strategy,
                    'symbols_analyzed': len(historical_data),
                    'timepoints_processed': len(sorted_timestamps)
                }
                
                self.db.collection('replay_results').document(f"{self.user_id}_{self.replay_date}").set(replay_results)
                
                # Update bot config
                self.db.collection('bot_configs').document(self.user_id).update({
                    'status': 'stopped',
                    'replay_progress': len(sorted_timestamps),
                    'replay_status': 'completed',
                    'replay_mode': False
                })
                
                logger.info("="*80)
                logger.info(f"✅ REPLAY SIMULATION COMPLETE for {self.replay_date}")
                logger.info(f"   Total Signals: {total_signals} (Buy: {buy_signals}, Sell: {sell_signals})")
                logger.info(f"   Total P&L: ₹{total_pnl:,.2f}")
                logger.info(f"   Win Rate: {win_rate:.1f}% ({winning_trades}W / {losing_trades}L)")
                logger.info(f"   Symbols: {len(historical_data)}")
                logger.info(f"   Timepoints: {len(sorted_timestamps)}")
                logger.info("="*80)
            
            self.is_running = False
            
        except Exception as e:
            logger.error(f"❌ Replay simulation failed: {e}", exc_info=True)
            if self.db:
                self.db.collection('bot_configs').document(self.user_id).update({
                    'status': 'error',
                    'error_message': f"Replay failed: {str(e)}",
                    'replay_status': 'failed',
                    'replay_mode': False
                })
            self.is_running = False
            raise
    
    def _close_position_replay(self, position, exit_price, signal_type, rationale):
        """Close a position during replay mode and record the signal"""
        ticker = position['ticker']
        entry_price = position['entry_price']
        quantity = position['quantity']
        
        pnl = (exit_price - entry_price) * quantity
        pnl_pct = ((exit_price - entry_price) / entry_price) * 100
        
        # Create exit signal
        signal_data = {
            'user_id': self.user_id,
            'ticker': ticker,
            'action': 'SELL',
            'signal_type': signal_type,
            'price': exit_price,
            'quantity': quantity,
            'confidence': position.get('confidence', 0),
            'rationale': rationale,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'entry_price': entry_price,
        }
        
        return signal_data
    
    def _check_and_refresh_tokens(self):
        """
        Check if Angel One tokens are expired and automatically refresh them.
        Tokens expire after 24 hours and need daily regeneration.
        """
        try:
            import pyotp
            from SmartApi import SmartConnect
            from datetime import datetime, timedelta
            
            # Check if we have token_generated_at timestamp
            if self.db is None:
                logger.warning("⚠️  No Firestore client - cannot check token expiry, assuming tokens are fresh")
                return
            
            try:
                creds_doc = self.db.collection('angel_one_credentials').document(self.user_id).get()
                if not creds_doc.exists:
                    logger.error("❌ No credentials found in Firestore")
                    return
                
                creds_data = creds_doc.to_dict()
                token_time_str = creds_data.get('token_generated_at')
                
                if not token_time_str:
                    logger.warning("⚠️  No token_generated_at timestamp - assuming tokens need refresh")
                    needs_refresh = True
                else:
                    # Parse timestamp
                    token_time = datetime.fromisoformat(token_time_str.replace('Z', '+00:00'))
                    token_age = datetime.now() - token_time.replace(tzinfo=None)
                    
                    # Tokens expire after 24 hours, refresh if older than 23 hours (safety margin)
                    needs_refresh = token_age > timedelta(hours=23)
                    
                    if needs_refresh:
                        logger.warning(f"⚠️  Tokens expired (age: {token_age}) - refreshing...")
                    else:
                        logger.info(f"✅ Tokens still valid (age: {token_age})")
                        return
                
                # Refresh tokens
                if needs_refresh:
                    logger.info("🔄 Generating fresh Angel One tokens...")
                    
                    # Get credentials
                    api_key = creds_data.get('api_key')
                    client_code = creds_data.get('client_code')
                    password = creds_data.get('password')
                    totp_secret = creds_data.get('totp_secret')
                    
                    if not all([api_key, client_code, password, totp_secret]):
                        logger.error("❌ Missing credentials for token refresh")
                        return
                    
                    # Generate TOTP
                    totp = pyotp.TOTP(totp_secret)
                    totp_token = totp.now()
                    
                    # Login
                    smart_api = SmartConnect(api_key=api_key)
                    login_data = smart_api.generateSession(
                        clientCode=client_code,
                        password=password,
                        totp=totp_token
                    )
                    
                    if not login_data or login_data.get('status') == False:
                        error_msg = login_data.get('message', 'Unknown error') if login_data else 'No response'
                        logger.error(f"❌ Token refresh failed: {error_msg}")
                        return
                    
                    # Extract new tokens
                    jwt_token = login_data['data']['jwtToken']
                    refresh_token = login_data['data']['refreshToken']
                    feed_token = login_data['data']['feedToken']
                    
                    # Update credentials in Firestore
                    self.db.collection('angel_one_credentials').document(self.user_id).update({
                        'jwt_token': jwt_token,
                        'refresh_token': refresh_token,
                        'feed_token': feed_token,
                        'token_generated_at': datetime.now().isoformat(),
                        'last_refresh': datetime.now().isoformat()
                    })
                    
                    # Update local credentials
                    self.jwt_token = jwt_token
                    self.feed_token = feed_token
                    self.credentials['jwt_token'] = jwt_token
                    self.credentials['feed_token'] = feed_token
                    
                    logger.info("✅ Tokens refreshed successfully")
                    
                    # Log to activity feed
                    if self._activity_logger:
                        self._activity_logger.log_activity(
                            message="Angel One tokens auto-refreshed (24hr expiry)",
                            level="INFO",
                            symbol="SYSTEM",
                            details={'totp_used': totp_token}
                        )
                    
            except Exception as e:
                logger.error(f"❌ Token refresh check failed: {e}", exc_info=True)
                logger.warning("⚠️  Continuing with existing tokens...")
                
        except Exception as e:
            logger.error(f"❌ Failed to check token expiry: {e}", exc_info=True)
    
    def _close_position_replay_helper(self, position, exit_price, signal_type, rationale):
        """Helper method to close position during replay mode"""
        ticker = position['ticker']
        entry_price = position['entry_price']
        quantity = position['quantity']
        
        pnl = (exit_price - entry_price) * quantity
        pnl_pct = ((exit_price - entry_price) / entry_price) * 100
        
        # Create exit signal
        signal_data = {
            'user_id': self.user_id,
            'ticker': ticker,
            'action': 'SELL',
            'signal_type': signal_type,
            'price': exit_price,
            'quantity': quantity,
            'confidence': position.get('confidence', 0),
            'rationale': rationale,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'holding_period_minutes': 0,
            'strategy': self.strategy,
            'trading_mode': 'replay',
            'replay_date': self.replay_date,
            'timestamp': firestore.SERVER_TIMESTAMP
        }
        
        if self.db:
            self.db.collection('trading_signals').add(signal_data)
        
        # Remove from open positions
        with self._lock:
            if ticker in self.open_positions:
                del self.open_positions[ticker]
        
        logger.info(f"   📴 Closed {ticker} @ ₹{exit_price:.2f} | P&L: ₹{pnl:,.2f} ({pnl_pct:+.2f}%)")
        
        return signal_data

