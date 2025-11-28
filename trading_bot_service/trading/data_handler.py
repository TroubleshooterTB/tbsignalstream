# src/trading/data_handler.py

import os
import logging
from SmartApi import SmartConnect
# Configuration moved inline (no src module in trading_bot_service)
ANGEL_ONE_API = {
    'API_KEY_HISTORICAL': 'YOUR_HISTORICAL_API_KEY_HERE',
    'API_KEY_TRADING': 'YOUR_TRADING_API_KEY_HERE',
}

class DataHandler:
    """
    Manages all communication with the Angel One SmartAPI, including
    authentication, token generation, and data fetching.
    """
    def __init__(self):
        # Use normalized config lookup (supports multiple env var name variants)
        self.api_key = ANGEL_ONE_API.get('API_KEY_TRADING')
        self.client_code = ANGEL_ONE_API.get('CLIENT_CODE')
        self.angel_one_password = ANGEL_ONE_API.get('PASSWORD')
        # TOTP token name in config is 'TOTP_TOKEN' (supports both TOKEN and SECRET variants)
        self.totp_secret = ANGEL_ONE_API.get('TOTP_TOKEN')

        if not all([self.api_key, self.client_code, self.totp_secret, self.angel_one_password]):
            raise ValueError("One or more Angel One credentials are not set in the environment.")

        # Initialize SmartAPI client
        self.smart_connect = SmartConnect(self.api_key)
        self.jwt_token = None
        self.refresh_token = None
        self.feed_token = None
        
        logging.info("DataHandler initialized.")

    def generate_daily_session(self):
        """
        Performs the daily login to generate the auth, refresh, and JWT tokens.
        This must be called once at the start of each trading day.
        """
        try:
            # Note: Angel One's TOTP generation logic would need to be implemented here.
            # For this example, we'll assume a placeholder for the TOTP.
            # In a real scenario, you'd use a library like 'pyotp'.
            import pyotp
            totp = pyotp.TOTP(self.totp_secret).now()

            logging.info("Attempting to generate daily session...")
            data = self.smart_connect.generateSession(self.client_code, self.angel_one_password, totp)

            if data['status'] and data['data']:
                self.jwt_token = data['data']['jwtToken']
                self.refresh_token = data['data']['refreshToken']
                self.feed_token = self.smart_connect.getfeedToken()
                logging.info("Session generated successfully. JWT and Feed Token obtained.")
                return True
            else:
                logging.error(f"Failed to generate session: {data['message']}")
                return False

        except Exception as e:
            logging.error(f"An error occurred during session generation: {e}")
            return False

    def get_jwt_token(self):
        return self.jwt_token

    def get_feed_token(self):
        return self.feed_token
        
    def fetch_latest_market_data(self):
        """
        Placeholder for fetching latest OHLCV data for the watchlist.
        """
        # In a real implementation, you would use the self.jwt_token
        # to make API calls to get historical or live data.
        logging.info("Fetching latest market data for watchlist...")
        # This would return a dictionary of symbol -> data
        return {} # Replace with actual data fetching logic

    def get_market_health(self):
        # Placeholder
        return "Neutral"

    def get_sector_performance(self, symbol):
        # Placeholder
        return "Neutral"