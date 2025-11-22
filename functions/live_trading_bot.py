# ==============================================================================
# Live Trading Bot Cloud Function
# Orchestrates real-time trading with WebSocket data and Angel One execution
# ==============================================================================

import functions_framework
from flask import jsonify
import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Dict, Optional, List
from firebase_admin import firestore, initialize_app
import firebase_admin

# Initialize Firebase Admin
if not firebase_admin._apps:
    initialize_app()

# Import core components
from src.config import ANGEL_ONE_API
from src.websocket.websocket_manager import AngelWebSocketManager
from src.trading.order_manager import OrderManager, OrderType, TransactionType, ProductType, OrderDuration
from src.trading.risk_manager import RiskManager, RiskLimits
from src.trading.execution_manager import ExecutionManager
from src.trading.position_manager import PositionManager
from src.trading.patterns import PatternDetector
from src.trading.price_action_engine import PriceActionEngine
from src.trading.wave_analyzer import WaveAnalyzer
from src.data.historical_data_manager import HistoricalDataManager

logging.basicConfig(level=logging.INFO)

# Global bot instances per user
active_bots: Dict[str, 'LiveTradingBot'] = {}


class LiveTradingBot:
    """
    Real-time trading bot that:
    1. Receives live WebSocket tick data
    2. Builds OHLC candles from ticks
    3. Runs pattern detection and 30-point validation
    4. Places orders via Angel One API
    5. Manages positions with risk controls
    """
    
    def __init__(self, user_id: str, symbols: List[str], interval: str = '5minute'):
        self.user_id = user_id
        self.symbols = symbols
        self.interval = interval
        self.db = firestore.client()
        
        # Initialize components
        self.ws_manager = AngelWebSocketManager(user_id)
        self.order_manager = OrderManager(user_id)
        self.risk_manager = RiskManager(
            max_portfolio_heat=0.06,  # 6% max portfolio risk
            max_position_size=0.02,   # 2% max per trade
            max_daily_loss=0.03,      # 3% max daily loss
            max_drawdown=0.10,        # 10% max drawdown
            max_correlation=0.7,      # Max 0.7 correlation
            max_open_positions=5,     # Max 5 concurrent positions
            min_risk_reward=2.0,      # Min 2:1 R:R
            max_sector_exposure=0.30  # Max 30% per sector
        )
        self.execution_manager = ExecutionManager()
        self.position_manager = PositionManager()
        self.pattern_detector = PatternDetector()
        self.price_action_engine = PriceActionEngine()
        self.wave_analyzer = WaveAnalyzer()
        self.historical_manager = HistoricalDataManager(user_id)
        
        # Candle building
        self.candle_data: Dict[str, pd.DataFrame] = {}  # symbol -> OHLCV DataFrame
        self.current_candles: Dict[str, Dict] = {}  # symbol -> current candle being built
        self.interval_seconds = self._get_interval_seconds(interval)
        
        # Position tracking
        self.open_positions: Dict[str, Dict] = {}  # symbol -> position details
        
        logging.info(f"[LiveTradingBot] Initialized for user {user_id}, symbols: {symbols}, interval: {interval}")
    
    def _get_interval_seconds(self, interval: str) -> int:
        """Convert interval string to seconds"""
        mapping = {
            '1minute': 60,
            '5minute': 300,
            '15minute': 900,
            '30minute': 1800,
            '1hour': 3600,
            '1day': 86400
        }
        return mapping.get(interval, 300)
    
    async def start(self):
        """Start the trading bot"""
        try:
            # Initialize historical data for each symbol
            for symbol in self.symbols:
                historical_data = await self.historical_manager.get_or_fetch_data(
                    symbol=symbol,
                    interval=self.interval,
                    from_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d %H:%M'),
                    to_date=datetime.now().strftime('%Y-%m-%d %H:%M')
                )
                
                if historical_data is not None and not historical_data.empty:
                    self.candle_data[symbol] = historical_data
                    logging.info(f"[LiveTradingBot] Loaded {len(historical_data)} historical candles for {symbol}")
                else:
                    # Initialize with empty DataFrame
                    self.candle_data[symbol] = pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume'])
                    logging.warning(f"[LiveTradingBot] No historical data for {symbol}, starting fresh")
            
            # Connect WebSocket and subscribe to symbols
            await self.ws_manager.connect()
            
            # Get token list for symbols
            token_list = []
            for symbol in self.symbols:
                # Fetch token from Firestore or API (simplified here)
                # In production, you'd have a symbol-to-token mapping
                token_list.append(symbol)  # Placeholder
            
            # Subscribe with tick callback
            await self.ws_manager.subscribe(
                mode=3,  # Snap Quote mode for full OHLC
                token_list=token_list
            )
            
            # Set up tick data callback
            self.ws_manager.add_tick_callback(self._on_tick_data)
            
            logging.info(f"[LiveTradingBot] Started successfully for {self.user_id}")
            
        except Exception as e:
            logging.error(f"[LiveTradingBot] Error starting bot: {e}", exc_info=True)
            raise
    
    async def _on_tick_data(self, tick_data: Dict):
        """
        Process incoming tick data and build candles
        WebSocket tick format: {token: {ltp, volume, open, high, low, close, timestamp}}
        """
        try:
            for token, data in tick_data.items():
                symbol = self._token_to_symbol(token)  # Convert token back to symbol
                if symbol not in self.symbols:
                    continue
                
                timestamp = datetime.fromtimestamp(data.get('timestamp', datetime.now().timestamp()))
                ltp = data.get('ltp', data.get('close'))
                volume = data.get('volume', 0)
                
                # Build candle from ticks
                self._build_candle(symbol, timestamp, ltp, volume)
                
                # Check if candle is complete
                if self._is_candle_complete(symbol, timestamp):
                    await self._on_candle_complete(symbol)
                    
        except Exception as e:
            logging.error(f"[LiveTradingBot] Error processing tick data: {e}", exc_info=True)
    
    def _token_to_symbol(self, token: str) -> str:
        """Convert token to symbol (simplified mapping)"""
        # In production, maintain a token->symbol mapping
        # For now, assume direct mapping
        return token
    
    def _build_candle(self, symbol: str, timestamp: datetime, price: float, volume: int):
        """Build OHLC candle from tick data"""
        candle_start = self._get_candle_start_time(timestamp)
        
        if symbol not in self.current_candles or self.current_candles[symbol]['timestamp'] != candle_start:
            # Start new candle
            self.current_candles[symbol] = {
                'timestamp': candle_start,
                'Open': price,
                'High': price,
                'Low': price,
                'Close': price,
                'Volume': volume
            }
        else:
            # Update existing candle
            candle = self.current_candles[symbol]
            candle['High'] = max(candle['High'], price)
            candle['Low'] = min(candle['Low'], price)
            candle['Close'] = price
            candle['Volume'] += volume
    
    def _get_candle_start_time(self, timestamp: datetime) -> datetime:
        """Get the start time of the candle for the given timestamp"""
        seconds_since_midnight = (timestamp - timestamp.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
        candle_number = int(seconds_since_midnight // self.interval_seconds)
        candle_start_seconds = candle_number * self.interval_seconds
        return timestamp.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(seconds=candle_start_seconds)
    
    def _is_candle_complete(self, symbol: str, current_timestamp: datetime) -> bool:
        """Check if the current candle is complete"""
        if symbol not in self.current_candles:
            return False
        
        candle_start = self.current_candles[symbol]['timestamp']
        candle_end = candle_start + timedelta(seconds=self.interval_seconds)
        return current_timestamp >= candle_end
    
    async def _on_candle_complete(self, symbol: str):
        """
        Called when a candle is complete
        1. Add candle to historical data
        2. Run pattern detection
        3. Run 30-point validation if pattern found
        4. Execute trade if all checks pass
        5. Manage open positions
        """
        try:
            if symbol not in self.current_candles:
                return
            
            candle = self.current_candles[symbol]
            
            # Add to historical data
            new_candle_df = pd.DataFrame([candle]).set_index('timestamp')
            if symbol in self.candle_data:
                self.candle_data[symbol] = pd.concat([self.candle_data[symbol], new_candle_df])
                # Keep last 200 candles in memory
                self.candle_data[symbol] = self.candle_data[symbol].tail(200)
            else:
                self.candle_data[symbol] = new_candle_df
            
            logging.info(f"[LiveTradingBot] Candle complete for {symbol}: O={candle['Open']:.2f}, H={candle['High']:.2f}, L={candle['Low']:.2f}, C={candle['Close']:.2f}, V={candle['Volume']}")
            
            # Get market data
            market_data = self.candle_data[symbol]
            if len(market_data) < 50:  # Need minimum data for analysis
                logging.info(f"[LiveTradingBot] Insufficient data for {symbol} ({len(market_data)} candles), waiting for more")
                return
            
            # Check if position already open
            if symbol in self.open_positions:
                # Manage existing position
                await self._manage_position(symbol, market_data)
            else:
                # Look for new entry
                await self._check_entry_signal(symbol, market_data)
                
        except Exception as e:
            logging.error(f"[LiveTradingBot] Error processing completed candle for {symbol}: {e}", exc_info=True)
    
    async def _check_entry_signal(self, symbol: str, market_data: pd.DataFrame):
        """
        Check for entry signal:
        1. Pattern detection
        2. 30-point validation
        3. Risk management
        4. Order placement
        """
        try:
            # Pattern detection
            detected_pattern = self.pattern_detector.scan(market_data, symbol)
            
            if not detected_pattern:
                return  # No pattern detected
            
            logging.info(f"[LiveTradingBot] Pattern detected for {symbol}: {detected_pattern.get('pattern_name')}")
            
            # Run 30-point Grandmaster Checklist
            is_valid = self.execution_manager.validate_trade_entry(market_data, detected_pattern)
            
            if not is_valid:
                logging.info(f"[LiveTradingBot] 30-point validation FAILED for {symbol}")
                return
            
            logging.info(f"[LiveTradingBot] 30-point validation PASSED for {symbol}")
            
            # Get entry parameters
            entry_price = market_data['Close'].iloc[-1]
            stop_loss = detected_pattern.get('initial_stop_loss')
            targets = detected_pattern.get('fibonacci_targets', [])
            
            if stop_loss is None:
                logging.warning(f"[LiveTradingBot] No stop loss defined for {symbol}, skipping trade")
                return
            
            # Calculate position size with risk management
            risk_per_share = abs(entry_price - stop_loss)
            
            # Get current positions for portfolio context
            current_positions = await self.order_manager.get_positions()
            
            # Validate with risk manager
            trade_params = {
                'symbol': symbol,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'target': targets[0] if targets else entry_price * 1.02,  # Default 2% target
                'quantity': 1  # Will be calculated by risk manager
            }
            
            position_size = self.risk_manager.calculate_position_size(
                entry_price=entry_price,
                stop_loss=stop_loss,
                account_size=100000,  # TODO: Get from user settings
                risk_per_trade=0.02
            )
            
            is_valid_risk, violations = self.risk_manager.validate_trade(
                symbol=symbol,
                position_size=position_size,
                entry_price=entry_price,
                stop_loss=stop_loss,
                current_positions=current_positions,
                account_equity=100000  # TODO: Get from broker
            )
            
            if not is_valid_risk:
                logging.warning(f"[LiveTradingBot] Risk validation FAILED for {symbol}: {violations}")
                return
            
            logging.info(f"[LiveTradingBot] Risk validation PASSED for {symbol}, position size: {position_size}")
            
            # Place order
            transaction_type = TransactionType.BUY if detected_pattern.get('direction') == 'bullish' else TransactionType.SELL
            
            order_result = await self.order_manager.place_order(
                symbol=symbol,
                quantity=position_size,
                transaction_type=transaction_type,
                order_type=OrderType.LIMIT,
                product_type=ProductType.INTRADAY,
                price=entry_price,
                duration=OrderDuration.DAY
            )
            
            if order_result.get('status') == 'success':
                order_id = order_result.get('data', {}).get('orderid')
                
                # Track position
                self.open_positions[symbol] = {
                    'order_id': order_id,
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'targets': targets,
                    'quantity': position_size,
                    'pattern': detected_pattern,
                    'entry_time': datetime.now(),
                    'transaction_type': transaction_type.value
                }
                
                # Store in Firestore
                await self._store_position(symbol, self.open_positions[symbol])
                
                logging.info(f"[LiveTradingBot] Order placed for {symbol}: {order_id}")
                
            else:
                logging.error(f"[LiveTradingBot] Order failed for {symbol}: {order_result.get('message')}")
                
        except Exception as e:
            logging.error(f"[LiveTradingBot] Error checking entry signal for {symbol}: {e}", exc_info=True)
    
    async def _manage_position(self, symbol: str, market_data: pd.DataFrame):
        """
        Manage open position:
        1. Check stop loss
        2. Check profit targets
        3. Trail stop loss
        4. Exit if needed
        """
        try:
            position = self.open_positions[symbol]
            current_price = market_data['Close'].iloc[-1]
            
            # Use position manager for exit logic
            closed_pnl = self.position_manager.manage_open_positions(market_data)
            
            if closed_pnl is not None:
                # Position was closed by position manager logic
                await self._close_position(symbol, current_price, "Position Manager Exit")
                logging.info(f"[LiveTradingBot] Position closed by manager for {symbol}, P&L: {closed_pnl*100:.2f}%")
                return
            
            # Manual exit checks
            stop_loss = position['stop_loss']
            targets = position['targets']
            transaction_type = position['transaction_type']
            
            # Check stop loss
            if transaction_type == TransactionType.BUY.value:
                if current_price <= stop_loss:
                    await self._close_position(symbol, current_price, "Stop Loss Hit")
                    return
            else:  # SELL
                if current_price >= stop_loss:
                    await self._close_position(symbol, current_price, "Stop Loss Hit")
                    return
            
            # Check profit targets
            if targets:
                for target in targets:
                    if transaction_type == TransactionType.BUY.value:
                        if current_price >= target:
                            await self._close_position(symbol, current_price, f"Target Hit: {target:.2f}")
                            return
                    else:  # SELL
                        if current_price <= target:
                            await self._close_position(symbol, current_price, f"Target Hit: {target:.2f}")
                            return
                            
        except Exception as e:
            logging.error(f"[LiveTradingBot] Error managing position for {symbol}: {e}", exc_info=True)
    
    async def _close_position(self, symbol: str, exit_price: float, reason: str):
        """Close position and place exit order"""
        try:
            position = self.open_positions[symbol]
            quantity = position['quantity']
            
            # Determine exit transaction type (opposite of entry)
            exit_transaction = TransactionType.SELL if position['transaction_type'] == TransactionType.BUY.value else TransactionType.BUY
            
            # Place exit order
            exit_result = await self.order_manager.place_order(
                symbol=symbol,
                quantity=quantity,
                transaction_type=exit_transaction,
                order_type=OrderType.MARKET,
                product_type=ProductType.INTRADAY
            )
            
            if exit_result.get('status') == 'success':
                # Calculate P&L
                entry_price = position['entry_price']
                if position['transaction_type'] == TransactionType.BUY.value:
                    pnl = (exit_price - entry_price) / entry_price
                else:
                    pnl = (entry_price - exit_price) / entry_price
                
                # Store trade history
                trade_record = {
                    'symbol': symbol,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'quantity': quantity,
                    'pnl_percent': pnl * 100,
                    'entry_time': position['entry_time'],
                    'exit_time': datetime.now(),
                    'exit_reason': reason,
                    'pattern': position['pattern']
                }
                
                await self._store_trade_history(trade_record)
                
                # Remove from open positions
                del self.open_positions[symbol]
                
                logging.info(f"[LiveTradingBot] Position closed for {symbol}: {reason}, P&L: {pnl*100:.2f}%")
            else:
                logging.error(f"[LiveTradingBot] Failed to close position for {symbol}: {exit_result.get('message')}")
                
        except Exception as e:
            logging.error(f"[LiveTradingBot] Error closing position for {symbol}: {e}", exc_info=True)
    
    async def _store_position(self, symbol: str, position: Dict):
        """Store position in Firestore"""
        try:
            self.db.collection('trading_positions').document(self.user_id).collection('open').document(symbol).set({
                **position,
                'entry_time': position['entry_time'].isoformat()
            })
        except Exception as e:
            logging.error(f"[LiveTradingBot] Error storing position: {e}")
    
    async def _store_trade_history(self, trade: Dict):
        """Store completed trade in Firestore"""
        try:
            self.db.collection('trading_positions').document(self.user_id).collection('history').add({
                **trade,
                'entry_time': trade['entry_time'].isoformat(),
                'exit_time': trade['exit_time'].isoformat()
            })
        except Exception as e:
            logging.error(f"[LiveTradingBot] Error storing trade history: {e}")
    
    async def stop(self):
        """Stop the trading bot"""
        try:
            await self.ws_manager.disconnect()
            logging.info(f"[LiveTradingBot] Stopped for user {self.user_id}")
        except Exception as e:
            logging.error(f"[LiveTradingBot] Error stopping bot: {e}", exc_info=True)


@functions_framework.http
def startLiveTradingBot(request):
    """
    Cloud Function to start the live trading bot
    Body: {symbols: string[], interval: string}
    """
    try:
        # Get user ID from auth token
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Unauthorized'}), 401
        
        # TODO: Verify Firebase token and get user_id
        user_id = "PiRehqxZQleR8QCZG0QczmQTY402"  # Placeholder
        
        data = request.get_json()
        symbols = data.get('symbols', ['RELIANCE', 'HDFCBANK', 'INFY'])
        interval = data.get('interval', '5minute')
        
        # Check if bot already running
        if user_id in active_bots:
            return jsonify({'error': 'Trading bot already running'}), 400
        
        # Create and start bot
        bot = LiveTradingBot(user_id, symbols, interval)
        import asyncio
        asyncio.run(bot.start())
        
        active_bots[user_id] = bot
        
        return jsonify({
            'status': 'success',
            'message': f'Live trading bot started for {len(symbols)} symbols',
            'symbols': symbols,
            'interval': interval
        }), 200
        
    except Exception as e:
        logging.error(f"Error starting live trading bot: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@functions_framework.http
def stopLiveTradingBot(request):
    """Cloud Function to stop the live trading bot"""
    try:
        # Get user ID from auth token
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Unauthorized'}), 401
        
        user_id = "PiRehqxZQleR8QCZG0QczmQTY402"  # Placeholder
        
        if user_id not in active_bots:
            return jsonify({'error': 'No active trading bot found'}), 404
        
        # Stop bot
        bot = active_bots[user_id]
        import asyncio
        asyncio.run(bot.stop())
        
        del active_bots[user_id]
        
        return jsonify({
            'status': 'success',
            'message': 'Live trading bot stopped'
        }), 200
        
    except Exception as e:
        logging.error(f"Error stopping live trading bot: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
