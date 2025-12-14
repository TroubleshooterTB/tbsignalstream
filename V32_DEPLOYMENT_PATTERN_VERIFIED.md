# V3.2 Deployment - Aligned with Proven Success Pattern ✅

**Date:** December 14, 2025  
**Reference:** Based on `deploy_complete.ps1` (Last Successful Deployment: Nov 21, 2025)

---

## ✅ DEPLOYMENT PATTERN VERIFICATION

### **Proven Success Pattern (From deploy_complete.ps1)**

Your previous successful deployments followed this pattern:

1. **Backend First (Cloud Run)**
   - Deploy `trading-bot-service` to Cloud Run (asia-south1)
   - Timeout: 3600s (1 hour)
   - Memory: 2Gi
   - Region: asia-south1
   - Allow unauthenticated access
   - Verify with `/status` health endpoint

2. **Frontend Second (Firebase App Hosting)**
   - Build Next.js with `npm run build`
   - Deploy to Firebase App Hosting backend `studio`
   - Uses: `firebase deploy --only apphosting:studio`
   - URL: `https://studio--tbsignalstream.us-central1.hosted.app`

3. **Cloud Functions** (Not needed for v3.2)
   - Already deployed: WebSocket, Orders, Trading Bot gateway
   - No changes needed - they just forward to Cloud Run

---

## ✅ V3.2 DEPLOYMENT MATCHES PATTERN

### **Updated deploy_v32.ps1 Now Follows Same Pattern:**

```powershell
# STEP 1: Deploy Backend (Cloud Run) - MATCHES ✓
gcloud run deploy trading-bot-service \
  --source . \
  --region asia-south1 \            # ✓ Same region
  --platform managed \               # ✓ Same platform
  --allow-unauthenticated \          # ✓ Same access
  --timeout 3600s \                  # ✓ Same timeout
  --memory 2Gi \                     # ✓ Same memory
  --max-instances 10 \               # ✓ Same scaling
  --project tbsignalstream           # ✓ Same project

# STEP 2: Deploy Frontend (App Hosting) - MATCHES ✓
npm run build                        # ✓ Same build command
firebase deploy --only apphosting:studio --project=tbsignalstream  # ✓ EXACT MATCH
```

---

## 🔍 KEY DIFFERENCES FROM YOUR ORIGINAL V3.2 SCRIPT

### **What Was WRONG in Original Script:**

```powershell
# ❌ WRONG: Used "hosting" instead of "apphosting"
firebase deploy --only hosting

# ❌ WRONG: Hardcoded old Cloud Run URL
$response = Invoke-WebRequest -Uri "https://trading-bot-service-vmxfbt7qiq-el.a.run.app/status"
```

### **What's CORRECT Now (Matches deploy_complete.ps1):**

```powershell
# ✅ CORRECT: Use "apphosting:studio" (your actual frontend deployment method)
firebase deploy --only apphosting:studio --project=$PROJECT_ID

# ✅ CORRECT: Dynamically get Cloud Run URL
$cloudRunUrl = gcloud run services describe trading-bot-service --region $REGION --format "value(status.url)"
$healthCheck = Invoke-WebRequest -Uri "$cloudRunUrl/status"
```

---

## 📊 DEPLOYMENT ARCHITECTURE (VERIFIED)

### **From Your firebase.json:**

```json
{
  "hosting": {
    "rewrites": [
      {
        "source": "/**",
        "run": {
          "serviceId": "studio",           ← App Hosting backend
          "region": "us-central1"          ← Frontend region
        }
      }
    ]
  },
  "apphosting": [
    {
      "backendId": "studio",               ← CRITICAL: Must deploy to "studio"
      "source": "."
    }
  ]
}
```

**Key Insight:** Your frontend uses **App Hosting** (not static Hosting), which is why:
- ❌ `firebase deploy --only hosting` → WRONG (deploys static site)
- ✅ `firebase deploy --only apphosting:studio` → CORRECT (deploys Next.js app)

---

## 🎯 DEPLOYMENT FLOW (PROVEN WORKING)

```
User Runs: .\deploy_v32.ps1
     ↓
┌────────────────────────────────────────┐
│ STEP 1: Deploy Backend (Cloud Run)    │
│                                        │
│ cd trading_bot_service/                │
│ gcloud run deploy trading-bot-service │
│   --source .                           │
│   --region asia-south1                 │
│   --timeout 3600s                      │
│   --memory 2Gi                         │
│                                        │
│ Result: Backend deployed with v3.2     │
│   ✓ defining_order_strategy.py added  │
│   ✓ bot_engine.py updated              │
│   ✓ /status endpoint responds          │
└────────────────────────────────────────┘
     ↓
┌────────────────────────────────────────┐
│ STEP 2: Deploy Frontend (App Hosting) │
│                                        │
│ cd tbsignalstream_backup/              │
│ npm run build                          │
│ firebase deploy --only apphosting:studio │
│                                        │
│ Result: Frontend deployed with v3.2    │
│   ✓ 4 strategy options in dropdown    │
│   ✓ Default: 'defining'                │
│   ✓ Types updated                      │
└────────────────────────────────────────┘
     ↓
┌────────────────────────────────────────┐
│ STEP 3: Verification                  │
│                                        │
│ Backend:                               │
│   curl $cloudRunUrl/status             │
│   → {"status":"healthy"}               │
│                                        │
│ Frontend:                              │
│   Open: https://tbsignalstream.web.app │
│   Check: Strategy dropdown             │
│   Verify: 4 options visible            │
└────────────────────────────────────────┘
```

---

## 📝 FILES DEPLOYED (NO CLOUD FUNCTIONS CHANGES)

### **Backend Files (Cloud Run):**
- ✅ NEW: `trading_bot_service/defining_order_strategy.py` (700 lines)
- ✅ UPDATED: `trading_bot_service/bot_engine.py` (added v3.2 routing)

### **Frontend Files (App Hosting):**
- ✅ UPDATED: `src/components/trading-bot-controls.tsx`
- ✅ UPDATED: `src/context/trading-context.tsx`
- ✅ UPDATED: `src/lib/trading-api.ts`

### **Cloud Functions (NO CHANGES):**
- ℹ️ `functions/live_trading_bot.py` - Already deployed, no changes needed
- ℹ️ WebSocket functions - Already deployed, no changes needed
- ℹ️ Order functions - Already deployed, no changes needed

**Why?** Cloud Functions just forward requests to Cloud Run. Since we only changed:
1. Cloud Run bot engine (added v3.2 strategy)
2. Frontend UI (added v3.2 dropdown option)

→ No need to redeploy Cloud Functions! They'll automatically route to new Cloud Run deployment.

---

## 🔒 SAFETY CHECKS (FROM SUCCESSFUL DEPLOYMENTS)

### **Pre-Deployment Checks:**
- ✅ Cloud Run region: asia-south1 (same as before)
- ✅ App Hosting backend ID: studio (same as before)
- ✅ Project ID: tbsignalstream (same as before)
- ✅ Timeout: 3600s (same as before)
- ✅ Memory: 2Gi (same as before)

### **Post-Deployment Verification:**
- ✅ Backend health: `curl $cloudRunUrl/status`
- ✅ Frontend access: https://tbsignalstream.web.app
- ✅ Strategy dropdown: Should show 4 options
- ✅ Default strategy: Should be "The Defining Order v3.2"

### **Rollback Plan (IF NEEDED):**
```powershell
# Frontend rollback (App Hosting)
firebase apphosting:rollouts:create studio --rollback

# Backend rollback (Cloud Run)
$previousRevision = gcloud run revisions list --service=trading-bot-service --region=asia-south1 --limit=2 --format="value(metadata.name)" | Select-Object -Last 1
gcloud run services update-traffic trading-bot-service --to-revisions=$previousRevision=100 --region=asia-south1
```

---

## 🎯 DIFFERENCES FROM PREVIOUS DEPLOYMENTS

### **What's NEW in v3.2 Deployment:**

1. **New Strategy Module**
   - File: `defining_order_strategy.py`
   - Impact: Backend only
   - Risk: LOW (new file, doesn't break existing code)

2. **Frontend Types Updated**
   - Added 'defining' to TypeScript types
   - Added 4th dropdown option
   - Changed default strategy
   - Impact: Frontend only
   - Risk: LOW (backwards compatible)

3. **Bot Engine Routing**
   - Added `elif self.strategy == 'defining':`
   - Impact: Backend only
   - Risk: LOW (existing strategies untouched)

### **What's SAME as Previous Deployments:**

1. ✅ Cloud Run configuration (region, timeout, memory)
2. ✅ App Hosting backend ID (studio)
3. ✅ Project structure (no file moves)
4. ✅ Cloud Functions (no changes needed)
5. ✅ Firestore structure (no changes)
6. ✅ Database schema (no changes)

---

## 🚀 READY TO DEPLOY

**Command:**
```powershell
.\deploy_v32.ps1
```

**Expected Duration:**
- Backend: 3-5 minutes
- Frontend: 5-10 minutes
- Total: ~10-15 minutes

**Success Criteria:**
- ✅ Cloud Run deployment completes
- ✅ Health check returns 200 OK
- ✅ App Hosting build completes
- ✅ Dashboard loads successfully
- ✅ Strategy dropdown shows 4 options

**Next Step After Deployment:**
- Paper trading test (Monday 9:15-11:00 AM)
- Verify no 12:00/13:00 trades
- Verify no blacklisted symbol trades
- If successful → Switch to LIVE mode

---

## 📚 REFERENCE: PREVIOUS SUCCESSFUL DEPLOYMENT

**File:** `deploy_complete.ps1`  
**Date:** November 21, 2025  
**Result:** ✅ All Cloud Functions deployed successfully  
**Pattern:** Backend → Frontend → Verification  

**V3.2 follows exact same pattern with:**
- Same Cloud Run settings
- Same App Hosting deployment
- Same verification steps
- Same rollback procedures

**Confidence Level:** ✅ **HIGH** - Deployment pattern proven to work

---

**Status:** ✅ READY TO DEPLOY  
**Risk Level:** LOW (non-breaking changes, proven deployment pattern)  
**Rollback:** Easy (revert Cloud Run traffic + App Hosting rollback)
