"""
Clear Old Firestore Trading Signals
Removes stale/test signals from previous hardcoded implementation
Run this locally to clean up old data
"""

import firebase_admin
from firebase_admin import credentials, firestore
import sys
from datetime import datetime

def clear_old_signals():
    """Delete all documents in trading_signals collection"""
    
    print("🔥 Firestore Signal Cleanup Tool")
    print("=" * 50)
    
    # Initialize Firebase Admin
    if not firebase_admin._apps:
        try:
            # Use Application Default Credentials
            firebase_admin.initialize_app()
            print("✅ Firebase initialized with default credentials")
        except Exception as e:
            print(f"❌ Failed to initialize Firebase: {e}")
            print("\nPlease run: gcloud auth application-default login")
            sys.exit(1)
    
    db = firestore.client()
    
    # Get all signals
    signals_ref = db.collection('trading_signals')
    
    print("\n📊 Fetching existing signals...")
    
    try:
        docs = list(signals_ref.stream())
        total_count = len(docs)
        
        if total_count == 0:
            print("✅ No signals found - collection is already clean!")
            return
        
        print(f"Found {total_count} signals to delete:")
        print("-" * 50)
        
        # Show sample of what will be deleted
        for i, doc in enumerate(docs[:5]):  # Show first 5
            data = doc.to_dict()
            symbol = data.get('symbol', 'UNKNOWN')
            signal_type = data.get('type', 'UNKNOWN')
            timestamp = data.get('timestamp', 'N/A')
            print(f"  {i+1}. {symbol} - {signal_type} @ {timestamp}")
        
        if total_count > 5:
            print(f"  ... and {total_count - 5} more")
        
        print("-" * 50)
        
        # Confirm deletion
        response = input(f"\n⚠️  Delete all {total_count} signals? (yes/no): ").strip().lower()
        
        if response != 'yes':
            print("❌ Deletion cancelled")
            return
        
        # Delete all documents
        print(f"\n🗑️  Deleting {total_count} signals...")
        
        deleted_count = 0
        failed_count = 0
        
        for doc in docs:
            try:
                doc.reference.delete()
                deleted_count += 1
                if deleted_count % 10 == 0:
                    print(f"  Deleted {deleted_count}/{total_count}...")
            except Exception as e:
                print(f"  ❌ Failed to delete {doc.id}: {e}")
                failed_count += 1
        
        print("\n" + "=" * 50)
        print(f"✅ Cleanup complete!")
        print(f"  Deleted: {deleted_count}")
        print(f"  Failed: {failed_count}")
        print("=" * 50)
        
        if deleted_count > 0:
            print("\n💡 Next steps:")
            print("  1. Clear browser cache (Ctrl+Shift+Delete)")
            print("  2. Hard reload dashboard (Ctrl+Shift+R)")
            print("  3. Start trading bot via dashboard")
            print("  4. New signals will appear when bot finds patterns")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        clear_old_signals()
    except KeyboardInterrupt:
        print("\n\n❌ Cleanup interrupted by user")
        sys.exit(1)
