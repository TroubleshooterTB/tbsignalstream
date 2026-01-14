"""
Angel One WebSocket Manager v2
Implements WebSocket Streaming 2.0 protocol as per official documentation.
Reference: https://smartapi.angelbroking.com/docs/WebSocket2
"""

import json
import logging
import struct
import time
import threading
from typing import Dict, List, Callable, Optional
import websocket

logger = logging.getLogger(__name__)


class AngelWebSocketV2Manager:
    """
    WebSocket manager implementing Angel One WebSocket Streaming 2.0 protocol.
    
    Features:
    - JSON request format with binary response
    - Persistent connection with heartbeat
    - Subscribe/unsubscribe without reconnecting
    - Up to 1000 token subscriptions per session
    - Supports LTP, Quote, and SnapQuote modes
    """
    
    # Exchange type constants
    EXCHANGE_NSE_CM = 1
    EXCHANGE_NSE_FO = 2
    EXCHANGE_BSE_CM = 3
    EXCHANGE_BSE_FO = 4
    EXCHANGE_MCX_FO = 5
    EXCHANGE_NCX_FO = 7
    EXCHANGE_CDE_FO = 13
    
    # Subscription mode constants
    MODE_LTP = 1        # Last Traded Price (51 bytes)
    MODE_QUOTE = 2      # Quote (123 bytes)
    MODE_SNAP_QUOTE = 3 # Snap Quote (379 bytes)
    
    def __init__(self, api_key: str, client_code: str, feed_token: str, jwt_token: str):
        """
        Initialize WebSocket v2 manager.
        
        Args:
            api_key: Angel One API key
            client_code: Client code (Angel One trading account ID)
            feed_token: Feed token from login API response
            jwt_token: JWT auth token from login API response
        """
        self.api_key = api_key
        self.client_code = client_code
        self.feed_token = feed_token
        self.jwt_token = jwt_token
        
        # WebSocket v2 URL
        self.ws_url = "wss://smartapisocket.angelone.in/smart-stream"
        
        # Connection state
        self.ws: Optional[websocket.WebSocketApp] = None
        self.is_connected = False
        self._ws_thread: Optional[threading.Thread] = None
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._stop_heartbeat = False
        
        # Subscription tracking (persist across reconnections)
        self.subscribed_tokens = set()
        self.subscription_mode = self.MODE_LTP  # Default mode
        self.subscription_payload = []  # Store last subscription for resubscribe
        self.tick_callbacks: List[Callable] = []
        
        # Reconnection management
        self._auto_reconnect = True
        self._reconnect_thread: Optional[threading.Thread] = None
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 10
        self._base_reconnect_delay = 2  # Start with 2 seconds
        self._stop_reconnect = False
        
    def connect(self) -> bool:
        """
        Establish WebSocket connection using v2 protocol.
        
        Connection includes authentication headers and uses query params
        for browser compatibility.
        
        Returns:
            bool: True if connection successful
            
        Raises:
            Exception: If connection fails
        """
        try:
            # Build URL with query params (required for browser-based clients)
            url = (
                f"{self.ws_url}?"
                f"clientCode={self.client_code}&"
                f"feedToken={self.feed_token}&"
                f"apiKey={self.api_key}"
            )
            
            # Authentication headers as per v2 protocol
            headers = {
                "Authorization": f"Bearer {self.jwt_token}",
                "x-api-key": self.api_key,
                "x-client-code": self.client_code,
                "x-feed-token": self.feed_token
            }
            
            logger.info(f"Connecting to Angel One WebSocket v2: {self.ws_url}")
            
            # Create WebSocket App
            self.ws = websocket.WebSocketApp(
                url,
                header=headers,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )
            
            # Run WebSocket in background thread
            self._ws_thread = threading.Thread(
                target=self.ws.run_forever,
                daemon=True
            )
            self._ws_thread.start()
            
            # Wait for connection (increased to 60 seconds for Cloud Run cold starts)
            timeout = 60
            start_time = time.time()
            logger.info(f"⏳ Waiting for WebSocket connection (timeout: {timeout}s)...")
            
            while not self.is_connected and (time.time() - start_time) < timeout:
                elapsed = time.time() - start_time
                if elapsed % 5 < 0.2:  # Log every 5 seconds
                    logger.info(f"⏳ Still waiting... ({elapsed:.1f}s / {timeout}s)")
                time.sleep(0.1)
            
            if not self.is_connected:
                logger.error(f"❌ WebSocket connection timeout after {timeout} seconds")
                logger.error(f"❌ URL: {self.ws_url}")
                logger.error(f"❌ Thread alive: {self._ws_thread.is_alive()}")
                raise Exception(f"WebSocket connection timeout after {timeout} seconds")
            
            logger.info("✅ WebSocket v2 connection established successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ WebSocket connection failed: {str(e)}")
            self.is_connected = False
            raise
    
    def subscribe(self, mode: int, tokens: List[Dict[str, any]]) -> bool:
        """
        Subscribe to market data using v2 JSON protocol.
        
        Args:
            mode: Subscription mode (1=LTP, 2=Quote, 3=SnapQuote)
            tokens: List of token groups
                    Example: [
                        {"exchangeType": 1, "tokens": ["3045", "1594"]},
                        {"exchangeType": 5, "tokens": ["234230", "234235"]}
                    ]
        
        Returns:
            bool: True if subscription request sent successfully
            
        Raises:
            Exception: If not connected or subscription fails
        """
        try:
            if not self.is_connected:
                raise Exception("WebSocket not connected. Call connect() first.")
            
            # Store subscription details for auto-resubscribe on reconnect
            self.subscription_mode = mode
            self.subscription_payload = tokens
            
            # Generate correlation ID for tracking
            correlation_id = f"sub_{int(time.time() * 1000)}"
            
            # Build v2 subscription payload
            payload = {
                "correlationID": correlation_id,
                "action": 1,  # 1 = Subscribe, 0 = Unsubscribe
                "params": {
                    "mode": mode,
                    "tokenList": tokens
                }
            }
            
            # Send JSON message
            message = json.dumps(payload)
            logger.info(f"Sending subscription: {message}")
            self.ws.send(message)
            
            # Track subscribed tokens
            for token_group in tokens:
                for token in token_group.get('tokens', []):
                    self.subscribed_tokens.add(token)
            
            total_tokens = sum(len(group.get('tokens', [])) for group in tokens)
            logger.info(f"✅ Subscribed to {total_tokens} tokens in mode {mode}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Subscription failed: {str(e)}")
            raise
    
    def unsubscribe(self, mode: int, tokens: List[Dict[str, any]]) -> bool:
        """
        Unsubscribe from market data using v2 JSON protocol.
        
        Args:
            mode: Subscription mode
            tokens: List of token groups to unsubscribe
            
        Returns:
            bool: True if unsubscription request sent successfully
        """
        try:
            if not self.is_connected:
                raise Exception("WebSocket not connected")
            
            correlation_id = f"unsub_{int(time.time() * 1000)}"
            
            payload = {
                "correlationID": correlation_id,
                "action": 0,  # Unsubscribe
                "params": {
                    "mode": mode,
                    "tokenList": tokens
                }
            }
            
            self.ws.send(json.dumps(payload))
            
            # Remove from tracked tokens
            for token_group in tokens:
                for token in token_group.get('tokens', []):
                    self.subscribed_tokens.discard(token)
            
            total_tokens = sum(len(group.get('tokens', [])) for group in tokens)
            logger.info(f"✅ Unsubscribed from {total_tokens} tokens")
            return True
            
        except Exception as e:
            logger.error(f"❌ Unsubscription failed: {str(e)}")
            raise
    
    def disconnect(self) -> bool:
        """
        Close WebSocket connection and cleanup.
        
        Returns:
            bool: True if disconnected successfully
        """
        try:
            logger.info("Disconnecting WebSocket...")
            
            # Disable auto-reconnect
            self._auto_reconnect = False
            self._stop_reconnect = True
            
            # Stop heartbeat
            self._stop_heartbeat = True
            if self._heartbeat_thread:
                self._heartbeat_thread.join(timeout=2)
            
            # Close WebSocket
            if self.ws:
                self.ws.close()
            
            self.is_connected = False
            self.subscribed_tokens.clear()
            
            logger.info("✅ WebSocket disconnected")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error during disconnect: {str(e)}")
            return False
    
    def add_tick_callback(self, callback: Callable):
        """
        Register callback for tick data.
        
        Args:
            callback: Function(tick_data) to be called on each tick
        """
        if callback not in self.tick_callbacks:
            self.tick_callbacks.append(callback)
            logger.debug(f"Added tick callback: {callback.__name__}")
    
    def remove_tick_callback(self, callback: Callable):
        """Remove registered callback."""
        if callback in self.tick_callbacks:
            self.tick_callbacks.remove(callback)
            logger.debug(f"Removed tick callback: {callback.__name__}")
    
    # ========== WebSocket Event Handlers ==========
    
    def _on_open(self, ws):
        """Called when WebSocket connection opens."""
        logger.info("🟢 WebSocket connection opened")
        self.is_connected = True
        
        # Start heartbeat thread (required every 30 seconds)
        self._start_heartbeat()
    
    def _on_message(self, ws, message):
        """
        Called when message received from server.
        
        Messages can be:
        1. Text: "pong" (heartbeat response)
        2. Text: JSON error response
        3. Binary: Market data tick
        """
        try:
            # Check if message is text (heartbeat or error)
            if isinstance(message, str):
                # Heartbeat response
                if message == "pong":
                    logger.debug("❤️ Heartbeat pong received")
                    return
                
                # Try to parse as JSON error
                try:
                    error_data = json.loads(message)
                    if 'errorCode' in error_data:
                        logger.error(
                            f"❌ WebSocket error: {error_data.get('errorCode')} - "
                            f"{error_data.get('errorMessage')}"
                        )
                    return
                except json.JSONDecodeError:
                    logger.warning(f"Unknown text message: {message}")
                    return
            
            # Binary message = market data tick
            if isinstance(message, bytes):
                tick_data = self._parse_binary_tick(message)
                
                # Call all registered callbacks
                for callback in self.tick_callbacks:
                    try:
                        callback(tick_data)
                    except Exception as e:
                        logger.error(f"Error in tick callback: {e}")
                        
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def _on_error(self, ws, error):
        """Called when WebSocket error occurs."""
        logger.error(f"❌ WebSocket error: {error}")
        logger.error(f"❌ Error type: {type(error).__name__}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
    
    def _on_close(self, ws, close_status_code, close_msg):
        """Called when WebSocket connection closes."""
        logger.warning(
            f"🔴 WebSocket closed (code: {close_status_code}, "
            f"message: {close_msg})"
        )
        self.is_connected = False
        self._stop_heartbeat = True
        
        # Trigger auto-reconnection if enabled
        if self._auto_reconnect and not self._stop_reconnect:
            logger.info("🔄 Connection lost - Initiating auto-reconnect...")
            self._start_reconnect()
    
    # ========== Auto-Reconnection Logic ==========
    
    def _start_reconnect(self):
        """Start reconnection thread with exponential backoff."""
        if self._reconnect_thread and self._reconnect_thread.is_alive():
            logger.debug("Reconnection already in progress")
            return
        
        self._reconnect_thread = threading.Thread(
            target=self._reconnect_loop,
            daemon=True
        )
        self._reconnect_thread.start()
    
    def _reconnect_loop(self):
        """Reconnect with exponential backoff."""
        self._reconnect_attempts = 0
        
        while self._auto_reconnect and not self._stop_reconnect:
            if self.is_connected:
                logger.info("✅ Reconnection successful - Stopping reconnect loop")
                self._reconnect_attempts = 0
                break
            
            if self._reconnect_attempts >= self._max_reconnect_attempts:
                logger.error(
                    f"❌ Max reconnection attempts ({self._max_reconnect_attempts}) "
                    f"reached. Giving up."
                )
                break
            
            self._reconnect_attempts += 1
            
            # Exponential backoff: 2s, 4s, 8s, 16s, 32s, max 60s
            delay = min(
                self._base_reconnect_delay * (2 ** (self._reconnect_attempts - 1)),
                60
            )
            
            logger.info(
                f"🔄 Reconnect attempt {self._reconnect_attempts}/"
                f"{self._max_reconnect_attempts} in {delay}s..."
            )
            
            time.sleep(delay)
            
            try:
                logger.info("🔄 Attempting to reconnect WebSocket...")
                
                # Close old connection if exists
                if self.ws:
                    try:
                        self.ws.close()
                    except:
                        pass
                
                # Reset state
                self.is_connected = False
                self._stop_heartbeat = True
                
                # Reconnect
                url = (
                    f"{self.ws_url}?"
                    f"clientCode={self.client_code}&"
                    f"feedToken={self.feed_token}&"
                    f"apiKey={self.api_key}"
                )
                
                headers = {
                    "Authorization": f"Bearer {self.jwt_token}",
                    "x-api-key": self.api_key,
                    "x-client-code": self.client_code,
                    "x-feed-token": self.feed_token
                }
                
                self.ws = websocket.WebSocketApp(
                    url,
                    header=headers,
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close
                )
                
                # Run in background
                self._ws_thread = threading.Thread(
                    target=self.ws.run_forever,
                    daemon=True
                )
                self._ws_thread.start()
                
                # Wait for connection
                timeout = 10
                start_time = time.time()
                while not self.is_connected and (time.time() - start_time) < timeout:
                    time.sleep(0.1)
                
                if self.is_connected:
                    logger.info("✅ WebSocket reconnected successfully")
                    
                    # Resubscribe to previous subscriptions
                    if self.subscription_payload:
                        logger.info("🔄 Resubscribing to previous symbols...")
                        time.sleep(1)  # Wait for connection to stabilize
                        try:
                            self.subscribe(self.subscription_mode, self.subscription_payload)
                            logger.info("✅ Resubscription successful")
                        except Exception as e:
                            logger.error(f"❌ Resubscription failed: {e}")
                    
                    # Reset attempt counter
                    self._reconnect_attempts = 0
                    break
                else:
                    logger.warning(f"⚠️ Reconnection attempt {self._reconnect_attempts} failed (timeout)")
                    
            except Exception as e:
                logger.error(f"❌ Reconnection attempt {self._reconnect_attempts} failed: {e}")
        
        logger.info("🔄 Reconnection loop ended")
    
    # ========== Binary Data Parsing ==========
    
    def _parse_binary_tick(self, data: bytes) -> Dict:
        """
        Parse binary tick data according to v2 protocol.
        
        Binary format (Little Endian):
        - Subscription Mode (1 byte): 1=LTP, 2=Quote, 3=SnapQuote
        - Exchange Type (1 byte): 1=NSE_CM, 2=NSE_FO, etc.
        - Token (25 bytes): Token ID as UTF-8 string
        - Sequence Number (8 bytes): int64
        - Exchange Timestamp (8 bytes): int64 milliseconds
        - LTP (8 bytes): int64 (in paise, divide by 100)
        - ... (additional fields based on mode)
        
        Args:
            data: Binary data from WebSocket
            
        Returns:
            Dict with parsed tick data
        """
        try:
            offset = 0
            
            # Subscription mode (1 byte)
            mode = struct.unpack_from('<B', data, offset)[0]
            offset += 1
            
            # Exchange type (1 byte)
            exchange_type = struct.unpack_from('<B', data, offset)[0]
            offset += 1
            
            # Token (25 bytes, null-terminated string)
            token_bytes = struct.unpack_from('<25s', data, offset)[0]
            token = token_bytes.decode('utf-8').rstrip('\x00')
            offset += 25
            
            # Sequence number (8 bytes)
            sequence = struct.unpack_from('<q', data, offset)[0]
            offset += 8
            
            # Exchange timestamp (8 bytes)
            timestamp = struct.unpack_from('<q', data, offset)[0]
            offset += 8
            
            # LTP (8 bytes) - in paise for equities, divide by 10000000 for currencies
            ltp_raw = struct.unpack_from('<q', data, offset)[0]
            ltp = ltp_raw / 100.0  # Convert paise to rupees
            offset += 8
            
            tick = {
                'mode': mode,
                'exchange_type': exchange_type,
                'token': token,
                'sequence': sequence,
                'timestamp': timestamp,
                'ltp': ltp
            }
            
            # If mode is LTP only (packet size = 51 bytes), return now
            if mode == self.MODE_LTP:
                return tick
            
            # Parse additional fields for Quote mode
            if len(data) >= 123:
                tick['last_traded_qty'] = struct.unpack_from('<q', data, offset)[0]
                offset += 8
                tick['avg_traded_price'] = struct.unpack_from('<q', data, offset)[0] / 100.0
                offset += 8
                tick['volume'] = struct.unpack_from('<q', data, offset)[0]
                offset += 8
                tick['total_buy_qty'] = struct.unpack_from('<d', data, offset)[0]
                offset += 8
                tick['total_sell_qty'] = struct.unpack_from('<d', data, offset)[0]
                offset += 8
                tick['open'] = struct.unpack_from('<q', data, offset)[0] / 100.0
                offset += 8
                tick['high'] = struct.unpack_from('<q', data, offset)[0] / 100.0
                offset += 8
                tick['low'] = struct.unpack_from('<q', data, offset)[0] / 100.0
                offset += 8
                tick['close'] = struct.unpack_from('<q', data, offset)[0] / 100.0
                offset += 8
            
            # If mode is Quote (packet size = 123 bytes), return now
            if mode == self.MODE_QUOTE:
                return tick
            
            # Parse additional fields for SnapQuote mode (379 bytes total)
            if len(data) >= 379:
                tick['last_traded_timestamp'] = struct.unpack_from('<q', data, offset)[0]
                offset += 8
                tick['open_interest'] = struct.unpack_from('<q', data, offset)[0]
                offset += 8
                # Skip OI change % (dummy field)
                offset += 8
                # Parse best 5 buy/sell (200 bytes)
                # ... (implement if needed)
                offset += 200
                tick['upper_circuit'] = struct.unpack_from('<q', data, offset)[0] / 100.0
                offset += 8
                tick['lower_circuit'] = struct.unpack_from('<q', data, offset)[0] / 100.0
                offset += 8
                tick['52_week_high'] = struct.unpack_from('<q', data, offset)[0] / 100.0
                offset += 8
                tick['52_week_low'] = struct.unpack_from('<q', data, offset)[0] / 100.0
                offset += 8
            
            return tick
            
        except Exception as e:
            logger.error(f"Error parsing binary tick data: {e}")
            return {}
    
    # ========== Heartbeat Management ==========
    
    def _start_heartbeat(self):
        """Start heartbeat thread to send 'ping' every 30 seconds."""
        self._stop_heartbeat = False
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            daemon=True
        )
        self._heartbeat_thread.start()
        logger.info("❤️ Heartbeat thread started")
    
    def _heartbeat_loop(self):
        """Send 'ping' message every 30 seconds to keep connection alive."""
        while not self._stop_heartbeat and self.is_connected:
            try:
                if self.ws:
                    self.ws.send("ping")
                    logger.debug("❤️ Sent heartbeat ping")
                time.sleep(30)  # Send every 30 seconds as per protocol
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                break
        
        logger.info("❤️ Heartbeat thread stopped")
    
    def __del__(self):
        """Cleanup on destruction."""
        self.disconnect()
