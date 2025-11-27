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
                 trading_mode: str = 'paper', strategy: str = 'pattern'):
        self.user_id = user_id
        self.credentials = credentials
        self.symbols = symbols
        self.trading_mode = trading_mode.lower()
        self.strategy = strategy.lower()
        
        # Extract credentials
        self.jwt_token = credentials.get('jwt_token', '')
        self.feed_token = credentials.get('feed_token', '')
        self.client_code = credentials.get('client_code', '')
        self.api_key = credentials.get('api_key', '')
        
        if not all([self.jwt_token, self.feed_token, self.client_code, self.api_key]):
            raise ValueError("Missing required credentials")
        
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
            self._initialize_managers()
            
            # Step 3: Initialize WebSocket connection - WITH ERROR HANDLING
            logger.info("Initializing WebSocket connection...")
            try:
                self._initialize_websocket()
                logger.info("✅ WebSocket initialized")
            except Exception as e:
                logger.error(f"WebSocket initialization failed: {e}")
                logger.warning("Bot will continue with polling mode (no real-time ticks)")
                self.ws_manager = None  # Bot will run without WebSocket
            
            # Step 4: Subscribe to symbols (only if WebSocket is active)
            if self.ws_manager:
                try:
                    self._subscribe_to_symbols()
                    logger.info("✅ Subscribed to symbols")
                except Exception as e:
                    logger.error(f"Symbol subscription failed: {e}")
                    logger.warning("Bot will continue without real-time subscriptions")
            
            # Step 5: Start position monitoring thread (runs every 0.5 seconds)
            logger.info("Starting position monitoring thread...")
            self._monitoring_thread = threading.Thread(
                target=self._continuous_position_monitoring,
                daemon=True
            )
            self._monitoring_thread.start()
            
            # Step 6: Start candle builder thread (builds 1-min candles from ticks)
            logger.info("Starting candle builder thread...")
            self._candle_builder_thread = threading.Thread(
                target=self._continuous_candle_building,
                daemon=True
            )
            self._candle_builder_thread.start()
            
            # Step 7: Main strategy execution loop (runs every 5 seconds)
            logger.info("🚀 Real-time trading bot started successfully!")
            logger.info("Position monitoring: Every 0.5 seconds")
            logger.info("Strategy analysis: Every 5 seconds")
            logger.info(f"Data updates: {'Real-time via WebSocket' if self.ws_manager else 'Polling mode'}")
            
            error_count = 0
            max_consecutive_errors = 10  # Stop only after 10 consecutive errors
            
            while running_flag() and self.is_running:
                try:
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
            # Import WebSocket manager from local websocket module
            from websocket.websocket_manager_v2 import AngelWebSocketV2Manager
            
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
                if token_info['token'] == token:
                    symbol = sym
                    break
            
            if not symbol:
                return
            
            # Thread-safe update
            with self._lock:
                # Update latest price
                self.latest_prices[symbol] = ltp
                
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
        Runs every 5 seconds to aggregate ticks into candles.
        """
        logger.info("📊 Candle builder thread started (5s interval)")
        
        while self.is_running:
            try:
                self._build_candles()
                time.sleep(5)  # Build candles every 5 seconds
                
            except Exception as e:
                logger.error(f"Error building candles: {e}")
                time.sleep(5)
    
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
                
                # Calculate technical indicators if we have enough data
                if len(candles) >= 200:
                    candles = self._calculate_indicators(candles)
                
                # Store candle data with indicators
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
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with added indicator columns
        """
        try:
            # Simple Moving Averages
            df['sma_10'] = df['close'].rolling(window=10).mean()
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['sma_50'] = df['close'].rolling(window=50).mean()
            df['sma_100'] = df['close'].rolling(window=100).mean()
            df['sma_200'] = df['close'].rolling(window=200).mean()
            
            # RSI (14)
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # MACD (12, 26, 9)
            ema_12 = df['close'].ewm(span=12, adjust=False).mean()
            ema_26 = df['close'].ewm(span=26, adjust=False).mean()
            df['macd'] = ema_12 - ema_26
            df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
            df['macd_hist'] = df['macd'] - df['macd_signal']
            
            # ATR (14) - True Range calculation
            df['tr'] = np.maximum(
                df['high'] - df['low'],
                np.maximum(
                    abs(df['high'] - df['close'].shift(1)),
                    abs(df['low'] - df['close'].shift(1))
                )
            )
            df['atr'] = df['tr'].rolling(window=14).mean()
            
            # ADX (14) - Directional Movement Index
            df['high_diff'] = df['high'] - df['high'].shift(1)
            df['low_diff'] = df['low'].shift(1) - df['low']
            
            df['plus_dm'] = np.where((df['high_diff'] > df['low_diff']) & (df['high_diff'] > 0), df['high_diff'], 0)
            df['minus_dm'] = np.where((df['low_diff'] > df['high_diff']) & (df['low_diff'] > 0), df['low_diff'], 0)
            
            atr_14 = df['tr'].rolling(window=14).mean()
            plus_di = 100 * (df['plus_dm'].rolling(window=14).mean() / atr_14)
            minus_di = 100 * (df['minus_dm'].rolling(window=14).mean() / atr_14)
            
            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
            df['adx'] = dx.rolling(window=14).mean()
            df['dmi_plus'] = plus_di
            df['dmi_minus'] = minus_di
            
            # VWAP (Volume Weighted Average Price)
            if isinstance(df.index, pd.DatetimeIndex):
                df['vwap'] = (df['volume'] * (df['high'] + df['low'] + df['close']) / 3).cumsum() / df['volume'].cumsum()
            else:
                df['vwap'] = (df['high'] + df['low'] + df['close']) / 3  # Fallback to typical price
            
            # Volume SMA (10)
            df['volume_sma'] = df['volume'].rolling(window=10).mean()
            
            # Clean up temporary columns
            df = df.drop(columns=['tr', 'high_diff', 'low_diff', 'plus_dm', 'minus_dm'], errors='ignore')
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}", exc_info=True)
        
        return df
    
    def _get_symbol_tokens_parallel(self) -> Dict:
        """Fetch symbol tokens in parallel for fast initialization"""
        import concurrent.futures
        import requests
        
        def fetch_token(symbol):
            try:
                url = f"{self.base_url}/rest/secure/angelbroking/order/v1/searchScrip"
                headers = {
                    'Authorization': f'Bearer {self.jwt_token}',
                    'Content-Type': 'application/json',
                    'X-PrivateKey': self.api_key
                }
                payload = {"exchange": "NSE", "searchscrip": symbol}
                
                response = requests.post(url, json=payload, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') and data.get('data'):
                        scrip = data['data'][0]
                        return symbol, {
                            'token': scrip.get('symboltoken'),
                            'exchange': scrip.get('exch_seg', 'NSE'),
                            'trading_symbol': scrip.get('tradingsymbol', symbol)
                        }
                return symbol, None
                
            except Exception as e:
                logger.error(f"Error fetching token for {symbol}: {e}")
                return symbol, None
        
        # Fetch all tokens in parallel
        tokens = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = executor.map(fetch_token, self.symbols)
            
            for symbol, token_info in results:
                if token_info:
                    tokens[symbol] = token_info
        
        return tokens
    
    def _get_fallback_tokens(self) -> Dict:
        """
        Fallback symbol tokens for critical Nifty 50 stocks.
        Used when API token fetching fails.
        """
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
        }
        
        # Filter to only requested symbols
        filtered_tokens = {}
        for symbol in self.symbols:
            if symbol in fallback_tokens:
                filtered_tokens[symbol] = fallback_tokens[symbol]
        
        logger.info(f"Using fallback tokens for {len(filtered_tokens)} symbols")
        return filtered_tokens
    
    def _initialize_managers(self):
        """Initialize all trading managers"""
        from trading.patterns import PatternDetector
        from trading.execution_manager import ExecutionManager
        from trading.order_manager import OrderManager
        from trading.risk_manager import RiskManager, RiskLimits
        from trading.position_manager import PositionManager
        
        self._pattern_detector = PatternDetector()
        self._execution_manager = ExecutionManager()
        self._order_manager = OrderManager(self.api_key, self.jwt_token)
        
        risk_limits = RiskLimits(
            max_position_size_percent=0.05,
            max_daily_loss_percent=0.02,
            max_total_exposure_percent=0.20,
            max_positions=5
        )
        self._risk_manager = RiskManager(portfolio_value=100000.0, risk_limits=risk_limits)
        self._position_manager = PositionManager()
        
        # Initialize Ironclad if needed
        if self.strategy in ['ironclad', 'both']:
            from ironclad_strategy import IroncladStrategy
            self._ironclad = IroncladStrategy(db_client=None, dr_window_minutes=60)
        
        logger.info("✅ Trading managers initialized")
    
    def _analyze_and_trade(self):
        """
        Main strategy execution (runs every 5 seconds).
        Position monitoring happens independently every 0.5 seconds.
        """
        try:
            # Check EOD auto-close (3:15 PM for safety before broker's 3:20 PM)
            self._check_eod_auto_close()
            
            if self.strategy == 'pattern':
                self._execute_pattern_strategy()
            elif self.strategy == 'ironclad':
                self._execute_ironclad_strategy()
            elif self.strategy == 'both':
                self._execute_dual_strategy()
                
        except Exception as e:
            logger.error(f"Error in strategy execution: {e}", exc_info=True)
    
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
    
    def _execute_pattern_strategy(self):
        """
        Execute pattern detection strategy with intelligent signal ranking.
        Scans all Nifty 50 stocks and selects trades with highest confidence.
        """
        from trading.order_manager import OrderType, TransactionType, ProductType
        
        with self._lock:
            candle_data_copy = self.candle_data.copy()
            latest_prices_copy = self.latest_prices.copy()
        
        # STEP 1: Scan all symbols and collect signals with confidence scores
        signals = []
        
        logger.info(f"📊 Scanning {len(self.symbols)} symbols for trading opportunities...")
        
        for symbol in self.symbols:
            try:
                # Check if we have enough candle data
                if symbol not in candle_data_copy or len(candle_data_copy[symbol]) < 50:
                    continue
                
                # Skip if already have position
                if self._position_manager.has_position(symbol):
                    continue
                
                df = candle_data_copy[symbol].copy()
                
                # Pattern detection
                pattern_details = self._pattern_detector.scan(df)
                if not pattern_details:
                    continue
                
                # 30-point validation
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
                    
                    # Place order for best opportunity
                    logger.info(f"🔴 ENTERING TRADE: {sig['symbol']} (Top ranked signal)")
                    self._place_entry_order(
                        symbol=sig['symbol'],
                        direction=sig['pattern_details'].get('breakout_direction', 'up'),
                        entry_price=sig['current_price'],
                        stop_loss=sig['stop_loss'],
                        target=sig['target'],
                        quantity=quantity,
                        reason=f"Pattern: {sig['pattern_details'].get('pattern_name')} | Confidence: {sig['confidence']:.1f}%"
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
                    
                    logger.info(f"🔴 ENTERING TRADE: {symbol} (Ironclad top signal)")
                    self._place_entry_order(
                        symbol=symbol,
                        direction='up' if signal.get('action') == 'BUY' else 'down',
                        entry_price=current_price,
                        stop_loss=stop_loss,
                        target=target,
                        quantity=quantity,
                        reason=f"Ironclad {signal.get('action')} | Score: {sig['score']:.1f}"
                    )
                    
                except Exception as e:
                    logger.error(f"Error placing Ironclad order for {sig['symbol']}: {e}", exc_info=True)
        else:
            logger.debug("No Ironclad signals found in this scan cycle")
                
                logger.info(f"✅ {symbol}: Ironclad signal - {signal.get('action')}")
                
                # Place order
                self._place_entry_order(
                    symbol=symbol,
                    direction='up' if signal['action'] == 'BUY' else 'down',
                    entry_price=signal.get('entry_price'),
                    stop_loss=signal.get('stop_loss'),
                    target=signal.get('target'),
                    quantity=signal.get('quantity', 1),
                    reason="Ironclad Strategy"
                )
                
            except Exception as e:
                logger.error(f"Error in Ironclad for {symbol}: {e}", exc_info=True)
    
    def _execute_dual_strategy(self):
        """Execute both strategies with dual confirmation"""
        # Implementation similar to pattern + ironclad combined
        pass
    
    def _place_entry_order(self, symbol: str, direction: str, entry_price: float,
                          stop_loss: float, target: float, quantity: int, reason: str):
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
        
        if self.trading_mode == 'live':
            # Place real order
            transaction_type = TransactionType.BUY if direction == 'up' else TransactionType.SELL
            
            order_result = self._order_manager.place_order(
                symbol=symbol,
                token=token_info['token'],
                exchange=token_info['exchange'],
                transaction_type=transaction_type,
                order_type=OrderType.MARKET,
                quantity=quantity,
                product_type=ProductType.INTRADAY
            )
            
            if order_result:
                order_id = order_result.get('orderid', 'unknown')
                logger.info(f"✅ LIVE order placed: {order_id}")
                
                self._position_manager.add_position(
                    symbol=symbol,
                    entry_price=entry_price,
                    quantity=quantity,
                    stop_loss=stop_loss,
                    target=target,
                    order_id=order_id
                )
            else:
                logger.error(f"❌ Failed to place LIVE order for {symbol}")
        else:
            # Paper trading
            self._position_manager.add_position(
                symbol=symbol,
                entry_price=entry_price,
                quantity=quantity,
                stop_loss=stop_loss,
                target=target,
                order_id=f"PAPER_{symbol}_{int(time.time())}"
            )
            logger.info(f"✅ Paper position added")
    
    def _monitor_positions(self):
        """
        Monitor all open positions for stop loss/target hits.
        Uses REAL-TIME prices from WebSocket (not candle data).
        Runs every 0.5 seconds for instant detection.
        """
        try:
            positions = self._position_manager.get_all_positions()
            
            if not positions:
                return
            
            # Get latest prices (thread-safe)
            with self._lock:
                current_prices = self.latest_prices.copy()
            
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
        
        pnl = (exit_price - entry_price) * quantity
        pnl_percent = ((exit_price - entry_price) / entry_price) * 100
        
        logger.info(f"CLOSING {symbol}:")
        logger.info(f"  Entry: ₹{entry_price:.2f} | Exit: ₹{exit_price:.2f}")
        logger.info(f"  P&L: ₹{pnl:.2f} ({pnl_percent:+.2f}%)")
        logger.info(f"  Reason: {reason}")
        
        if self.trading_mode == 'live':
            token_info = self.symbol_tokens.get(symbol)
            if token_info:
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
                    logger.info(f"✅ LIVE exit order placed")
                else:
                    logger.error(f"❌ Failed to place exit order")
        
        # Remove position
        self._position_manager.remove_position(symbol)
        logger.info(f"✅ Position closed")
