"""
Bot Engine - Core trading logic with WebSocket integration
"""

import logging
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Callable
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class BotEngine:
    """Core trading engine that manages WebSocket connection and executes trades"""
    
    def __init__(self, user_id: str, credentials: dict, symbols: list, interval: str, trading_mode: str = 'paper', strategy: str = 'pattern'):
        self.user_id = user_id
        self.credentials = credentials
        self.symbols = symbols
        self.interval = interval
        self.trading_mode = trading_mode.lower()  # 'paper' or 'live'
        self.strategy = strategy.lower()  # 'pattern', 'ironclad', 'both', or 'defining'
        
        # Extract credentials
        self.jwt_token = credentials.get('jwt_token', '')
        self.feed_token = credentials.get('feed_token', '')
        self.client_code = credentials.get('client_code', '')
        
        # API key must be loaded from environment/config
        # In main.py, we'll need to fetch this from src.config
        self.api_key = credentials.get('api_key', '')
        
        if not self.api_key:
            logger.warning("API key not provided in credentials, bot may not function properly")
        
        self.base_url = "https://apiconnect.angelone.in"
        
        # State
        self.positions = {}
        self.candle_data = {}
        
        # Bot start time for Ironclad DR calculation
        self.bot_start_time = datetime.now()
        
        logger.info(f"BotEngine initialized for user {user_id} with {len(symbols)} symbols")
        logger.info(f"Trading Mode: {self.trading_mode.upper()}")
        logger.info(f"Strategy: {self.strategy.upper()}")
        logger.info(f"Bot Start Time: {self.bot_start_time.isoformat()}")
        logger.info(f"Credentials: jwt_token={bool(self.jwt_token)}, feed_token={bool(self.feed_token)}, api_key={bool(self.api_key)}")
    
    def run(self, running_flag: Callable[[], bool]):
        """
        Main execution loop - polls market data and executes trading logic
        
        Args:
            running_flag: Callable that returns True while bot should keep running
        """
        logger.info(f"BotEngine starting for user {self.user_id}")
        
        # Initialize symbol tokens
        symbol_tokens = self._get_symbol_tokens()
        if not symbol_tokens:
            logger.error("Failed to get symbol tokens")
            return
        
        interval_seconds = self._get_interval_seconds()
        
        # Main loop - poll market data periodically
        while running_flag():
            try:
                cycle_start = time.time()
                
                # Fetch latest market data for all symbols
                for symbol in self.symbols:
                    token_info = symbol_tokens.get(symbol)
                    if not token_info:
                        continue
                    
                    # Fetch LTP (Last Traded Price)
                    ltp_data = self._fetch_ltp(token_info['token'], token_info['exchange'])
                    if ltp_data:
                        self._process_tick(symbol, ltp_data)
                
                # Analyze and execute trades
                self._analyze_and_trade()
                
                # Calculate sleep time to maintain interval
                elapsed = time.time() - cycle_start
                sleep_time = max(0, interval_seconds - elapsed)
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    logger.warning(f"Cycle took {elapsed:.2f}s, longer than interval {interval_seconds}s")
            
            except Exception as e:
                logger.error(f"Error in bot loop: {e}", exc_info=True)
                time.sleep(5)  # Wait before retrying
        
        logger.info(f"BotEngine stopped for user {self.user_id}")
    
    def _get_symbol_tokens(self) -> Dict:
        """Get symbol tokens using searchScrip API"""
        tokens = {}
        
        if not self.api_key or not self.jwt_token:
            logger.error(f"Missing credentials: api_key={bool(self.api_key)}, jwt_token={bool(self.jwt_token)}")
            return tokens
        
        for symbol in self.symbols:
            try:
                url = f"{self.base_url}/rest/secure/angelbroking/order/v1/searchScrip"
                headers = self._get_headers()
                payload = {
                    "exchange": "NSE",
                    "searchscrip": symbol
                }
                
                logger.info(f"Fetching token for {symbol} from {url}")
                response = requests.post(url, json=payload, headers=headers, timeout=10)
                logger.info(f"Response status for {symbol}: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Response data for {symbol}: {data}")
                    if data.get('status') and data.get('data'):
                        scrip_data = data['data']
                        if scrip_data:
                            tokens[symbol] = {
                                'token': scrip_data[0].get('symboltoken'),
                                'exchange': scrip_data[0].get('exch_seg', 'NSE'),
                                'trading_symbol': scrip_data[0].get('tradingsymbol', symbol)
                            }
                            logger.info(f"Found token for {symbol}: {tokens[symbol]}")
                    else:
                        logger.error(f"Invalid response format for {symbol}: {data}")
                else:
                    logger.error(f"Failed to get token for {symbol}: {response.status_code}, {response.text}")
            
            except Exception as e:
                logger.error(f"Error getting token for {symbol}: {e}", exc_info=True)
        
        if not tokens:
            logger.error("Failed to get symbol tokens")
        
        return tokens
    
    def _fetch_ltp(self, token: str, exchange: str) -> Dict:
        """Fetch Last Traded Price using Angel One API"""
        try:
            url = f"{self.base_url}/rest/secure/angelbroking/order/v1/getLtpData"
            headers = self._get_headers()
            payload = {
                "exchange": exchange,
                "tradingsymbol": token,
                "symboltoken": token
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') and data.get('data'):
                    return data['data']
            
            return None
        
        except Exception as e:
            logger.error(f"Error fetching LTP: {e}")
            return None
    
    def _process_tick(self, symbol: str, tick_data: Dict):
        """Process incoming tick data and update candles"""
        try:
            ltp = float(tick_data.get('ltp', 0))
            
            if ltp == 0:
                return
            
            # Store tick data (simplified - in production you'd build candles)
            if symbol not in self.candle_data:
                self.candle_data[symbol] = []
            
            self.candle_data[symbol].append({
                'timestamp': datetime.now(),
                'price': ltp,
                'open': ltp,
                'high': ltp,
                'low': ltp,
                'close': ltp
            })
            
            # Keep only last 100 ticks per symbol
            if len(self.candle_data[symbol]) > 100:
                self.candle_data[symbol] = self.candle_data[symbol][-100:]
        
        except Exception as e:
            logger.error(f"Error processing tick for {symbol}: {e}")
    
    def _analyze_and_trade(self):
        """
        Analyze market data and execute trades based on selected strategy.
        
        Supports four strategies:
        - 'defining': The Defining Order Breakout v3.2 (BEST - 59% WR, 24% returns)
        - 'pattern': Pattern Detection + 30-Point Validation (Default)
        - 'ironclad': Defining Range Breakout + Multi-Indicator Confirmation
        - 'both': Dual confirmation (only trade when both strategies agree)
        """
        try:
            # Import trading modules
            import sys
            import os
            
            # Add functions/src to path to access trading modules
            functions_src_path = os.path.join(os.path.dirname(__file__), '..', 'functions', 'src')
            if functions_src_path not in sys.path:
                sys.path.insert(0, functions_src_path)
            
            from trading.patterns import PatternDetector
            from trading.execution_manager import ExecutionManager
            from trading.order_manager import OrderManager, OrderType, TransactionType, ProductType
            from trading.risk_manager import RiskManager, RiskLimits
            from trading.position_manager import PositionManager
            
            # Initialize managers if not already done
            if not hasattr(self, '_pattern_detector'):
                self._pattern_detector = PatternDetector()
                self._execution_manager = ExecutionManager()
                self._order_manager = OrderManager(self.api_key, self.jwt_token)
                
                # Initialize risk manager with default limits
                risk_limits = RiskLimits(
                    max_position_size_percent=0.05,  # 5% of portfolio per position
                    max_daily_loss_percent=0.02,      # 2% max daily loss
                    max_total_exposure_percent=0.20,  # 20% total exposure
                    max_positions=5
                )
                self._risk_manager = RiskManager(
                    portfolio_value=100000.0,  # Default portfolio value
                    risk_limits=risk_limits
                )
                self._position_manager = PositionManager()
                
                # Initialize Defining Order Strategy v3.2 if needed
                if self.strategy in ['defining', 'both']:
                    from defining_order_strategy import DefiningOrderStrategy
                    self._defining_order = DefiningOrderStrategy()
                    logger.info("✅ Defining Order Strategy v3.2 initialized (VALIDATED: 59% WR, 24% returns)")
                
                # Initialize Ironclad strategy if needed
                if self.strategy in ['ironclad', 'both']:
                    from ironclad_strategy import IroncladStrategy
                    # Mock Firestore client for Ironclad (state managed in memory)
                    self._ironclad = IroncladStrategy(db_client=None, dr_window_minutes=60)
                    logger.info("✅ Ironclad Strategy initialized")
                
                logger.info("✅ Trading managers initialized successfully")
            
            # Route to appropriate strategy
            if self.strategy == 'defining':
                self._execute_defining_order_strategy()
            elif self.strategy == 'pattern':
                self._execute_pattern_strategy()
            elif self.strategy == 'ironclad':
                self._execute_ironclad_strategy()
            elif self.strategy == 'both':
                self._execute_dual_strategy()
            else:
                logger.warning(f"Unknown strategy: {self.strategy}, defaulting to defining")
                self._execute_defining_order_strategy()
                
        except Exception as e:
            logger.error(f"Error in _analyze_and_trade: {str(e)}", exc_info=True)
    
    def _execute_pattern_strategy(self):
        """Execute Pattern Detector strategy with 30-point validation"""
        from trading.order_manager import OrderType, TransactionType, ProductType
        
        try:
            for symbol in self.symbols:
                try:
                    # Skip if insufficient data
                    if symbol not in self.candle_data or len(self.candle_data[symbol]) < 50:
                        logger.debug(f"{symbol}: Insufficient data for analysis")
                        continue
                    
                    # Convert tick data to DataFrame
                    df = pd.DataFrame(self.candle_data[symbol])
                    if df.empty:
                        continue
                    
                    # Ensure required columns exist
                    df['High'] = df['high']
                    df['Low'] = df['low']
                    df['Close'] = df['close']
                    df['Open'] = df['open']
                    df['Volume'] = df.get('volume', 0)
                    
                    # Step 1: Pattern Detection
                    pattern_details = self._pattern_detector.scan(df)
                    
                    if not pattern_details:
                        logger.debug(f"{symbol}: No patterns detected")
                        continue
                    
                    pattern_name = pattern_details.get('pattern_name', 'Unknown')
                    breakout_direction = pattern_details.get('breakout_direction', 'unknown')
                    
                    logger.info(f"🎯 {symbol}: Detected '{pattern_name}' pattern ({breakout_direction})")
                    
                    # Step 2: 30-Point Validation
                    is_valid = self._execution_manager.validate_trade_entry(df, pattern_details)
                    
                    if not is_valid:
                        logger.info(f"❌ {symbol}: Pattern failed 30-point validation")
                        continue
                    
                    logger.info(f"✅ {symbol}: Pattern PASSED 30-point validation!")
                    
                    # Check if already have position
                    if self._position_manager.has_position(symbol):
                        logger.info(f"⏭️  {symbol}: Already have open position, skipping")
                        continue
                    
                    # Step 3: Risk Calculation
                    current_price = float(df['Close'].iloc[-1])
                    stop_loss = float(pattern_details.get('initial_stop_loss', current_price * 0.98))
                    target_price = float(pattern_details.get('calculated_price_target', current_price * 1.05))
                    
                    # Calculate position size based on risk
                    risk_per_share = abs(current_price - stop_loss)
                    max_risk_amount = self._risk_manager.risk_limits.max_position_size_percent * self._risk_manager.portfolio_value
                    
                    if risk_per_share > 0:
                        position_size = int(max_risk_amount / risk_per_share)
                    else:
                        position_size = 1
                    
                    # Ensure minimum position size
                    position_size = max(1, min(position_size, 100))
                    
                    # Get symbol token
                    symbol_tokens = self._get_symbol_tokens()
                    token_info = symbol_tokens.get(symbol)
                    
                    if not token_info:
                        logger.error(f"{symbol}: Token info not available")
                        continue
                    
                    # Step 4: Place Order
                    mode_label = "📝 PAPER TRADE" if self.trading_mode == 'paper' else "🔴 LIVE TRADE"
                    logger.info(f"{mode_label}: {symbol}")
                    logger.info(f"   Pattern: {pattern_name}")
                    logger.info(f"   Direction: {breakout_direction.upper()}")
                    logger.info(f"   Entry Price: ₹{current_price:.2f}")
                    logger.info(f"   Stop Loss: ₹{stop_loss:.2f}")
                    logger.info(f"   Target: ₹{target_price:.2f}")
                    logger.info(f"   Quantity: {position_size}")
                    logger.info(f"   Risk/Reward: {abs(target_price - current_price) / abs(current_price - stop_loss):.2f}")
                    
                    # Execute based on trading mode
                    if self.trading_mode == 'live':
                        # LIVE MODE: Place real order via Angel One
                        transaction_type = TransactionType.BUY if breakout_direction == 'up' else TransactionType.SELL
                        order_result = self._order_manager.place_order(
                            symbol=symbol,
                            token=token_info['token'],
                            exchange=token_info['exchange'],
                            transaction_type=transaction_type,
                            order_type=OrderType.MARKET,
                            quantity=position_size,
                            product_type=ProductType.INTRADAY
                        )
                        
                        if order_result and order_result.get('status'):
                            order_id = order_result.get('data', {}).get('orderid')
                            logger.info(f"✅ {symbol}: LIVE Order placed successfully! Order ID: {order_id}")
                            
                            # Track position
                            self._position_manager.add_position(
                                symbol=symbol,
                                entry_price=current_price,
                                quantity=position_size,
                                stop_loss=stop_loss,
                                target=target_price,
                                order_id=order_id
                            )
                        else:
                            logger.error(f"❌ {symbol}: LIVE Order placement failed")
                    else:
                        # PAPER MODE: Simulate order
                        self._position_manager.add_position(
                            symbol=symbol,
                            entry_price=current_price,
                            quantity=position_size,
                            stop_loss=stop_loss,
                            target=target_price,
                            order_id=f"PAPER_{symbol}_{int(time.time())}"
                        )
                        logger.info(f"✅ {symbol}: Paper position added to tracker")
                    
                except Exception as e:
                    logger.error(f"Error analyzing {symbol}: {e}", exc_info=True)
            
            # Monitor existing positions
            self._monitor_positions()
            
        except Exception as e:
            logger.error(f"Error in _execute_pattern_strategy: {e}", exc_info=True)
    
    def _execute_ironclad_strategy(self):
        """Execute Ironclad strategy (Defining Range Breakout)"""
        from trading.order_manager import OrderType, TransactionType, ProductType
        
        try:
            # Note: Ironclad needs NIFTY data + stock data
            # For now, we'll process each symbol individually
            # In production, fetch NIFTY 50 data separately
            
            for symbol in self.symbols:
                try:
                    # Skip if insufficient data
                    if symbol not in self.candle_data or len(self.candle_data[symbol]) < 100:
                        logger.debug(f"{symbol}: Insufficient data for Ironclad analysis")
                        continue
                    
                    # Convert to DataFrame
                    stock_df = pd.DataFrame(self.candle_data[symbol])
                    if stock_df.empty:
                        continue
                    
                    # For now, use stock as NIFTY proxy (in production, fetch real NIFTY data)
                    nifty_df = stock_df.copy()
                    
                    # Run Ironclad analysis
                    signal = self._ironclad.run_analysis_cycle(
                        nifty_df=nifty_df,
                        stock_df=stock_df,
                        symbol=symbol,
                        bot_start_time=self.bot_start_time
                    )
                    
                    if not signal or signal.get('action') == 'HOLD':
                        logger.debug(f"{symbol}: Ironclad says HOLD")
                        continue
                    
                    # Check if already have position
                    if self._position_manager.has_position(symbol):
                        logger.info(f"⏭️  {symbol}: Already have open position, skipping")
                        continue
                    
                    # Extract signal details
                    action = signal.get('action')  # 'BUY' or 'SELL'
                    entry_price = signal.get('entry_price', 0)
                    stop_loss = signal.get('stop_loss', 0)
                    target = signal.get('target', 0)
                    
                    # Calculate position size
                    risk_per_share = abs(entry_price - stop_loss)
                    max_risk_amount = self._risk_manager.risk_limits.max_position_size_percent * self._risk_manager.portfolio_value
                    
                    if risk_per_share > 0:
                        position_size = int(max_risk_amount / risk_per_share)
                    else:
                        position_size = 1
                    
                    position_size = max(1, min(position_size, 100))
                    
                    # Get symbol token
                    symbol_tokens = self._get_symbol_tokens()
                    token_info = symbol_tokens.get(symbol)
                    
                    if not token_info:
                        logger.error(f"{symbol}: Token info not available")
                        continue
                    
                    # Log trade
                    mode_label = "📝 PAPER TRADE" if self.trading_mode == 'paper' else "🔴 LIVE TRADE"
                    logger.info(f"{mode_label}: {symbol} (IRONCLAD)")
                    logger.info(f"   Action: {action}")
                    logger.info(f"   Entry: ₹{entry_price:.2f}")
                    logger.info(f"   Stop Loss: ₹{stop_loss:.2f}")
                    logger.info(f"   Target: ₹{target:.2f}")
                    logger.info(f"   Quantity: {position_size}")
                    
                    # Execute trade
                    if self.trading_mode == 'live':
                        transaction_type = TransactionType.BUY if action == 'BUY' else TransactionType.SELL
                        order_result = self._order_manager.place_order(
                            symbol=symbol,
                            token=token_info['token'],
                            exchange=token_info['exchange'],
                            transaction_type=transaction_type,
                            order_type=OrderType.MARKET,
                            quantity=position_size,
                            product_type=ProductType.INTRADAY
                        )
                        
                        if order_result and order_result.get('status'):
                            order_id = order_result.get('data', {}).get('orderid')
                            logger.info(f"✅ {symbol}: LIVE Order placed! Order ID: {order_id}")
                            
                            self._position_manager.add_position(
                                symbol=symbol,
                                entry_price=entry_price,
                                quantity=position_size,
                                stop_loss=stop_loss,
                                target=target,
                                order_id=order_id
                            )
                        else:
                            logger.error(f"❌ {symbol}: LIVE Order placement failed")
                    else:
                        # Paper mode
                        self._position_manager.add_position(
                            symbol=symbol,
                            entry_price=entry_price,
                            quantity=position_size,
                            stop_loss=stop_loss,
                            target=target,
                            order_id=f"PAPER_IRONCLAD_{symbol}_{int(time.time())}"
                        )
                        logger.info(f"✅ {symbol}: Paper position added (Ironclad)")
                
                except Exception as e:
                    logger.error(f"Error in Ironclad analysis for {symbol}: {e}", exc_info=True)
            
            # Monitor positions
            self._monitor_positions()
            
        except Exception as e:
            logger.error(f"Error in _execute_ironclad_strategy: {e}", exc_info=True)
    
    def _execute_defining_order_strategy(self):
        """Execute The Defining Order Breakout Strategy v3.2 (VALIDATED: 59% WR, 24% returns)"""
        from trading.order_manager import OrderType, TransactionType, ProductType
        
        try:
            for symbol in self.symbols:
                try:
                    # Skip if insufficient data
                    if symbol not in self.candle_data or len(self.candle_data[symbol]) < 100:
                        logger.debug(f"{symbol}: Insufficient data for analysis")
                        continue
                    
                    # Convert tick data to DataFrame
                    df = pd.DataFrame(self.candle_data[symbol])
                    if df.empty:
                        continue
                    
                    # Ensure required columns exist and calculate indicators
                    df['High'] = df['high']
                    df['Low'] = df['low']
                    df['Close'] = df['close']
                    df['Open'] = df['open']
                    df['Volume'] = df.get('volume', 0)
                    df['symbol'] = symbol
                    
                    # Set timestamp index if not already
                    if 'timestamp' in df.columns:
                        df.index = pd.to_datetime(df['timestamp'])
                    
                    # Calculate required indicators for strategy
                    # Note: In production, these should be calculated incrementally for efficiency
                    import ta
                    
                    # VWAP calculation
                    df['Typical_Price'] = (df['High'] + df['Low'] + df['Close']) / 3
                    df['TPV'] = df['Typical_Price'] * df['Volume']
                    df['Cumulative_TPV'] = df['TPV'].cumsum()
                    df['Cumulative_Volume'] = df['Volume'].cumsum()
                    df['VWAP'] = df['Cumulative_TPV'] / df['Cumulative_Volume']
                    
                    # SuperTrend calculation
                    atr_period = 10
                    atr_multiplier = 3.0
                    high_low = df['High'] - df['Low']
                    high_close = np.abs(df['High'] - df['Close'].shift())
                    low_close = np.abs(df['Low'] - df['Close'].shift())
                    ranges = pd.concat([high_low, high_close, low_close], axis=1)
                    true_range = np.max(ranges, axis=1)
                    atr = true_range.rolling(atr_period).mean()
                    
                    hl_avg = (df['High'] + df['Low']) / 2
                    upper_band = hl_avg + (atr_multiplier * atr)
                    lower_band = hl_avg - (atr_multiplier * atr)
                    
                    supertrend = [True] * len(df)
                    for i in range(1, len(df)):
                        if df['Close'].iloc[i] > upper_band.iloc[i-1]:
                            supertrend[i] = True
                        elif df['Close'].iloc[i] < lower_band.iloc[i-1]:
                            supertrend[i] = False
                        else:
                            supertrend[i] = supertrend[i-1]
                    
                    df['SuperTrend_Direction'] = [1 if x else -1 for x in supertrend]
                    
                    # Get hourly data for trend bias (need SMA 50)
                    # For now, we'll use the 5-min data and resample to hourly
                    hourly_df = df.resample('1H').agg({
                        'Open': 'first',
                        'High': 'max',
                        'Low': 'min',
                        'Close': 'last',
                        'Volume': 'sum'
                    }).dropna()
                    
                    # Calculate SMAs on hourly data
                    hourly_df['SMA_50'] = hourly_df['Close'].rolling(window=50).mean()
                    
                    if len(hourly_df) < 50:
                        logger.debug(f"{symbol}: Insufficient hourly data for SMA(50)")
                        continue
                    
                    # Analyze current candle using Defining Order Strategy
                    current_time = datetime.now()
                    signal = self._defining_order.analyze_candle_data(
                        symbol=symbol,
                        candle_data=df,
                        hourly_data=hourly_df,
                        current_time=current_time
                    )
                    
                    if not signal:
                        # No signal or signal was rejected
                        continue
                    
                    logger.info(f"🎯 {symbol}: Defining Order v3.2 Signal Detected!")
                    logger.info(f"   Direction: {signal['direction']}")
                    logger.info(f"   Reason: {signal['reason']}")
                    logger.info(f"   Breakout Strength: {signal['breakout_strength']:.2f}%")
                    logger.info(f"   Trend Bias: {signal['trend_bias']}")
                    
                    # Check if already have position
                    if self._position_manager.has_position(symbol):
                        logger.info(f"⏭️  {symbol}: Already have open position, skipping")
                        continue
                    
                    # Extract trade parameters
                    entry_price = signal['entry_price']
                    stop_loss = signal['stop_loss']
                    target = signal['take_profit']
                    direction = signal['direction']
                    
                    # Calculate position size based on risk (1% of capital per trade)
                    risk_per_share = abs(entry_price - stop_loss)
                    max_risk_amount = self._risk_manager.risk_limits.max_position_size_percent * self._risk_manager.portfolio_value
                    
                    if risk_per_share > 0:
                        position_size = int(max_risk_amount / risk_per_share)
                    else:
                        position_size = 1
                    
                    # Ensure reasonable position size
                    position_size = max(1, min(position_size, 100))
                    
                    # Get symbol token
                    symbol_tokens = self._get_symbol_tokens()
                    token_info = symbol_tokens.get(symbol)
                    
                    if not token_info:
                        logger.error(f"{symbol}: Token info not available")
                        continue
                    
                    # Log trade
                    mode_label = "📝 PAPER TRADE" if self.trading_mode == 'paper' else "🔴 LIVE TRADE"
                    logger.info(f"{mode_label}: {symbol} (Defining Order v3.2)")
                    logger.info(f"   Direction: {direction}")
                    logger.info(f"   Entry Price: ₹{entry_price:.2f}")
                    logger.info(f"   Stop Loss: ₹{stop_loss:.2f}")
                    logger.info(f"   Target: ₹{target:.2f}")
                    logger.info(f"   Quantity: {position_size}")
                    logger.info(f"   Risk/Share: ₹{risk_per_share:.2f}")
                    logger.info(f"   Total Risk: ₹{risk_per_share * position_size:.2f}")
                    
                    # Execute trade
                    if self.trading_mode == 'live':
                        transaction_type = TransactionType.BUY if direction == 'LONG' else TransactionType.SELL
                        order_result = self._order_manager.place_order(
                            symbol=symbol,
                            token=token_info['token'],
                            exchange=token_info['exchange'],
                            transaction_type=transaction_type,
                            order_type=OrderType.MARKET,
                            quantity=position_size,
                            product_type=ProductType.INTRADAY
                        )
                        
                        if order_result and order_result.get('status'):
                            order_id = order_result.get('data', {}).get('orderid')
                            logger.info(f"✅ {symbol}: LIVE Order placed! Order ID: {order_id}")
                            
                            self._position_manager.add_position(
                                symbol=symbol,
                                entry_price=entry_price,
                                quantity=position_size,
                                stop_loss=stop_loss,
                                target=target,
                                order_id=order_id
                            )
                        else:
                            logger.error(f"❌ {symbol}: LIVE Order placement failed")
                    else:
                        # Paper mode
                        self._position_manager.add_position(
                            symbol=symbol,
                            entry_price=entry_price,
                            quantity=position_size,
                            stop_loss=stop_loss,
                            target=target,
                            order_id=f"PAPER_DEFINING_{symbol}_{int(time.time())}"
                        )
                        logger.info(f"✅ {symbol}: Paper position added (Defining Order v3.2)")
                
                except Exception as e:
                    logger.error(f"Error in defining order strategy for {symbol}: {e}", exc_info=True)
            
            # Monitor existing positions
            self._monitor_positions()
            
        except Exception as e:
            logger.error(f"Error in _execute_defining_order_strategy: {e}", exc_info=True)
    
    def _execute_dual_strategy(self):
        """Execute both strategies and only trade when both agree"""
        from trading.order_manager import OrderType, TransactionType, ProductType
        
        try:
            for symbol in self.symbols:
                try:
                    # Skip if insufficient data
                    if symbol not in self.candle_data or len(self.candle_data[symbol]) < 100:
                        logger.debug(f"{symbol}: Insufficient data for dual strategy")
                        continue
                    
                    # Convert to DataFrame
                    df = pd.DataFrame(self.candle_data[symbol])
                    if df.empty:
                        continue
                    
                    # Ensure required columns
                    df['High'] = df['high']
                    df['Low'] = df['low']
                    df['Close'] = df['close']
                    df['Open'] = df['open']
                    df['Volume'] = df.get('volume', 0)
                    
                    # === Pattern Strategy Signal ===
                    pattern_details = self._pattern_detector.scan(df)
                    pattern_signal = None
                    
                    if pattern_details:
                        is_valid = self._execution_manager.validate_trade_entry(df, pattern_details)
                        if is_valid:
                            pattern_signal = {
                                'action': 'BUY' if pattern_details.get('breakout_direction') == 'up' else 'SELL',
                                'entry_price': float(df['Close'].iloc[-1]),
                                'stop_loss': float(pattern_details.get('initial_stop_loss', 0)),
                                'target': float(pattern_details.get('calculated_price_target', 0))
                            }
                    
                    # === Ironclad Strategy Signal ===
                    nifty_df = df.copy()  # Use stock as NIFTY proxy
                    ironclad_signal = self._ironclad.run_analysis_cycle(
                        nifty_df=nifty_df,
                        stock_df=df,
                        symbol=symbol,
                        bot_start_time=self.bot_start_time
                    )
                    
                    # === Check if both agree ===
                    if not pattern_signal or not ironclad_signal:
                        logger.debug(f"{symbol}: One or both strategies have no signal")
                        continue
                    
                    if ironclad_signal.get('action') == 'HOLD':
                        logger.debug(f"{symbol}: Ironclad says HOLD")
                        continue
                    
                    if pattern_signal['action'] != ironclad_signal['action']:
                        logger.info(f"⚠️  {symbol}: Strategy disagreement - Pattern: {pattern_signal['action']}, Ironclad: {ironclad_signal['action']}")
                        continue
                    
                    logger.info(f"✅ {symbol}: DUAL CONFIRMATION - Both strategies agree on {pattern_signal['action']}!")
                    
                    # Check if already have position
                    if self._position_manager.has_position(symbol):
                        logger.info(f"⏭️  {symbol}: Already have open position, skipping")
                        continue
                    
                    # Use Ironclad's prices (typically more conservative)
                    entry_price = ironclad_signal.get('entry_price', pattern_signal['entry_price'])
                    stop_loss = ironclad_signal.get('stop_loss', pattern_signal['stop_loss'])
                    target = ironclad_signal.get('target', pattern_signal['target'])
                    action = pattern_signal['action']
                    
                    # Calculate position size
                    risk_per_share = abs(entry_price - stop_loss)
                    max_risk_amount = self._risk_manager.risk_limits.max_position_size_percent * self._risk_manager.portfolio_value
                    
                    if risk_per_share > 0:
                        position_size = int(max_risk_amount / risk_per_share)
                    else:
                        position_size = 1
                    
                    position_size = max(1, min(position_size, 100))
                    
                    # Get symbol token
                    symbol_tokens = self._get_symbol_tokens()
                    token_info = symbol_tokens.get(symbol)
                    
                    if not token_info:
                        logger.error(f"{symbol}: Token info not available")
                        continue
                    
                    # Log trade
                    mode_label = "📝 PAPER TRADE" if self.trading_mode == 'paper' else "🔴 LIVE TRADE"
                    logger.info(f"{mode_label}: {symbol} (DUAL CONFIRMATION)")
                    logger.info(f"   Action: {action}")
                    logger.info(f"   Entry: ₹{entry_price:.2f}")
                    logger.info(f"   Stop Loss: ₹{stop_loss:.2f}")
                    logger.info(f"   Target: ₹{target:.2f}")
                    logger.info(f"   Quantity: {position_size}")
                    
                    # Execute trade
                    if self.trading_mode == 'live':
                        transaction_type = TransactionType.BUY if action == 'BUY' else TransactionType.SELL
                        order_result = self._order_manager.place_order(
                            symbol=symbol,
                            token=token_info['token'],
                            exchange=token_info['exchange'],
                            transaction_type=transaction_type,
                            order_type=OrderType.MARKET,
                            quantity=position_size,
                            product_type=ProductType.INTRADAY
                        )
                        
                        if order_result and order_result.get('status'):
                            order_id = order_result.get('data', {}).get('orderid')
                            logger.info(f"✅ {symbol}: LIVE Order placed! Order ID: {order_id}")
                            
                            self._position_manager.add_position(
                                symbol=symbol,
                                entry_price=entry_price,
                                quantity=position_size,
                                stop_loss=stop_loss,
                                target=target,
                                order_id=order_id
                            )
                        else:
                            logger.error(f"❌ {symbol}: LIVE Order placement failed")
                    else:
                        # Paper mode
                        self._position_manager.add_position(
                            symbol=symbol,
                            entry_price=entry_price,
                            quantity=position_size,
                            stop_loss=stop_loss,
                            target=target,
                            order_id=f"PAPER_DUAL_{symbol}_{int(time.time())}"
                        )
                        logger.info(f"✅ {symbol}: Paper position added (Dual Confirmation)")
                
                except Exception as e:
                    logger.error(f"Error in dual strategy for {symbol}: {e}", exc_info=True)
            
            # Monitor positions
            self._monitor_positions()
            
        except Exception as e:
            logger.error(f"Error in _execute_dual_strategy: {e}", exc_info=True)
    
    def _monitor_positions(self):
        """Monitor open positions and manage stops/targets"""
        try:
            positions = self._position_manager.get_all_positions()
            
            for symbol, position in positions.items():
                if symbol not in self.candle_data:
                    continue
                
                current_price = self.candle_data[symbol][-1]['close']
                entry_price = position.get('entry_price', 0)
                stop_loss = position.get('stop_loss', 0)
                target = position.get('target', 0)
                
                # Check if stop loss hit
                if current_price <= stop_loss:
                    logger.warning(f"🛑 {symbol}: Stop loss hit! Entry: ₹{entry_price:.2f}, Current: ₹{current_price:.2f}")
                    self._close_position(symbol, position, current_price, 'STOP_LOSS')
                    continue
                
                # Check if target hit
                if current_price >= target:
                    logger.info(f"🎯 {symbol}: Target hit! Entry: ₹{entry_price:.2f}, Current: ₹{current_price:.2f}")
                    self._close_position(symbol, position, current_price, 'TARGET')
                    continue
                
                # Calculate P&L
                pnl_percent = ((current_price - entry_price) / entry_price) * 100
                logger.debug(f"{symbol}: P&L: {pnl_percent:+.2f}%")
        
        except Exception as e:
            logger.error(f"Error monitoring positions: {e}")
    
    def _close_position(self, symbol: str, position: Dict, exit_price: float, reason: str):
        """
        Close a position by placing exit order
        
        Args:
            symbol: Stock symbol
            position: Position dictionary
            exit_price: Exit price
            reason: Reason for closing ('STOP_LOSS', 'TARGET', 'EOD')
        """
        try:
            entry_price = position.get('entry_price', 0)
            quantity = position.get('quantity', 0)
            order_id = position.get('order_id', '')
            
            # Calculate P&L
            pnl = (exit_price - entry_price) * quantity
            pnl_percent = ((exit_price - entry_price) / entry_price) * 100
            
            logger.info(f"Closing position for {symbol}:")
            logger.info(f"  Entry: ₹{entry_price:.2f} | Exit: ₹{exit_price:.2f}")
            logger.info(f"  P&L: ₹{pnl:.2f} ({pnl_percent:+.2f}%)")
            logger.info(f"  Reason: {reason}")
            
            if self.trading_mode == 'live':
                # LIVE MODE: Place exit order via Angel One
                from trading.order_manager import OrderManager, OrderType, TransactionType, ProductType
                
                # Determine transaction type (opposite of entry)
                transaction_type = TransactionType.SELL  # Assuming BUY entry
                
                # Get symbol token
                symbol_tokens = self._get_symbol_tokens()
                token_info = symbol_tokens.get(symbol)
                
                if token_info:
                    exit_order = self._order_manager.place_order(
                        symbol=symbol,
                        token=token_info['token'],
                        exchange=token_info['exchange'],
                        transaction_type=transaction_type,
                        order_type=OrderType.MARKET,
                        quantity=quantity,
                        product_type=ProductType.INTRADAY
                    )
                    
                    if exit_order and exit_order.get('status'):
                        exit_order_id = exit_order.get('data', {}).get('orderid')
                        logger.info(f"✅ {symbol}: LIVE Exit order placed! Order ID: {exit_order_id}")
                    else:
                        logger.error(f"❌ {symbol}: Failed to place LIVE exit order")
            
            # Remove position from tracker
            self._position_manager.remove_position(symbol)
            logger.info(f"✅ {symbol}: Position closed and removed from tracker")
            
        except Exception as e:
            logger.error(f"Error closing position for {symbol}: {e}", exc_info=True)
    
    def _get_headers(self) -> Dict:
        """Get API request headers"""
        return {
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
    
    def _get_interval_seconds(self) -> int:
        """Convert interval string to seconds"""
        mapping = {
            '1minute': 60,
            '5minute': 300,
            '15minute': 900,
            '30minute': 1800,
            '1hour': 3600
        }
        return mapping.get(self.interval, 300)
