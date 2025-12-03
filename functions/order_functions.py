"""
Order Placement Cloud Functions
Endpoints for placing, modifying, and tracking orders
"""

import json
import logging
import firebase_admin
from firebase_admin import firestore, auth
from firebase_functions import https_fn, options
from src.config import ANGEL_ONE_API
from src.trading.order_manager import (
    OrderManager, OrderType, TransactionType, 
    ProductType, OrderDuration
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Firebase if not already initialized
if not firebase_admin._apps:
    firebase_admin.initialize_app()


def _get_db():
    """Lazy initialization of Firestore client"""
    return firestore.client()


@https_fn.on_request(
    cors=options.CorsOptions(cors_origins="*", cors_methods=["post"])
)
def placeOrder(request: https_fn.Request) -> https_fn.Response:
    """
    Place a new order to Angel One broker.
    """
    try:
        # Verify user
        id_token = request.headers.get('Authorization', '').split('Bearer ')[-1]
        if not id_token:
            return https_fn.Response(
                json.dumps({"error": "Authentication required"}),
                status=401
            )
        
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        
        # Get user credentials
        user_doc = _get_db().collection('angel_one_credentials').document(uid).get()
        if not user_doc.exists:
            return https_fn.Response(
                json.dumps({"error": "Angel One not connected"}),
                status=403
            )
        
        user_data = user_doc.to_dict()
        jwt_token = user_data.get('jwt_token')
        
        # Get API key
        api_key = ANGEL_ONE_API.get('API_KEY_TRADING')
        if not api_key or not jwt_token:
            return https_fn.Response(
                json.dumps({"error": "Configuration error"}),
                status=500
            )
        
        # Parse order details
        data = request.get_json()
        symbol = data.get('symbol')
        token = data.get('token')
        exchange = data.get('exchange', 'NSE')
        transaction_type = TransactionType[data.get('transactionType', 'BUY')]
        order_type = OrderType[data.get('orderType', 'MARKET')]
        quantity = int(data.get('quantity', 1))
        product_type = ProductType[data.get('productType', 'INTRADAY')]
        price = float(data.get('price', 0))
        trigger_price = float(data.get('triggerPrice', 0))
        
        if not all([symbol, token]):
            return https_fn.Response(
                json.dumps({"error": "Missing required fields"}),
                status=400
            )
        
        # Create order manager
        order_mgr = OrderManager(api_key, jwt_token)
        
        # Place order
        result = order_mgr.place_order(
            symbol=symbol,
            token=token,
            exchange=exchange,
            transaction_type=transaction_type,
            order_type=order_type,
            quantity=quantity,
            product_type=product_type,
            price=price,
            trigger_price=trigger_price,
            client_local_ip=request.remote_addr or "127.0.0.1"
        )
        
        if result:
            # Log order in Firestore
            _get_db().collection('orders').document(uid).collection('order_history').add({
                'order_id': result.get('orderid'),
                'symbol': symbol,
                'transaction_type': transaction_type.value,
                'order_type': order_type.value,
                'quantity': quantity,
                'price': price,
                'status': 'placed',
                'timestamp': firestore.SERVER_TIMESTAMP
            })
            
            return https_fn.Response(
                json.dumps({
                    "status": "success",
                    "data": result
                }),
                status=200
            )
        else:
            return https_fn.Response(
                json.dumps({"error": "Order placement failed"}),
                status=500
            )
        
    except Exception as e:
        logger.error(f"Error placing order: {e}")
        return https_fn.Response(
            json.dumps({"error": str(e)}),
            status=500
        )


@https_fn.on_request(
    cors=options.CorsOptions(cors_origins="*", cors_methods=["post"])
)
def modifyOrder(request: https_fn.Request) -> https_fn.Response:
    """
    Modify an existing order.
    """
    try:
        # Verify user
        id_token = request.headers.get('Authorization', '').split('Bearer ')[-1]
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        
        # Get credentials
        user_doc = _get_db().collection('angel_one_credentials').document(uid).get()
        user_data = user_doc.to_dict()
        jwt_token = user_data.get('jwt_token')
        api_key = ANGEL_ONE_API.get('API_KEY_TRADING')
        
        # Parse request
        data = request.get_json()
        order_id = data.get('orderId')
        order_type = OrderType[data.get('orderType', 'MARKET')]
        quantity = int(data.get('quantity'))
        price = float(data.get('price', 0))
        trigger_price = float(data.get('triggerPrice', 0))
        
        # Modify order
        order_mgr = OrderManager(api_key, jwt_token)
        success = order_mgr.modify_order(
            order_id=order_id,
            order_type=order_type,
            quantity=quantity,
            price=price,
            trigger_price=trigger_price,
            client_local_ip=request.remote_addr or "127.0.0.1"
        )
        
        return https_fn.Response(
            json.dumps({"status": "success" if success else "failed"}),
            status=200 if success else 500
        )
        
    except Exception as e:
        logger.error(f"Error modifying order: {e}")
        return https_fn.Response(
            json.dumps({"error": str(e)}),
            status=500
        )


@https_fn.on_request(
    cors=options.CorsOptions(cors_origins="*", cors_methods=["post"])
)
def cancelOrder(request: https_fn.Request) -> https_fn.Response:
    """
    Cancel an existing order.
    """
    try:
        # Verify user
        id_token = request.headers.get('Authorization', '').split('Bearer ')[-1]
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        
        # Get credentials
        user_doc = _get_db().collection('angel_one_credentials').document(uid).get()
        user_data = user_doc.to_dict()
        jwt_token = user_data.get('jwt_token')
        api_key = ANGEL_ONE_API.get('API_KEY_TRADING')
        
        # Parse request
        data = request.get_json()
        order_id = data.get('orderId')
        
        # Cancel order
        order_mgr = OrderManager(api_key, jwt_token)
        success = order_mgr.cancel_order(
            order_id=order_id,
            client_local_ip=request.remote_addr or "127.0.0.1"
        )
        
        return https_fn.Response(
            json.dumps({"status": "success" if success else "failed"}),
            status=200 if success else 500
        )
        
    except Exception as e:
        logger.error(f"Error cancelling order: {e}")
        return https_fn.Response(
            json.dumps({"error": str(e)}),
            status=500
        )


@https_fn.on_request(
    cors=options.CorsOptions(
        cors_origins="*",
        cors_methods=["get", "post", "options"]
    )
)
def getOrderBook(request: https_fn.Request) -> https_fn.Response:
    """
    Get order book for the user.
    """
    try:
        # Verify user
        id_token = request.headers.get('Authorization', '').split('Bearer ')[-1]
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        
        # Get credentials
        user_doc = _get_db().collection('angel_one_credentials').document(uid).get()
        user_data = user_doc.to_dict()
        jwt_token = user_data.get('jwt_token')
        api_key = ANGEL_ONE_API.get('API_KEY_TRADING')
        
        # Get order book
        order_mgr = OrderManager(api_key, jwt_token)
        orders = order_mgr.get_order_book(request.remote_addr or "127.0.0.1")
        
        return https_fn.Response(
            json.dumps({"status": "success", "data": orders}),
            status=200
        )
        
    except Exception as e:
        logger.error(f"Error getting order book: {e}")
        return https_fn.Response(
            json.dumps({"error": str(e)}),
            status=500
        )


@https_fn.on_request(
    cors=options.CorsOptions(
        cors_origins="*",
        cors_methods=["get", "post", "options"]
    )
)
def getPositions(request: https_fn.Request) -> https_fn.Response:
    """
    Get current positions for the user.
    """
    try:
        # Verify user
        id_token = request.headers.get('Authorization', '').split('Bearer ')[-1]
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        
        # Get credentials
        user_doc = _get_db().collection('angel_one_credentials').document(uid).get()
        user_data = user_doc.to_dict()
        jwt_token = user_data.get('jwt_token')
        api_key = ANGEL_ONE_API.get('API_KEY_TRADING')
        
        # Get positions
        order_mgr = OrderManager(api_key, jwt_token)
        positions = order_mgr.get_positions(request.remote_addr or "127.0.0.1")
        
        return https_fn.Response(
            json.dumps({"status": "success", "data": positions}),
            status=200
        )
        
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        return https_fn.Response(
            json.dumps({"error": str(e)}),
            status=500
        )
