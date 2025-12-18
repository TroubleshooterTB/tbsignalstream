"""
Quick check of Firestore collections and authentication setup
"""

from google.cloud import firestore
import os

db = firestore.Client()

print("\n" + "="*80)
print("🔍 FIRESTORE STRUCTURE CHECK")
print("="*80)

# List all collections
print("\n📂 Available Collections:")
collections = list(db.collections())
if not collections:
    print("   ❌ NO COLLECTIONS FOUND!")
    print("   → Firestore may not be initialized")
    print("   → Or permissions issue")
else:
    for coll in collections:
        count = len(list(coll.limit(5).stream()))
        print(f"   • {coll.id}: {count}+ documents")

print("\n" + "="*80)
print("🔐 AUTHENTICATION CHECK")
print("="*80)

# Check Firebase config
print("\n📋 Environment Variables:")
project_id = os.environ.get('GOOGLE_CLOUD_PROJECT') or os.environ.get('GCP_PROJECT')
print(f"   Project ID: {project_id or 'NOT SET'}")

creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
print(f"   Credentials: {creds_path or 'NOT SET'}")

print("\n" + "="*80)
print("💡 RECOMMENDATION")
print("="*80)

if not collections or len([c for c in collections if c.id == 'users']) == 0:
    print("""
❌ CRITICAL: Firestore not set up correctly

Your system has NEVER been used because:
   • No user authentication completed
   • No Firestore collections initialized
   • Dashboard UI works but backend is disconnected

TO FIX - You need to:

1. DEPLOY THE SYSTEM PROPERLY
   ────────────────────────────
   Your code is ready but NOT deployed to production.
   
   The dashboard you're seeing is running locally but has no backend.
   
   You need to:
   • Deploy to Firebase/Google Cloud
   • Set up Firestore database
   • Configure authentication
   • Deploy Cloud Functions

2. OR RUN LOCALLY FOR TESTING
   ────────────────────────────
   If you want to test without cloud deployment:
   
   • Set up local Firestore emulator
   • Configure local authentication
   • Run backend services locally
   
   This is complex - better to deploy to cloud first.

3. IMMEDIATE ACTION
   ────────────────────────────
   Read: DEPLOYMENT_SUCCESS.md or DEPLOYMENT_READY_GUIDE.md
   
   These files have complete deployment instructions.
   
   The bot will NOT work until properly deployed!
""")
else:
    print("""
✅ Firestore exists but user not registered

You need to:
   1. Open dashboard in browser
   2. Sign up / Sign in with email
   3. Complete Angel One connection
   4. THEN start the bot
""")

print("\n" + "="*80)
