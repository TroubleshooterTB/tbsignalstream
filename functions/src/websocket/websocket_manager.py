"""
Angel One WebSocket Manager
Handles real-time market data streaming via WebSocket
"""

import asyncio
import json
import logging
from typing import Dict, List, Callable, Optional
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
from SmartApi import SmartConnect

logger = logging.getLogger(__name__)


class AngelWebSocketManager:
    """
    Manages WebSocket connection to Angel One for real-time market data.
    """
    
    def __init__(self, api_key: str, client_code: str, feed_token: str):
        """
        Initialize WebSocket manager.
        
        Args:
            api_key: Angel One API key
            client_code: User's client code
            feed_token: Feed token from login response
        """
        self.api_key = api_key
        self.client_code = client_code
        self.feed_token = feed_token
        self.ws = None
        self.is_connected = False
        self.subscribed_tokens = set()
        self.tick_callbacks: List[Callable] = []
        
    def on_tick(self, ws, tick_data):
        """
        Called when tick data is received.
        
        Args:
            ws: WebSocket instance
            tick_data: Tick data from Angel One
        """
        try:
            logger.debug(f"Received tick data: {tick_data}")
            
            # Process tick data
            processed_data = self._process_tick_data(tick_data)
            
            # Call all registered callbacks
            for callback in self.tick_callbacks:
                try:
                    callback(processed_data)
                except Exception as e:
                    logger.error(f"Error in tick callback: {e}")
                    
        except Exception as e:
            logger.error(f"Error processing tick data: {e}")
    
    def on_open(self, ws):
        """Called when WebSocket connection opens."""
        logger.info("WebSocket connection opened")
        self.is_connected = True
        
    def on_close(self, ws):
        """Called when WebSocket connection closes."""
        logger.info("WebSocket connection closed")
        self.is_connected = False
        
    def on_error(self, ws, error):
        """Called when WebSocket encounters an error."""
        logger.error(f"WebSocket error: {error}")
        self.is_connected = False
    
    def _process_tick_data(self, tick_data: Dict) -> Dict:
        """
        Process raw tick data into standardized format.
        
        Args:
            tick_data: Raw tick data from Angel One
            
        Returns:
            Processed tick data
        """
        if not tick_data:
            return {}
            
        processed = {}
        
        # Angel One tick data format
        # {"name":"trading_symbol","token":"exchange_token","ltp":price,...}
        for tick in tick_data.get('data', []) if isinstance(tick_data, dict) else [tick_data]:
            token = str(tick.get('token', ''))
            if token:
                processed[token] = {
                    'token': token,
                    'ltp': float(tick.get('ltp', 0)),
                    'volume': int(tick.get('volume', 0)),
                    'open': float(tick.get('open', 0)),
                    'high': float(tick.get('high', 0)),
                    'low': float(tick.get('low', 0)),
                    'close': float(tick.get('close', 0)),
                    'timestamp': tick.get('timestamp', ''),
                    'exchange': tick.get('exchange', 'NSE')
                }
        
        return processed
    
    def connect(self):
        """Establish WebSocket connection."""
        try:
            logger.info("Connecting to Angel One WebSocket...")
            
            correlation_id = f"ws_{self.client_code}"
            
            self.ws = SmartWebSocketV2(
                auth_token=self.feed_token,
                api_key=self.api_key,
                client_code=self.client_code,
                feed_token=self.feed_token
            )
            
            # Register callbacks
            self.ws.on_open = self.on_open
            self.ws.on_data = self.on_tick
            self.ws.on_error = self.on_error
            self.ws.on_close = self.on_close
            
            # Connect
            self.ws.connect()
            
            logger.info("WebSocket connection initiated")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect WebSocket: {e}")
            return False
    
    def subscribe(self, mode: int, tokens: List[Dict[str, str]]):
        """
        Subscribe to market data for specified tokens.
        
        Args:
            mode: Subscription mode (1=LTP, 2=Quote, 3=Snap Quote)
            tokens: List of token dictionaries [{"exchangeType": 1, "tokens": ["token1", "token2"]}]
        """
        try:
            if not self.is_connected:
                logger.warning("WebSocket not connected. Cannot subscribe.")
                return False
            
            logger.info(f"Subscribing to tokens: {tokens} with mode {mode}")
            
            # Subscribe to tokens
            self.ws.subscribe(correlation_id="correlation_id", mode=mode, token_list=tokens)
            
            # Track subscribed tokens
            for token_group in tokens:
                for token in token_group.get('tokens', []):
                    self.subscribed_tokens.add(token)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to subscribe to tokens: {e}")
            return False
    
    def unsubscribe(self, mode: int, tokens: List[Dict[str, str]]):
        """
        Unsubscribe from market data.
        
        Args:
            mode: Subscription mode
            tokens: List of token dictionaries
        """
        try:
            if not self.is_connected:
                return False
            
            logger.info(f"Unsubscribing from tokens: {tokens}")
            
            self.ws.unsubscribe(correlation_id="correlation_id", mode=mode, token_list=tokens)
            
            # Remove from tracked tokens
            for token_group in tokens:
                for token in token_group.get('tokens', []):
                    self.subscribed_tokens.discard(token)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to unsubscribe from tokens: {e}")
            return False
    
    def add_tick_callback(self, callback: Callable):
        """
        Register a callback function to be called on each tick.
        
        Args:
            callback: Function that accepts processed tick data
        """
        if callback not in self.tick_callbacks:
            self.tick_callbacks.append(callback)
    
    def remove_tick_callback(self, callback: Callable):
        """Remove a registered callback."""
        if callback in self.tick_callbacks:
            self.tick_callbacks.remove(callback)
    
    def disconnect(self):
        """Close WebSocket connection."""
        try:
            if self.ws and self.is_connected:
                logger.info("Closing WebSocket connection...")
                self.ws.close()
                self.is_connected = False
                self.subscribed_tokens.clear()
                return True
        except Exception as e:
            logger.error(f"Error closing WebSocket: {e}")
            return False
    
    def __del__(self):
        """Cleanup on destruction."""
        self.disconnect()
