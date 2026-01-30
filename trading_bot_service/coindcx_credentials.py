"""
CoinDCX Credentials Management
==============================
Secure storage and retrieval of CoinDCX API credentials.
"""

import logging
from typing import Optional, Dict
from firebase_admin import firestore
from cryptography.fernet import Fernet
import os

logger = logging.getLogger(__name__)


class CoinDCXCredentials:
    """Manage CoinDCX API credentials in Firestore"""
    
    # Encryption key (should be stored in environment variable in production)
    ENCRYPTION_KEY = os.getenv('CREDENTIALS_ENCRYPTION_KEY', Fernet.generate_key())
    
    @staticmethod
    def save_credentials(user_id: str, api_key: str, api_secret: str, 
                        firestore_client=None) -> bool:
        """
        Save CoinDCX credentials to Firestore (encrypted).
        
        Args:
            user_id: User identifier
            api_key: CoinDCX API key
            api_secret: CoinDCX API secret
            firestore_client: Firestore client
            
        Returns:
            True if successful
        """
        try:
            db = firestore_client or firestore.client()
            
            # Encrypt API secret
            fernet = Fernet(CoinDCXCredentials.ENCRYPTION_KEY)
            encrypted_secret = fernet.encrypt(api_secret.encode()).decode()
            
            # Save to Firestore
            doc_ref = db.collection('coindcx_credentials').document(user_id)
            doc_ref.set({
                'api_key': api_key,
                'api_secret_encrypted': encrypted_secret,
                'enabled': True,
                'timestamp': firestore.SERVER_TIMESTAMP
            })
            
            logger.info(f"✅ CoinDCX credentials saved for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save credentials: {e}")
            return False
    
    @staticmethod
    def get_credentials(user_id: str, firestore_client=None) -> Optional[Dict]:
        """
        Get CoinDCX credentials from Firestore (decrypted).
        
        Args:
            user_id: User identifier
            firestore_client: Firestore client
            
        Returns:
            Dict with api_key and api_secret, or None if not found
        """
        try:
            db = firestore_client or firestore.client()
            
            # Get from Firestore
            doc_ref = db.collection('coindcx_credentials').document(user_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                logger.warning(f"⚠️  No CoinDCX credentials found for user {user_id}")
                return None
            
            data = doc.to_dict()
            
            if not data.get('enabled', False):
                logger.warning(f"⚠️  CoinDCX credentials disabled for user {user_id}")
                return None
            
            # Decrypt API secret
            fernet = Fernet(CoinDCXCredentials.ENCRYPTION_KEY)
            encrypted_secret = data['api_secret_encrypted']
            api_secret = fernet.decrypt(encrypted_secret.encode()).decode()
            
            logger.info(f"✅ CoinDCX credentials retrieved for user {user_id}")
            
            return {
                'api_key': data['api_key'],
                'api_secret': api_secret
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get credentials: {e}")
            return None
    
    @staticmethod
    def delete_credentials(user_id: str, firestore_client=None) -> bool:
        """
        Delete CoinDCX credentials from Firestore.
        
        Args:
            user_id: User identifier
            firestore_client: Firestore client
            
        Returns:
            True if successful
        """
        try:
            db = firestore_client or firestore.client()
            
            doc_ref = db.collection('coindcx_credentials').document(user_id)
            doc_ref.delete()
            
            logger.info(f"✅ CoinDCX credentials deleted for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete credentials: {e}")
            return False
    
    @staticmethod
    def disable_credentials(user_id: str, firestore_client=None) -> bool:
        """
        Disable CoinDCX credentials (soft delete).
        
        Args:
            user_id: User identifier
            firestore_client: Firestore client
            
        Returns:
            True if successful
        """
        try:
            db = firestore_client or firestore.client()
            
            doc_ref = db.collection('coindcx_credentials').document(user_id)
            doc_ref.update({'enabled': False})
            
            logger.info(f"✅ CoinDCX credentials disabled for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to disable credentials: {e}")
            return False
