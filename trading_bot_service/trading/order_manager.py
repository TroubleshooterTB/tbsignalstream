"""
Order Management System for Angel One
Handles order placement, modification, cancellation, and tracking
"""

import logging
import requests
from typing import Dict, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Order types supported by Angel One"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOPLOSS_LIMIT = "STOPLOSS_LIMIT"
    STOPLOSS_MARKET = "STOPLOSS_MARKET"


class TransactionType(Enum):
    """Transaction types"""
    BUY = "BUY"
    SELL = "SELL"


class ProductType(Enum):
    """Product types"""
    DELIVERY = "DELIVERY"
    INTRADAY = "INTRADAY"
    MARGIN = "MARGIN"
    BO = "BO"  # Bracket Order
    CO = "CO"  # Cover Order


class OrderDuration(Enum):
    """Order duration"""
    DAY = "DAY"
    IOC = "IOC"  # Immediate or Cancel


class OrderManager:
    """
    Manages order placement and tracking for Angel One broker.
    """
    
    def __init__(self, api_key: str, jwt_token: str):
        """
        Initialize Order Manager.
        
        Args:
            api_key: Angel One API key
            jwt_token: User's JWT token from login
        """
        self.api_key = api_key
        self.jwt_token = jwt_token
        self.base_url = "https://apiconnect.angelone.in"
        
    def _get_headers(self, client_local_ip: str = "127.0.0.1") -> Dict:
        """Get request headers for Angel One API."""
        return {
            'Authorization': f'Bearer {self.jwt_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-UserType': 'USER',
            'X-SourceID': 'WEB',
            'X-ClientLocalIP': client_local_ip,
            'X-ClientPublicIP': client_local_ip,
            'X-MACAddress': '00:00:00:00:00:00',
            'X-PrivateKey': self.api_key
        }
    
    def place_order(
        self,
        symbol: str,
        token: str,
        exchange: str,
        transaction_type: TransactionType,
        order_type: OrderType,
        quantity: int,
        product_type: ProductType = ProductType.INTRADAY,
        price: float = 0.0,
        trigger_price: float = 0.0,
        duration: OrderDuration = OrderDuration.DAY,
        disclosed_quantity: int = 0,
        client_local_ip: str = "127.0.0.1"
    ) -> Optional[Dict]:
        """
        Place a new order.
        
        Args:
            symbol: Trading symbol (e.g., "RELIANCE-EQ")
            token: Symbol token
            exchange: Exchange (NSE/BSE)
            transaction_type: BUY or SELL
            order_type: MARKET, LIMIT, etc.
            quantity: Number of shares
            product_type: DELIVERY, INTRADAY, etc.
            price: Limit price (for LIMIT orders)
            trigger_price: Trigger price (for STOPLOSS orders)
            duration: Order validity (DAY/IOC)
            disclosed_quantity: Disclosed quantity for iceberg orders
            client_local_ip: Client's IP address
            
        Returns:
            Order response dict or None on failure
        """
        try:
            url = f"{self.base_url}/rest/secure/angelbroking/order/v1/placeOrder"
            
            payload = {
                "variety": "NORMAL",
                "tradingsymbol": symbol,
                "symboltoken": str(token),
                "transactiontype": transaction_type.value,
                "exchange": exchange,
                "ordertype": order_type.value,
                "producttype": product_type.value,
                "duration": duration.value,
                "price": str(price) if price > 0 else "0",
                "squareoff": "0",
                "stoploss": "0",
                "quantity": str(quantity),
                "triggerprice": str(trigger_price) if trigger_price > 0 else "0",
                "disclosedquantity": str(disclosed_quantity)
            }
            
            logger.info(f"Placing order: {transaction_type.value} {quantity} {symbol}")
            
            response = requests.post(
                url,
                headers=self._get_headers(client_local_ip),
                json=payload,
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('status'):
                order_id = result.get('data', {}).get('orderid')
                logger.info(f"Order placed successfully. Order ID: {order_id}")
                return result['data']
            else:
                logger.error(f"Order placement failed: {result.get('message')}")
                return None
                
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None
    
    def modify_order(
        self,
        order_id: str,
        order_type: OrderType,
        quantity: int,
        price: float = 0.0,
        trigger_price: float = 0.0,
        client_local_ip: str = "127.0.0.1"
    ) -> bool:
        """
        Modify an existing order.
        
        Args:
            order_id: Order ID to modify
            order_type: New order type
            quantity: New quantity
            price: New price
            trigger_price: New trigger price
            client_local_ip: Client's IP
            
        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.base_url}/rest/secure/angelbroking/order/v1/modifyOrder"
            
            payload = {
                "variety": "NORMAL",
                "orderid": order_id,
                "ordertype": order_type.value,
                "producttype": "INTRADAY",
                "duration": "DAY",
                "price": str(price) if price > 0 else "0",
                "quantity": str(quantity),
                "triggerprice": str(trigger_price) if trigger_price > 0 else "0"
            }
            
            logger.info(f"Modifying order {order_id}")
            
            response = requests.post(
                url,
                headers=self._get_headers(client_local_ip),
                json=payload,
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('status'):
                logger.info(f"Order modified successfully: {order_id}")
                return True
            else:
                logger.error(f"Order modification failed: {result.get('message')}")
                return False
                
        except Exception as e:
            logger.error(f"Error modifying order: {e}")
            return False
    
    def cancel_order(
        self,
        order_id: str,
        variety: str = "NORMAL",
        client_local_ip: str = "127.0.0.1"
    ) -> bool:
        """
        Cancel an existing order.
        
        Args:
            order_id: Order ID to cancel
            variety: Order variety
            client_local_ip: Client's IP
            
        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.base_url}/rest/secure/angelbroking/order/v1/cancelOrder"
            
            payload = {
                "variety": variety,
                "orderid": order_id
            }
            
            logger.info(f"Cancelling order {order_id}")
            
            response = requests.post(
                url,
                headers=self._get_headers(client_local_ip),
                json=payload,
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('status'):
                logger.info(f"Order cancelled successfully: {order_id}")
                return True
            else:
                logger.error(f"Order cancellation failed: {result.get('message')}")
                return False
                
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return False
    
    def get_order_book(self, client_local_ip: str = "127.0.0.1") -> Optional[List[Dict]]:
        """
        Get order book (all orders for the day).
        
        Args:
            client_local_ip: Client's IP
            
        Returns:
            List of orders or None on failure
        """
        try:
            url = f"{self.base_url}/rest/secure/angelbroking/order/v1/getOrderBook"
            
            response = requests.get(
                url,
                headers=self._get_headers(client_local_ip),
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('status'):
                return result.get('data', [])
            else:
                logger.error(f"Failed to get order book: {result.get('message')}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting order book: {e}")
            return None
    
    def get_trade_book(self, client_local_ip: str = "127.0.0.1") -> Optional[List[Dict]]:
        """
        Get trade book (executed trades for the day).
        
        Args:
            client_local_ip: Client's IP
            
        Returns:
            List of trades or None on failure
        """
        try:
            url = f"{self.base_url}/rest/secure/angelbroking/order/v1/getTradeBook"
            
            response = requests.get(
                url,
                headers=self._get_headers(client_local_ip),
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('status'):
                return result.get('data', [])
            else:
                logger.error(f"Failed to get trade book: {result.get('message')}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting trade book: {e}")
            return None
    
    def get_positions(self, client_local_ip: str = "127.0.0.1") -> Optional[Dict]:
        """
        Get current positions (day and net).
        
        Args:
            client_local_ip: Client's IP
            
        Returns:
            Positions dict or None on failure
        """
        try:
            url = f"{self.base_url}/rest/secure/angelbroking/order/v1/getPosition"
            
            response = requests.get(
                url,
                headers=self._get_headers(client_local_ip),
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('status'):
                return result.get('data', {})
            else:
                logger.error(f"Failed to get positions: {result.get('message')}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return None
    
    def get_holdings(self, client_local_ip: str = "127.0.0.1") -> Optional[List[Dict]]:
        """
        Get holdings (delivery positions).
        
        Args:
            client_local_ip: Client's IP
            
        Returns:
            List of holdings or None on failure
        """
        try:
            url = f"{self.base_url}/rest/secure/angelbroking/portfolio/v1/getHolding"
            
            response = requests.get(
                url,
                headers=self._get_headers(client_local_ip),
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('status'):
                return result.get('data', {}).get('holdings', [])
            else:
                logger.error(f"Failed to get holdings: {result.get('message')}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting holdings: {e}")
            return None
