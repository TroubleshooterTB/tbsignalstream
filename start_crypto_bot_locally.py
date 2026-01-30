"""
Start Crypto Bot Locally for Testing
====================================
Test CoinDCX crypto bot on your local machine before deploying to production.

Usage:
    python start_crypto_bot_locally.py --user <user_id> --pair <BTC|ETH>
    
Example:
    python start_crypto_bot_locally.py --user test_user --pair BTC
"""

import asyncio
import argparse
import logging
import sys
import os
import io
from datetime import datetime

# Force UTF-8 output on Windows for emoji support
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Firebase setup
import firebase_admin
from firebase_admin import credentials, firestore

# Import crypto bot
from trading_bot_service.crypto_bot_engine import CryptoBotEngine
from trading_bot_service.coindcx_credentials import CoinDCXCredentials

# Setup logging with UTF-8 encoding for emoji support
import sys
import io

# Force UTF-8 output on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'crypto_bot_local_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)


def init_firebase():
    """Initialize Firebase"""
    try:
        # Check if already initialized
        firebase_admin.get_app()
        logger.info("✅ Firebase already initialized")
    except ValueError:
        # Initialize with service account
        cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '../firestore-key.json')
        
        # Try current directory first, then parent
        if not os.path.exists(cred_path):
            cred_path = 'firestore-key.json'
        
        if not os.path.exists(cred_path):
            logger.error(f"Firebase credentials not found in current or parent directory")
            logger.error("   Set GOOGLE_APPLICATION_CREDENTIALS environment variable")
            sys.exit(1)
        
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        logger.info("✅ Firebase initialized")


async def main(user_id: str, initial_pair: str):
    """
    Start crypto bot locally.
    
    Args:
        user_id: User identifier
        initial_pair: Starting trading pair ("BTC" or "ETH")
    """
    running_flag = asyncio.Event()
    running_flag.set()
    
    try:
        logger.info("="*70)
        logger.info("🚀 STARTING CRYPTO BOT LOCALLY")
        logger.info("="*70)
        logger.info(f"User: {user_id}")
        logger.info(f"Initial Pair: {initial_pair}")
        logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*70)
        
        # Initialize Firebase
        init_firebase()
        
        # Get CoinDCX credentials from Firestore
        logger.info("🔐 Retrieving CoinDCX credentials...")
        creds = CoinDCXCredentials.get_credentials(user_id)
        
        if not creds:
            logger.error("❌ No CoinDCX credentials found!")
            logger.error(f"   Please add credentials for user '{user_id}' to Firestore")
            logger.error(f"   Collection: coindcx_credentials")
            logger.error(f"   Document: {user_id}")
            logger.error(f"   Fields:")
            logger.error(f"     - api_key: <your_coindcx_api_key>")
            logger.error(f"     - api_secret_encrypted: <encrypted_secret>")
            logger.error(f"     - enabled: true")
            sys.exit(1)
        
        logger.info("✅ Credentials retrieved")
        logger.info(f"   API Key: {creds['api_key'][:8]}...")
        
        # Create bot instance
        logger.info("🤖 Creating crypto bot instance...")
        bot = CryptoBotEngine(
            user_id=user_id,
            api_key=creds['api_key'],
            api_secret=creds['api_secret'],
            initial_pair=initial_pair
        )
        
        # Start bot
        logger.info("▶️  Starting bot...")
        await bot.start(running_flag)
        
    except KeyboardInterrupt:
        logger.info("\n⚠️  Keyboard interrupt received - stopping bot...")
        running_flag.clear()
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        running_flag.clear()
        sys.exit(1)


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Start CoinDCX crypto trading bot locally',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start with BTC
  python start_crypto_bot_locally.py --user test_user --pair BTC
  
  # Start with ETH
  python start_crypto_bot_locally.py --user test_user --pair ETH
  
  # Use custom credentials file
  GOOGLE_APPLICATION_CREDENTIALS=my-creds.json python start_crypto_bot_locally.py --user test_user --pair BTC

Environment Variables:
  GOOGLE_APPLICATION_CREDENTIALS  Path to Firebase service account key (default: firestore-key.json)
  CREDENTIALS_ENCRYPTION_KEY      Encryption key for API secrets

Notes:
  - Bot runs 24/7 (no market hours restrictions)
  - Press Ctrl+C to stop gracefully
  - Check logs in crypto_bot_local_YYYYMMDD_HHMMSS.log
  - Requires CoinDCX credentials in Firestore (collection: coindcx_credentials)
        """
    )
    
    parser.add_argument(
        '--user',
        type=str,
        required=True,
        help='User ID (must have credentials in Firestore)'
    )
    
    parser.add_argument(
        '--pair',
        type=str,
        choices=['BTC', 'ETH'],
        default='BTC',
        help='Initial trading pair (default: BTC)'
    )
    
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║               🚀 24/7 CRYPTO TRADING BOT (LOCAL)                ║
║                                                                  ║
║  Exchange: CoinDCX                                               ║
║  Pairs: BTC/USDT, ETH/USDT                                       ║
║  Hours: 24/7 (no restrictions)                                   ║
║                                                                  ║
║  Press Ctrl+C to stop gracefully                                 ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        asyncio.run(main(args.user, args.pair))
    except KeyboardInterrupt:
        print("\n✅ Bot stopped by user")
        sys.exit(0)
