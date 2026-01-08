#!/usr/bin/env python3
"""
Comprehensive Activity Feed Diagnostics
Checks why bot activity is not showing on dashboard
"""

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
import sys

print("=" * 80)
print("BOT ACTIVITY FEED DIAGNOSTICS")
print("=" * 80)

try:
    # Initialize Firebase
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {
        'projectId': 'tbsignalstream',
    })
    db = firestore.client()
    print("✅ Firebase initialized")
except Exception as e:
    print(f"❌ Firebase initialization failed: {e}")
    sys.exit(1)

# Check 1: Bot Configs (Is bot running?)
print("\n" + "=" * 80)
print("CHECK 1: BOT STATUS IN FIRESTORE")
print("=" * 80)

bot_configs = db.collection('bot_configs').stream()
bot_running = False
user_id = None

for doc in bot_configs:
    data = doc.to_dict()
    user_id = doc.id
    is_running = data.get('is_running', False)
    status = data.get('status', 'N/A')
    
    print(f"\n📋 User: {user_id}")
    print(f"   Status: {status}")
    print(f"   Is Running: {is_running}")
    print(f"   Last Started: {data.get('last_started', 'Never')}")
    
    if is_running or status == 'running':
        bot_running = True
        print("   ✅ Bot is RUNNING")
    else:
        print("   ❌ Bot is STOPPED - This is the problem!")
        print("   💡 Solution: Click 'Start Trading Bot' on the dashboard")

if not bot_running:
    print("\n" + "⚠️ " * 20)
    print("CRITICAL: BOT IS NOT RUNNING!")
    print("⚠️ " * 20)
    print("\nNo bot instance means:")
    print("  ❌ No scanning")
    print("  ❌ No pattern detection")
    print("  ❌ No activity logs")
    print("  ❌ Activity feed will stay empty")
    print("\n👉 ACTION REQUIRED: Start the bot from the dashboard")

# Check 2: Bot Activity Collection
print("\n" + "=" * 80)
print("CHECK 2: BOT ACTIVITY COLLECTION")
print("=" * 80)

# Recent activities (last 1 hour)
one_hour_ago = datetime.now() - timedelta(hours=1)
activities = db.collection('bot_activity').where(
    'timestamp', '>=', one_hour_ago
).order_by('timestamp', direction=firestore.Query.DESCENDING).limit(20).stream()

activity_list = list(activities)
print(f"\n📊 Found {len(activity_list)} activities in last hour")

if len(activity_list) == 0:
    print("❌ No activities found - Bot is not logging")
    print("\nPossible reasons:")
    print("  1. Bot is not running (see CHECK 1)")
    print("  2. Bot is running but activity logger is disabled")
    print("  3. Bot is running but Firestore write permissions issue")
else:
    print(f"✅ Bot IS logging activities!")
    print("\nRecent activities:")
    for i, doc in enumerate(activity_list[:5], 1):
        data = doc.to_dict()
        timestamp = data.get('timestamp', 'Unknown')
        activity_type = data.get('type', 'Unknown')
        symbol = data.get('symbol', 'N/A')
        
        print(f"\n  {i}. {timestamp}")
        print(f"     Type: {activity_type}")
        print(f"     Symbol: {symbol}")
        if 'pattern' in data:
            print(f"     Pattern: {data['pattern']}")
        if 'reason' in data:
            print(f"     Reason: {data['reason']}")

# Check 3: Activity by Type
print("\n" + "=" * 80)
print("CHECK 3: ACTIVITY BREAKDOWN (Last 24 hours)")
print("=" * 80)

yesterday = datetime.now() - timedelta(hours=24)
all_activities = db.collection('bot_activity').where(
    'timestamp', '>=', yesterday
).stream()

type_counts = {}
for doc in all_activities:
    data = doc.to_dict()
    activity_type = data.get('type', 'unknown')
    type_counts[activity_type] = type_counts.get(activity_type, 0) + 1

if type_counts:
    print("\n📊 Activity Types:")
    for activity_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {activity_type:30} : {count:5} occurrences")
else:
    print("❌ No activities in last 24 hours")

# Check 4: Firestore Rules
print("\n" + "=" * 80)
print("CHECK 4: FIRESTORE PERMISSIONS")
print("=" * 80)

try:
    # Try to write a test activity
    test_doc_ref = db.collection('bot_activity').document('_test_write')
    test_doc_ref.set({
        'user_id': user_id or 'test_user',
        'timestamp': firestore.SERVER_TIMESTAMP,
        'type': 'test',
        'symbol': 'TEST',
        'message': 'Test write from diagnostic script'
    })
    print("✅ Write test PASSED - Firestore allows writes to bot_activity")
    
    # Clean up test document
    test_doc_ref.delete()
    print("✅ Cleanup successful")
    
except Exception as e:
    print(f"❌ Write test FAILED: {e}")
    print("\n💡 Firestore rules may be blocking writes")
    print("   Check: firestore.rules - bot_activity collection needs write permission")

# Check 5: User-specific activities
if user_id:
    print("\n" + "=" * 80)
    print(f"CHECK 5: USER-SPECIFIC ACTIVITIES ({user_id})")
    print("=" * 80)
    
    user_activities = db.collection('bot_activity').where(
        'user_id', '==', user_id
    ).order_by('timestamp', direction=firestore.Query.DESCENDING).limit(10).stream()
    
    user_activity_list = list(user_activities)
    print(f"\n📊 Found {len(user_activity_list)} activities for this user")
    
    if len(user_activity_list) > 0:
        print("\nMost recent:")
        for i, doc in enumerate(user_activity_list[:3], 1):
            data = doc.to_dict()
            print(f"  {i}. {data.get('timestamp')} - {data.get('type')} - {data.get('symbol')}")
    else:
        print("❌ No activities for this user")

# Final Summary
print("\n" + "=" * 80)
print("DIAGNOSTIC SUMMARY")
print("=" * 80)

issues = []
solutions = []

if not bot_running:
    issues.append("❌ Bot is not running")
    solutions.append("👉 Click 'Start Trading Bot' on the dashboard")

if len(activity_list) == 0:
    issues.append("❌ No activities logged in last hour")
    if bot_running:
        solutions.append("👉 Check Cloud Run logs: gcloud logging read ...")
        solutions.append("👉 Verify activity logger is initialized in bot code")

if not issues:
    print("\n✅ All checks passed!")
    print("\nIf dashboard still shows 'Waiting for bot activity...':")
    print("  1. Check browser console for errors (F12)")
    print("  2. Verify frontend is listening to 'bot_activity' collection")
    print("  3. Clear browser cache and reload")
    print("  4. Check if user_id filter matches in frontend query")
else:
    print("\n🔴 Issues Found:")
    for issue in issues:
        print(f"  {issue}")
    
    print("\n💡 Solutions:")
    for solution in solutions:
        print(f"  {solution}")

print("\n" + "=" * 80)
print("To check Cloud Run logs:")
print("gcloud logging read \"resource.type=cloud_run_revision\" --limit=50 --format=\"value(timestamp,textPayload)\"")
print("=" * 80)
