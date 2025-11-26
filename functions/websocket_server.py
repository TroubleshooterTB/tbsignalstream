"""
WebSocket Server for Real-Time Market Data
Runs as a Cloud Function to manage WebSocket connections and stream data to clients
"""

import os
import json
import logging
from typing import Dict, Set
import firebase_admin
from firebase_admin import firestore, auth
from firebase_functions import https_fn, options
from src.config import ANGEL_ONE_API
from src.websocket.websocket_manager_v2 import AngelWebSocketV2Manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Firebase if not already initialized
if not firebase_admin._apps:
    firebase_admin.initialize_app()

# Store active WebSocket connections per user
active_connections: Dict[str, AngelWebSocketV2Manager] = {}


def _get_db():
    """Lazy initialization of Firestore client"""
    return firestore.client()


@https_fn.on_request(
    cors=options.CorsOptions(cors_origins="*", cors_methods=["post"]),
    memory=options.MemoryOption.GB_1,
    timeout_sec=540
)
def initializeWebSocket(request: https_fn.Request) -> https_fn.Response:
    """
    Initialize WebSocket connection for a user.
    This endpoint starts the WebSocket connection and subscribes to tokens.
    """
    try:
        # Verify Firebase ID token
        id_token = request.headers.get('Authorization', '').split('Bearer ')[-1]
        if not id_token:
            return https_fn.Response(
                json.dumps({"error": "Authentication required"}),
                status=401
            )
        
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        
        # Get request data
        data = request.get_json() or {}
        tokens_to_subscribe = data.get('tokens', [])
        mode = data.get('mode', 1)  # 1=LTP, 2=Quote, 3=Snap Quote
        
        # Get user's Angel One credentials
        user_doc = _get_db().collection('angel_one_credentials').document(uid).get()
        if not user_doc.exists:
            return https_fn.Response(
                json.dumps({"error": "Angel One not connected"}),
                status=403
            )
        
        user_data = user_doc.to_dict()
        feed_token = user_data.get('feed_token')
        client_code = user_data.get('client_code')
        jwt_token = user_data.get('jwt_token')
        
        if not feed_token or not client_code or not jwt_token:
            return https_fn.Response(
                json.dumps({"error": "Invalid credentials - missing feed_token, client_code, or jwt_token"}),
                status=403
            )
        
        # Get API key
        api_key = ANGEL_ONE_API.get('API_KEY_TRADING')
        if not api_key:
            return https_fn.Response(
                json.dumps({"error": "Server configuration error"}),
                status=500
            )
        
        # Check if connection already exists
        if uid in active_connections:
            logger.info(f"Reusing existing WebSocket for user {uid}")
            ws_manager = active_connections[uid]
        else:
            # Create new WebSocket connection using v2 protocol
            logger.info(f"Creating new WebSocket v2 connection for user {uid}")
            ws_manager = AngelWebSocketV2Manager(api_key, client_code, feed_token, jwt_token)
            
            # Add callback to store ticks in Firestore
            def tick_callback(tick_data):
                try:
                    # Store latest ticks for this user
                    _get_db().collection('live_ticks').document(uid).set({
                        'data': tick_data,
                        'timestamp': firestore.SERVER_TIMESTAMP
                    }, merge=True)
                except Exception as e:
                    logger.error(f"Error storing tick data: {e}")
            
            ws_manager.add_tick_callback(tick_callback)
            
            # Connect WebSocket
            if not ws_manager.connect():
                return https_fn.Response(
                    json.dumps({"error": "Failed to connect WebSocket"}),
                    status=500
                )
            
            active_connections[uid] = ws_manager
        
        # Subscribe to tokens if provided
        if tokens_to_subscribe:
            success = ws_manager.subscribe(mode, tokens_to_subscribe)
            if not success:
                return https_fn.Response(
                    json.dumps({"error": "Failed to subscribe to tokens"}),
                    status=500
                )
        
        return https_fn.Response(
            json.dumps({
                "status": "success",
                "message": "WebSocket initialized",
                "subscribed_tokens": list(ws_manager.subscribed_tokens)
            }),
            status=200
        )
        
    except Exception as e:
        logger.error(f"Error initializing WebSocket: {e}")
        return https_fn.Response(
            json.dumps({"error": str(e)}),
            status=500
        )


@https_fn.on_request(
    cors=options.CorsOptions(cors_origins="*", cors_methods=["post"])
)
def subscribeWebSocket(request: https_fn.Request) -> https_fn.Response:
    """
    Subscribe to additional tokens on existing WebSocket connection.
    """
    try:
        # Verify user
        id_token = request.headers.get('Authorization', '').split('Bearer ')[-1]
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        
        # Get request data
        data = request.get_json() or {}
        tokens = data.get('tokens', [])
        mode = data.get('mode', 1)
        
        # Get WebSocket connection
        if uid not in active_connections:
            return https_fn.Response(
                json.dumps({"error": "WebSocket not initialized"}),
                status=400
            )
        
        ws_manager = active_connections[uid]
        
        # Subscribe
        success = ws_manager.subscribe(mode, tokens)
        
        return https_fn.Response(
            json.dumps({
                "status": "success" if success else "failed",
                "subscribed_tokens": list(ws_manager.subscribed_tokens)
            }),
            status=200 if success else 500
        )
        
    except Exception as e:
        logger.error(f"Error subscribing: {e}")
        return https_fn.Response(
            json.dumps({"error": str(e)}),
            status=500
        )


@https_fn.on_request(
    cors=options.CorsOptions(cors_origins="*", cors_methods=["post"])
)
def closeWebSocket(request: https_fn.Request) -> https_fn.Response:
    """
    Close WebSocket connection for a user.
    """
    try:
        # Verify user
        id_token = request.headers.get('Authorization', '').split('Bearer ')[-1]
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        
        # Get WebSocket connection
        if uid in active_connections:
            ws_manager = active_connections[uid]
            ws_manager.disconnect()
            del active_connections[uid]
            
            return https_fn.Response(
                json.dumps({"status": "success", "message": "WebSocket closed"}),
                status=200
            )
        else:
            return https_fn.Response(
                json.dumps({"status": "success", "message": "No active connection"}),
                status=200
            )
        
    except Exception as e:
        logger.error(f"Error closing WebSocket: {e}")
        return https_fn.Response(
            json.dumps({"error": str(e)}),
            status=500
        )
