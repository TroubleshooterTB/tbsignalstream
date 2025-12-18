"""
LIVE TRADING BOT - v3.2 Strategy
Based on successful backtest: 53.49% WR, 24.10% returns
Deploy on: December 15, 2025

CRITICAL: This uses the EXACT same logic as run_backtest_defining_order.py v3.2
"""

import pandas as pd
import numpy as np
from datetime import datetime, time, timedelta
from typing import Dict, List, Tuple, Optional
import logging
import requests
import ta
import time as time_module
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'live_trading_{datetime.now().strftime("%Y%m%d")}.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import the exact strategy class from backtest
sys.path.append('.')
from run_backtest_defining_order import DefiningOrderStrategy
from SmartApi import SmartConnect
import pyotp
import firebase_admin
from firebase_admin import firestore

class LiveTradingBot:
    """
    Live trading bot using v3.2 validated strategy
    Connected to Firestore for dashboard integration
    """
    
    def __init__(self, api_key: str, client_code: str, password: str, totp_code: str, 
                 initial_capital: float = 100000, paper_trade: bool = True, user_id: str = "local_bot_user"):
        """
        Initialize live trading bot
        
        Args:
            api_key: Angel One API key
            client_code: Angel One client code
            password: Trading password
            totp_code: 6-digit TOTP code from authenticator app
            initial_capital: Starting capital
            paper_trade: If True, simulate trades without real execution
            user_id: User ID for Firestore tracking
        """
        # Initialize Firestore
        if not firebase_admin._apps:
            firebase_admin.initialize_app()
        self.db = firestore.client()
        self.user_id = user_id
        
        # Authenticate with Angel One first
        logger.info("Authenticating with Angel One...")
        try:
            smart_api = SmartConnect(api_key=api_key)
            
            # Login with the 6-digit TOTP code directly
            session_data = smart_api.generateSession(client_code, password, totp_code)
            jwt_token = session_data['data']['jwtToken']
            logger.info("Authentication successful!")
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise
        
        # Initialize strategy with authenticated token
        self.strategy = DefiningOrderStrategy(api_key, jwt_token)
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.paper_trade = paper_trade
        self.open_positions = {}
        self.trade_log = []
        self.bot_start_time = datetime.now()
        
        # Write initial bot status to Firestore
        self._update_bot_status("running")
        
        logger.info("="*80)
        logger.info("🚀 LIVE TRADING BOT v3.2 INITIALIZED")
        logger.info("="*80)
        logger.info(f"Mode: {'PAPER TRADING' if paper_trade else '⚠️ LIVE TRADING'}")
        logger.info(f"Initial Capital: ₹{initial_capital:,.2f}")
        logger.info(f"Strategy: The Defining Order - Ironclad v3.2")
        logger.info(f"Dashboard: Connected to Firestore")
        logger.info("="*80)
    
    def _update_bot_status(self, status: str):
        """Update bot status in Firestore for dashboard"""
        try:
            self.db.collection('bot_status').document(self.user_id).set({
                'status': status,
                'strategy': 'alpha-ensemble',
                'mode': 'paper' if self.paper_trade else 'live',
                'capital': self.current_capital,
                'open_positions': len(self.open_positions),
                'total_trades': len(self.trade_log),
                'last_update': firestore.SERVER_TIMESTAMP,
                'started_at': self.bot_start_time
            }, merge=True)
        except Exception as e:
            logger.error(f"Failed to update bot status: {e}")
    
    def _log_activity(self, action: str, details: dict):
        """Log bot activity to Firestore for activity feed"""
        try:
            self.db.collection('bot_activity').add({
                'user_id': self.user_id,
                'action': action,
                'details': details,
                'timestamp': firestore.SERVER_TIMESTAMP
            })
        except Exception as e:
            logger.error(f"Failed to log activity: {e}")
    
    def _save_signal(self, signal_info: dict):
        """Save trade signal to Firestore"""
        try:
            self.db.collection('signals').add({
                'user_id': self.user_id,
                'symbol': signal_info['symbol'],
                'direction': signal_info['direction'],
                'entry_price': signal_info['entry'],
                'stop_loss': signal_info['sl'],
                'take_profit': signal_info['tp'],
                'strategy': 'alpha-ensemble',
                'timestamp': firestore.SERVER_TIMESTAMP,
                'status': 'executed'
            })
        except Exception as e:
            logger.error(f"Failed to save signal: {e}")
    
    def _save_trade(self, trade: dict):
        """Save completed trade to Firestore"""
        try:
            self.db.collection('trades').add({
                'user_id': self.user_id,
                'symbol': trade['symbol'],
                'direction': trade['direction'],
                'entry_price': trade['entry'],
                'exit_price': trade['exit'],
                'quantity': trade['quantity'],
                'pnl': trade['pnl'],
                'exit_reason': trade['reason'],
                'entry_time': trade['entry_time'],
                'exit_time': trade['exit_time'],
                'strategy': 'alpha-ensemble',
                'mode': 'paper' if self.paper_trade else 'live'
            })
        except Exception as e:
            logger.error(f"Failed to save trade: {e}")
        
    def get_live_data(self, symbol: str, token: str) -> Optional[pd.DataFrame]:
        """
        Fetch latest hourly candle data for analysis
        """
        try:
            # Get today's date
            today = datetime.now()
            start_date = today.strftime("%Y-%m-%d")
            
            # Fetch last 60 days for SMA calculation
            sma_start = (today - timedelta(days=60)).strftime("%Y-%m-%d")
            
            # Get hourly data
            candle_data = self.strategy.fetch_historical_data(
                symbol, token, "ONE_HOUR",
                sma_start + " 09:15", start_date + " 15:30"
            )
            
            if candle_data is None or len(candle_data) == 0:
                return None
                
            # Calculate indicators
            candle_data = self.strategy.calculate_vwap(candle_data)
            candle_data = self.strategy.calculate_indicators(candle_data)
            
            return candle_data
            
        except Exception as e:
            logger.error(f"❌ Error fetching live data for {symbol}: {e}")
            return None
    
    def check_for_signals(self, symbols: List[Dict]) -> List[Dict]:
        """
        Check all symbols for trading signals
        Returns list of signal dictionaries
        """
        signals = []
        current_time = datetime.now().time()
        
        # Skip if market not open
        if current_time < time(9, 15) or current_time > time(15, 30):
            return signals
        
        for symbol_info in symbols:
            symbol = symbol_info['symbol']
            token = symbol_info['token']
            
            try:
                # Get live data
                data = self.get_live_data(symbol, token)
                if data is None or len(data) == 0:
                    continue
                
                # Get latest candle
                latest = data.iloc[-1]
                current_hour = latest['Datetime'].hour
                
                # Check for signal using exact backtest logic
                signal = self.strategy.check_breakout_signal(
                    latest, data, symbol, current_hour
                )
                
                if signal:
                    signals.append({
                        'symbol': symbol,
                        'token': token,
                        'signal': signal,
                        'data': latest
                    })
                    logger.info(f"🎯 SIGNAL: {symbol} {signal['direction']} at ₹{signal['entry']:.2f}")
                    
            except Exception as e:
                logger.error(f"❌ Error checking {symbol}: {e}")
                continue
        
        return signals
    
    def execute_trade(self, signal_info: Dict) -> bool:
        """
        Execute trade based on signal
        """
        signal = signal_info['signal']
        symbol = signal_info['symbol']
        
        if self.paper_trade:
            # Paper trade - just log
            logger.info(f"📝 PAPER TRADE: {symbol} {signal['direction']} at ₹{signal['entry']:.2f}")
            logger.info(f"   SL: ₹{signal['sl']:.2f}, TP: ₹{signal['tp']:.2f}, Qty: {signal['quantity']}")
            
            # Track position
            self.open_positions[symbol] = {
                'entry': signal['entry'],
                'sl': signal['sl'],
                'tp': signal['tp'],
                'quantity': signal['quantity'],
                'direction': signal['direction'],
                'entry_time': datetime.now()
            }
            
            # Save to Firestore
            self._save_signal(signal_info)
            self._log_activity('signal_generated', {
                'symbol': symbol,
                'direction': signal['direction'],
                'entry': signal['entry']
            })
            self._update_bot_status("running")
            
            return True
            
        else:
            # LIVE TRADE - execute via Angel One API
            logger.warning("⚠️ LIVE TRADING NOT IMPLEMENTED YET - USE PAPER MODE")
            return False
    
    def monitor_positions(self, symbols: List[Dict]):
        """
        Monitor open positions for SL/TP hits
        """
        if not self.open_positions:
            return
        
        for symbol, position in list(self.open_positions.items()):
            try:
                # Get current price
                token = next(s['token'] for s in symbols if s['symbol'] == symbol)
                data = self.get_live_data(symbol, token)
                if data is None:
                    continue
                
                current_price = data.iloc[-1]['close']
                
                # Check SL/TP
                if position['direction'] == 'LONG':
                    if current_price <= position['sl']:
                        self.close_position(symbol, current_price, 'SL')
                    elif current_price >= position['tp']:
                        self.close_position(symbol, current_price, 'TP')
                else:  # SHORT
                    if current_price >= position['sl']:
                        self.close_position(symbol, current_price, 'SL')
                    elif current_price <= position['tp']:
                        self.close_position(symbol, current_price, 'TP')
                        
            except Exception as e:
                logger.error(f"❌ Error monitoring {symbol}: {e}")
    
    def close_position(self, symbol: str, exit_price: float, reason: str):
        """
        Close position and calculate P&L
        """
        position = self.open_positions.pop(symbol)
        
        # Calculate P&L
        if position['direction'] == 'LONG':
            pnl = (exit_price - position['entry']) * position['quantity']
        else:  # SHORT
            pnl = (position['entry'] - exit_price) * position['quantity']
        
        self.current_capital += pnl
        
        # Log trade
        trade = {
            'symbol': symbol,
            'direction': position['direction'],
            'entry': position['entry'],
            'exit': exit_price,
            'quantity': position['quantity'],
            'pnl': pnl,
            'reason': reason,
            'entry_time': position['entry_time'],
            'exit_time': datetime.now()
        }
        self.trade_log.append(trade)
        
        # Save to Firestore
        self._save_trade(trade)
        self._log_activity('trade_closed', {
            'symbol': symbol,
            'pnl': pnl,
            'reason': reason
        })
        self._update_bot_status("running")
        
        # Display result
        emoji = '✅' if pnl > 0 else '❌'
        logger.info(f"{emoji} {reason} Hit: {symbol} {position['direction']} at ₹{exit_price:.2f}, P&L: ₹{pnl:,.2f}")
        logger.info(f"   Current Capital: ₹{self.current_capital:,.2f} ({(self.current_capital/self.initial_capital - 1)*100:.2f}%)")
    
    def run(self, symbols: List[Dict], check_interval: int = 60):
        """
        Main trading loop
        
        Args:
            symbols: List of symbols to trade
            check_interval: How often to check for signals (seconds)
        """
        logger.info("\n" + "="*80)
        logger.info("🤖 BOT STARTED - Monitoring markets...")
        logger.info("="*80)
        logger.info(f"Symbols: {len(symbols)}")
        logger.info(f"Check Interval: {check_interval}s")
        logger.info(f"Mode: {'PAPER TRADING' if self.paper_trade else 'LIVE TRADING'}")
        logger.info("="*80 + "\n")
        
        # Log bot start
        self._log_activity('bot_started', {
            'mode': 'paper' if self.paper_trade else 'live',
            'strategy': 'alpha-ensemble',
            'symbols_count': len(symbols)
        })
        
        try:
            while True:
                current_time = datetime.now()
                
                # Only trade during market hours
                if time(9, 15) <= current_time.time() <= time(15, 30):
                    
                    # Check for new signals
                    signals = self.check_for_signals(symbols)
                    
                    # Execute signals
                    for signal_info in signals:
                        if len(self.open_positions) < 5:  # Max 5 concurrent positions
                            self.execute_trade(signal_info)
                    
                    # Monitor existing positions
                    self.monitor_positions(symbols)
                    
                    # Update bot status periodically
                    self._update_bot_status("running")
                    
                    # Status update
                    logger.info(f"⏰ {current_time.strftime('%H:%M:%S')} | "
                              f"Positions: {len(self.open_positions)} | "
                              f"Capital: ₹{self.current_capital:,.2f} | "
                              f"Trades: {len(self.trade_log)}")
                
                else:
                    logger.info(f"🌙 Market closed - waiting... ({current_time.strftime('%H:%M:%S')})")
                    self._update_bot_status("idle")
                
                # Wait before next check
                time_module.sleep(check_interval)
                
        except KeyboardInterrupt:
            logger.info("\n⚠️ Bot stopped by user")
            self.shutdown()
    
    def shutdown(self):
        """
        Graceful shutdown - close positions and save results
        """
        logger.info("\n" + "="*80)
        logger.info("🛑 SHUTTING DOWN BOT")
        logger.info("="*80)
        
        try:
            # Update Firestore
            self._update_bot_status("stopped")
            self._log_activity('bot_stopped', {
                'total_trades': len(self.trade_log),
                'final_capital': self.current_capital,
                'pnl': self.current_capital - self.initial_capital
            })
            logger.info("Dashboard updated - bot stopped")
        except Exception as e:
            logger.error(f"Failed to update dashboard: {e}")
        
        # Close all open positions
        if self.open_positions:
            logger.warning(f"⚠️ {len(self.open_positions)} positions still open - closing...")
            for symbol in list(self.open_positions.keys()):
                logger.info(f"Closing {symbol}...")
                # In paper mode, close at last known price
                # In live mode, would place market order
        
        # Save trade log
        if self.trade_log:
            df = pd.DataFrame(self.trade_log)
            filename = f"live_trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(filename, index=False)
            logger.info(f"✅ Trade log saved to {filename}")
            
            # Display summary
            wins = len([t for t in self.trade_log if t['pnl'] > 0])
            losses = len([t for t in self.trade_log if t['pnl'] <= 0])
            total_pnl = sum(t['pnl'] for t in self.trade_log)
            
            logger.info("\n" + "="*80)
            logger.info("📊 SESSION SUMMARY")
            logger.info("="*80)
            logger.info(f"Total Trades: {len(self.trade_log)}")
            logger.info(f"Wins: {wins}")
            logger.info(f"Losses: {losses}")
            logger.info(f"Win Rate: {wins/len(self.trade_log)*100:.2f}%")
            logger.info(f"Total P&L: ₹{total_pnl:,.2f}")
            logger.info(f"Final Capital: ₹{self.current_capital:,.2f}")
            logger.info(f"Return: {(self.current_capital/self.initial_capital - 1)*100:.2f}%")
            logger.info("="*80)


if __name__ == "__main__":
    # Get credentials
    print("\n" + "="*80)
    print("🚀 LIVE TRADING BOT v3.2 - The Defining Order")
    print("="*80)
    print("\nPlease enter your Angel One credentials:")
    print()
    
    api_key = input("API Key: ")
    client_code = input("Client Code: ")
    password = input("Trading Password: ")
    totp = input("TOTP (6-digit code from authenticator): ")
    
    # Ask for trading mode
    print("\n" + "="*80)
    mode = input("Trading Mode (1=PAPER, 2=LIVE): ")
    paper_trade = (mode != '2')
    
    if not paper_trade:
        confirm = input("⚠️ LIVE TRADING - Are you sure? (type 'YES' to confirm): ")
        if confirm != 'YES':
            print("Switching to PAPER mode for safety")
            paper_trade = True
    
    # Initialize bot
    bot = LiveTradingBot(
        api_key=api_key,
        client_code=client_code,
        password=password,
        totp=totp,
        initial_capital=100000,
        paper_trade=paper_trade
    )
    
    # NIFTY 50 symbols (same as backtest)
    symbols = [
        {'symbol': 'RELIANCE-EQ', 'token': '2885'},
        {'symbol': 'TCS-EQ', 'token': '11536'},
        {'symbol': 'HDFCBANK-EQ', 'token': '1333'},
        {'symbol': 'INFY-EQ', 'token': '1594'},
        {'symbol': 'ICICIBANK-EQ', 'token': '4963'},
        {'symbol': 'HINDUNILVR-EQ', 'token': '1394'},
        {'symbol': 'ITC-EQ', 'token': '424'},
        {'symbol': 'SBIN-EQ', 'token': '3045'},  # BLACKLISTED
        {'symbol': 'BHARTIARTL-EQ', 'token': '10604'},
        {'symbol': 'KOTAKBANK-EQ', 'token': '1922'},
        {'symbol': 'BAJFINANCE-EQ', 'token': '317'},
        {'symbol': 'LT-EQ', 'token': '11483'},
        {'symbol': 'ASIANPAINT-EQ', 'token': '236'},
        {'symbol': 'AXISBANK-EQ', 'token': '5900'},
        {'symbol': 'HCLTECH-EQ', 'token': '7229'},
        {'symbol': 'MARUTI-EQ', 'token': '10999'},
        {'symbol': 'SUNPHARMA-EQ', 'token': '3351'},
        {'symbol': 'TITAN-EQ', 'token': '3506'},
        {'symbol': 'NESTLEIND-EQ', 'token': '17963'},
        {'symbol': 'ULTRACEMCO-EQ', 'token': '11532'},
        {'symbol': 'WIPRO-EQ', 'token': '3787'},
        {'symbol': 'NTPC-EQ', 'token': '11630'},
        {'symbol': 'TATAMOTORS-EQ', 'token': '3456'},
        {'symbol': 'BAJAJFINSV-EQ', 'token': '16675'},
        {'symbol': 'POWERGRID-EQ', 'token': '14977'},  # BLACKLISTED
        {'symbol': 'TATASTEEL-EQ', 'token': '3499'},
        {'symbol': 'TECHM-EQ', 'token': '13538'},
        {'symbol': 'ADANIENT-EQ', 'token': '25'},
        {'symbol': 'ONGC-EQ', 'token': '2475'},
        {'symbol': 'COALINDIA-EQ', 'token': '20374'},
        {'symbol': 'HINDALCO-EQ', 'token': '1363'},
        {'symbol': 'INDUSINDBK-EQ', 'token': '5258'},
        {'symbol': 'EICHERMOT-EQ', 'token': '910'},
        {'symbol': 'DIVISLAB-EQ', 'token': '10940'},
        {'symbol': 'BRITANNIA-EQ', 'token': '547'},
        {'symbol': 'DRREDDY-EQ', 'token': '881'},
        {'symbol': 'APOLLOHOSP-EQ', 'token': '157'},
        {'symbol': 'CIPLA-EQ', 'token': '694'},
        {'symbol': 'GRASIM-EQ', 'token': '1232'},
        {'symbol': 'HEROMOTOCO-EQ', 'token': '1348'},
        {'symbol': 'JSWSTEEL-EQ', 'token': '11723'},  # BLACKLISTED
        {'symbol': 'ADANIPORTS-EQ', 'token': '15083'},
        {'symbol': 'HINDZINC-EQ', 'token': '364'},
        {'symbol': 'M&M-EQ', 'token': '2031'},
        {'symbol': 'BPCL-EQ', 'token': '526'},
        {'symbol': 'SHRIRAMFIN-EQ', 'token': '4306'},  # BLACKLISTED
        {'symbol': 'TRENT-EQ', 'token': '1964'},
        {'symbol': 'ADANIGREEN-EQ', 'token': '25615'},
        {'symbol': 'LTIM-EQ', 'token': '17818'},
    ]
    
    # Start trading
    bot.run(symbols, check_interval=300)  # Check every 5 minutes
