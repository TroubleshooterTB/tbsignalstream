"""
24/7 Cryptocurrency Trading Bot Engine
======================================
CoinDCX integration with BTC/ETH switching capability.

Key Features:
- 24/7 trading (no market hours restrictions)
- BTC/USDT and ETH/USDT support with toggle switch
- Real-time WebSocket price feeds
- Self-healing (same patterns as stock bot)
- Strategy placeholder architecture (user to provide comprehensive strategies)
- Separate capital management
"""

import asyncio
import logging
import time
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Optional, List
from firebase_admin import firestore

from .brokers.coindcx_broker import CoinDCXBroker
from .brokers.coindcx_websocket import CoinDCXWebSocket

logger = logging.getLogger(__name__)


class CryptoBotEngine:
    """24/7 Cryptocurrency Trading Bot"""
    
    def __init__(self, user_id: str, api_key: str, api_secret: str, 
                 initial_pair: str = "BTC", firestore_client=None):
        """
        Initialize crypto bot.
        
        Args:
            user_id: User identifier
            api_key: CoinDCX API key
            api_secret: CoinDCX API secret
            initial_pair: Starting trading pair ("BTC" or "ETH")
            firestore_client: Firestore client for data persistence
        """
        self.user_id = user_id
        self.firestore_client = firestore_client or firestore.client()
        
        # Initialize brokers
        self.broker = CoinDCXBroker(api_key, api_secret)
        self.ws = CoinDCXWebSocket(api_key, api_secret)
        
        # ========================================
        # BTC/ETH SWITCHING MECHANISM
        # ========================================
        self.trading_pairs = {
            "BTC": "BTCUSDT",
            "ETH": "ETHUSDT"
        }
        self.ws_pairs = {
            "BTC": "B-BTC_USDT",
            "ETH": "B-ETH_USDT"
        }
        self.active_pair = initial_pair  # "BTC" or "ETH"
        
        # Bot state
        self.is_running = False
        self.is_bootstrapped = False
        self.positions = {}  # {symbol: position_info}
        self.daily_pnl = 0
        self.total_trades = 0
        
        # Historical data
        self.candles = {}  # {symbol: [candles]}
        self.price_history = {}  # {symbol: [prices]}
        
        # Performance tracking
        self.start_time = None
        self.last_health_check = time.time()
        self.health_check_interval = 60  # seconds
        
        # Strategy state
        self.strategy_state = {
            'indicators': {},
            'signals': {},
            'last_analysis_time': 0
        }
        
        # Risk management parameters
        self.risk_params = {
            'target_volatility': 0.25,  # 25% annualized
            'max_position_weight': 2.0,  # 200% max exposure
            'rebalance_threshold': 0.20,  # 20% deviation triggers rebalance
            'fee_barrier_pct': 0.0015,  # 0.15% (covers entry + exit + slippage)
            'min_daily_volume_usd': 1_000_000,  # $1M minimum liquidity
            'max_daily_loss_pct': 0.05,  # 5% max daily loss
            'stop_loss_day_pct': 0.02,  # 2% stop loss for day strategy
            'stop_loss_night_multiplier': 0.5,  # 50% of daily volatility for night
        }
        
        # Performance tracking
        self.daily_starting_capital = 0
        self.daily_loss_limit_triggered = False
        
        # Indicator history
        self.indicator_history = {
            'ema8': [],
            'ema16': [],
            'ema32': [],
            'rsi': [],
            'bb_upper': [],
            'bb_middle': [],
            'bb_lower': [],
            'volatility': []
        }
        
        logger.info(f"✅ CryptoBotEngine initialized for {user_id}")
        logger.info(f"   Active pair: {self.active_pair} ({self.get_active_symbol()})")
        logger.info(f"   Day Strategy: Momentum Scalping (5m candles, Triple EMA + RSI)")
        logger.info(f"   Night Strategy: Mean Reversion (1h candles, Bollinger Bands + RSI)")
        logger.info(f"   Risk Management: {self.risk_params['target_volatility']*100}% target volatility")
    
    # ========================================
    # PAIR SWITCHING
    # ========================================
    
    def switch_pair(self, pair: str):
        """
        Switch between BTC and ETH.
        
        Args:
            pair: "BTC" or "ETH"
        """
        if pair not in self.trading_pairs:
            logger.error(f"❌ Invalid pair: {pair}")
            return False
        
        old_pair = self.active_pair
        old_symbol = self.get_active_symbol()
        
        # Close any open positions on current pair
        if old_symbol in self.positions:
            logger.info(f"⚠️  Closing position on {old_symbol} before switching...")
            # TODO: Implement position closing logic
        
        # Switch to new pair
        self.active_pair = pair
        new_symbol = self.get_active_symbol()
        
        logger.info(f"🔄 Switched from {old_pair} to {pair}")
        logger.info(f"   Symbol: {old_symbol} → {new_symbol}")
        
        # Save to Firestore
        self._save_pair_switch(old_pair, pair)
        
        return True
    
    def get_active_symbol(self) -> str:
        """Get current active trading pair symbol (e.g., 'BTCUSDT')"""
        return self.trading_pairs[self.active_pair]
    
    def get_active_ws_symbol(self) -> str:
        """Get current active WebSocket symbol (e.g., 'B-BTC_USDT')"""
        return self.ws_pairs[self.active_pair]
    
    # ========================================
    # MAIN BOT LIFECYCLE
    # ========================================
    
    async def start(self, running_flag):
        """
        Start 24/7 trading bot.
        
        Args:
            running_flag: asyncio.Event to control bot lifecycle
        """
        try:
            self.is_running = True
            self.start_time = time.time()
            
            logger.info("="*60)
            logger.info("🚀 STARTING 24/7 CRYPTO TRADING BOT")
            logger.info("="*60)
            logger.info(f"User: {self.user_id}")
            logger.info(f"Trading Pair: {self.active_pair} ({self.get_active_symbol()})")
            logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("="*60)
            
            # Step 1: Connect WebSocket
            await self._connect_websocket()
            
            # Step 2: Bootstrap historical data
            await self._bootstrap_data()
            
            # Step 3: Start main trading loop
            await self._main_loop(running_flag)
            
        except Exception as e:
            logger.error(f"❌ Fatal error in bot: {e}", exc_info=True)
            raise
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop bot gracefully"""
        try:
            logger.info("🛑 Stopping crypto bot...")
            
            self.is_running = False
            
            # Close WebSocket
            if self.ws.is_connected:
                await self.ws.disconnect()
            
            # Close any open positions
            await self._close_all_positions()
            
            # Save final state
            self._save_final_state()
            
            logger.info("✅ Crypto bot stopped")
            
        except Exception as e:
            logger.error(f"❌ Error during stop: {e}")
    
    # ========================================
    # BOOTSTRAP & INITIALIZATION
    # ========================================
    
    async def _connect_websocket(self):
        """Connect to WebSocket with retry logic"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"🔌 Connecting WebSocket (attempt {attempt}/{max_retries})...")
                
                await self.ws.connect()
                
                # Subscribe to active pair
                symbol = self.get_active_ws_symbol()
                await self.ws.subscribe_ticker([symbol])
                await self.ws.subscribe_orderbook([symbol], depth=20)
                await self.ws.subscribe_trades([symbol])
                
                # Start heartbeat loop
                asyncio.create_task(self.ws.heartbeat_loop())
                
                logger.info("✅ WebSocket connected and subscribed")
                return
                
            except Exception as e:
                logger.error(f"❌ WebSocket connection failed (attempt {attempt}): {e}")
                
                if attempt < max_retries:
                    wait_time = retry_delay * attempt
                    logger.info(f"⏳ Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    raise Exception("Failed to connect WebSocket after max retries")
    
    async def _bootstrap_data(self):
        """Bootstrap historical data for strategy"""
        try:
            logger.info("📊 Bootstrapping historical data...")
            
            symbol = self.get_active_symbol()
            
            # Get historical candles (need 100+ periods for indicator warm-up)
            candles_5m = self.broker.get_historical_candles(symbol, '5m', limit=500)
            candles_1h = self.broker.get_historical_candles(symbol, '1h', limit=200)
            candles_4h = self.broker.get_historical_candles(symbol, '4h', limit=100)
            
            self.candles[symbol] = {
                '5m': candles_5m,
                '1h': candles_1h,
                '4h': candles_4h
            }
            
            # Convert to DataFrame for indicator calculation
            self.df_5m = pd.DataFrame(candles_5m)
            self.df_1h = pd.DataFrame(candles_1h)
            self.df_4h = pd.DataFrame(candles_4h)
            
            # Get current balance
            btc_balance = self.broker.get_balance_by_currency('BTC')
            eth_balance = self.broker.get_balance_by_currency('ETH')
            usdt_balance = self.broker.get_balance_by_currency('USDT')
            
            usdt_available = float(usdt_balance.get('balance', 0))
            self.daily_starting_capital = usdt_available
            
            logger.info(f"   BTC Balance: {btc_balance.get('balance', 0)}")
            logger.info(f"   ETH Balance: {eth_balance.get('balance', 0)}")
            logger.info(f"   USDT Balance: {usdt_available}")
            logger.info(f"   Daily Starting Capital: ${usdt_available:,.2f}")
            
            # Get ticker
            ticker = self.broker.get_ticker(symbol)
            current_price = float(ticker.get('last_price', 0))
            
            logger.info(f"   Current Price: ${current_price:,.2f}")
            logger.info(f"   5m Candles: {len(candles_5m)}")
            logger.info(f"   1h Candles: {len(candles_1h)}")
            logger.info(f"   4h Candles: {len(candles_4h)}")
            
            # Pre-calculate initial indicators
            logger.info("📊 Pre-calculating indicators (warm-up period)...")
            self._calculate_indicators_day()
            self._calculate_indicators_night()
            
            self.is_bootstrapped = True
            logger.info("✅ Bootstrap complete")
            
        except Exception as e:
            logger.error(f"❌ Bootstrap failed: {e}")
            raise
    
    # ========================================
    # MAIN TRADING LOOP (24/7 - NO MARKET HOURS!)
    # ========================================
    
    async def _main_loop(self, running_flag):
        """
        Main 24/7 trading loop.
        
        Note: Unlike stock bot, this runs continuously with NO market hours check!
        """
        logger.info("🔄 Starting 24/7 trading loop...")
        
        loop_count = 0
        
        while running_flag.is_set() and self.is_running:
            try:
                loop_count += 1
                
                # Get current price from WebSocket
                symbol = self.get_active_ws_symbol()
                current_price = self.ws.prices.get(symbol, 0)
                
                if current_price == 0:
                    await asyncio.sleep(1)
                    continue
                
                # Check daily loss limit
                if self._check_daily_loss_limit():
                    logger.warning("⚠️  Daily loss limit reached - pausing trading for today")
                    await asyncio.sleep(60)  # Check every minute
                    continue
                
                # Log every 60 seconds
                if loop_count % 60 == 0:
                    logger.info(f"💓 Loop {loop_count}: {self.active_pair} = ${current_price:,.2f}")
                
                # ========================================
                # STRATEGY ANALYSIS
                # ========================================
                
                # Determine if it's day or night (IST timezone)
                current_hour_ist = (datetime.utcnow().hour + 5) % 24  # Convert UTC to IST
                
                if 9 <= current_hour_ist < 21:
                    # Day strategy (9 AM - 9 PM IST): Momentum Scalping
                    await self._day_strategy_analysis(current_price)
                else:
                    # Night strategy (9 PM - 9 AM IST): Mean Reversion
                    await self._night_strategy_analysis(current_price)
                
                # Sleep 1 second
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Main loop error: {e}", exc_info=True)
                await asyncio.sleep(5)  # Wait before retrying
        
        logger.info("🛑 Trading loop stopped")
    
    # ========================================
    # TECHNICAL INDICATORS
    # ========================================
    
    def _calculate_ema(self, data: pd.Series, period: int) -> float:
        """Calculate Exponential Moving Average"""
        return data.ewm(span=period, adjust=False).mean().iloc[-1]
    
    def _calculate_rsi(self, data: pd.Series, period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]
    
    def _calculate_bollinger_bands(self, data: pd.Series, period: int = 20, std_dev: float = 2):
        """Calculate Bollinger Bands"""
        sma = data.rolling(window=period).mean()
        std = data.rolling(window=period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        return {
            'upper': upper.iloc[-1],
            'middle': sma.iloc[-1],
            'lower': lower.iloc[-1]
        }
    
    def _calculate_volatility(self, data: pd.Series, period: int = 90) -> float:
        """Calculate annualized volatility (rolling)"""
        returns = data.pct_change()
        volatility = returns.rolling(window=period).std() * np.sqrt(252)  # Annualized
        return volatility.iloc[-1]
    
    def _calculate_donchian_midpoint(self, highs: pd.Series, lows: pd.Series, period: int = 20) -> float:
        """Calculate Donchian Channel midpoint for trailing stop"""
        highest_high = highs.rolling(window=period).max().iloc[-1]
        lowest_low = lows.rolling(window=period).min().iloc[-1]
        return (highest_high + lowest_low) / 2
    
    def _calculate_indicators_day(self):
        """Pre-calculate indicators for day strategy (5m candles)"""
        if self.df_5m is None or len(self.df_5m) < 100:
            return
        
        # Calculate EMAs
        close_prices = self.df_5m['close']
        self.indicators['ema8'] = self._calculate_ema(close_prices, 8)
        self.indicators['ema16'] = self._calculate_ema(close_prices, 16)
        self.indicators['ema32'] = self._calculate_ema(close_prices, 32)
        
        # Calculate RSI
        self.indicators['rsi'] = self._calculate_rsi(close_prices, 14)
    
    def _calculate_indicators_night(self):
        """Pre-calculate indicators for night strategy (1h candles)"""
        if self.df_1h is None or len(self.df_1h) < 100:
            return
        
        # Calculate Bollinger Bands
        close_prices = self.df_1h['close']
        bb = self._calculate_bollinger_bands(close_prices, 20, 2)
        self.indicators['bb_upper'] = bb['upper']
        self.indicators['bb_middle'] = bb['middle']
        self.indicators['bb_lower'] = bb['lower']
        
        # Calculate RSI
        self.indicators['rsi'] = self._calculate_rsi(close_prices, 14)
    
    # ========================================
    # RISK MANAGEMENT
    # ========================================
    
    async def _calculate_position_size(self, current_price: float) -> float:
        """
        Calculate position size based on volatility targeting.
        
        Formula: Weight = Target_Volatility / Current_Volatility
        Constraint: Max 200% exposure (with leverage)
        
        Returns:
            Position size in base currency (BTC or ETH)
        """
        try:
            # Get available capital (USDT)
            usdt_balance = self.broker.get_balance_by_currency('USDT')
            usdt_available = float(usdt_balance.get('balance', 0))
            
            if usdt_available < 10:  # Minimum $10 to trade
                logger.warning(f"⚠️  Insufficient capital: ${usdt_available:.2f}")
                return 0
            
            # Calculate current volatility
            symbol = self.get_active_symbol()
            if len(self.indicator_history.get('volatility', [])) > 0:
                current_volatility = self.indicator_history['volatility'].iloc[-1]
            else:
                current_volatility = 0.30  # Default 30% if not calculated
            
            # Volatility targeting
            target_vol = self.risk_params['target_volatility']
            weight = min(target_vol / current_volatility, self.risk_params['max_position_weight'])
            
            # Calculate position value in USDT
            position_value_usdt = usdt_available * weight
            
            # Convert to base currency (BTC or ETH)
            position_size = position_value_usdt / current_price
            
            # Validate against exchange minimums
            # TODO: Use broker.validate_order_params()
            min_notional = 10  # $10 minimum order value
            if position_value_usdt < min_notional:
                logger.warning(f"⚠️  Position value ${position_value_usdt:.2f} < min ${min_notional}")
                return 0
            
            logger.info(f"📊 Position Sizing:")
            logger.info(f"   Available Capital: ${usdt_available:.2f}")
            logger.info(f"   Current Volatility: {current_volatility*100:.1f}%")
            logger.info(f"   Target Volatility: {target_vol*100:.1f}%")
            logger.info(f"   Weight: {weight*100:.1f}%")
            logger.info(f"   Position Value: ${position_value_usdt:.2f}")
            logger.info(f"   Position Size: {position_size:.6f} {self.active_pair}")
            
            return position_size
            
        except Exception as e:
            logger.error(f"❌ Position sizing error: {e}")
            return 0
    
    async def _check_liquidity(self, symbol: str) -> bool:
        """
        Check if asset meets minimum liquidity requirements.
        
        Rule: Median daily volume must be > $1M
        
        Returns:
            True if sufficient liquidity
        """
        try:
            # Get recent trade history
            trades = self.broker.get_trade_history(symbol, limit=100)
            
            if not trades or len(trades) < 50:
                logger.warning(f"⚠️  Insufficient trade history for liquidity check")
                return False
            
            # Calculate approximate daily volume (rough estimate)
            # In production, use actual 24h volume from ticker
            ticker = self.broker.get_ticker(symbol)
            volume_24h = float(ticker.get('volume', 0))
            
            if volume_24h < self.risk_params['min_daily_volume_usd']:
                logger.warning(f"⚠️  Low liquidity: ${volume_24h:,.0f} < ${self.risk_params['min_daily_volume_usd']:,.0f}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Liquidity check error: {e}")
            return False
    
    def _check_daily_loss_limit(self) -> bool:
        """
        Check if daily loss limit has been reached.
        
        Rule: Max 5% daily loss
        
        Returns:
            True if loss limit triggered (stop trading)
        """
        try:
            if self.daily_loss_limit_triggered:
                return True
            
            # Get current balance
            usdt_balance = self.broker.get_balance_by_currency('USDT')
            usdt_current = float(usdt_balance.get('balance', 0))
            
            # Calculate daily P&L
            daily_pnl_pct = (usdt_current - self.daily_starting_capital) / self.daily_starting_capital
            
            if daily_pnl_pct < -self.risk_params['max_daily_loss_pct']:
                logger.error(f"❌ DAILY LOSS LIMIT TRIGGERED: {daily_pnl_pct*100:.2f}% loss")
                logger.error(f"   Starting Capital: ${self.daily_starting_capital:.2f}")
                logger.error(f"   Current Capital: ${usdt_current:.2f}")
                logger.error(f"   Loss: ${self.daily_starting_capital - usdt_current:.2f}")
                
                self.daily_loss_limit_triggered = True
                
                # Close all positions immediately
                asyncio.create_task(self._close_all_positions())
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Daily loss check error: {e}")
            return False
    
    # ========================================
    #   closes = self.df_5m['close']
        
        # Triple EMA (8, 16, 32)
        self.indicator_history['ema8'] = closes.ewm(span=8, adjust=False).mean()
        self.indicator_history['ema16'] = closes.ewm(span=16, adjust=False).mean()
        self.indicator_history['ema32'] = closes.ewm(span=32, adjust=False).mean()
        
        # RSI (14)
        self.indicator_history['rsi'] = self._calculate_rsi_series(closes, 14)
    
    def _calculate_indicators_night(self):
        """Pre-calculate indicators for night strategy (1h candles)"""
        if self.df_1h is None or len(self.df_1h) < 100:
            return
        
        closes = self.df_1h['close']
        
        # Bollinger Bands (20-period, 2 std dev)
        sma = closes.rolling(window=20).mean()
        std = closes.rolling(window=20).std()
        self.indicator_history['bb_upper'] = sma + (std * 2)
        self.indicator_history['bb_middle'] = sma
        self.indicator_history['bb_lower'] = sma - (std * 2)
        
        # RSI (14)
        self.indicator_history['rsi'] = self._calculate_rsi_series(closes, 14)
        
        # Volatility
        self.indicator_history['volatility'] = closes.pct_change().rolling(window=90).std() * np.sqrt(252)
    
    def _calculate_rsi_series(self, data: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI series for entire dataset"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    # ========================================
    # DAY STRATEGY: MOMENTUM SCALPING
    # ========================================
    
    async def _day_strategy_analysis(self, current_price: float):
        """
        Day Trading Strategy: Momentum Scalping (5m candles)
        
        Indicators:
        - Triple EMA (8, 16, 32 periods)
        - RSI (14 periods)
        
        Entry (Long):
        - EMA8 crosses above EMA16
        - EMA16 > EMA32 (uptrend confirmation)
        - RSI between 50 and 70 (momentum but not overbought)
        
        Exit:
        - EMA8 crosses below EMA16 (momentum loss)
        - OR RSI > 70 (overbought)
        
        Stop Loss:
        - Donchian Channel midpoint (20-period) or 2% hard stop
        """
        try:
            symbol = self.get_active_symbol()
            
            # Check if we have open position
            has_position = symbol in self.positions
            
            # Get latest indicators
            ema8 = self.indicator_history['ema8'].iloc[-1]
            ema16 = self.indicator_history['ema16'].iloc[-1]
            ema32 = self.indicator_history['ema32'].iloc[-1]
            rsi = self.indicator_history['rsi'].iloc[-1]
            
            # Previous values for crossover detection
            ema8_prev = self.indicator_history['ema8'].iloc[-2]
            ema16_prev = self.indicator_history['ema16'].iloc[-2]
            
            # ========================================
            # EXIT LOGIC (check first)
            # ========================================
            if has_position:
                position = self.positions[symbol]
                entry_price = position['entry_price']
                
                # Exit Signal 1: EMA8 crosses below EMA16
                bearish_crossover = ema8 < ema16 and ema8_prev >= ema16_prev
                
                # Exit Signal 2: RSI overbought
                rsi_overbought = rsi > 70
                
                # Stop Loss: 2% or Donchian midpoint
                current_loss_pct = (current_price - entry_price) / entry_price
                stop_loss_triggered = current_loss_pct < -self.risk_params['stop_loss_day_pct']
                
                if bearish_crossover:
                    logger.info(f"🔻 DAY EXIT: EMA8 crossed below EMA16 (momentum loss)")
                    await self._close_position(symbol)
                    return
                
                if rsi_overbought:
                    logger.info(f"🔻 DAY EXIT: RSI overbought ({rsi:.1f} > 70)")
                    await self._close_position(symbol)
                    return
                
                if stop_loss_triggered:
                    logger.warning(f"⛔ DAY STOP LOSS: Loss {current_loss_pct*100:.2f}% triggered")
                    await self._close_position(symbol)
                    return
            
            # ========================================
            # ENTRY LOGIC
            # ========================================
            if not has_position:
                # Entry Signal 1: EMA8 crosses above EMA16
                bullish_crossover = ema8 > ema16 and ema8_prev <= ema16_prev
                
                # Entry Signal 2: EMA16 > EMA32 (uptrend)
                uptrend = ema16 > ema32
                
                # Entry Signal 3: RSI between 50 and 70
                rsi_momentum = 50 <= rsi <= 70
                
                # Check all conditions
                if bullish_crossover and uptrend and rsi_momentum:
                    # Liquidity filter
                    if not await self._check_liquidity(symbol):
                        logger.warning(f"⚠️  DAY ENTRY: Insufficient liquidity - skipping")
                        return
                    
                    # Fee barrier check
                    projected_profit_pct = 0.02  # Target 2% move
                    if projected_profit_pct < self.risk_params['fee_barrier_pct']:
                        logger.warning(f"⚠️  DAY ENTRY: Projected profit below fee barrier - skipping")
                        return
                    
                    # Calculate position size (dynamic based on volatility)
                    position_size = await self._calculate_position_size(current_price)
                    
                    if position_size > 0:
                        logger.info(f"🚀 DAY ENTRY SIGNAL:")
                        logger.info(f"   EMA8: {ema8:.2f} > EMA16: {ema16:.2f} (bullish crossover)")
                        logger.info(f"   EMA16: {ema16:.2f} > EMA32: {ema32:.2f} (uptrend)")
                        logger.info(f"   RSI: {rsi:.1f} (momentum zone)")
                        logger.info(f"   Position Size: {position_size:.6f} {self.active_pair}")
                        
                        await self._open_position('buy', position_size, current_price)
                    else:
                        logger.warning(f"⚠️  DAY ENTRY: Position size too small - skipping")
        
        except Exception as e:
            logger.error(f"❌ Day strategy error: {e}", exc_info=True)
    
    # ========================================
    # NIGHT STRATEGY: MEAN REVERSION
    # ========================================
    
    async def _night_strategy_analysis(self, current_price: float):
        """
        Night Trading Strategy: Mean Reversion (1h candles)
        
        Indicators:
        - Bollinger Bands (20-period SMA, 2 std dev)
        - RSI (14 periods)
        
        Entry (Long):
        - Price touches/crosses below Lower Bollinger Band
        - RSI < 30 (oversold)
        - Wait for candle close, next candle opens higher (confirmation)
        
        Exit:
        - Price touches Upper Bollinger Band AND RSI > 70
        - Target: Middle Band (mean reversion)
        
        Stop Loss:
        - Volatility-based: 50% of daily volatility
        """
        try:
            symbol = self.get_active_symbol()
            
            # Check if we have open position
            has_position = symbol in self.positions
            
            # Get latest indicators
            bb_upper = self.indicator_history['bb_upper'].iloc[-1]
            bb_middle = self.indicator_history['bb_middle'].iloc[-1]
            bb_lower = self.indicator_history['bb_lower'].iloc[-1]
            rsi = self.indicator_history['rsi'].iloc[-1]
            volatility = self.indicator_history['volatility'].iloc[-1] if len(self.indicator_history['volatility']) > 0 else 0.25
            
            # ========================================
            # EXIT LOGIC (check first)
            # ========================================
            if has_position:
                position = self.positions[symbol]
                entry_price = position['entry_price']
                
                # Exit Signal 1: Price at upper band + RSI overbought
                at_upper_band = current_price >= bb_upper
                rsi_overbought = rsi > 70
                
                # Exit Signal 2: Target reached (middle band = mean)
                at_middle_band = abs(current_price - bb_middle) / bb_middle < 0.005  # Within 0.5%
                
                # Stop Loss: Volatility-based (50% of daily volatility)
                current_loss_pct = (current_price - entry_price) / entry_price
                volatility_stop = -self.risk_params['stop_loss_night_multiplier'] * volatility
                stop_loss_triggered = current_loss_pct < volatility_stop
                
                if at_upper_band and rsi_overbought:
                    logger.info(f"🔻 NIGHT EXIT: Upper BB reached + RSI overbought ({rsi:.1f})")
                    await self._close_position(symbol)
                    return
                
                if at_middle_band:
                    logger.info(f"🎯 NIGHT EXIT: Target reached (middle band = mean reversion)")
                    await self._close_position(symbol)
                    return
                
                if stop_loss_triggered:
                    logger.warning(f"⛔ NIGHT STOP LOSS: Loss {current_loss_pct*100:.2f}% > volatility stop {volatility_stop*100:.2f}%")
                    await self._close_position(symbol)
                    return
            
            # ========================================
            # ENTRY LOGIC
            # ========================================
            if not has_position:
                # Entry Signal 1: Price at/below lower Bollinger Band
                at_lower_band = current_price <= bb_lower
                
                # Entry Signal 2: RSI oversold
                rsi_oversold = rsi < 30
                
                # TODO: Add candle confirmation (wait for next candle open higher)
                # For now, using immediate entry
                
                if at_lower_band and rsi_oversold:
                    # Liquidity filter
                    if not await self._check_liquidity(symbol):
                        logger.warning(f"⚠️  NIGHT ENTRY: Insufficient liquidity - skipping")
                        return
                    
                    # Fee barrier check (target: middle band)
                    projected_profit_pct = abs(bb_middle - current_price) / current_price
                    if projected_profit_pct < self.risk_params['fee_barrier_pct']:
                        logger.warning(f"⚠️  NIGHT ENTRY: Projected profit below fee barrier - skipping")
                        return
                    
                    # Calculate position size (dynamic based on volatility)
                    position_size = await self._calculate_position_size(current_price)
                    
                    if position_size > 0:
                        logger.info(f"🌙 NIGHT ENTRY SIGNAL:")
                        logger.info(f"   Price: ${current_price:.2f} <= Lower BB: ${bb_lower:.2f}")
                        logger.info(f"   RSI: {rsi:.1f} < 30 (oversold)")
                        logger.info(f"   Target: ${bb_middle:.2f} (middle band)")
                        logger.info(f"   Position Size: {position_size:.6f} {self.active_pair}")
                        
                        await self._open_position('buy', position_size, current_price)
                    else:
                        logger.warning(f"⚠️  NIGHT ENTRY: Position size too small - skipping")
        
        except Exception as e:
            logger.error(f"❌ Night strategy error: {e}", exc_info=True)
    
    # ========================================
    # POSITION MANAGEMENT
    # ========================================
    
    async def _open_position(self, side: str, quantity: float, price: float):
        """Open a position"""
        try:
            symbol = self.get_active_symbol()
            
            # Place market order
            order = self.broker.place_order(
                symbol=symbol,
                side=side,
                order_type='market_order',
                quantity=quantity
            )
            
            # Store position
            self.positions[symbol] = {
                'side': side,
                'quantity': quantity,
                'entry_price': price,
                'entry_time': time.time(),
                'order_id': order.get('id')
            }
            
            logger.info(f"✅ {side.upper()} position opened: {quantity} {self.active_pair} @ ${price:,.2f}")
            
            # Save to Firestore
            self._save_position_opened(symbol, side, quantity, price)
            
        except Exception as e:
            logger.error(f"❌ Failed to open position: {e}")
    
    async def _close_position(self, symbol: str):
        """Close a position"""
        try:
            if symbol not in self.positions:
                return
            
            position = self.positions[symbol]
            
            # Place opposite order
            opposite_side = 'sell' if position['side'] == 'buy' else 'buy'
            
            order = self.broker.place_order(
                symbol=symbol,
                side=opposite_side,
                order_type='market_order',
                quantity=position['quantity']
            )
            
            logger.info(f"✅ Position closed: {symbol}")
            
            # Calculate P&L
            # TODO: Implement P&L calculation
            
            # Remove position
            del self.positions[symbol]
            
            # Save to Firestore
            self._save_position_closed(symbol)
            
        except Exception as e:
            logger.error(f"❌ Failed to close position: {e}")
    
    async def _close_all_positions(self):
        """Close all open positions"""
        for symbol in list(self.positions.keys()):
            await self._close_position(symbol)
    
    # ========================================
    # HEALTH MONITORING (Self-Healing)
    # ========================================
    
    async def _health_check(self):
        """Monitor bot health (same as stock bot pattern)"""
        current_time = time.time()
        
        if current_time - self.last_health_check < self.health_check_interval:
            return
        
        self.last_health_check = current_time
        
        # Check WebSocket health
        if not self.ws.is_healthy():
            logger.warning("⚠️  WebSocket unhealthy - attempting reconnection...")
            try:
                await self._connect_websocket()
            except Exception as e:
                logger.error(f"❌ WebSocket reconnection failed: {e}")
        
        # Check API connectivity
        try:
            ticker = self.broker.get_ticker(self.get_active_symbol())
            if not ticker:
                logger.warning("⚠️  API connectivity issue detected")
        except Exception as e:
            logger.error(f"❌ API health check failed: {e}")
    
    # ========================================
    # PERSISTENCE (Firestore)
    # ========================================
    
    def _save_pair_switch(self, old_pair: str, new_pair: str):
        """Save pair switch to Firestore"""
        try:
            self.firestore_client.collection('crypto_bot_activity').add({
                'user_id': self.user_id,
                'type': 'pair_switch',
                'old_pair': old_pair,
                'new_pair': new_pair,
                'timestamp': firestore.SERVER_TIMESTAMP
            })
        except Exception as e:
            logger.error(f"❌ Failed to save pair switch: {e}")
    
    def _save_position_opened(self, symbol: str, side: str, quantity: float, price: float):
        """Save position opened to Firestore"""
        try:
            self.firestore_client.collection('crypto_bot_activity').add({
                'user_id': self.user_id,
                'type': 'position_opened',
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': price,
                'timestamp': firestore.SERVER_TIMESTAMP
            })
        except Exception as e:
            logger.error(f"❌ Failed to save position: {e}")
    
    def _save_position_closed(self, symbol: str):
        """Save position closed to Firestore"""
        try:
            self.firestore_client.collection('crypto_bot_activity').add({
                'user_id': self.user_id,
                'type': 'position_closed',
                'symbol': symbol,
                'timestamp': firestore.SERVER_TIMESTAMP
            })
        except Exception as e:
            logger.error(f"❌ Failed to save position close: {e}")
    
    def _save_final_state(self):
        """Save final bot state to Firestore"""
        try:
            runtime = time.time() - self.start_time if self.start_time else 0
            
            self.firestore_client.collection('crypto_bot_sessions').add({
                'user_id': self.user_id,
                'active_pair': self.active_pair,
                'runtime_seconds': runtime,
                'total_trades': self.total_trades,
                'daily_pnl': self.daily_pnl,
                'end_time': firestore.SERVER_TIMESTAMP
            })
        except Exception as e:
            logger.error(f"❌ Failed to save final state: {e}")
    
    # ========================================
    # STATUS & REPORTING
    # ========================================
    
    def get_status(self) -> Dict:
        """Get bot status"""
        return {
            'is_running': self.is_running,
            'is_bootstrapped': self.is_bootstrapped,
            'active_pair': self.active_pair,
            'symbol': self.get_active_symbol(),
            'open_positions': len(self.positions),
            'total_trades': self.total_trades,
            'daily_pnl': self.daily_pnl,
            'websocket_connected': self.ws.is_connected,
            'websocket_authenticated': self.ws.is_authenticated,
            'uptime_seconds': time.time() - self.start_time if self.start_time else 0
        }
    
    def __repr__(self):
        status = "running" if self.is_running else "stopped"
        return f"CryptoBotEngine(user={self.user_id}, pair={self.active_pair}, status={status})"
