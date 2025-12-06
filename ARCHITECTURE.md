# TBSignalStream - System Architecture

**Last Updated:** December 7, 2025, 00:40 IST

## 🌐 LIVE URLs - USE THESE

### Production Frontend (Next.js App)
- **URL:** https://studio--tbsignalstream.us-central1.hosted.app
- **Platform:** Firebase App Hosting
- **Auto-deploys:** Yes, from GitHub `master` branch
- **Tech:** Next.js 14 (App Router), React, TypeScript

### Trading Bot Backend (Python)
- **URL:** https://trading-bot-service-vmxfbt7qiq-el.a.run.app
- **Platform:** Google Cloud Run
- **Region:** asia-south1 (Mumbai)
- **Deployment:** Manual via `gcloud run deploy` from `trading_bot_service/` directory
- **Tech:** Python Flask, WebSocket (Angel One), Firestore

### Firebase Cloud Functions (Auth & Utils)
- **Base URL:** https://us-central1-tbsignalstream.cloudfunctions.net
- **Region:** us-central1
- **Deployment:** Manual via `firebase deploy --only functions`
- **Tech:** Node.js, TypeScript

---

## 📦 Tech Stack Breakdown

### Frontend (Next.js)
```
Location: Root directory (src/, app/, components/, lib/)
Framework: Next.js 14 (App Router)
Language: TypeScript
UI Library: React 18
Styling: Tailwind CSS
Components: Radix UI, shadcn/ui
State: Nanostores
Auth: Firebase Auth
Database Client: Firebase SDK (Firestore, Functions)
Deployment: Firebase App Hosting
Build Command: npm run build
Environment: apphosting.yaml
```

### Backend - Trading Bot Service
```
Location: trading_bot_service/
Framework: Flask (Python 3.11)
Language: Python
Server: Gunicorn (multi-threaded)
WebSocket: websocket-client (Angel One SmartAPI)
Database: Firestore (Google Cloud)
Deployment: Google Cloud Run
Container: Docker (Dockerfile in trading_bot_service/)
Resources: 2GB RAM, 2 vCPU, 3600s timeout
Region: asia-south1 (Mumbai)
```

### Backend - Firebase Functions
```
Location: functions/
Runtime: Node.js 18
Language: TypeScript
Functions:
  - directAngelLogin (Angel One OAuth)
  - Other utility functions
Deployment: Firebase Functions
Region: us-central1
```

---

## 🔗 Service Integration Map

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                             │
│                                                                  │
│  URL: https://studio--tbsignalstream.us-central1.hosted.app    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FIREBASE APP HOSTING                          │
│                    (Next.js Frontend)                            │
│                                                                  │
│  • Server-Side Rendering (SSR)                                  │
│  • API Routes (/api/*)                                          │
│  • Static Assets                                                │
│  • Auto-deploys from GitHub master                              │
└─────────┬───────────────────────┬───────────────────────────────┘
          │                       │
          │                       │
          ▼                       ▼
┌──────────────────┐    ┌─────────────────────────────────────────┐
│  FIREBASE AUTH   │    │     FIRESTORE DATABASE                  │
│                  │    │                                         │
│  • User Login    │    │  Collections:                           │
│  • JWT Tokens    │    │    - users                              │
│  • Session Mgmt  │    │    - signals                            │
└──────────────────┘    │    - bot_configs                        │
                        │    - angel_one_credentials              │
                        │    - positions                          │
                        │    - orders                             │
                        └─────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│              FIREBASE CLOUD FUNCTIONS                            │
│              (us-central1)                                       │
│                                                                  │
│  • directAngelLogin: Angel One OAuth flow                       │
│  • Other utility functions                                      │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│              GOOGLE CLOUD RUN                                    │
│              trading-bot-service (asia-south1)                   │
│                                                                  │
│  URL: https://trading-bot-service-vmxfbt7qiq-el.a.run.app      │
│                                                                  │
│  Endpoints:                                                     │
│    POST /start     - Start trading bot                         │
│    POST /stop      - Stop trading bot                          │
│    GET  /status    - Bot status                                │
│    GET  /health    - Health check                              │
│                                                                  │
│  Features:                                                      │
│    • Real-time WebSocket to Angel One                          │
│    • Pattern detection (22 levels)                             │
│    • Ironclad strategy                                         │
│    • Position monitoring (0.5s interval)                       │
│    • Risk management                                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ANGEL ONE SMART API                           │
│                    (External Broker)                             │
│                                                                  │
│  • Market Data WebSocket                                        │
│  • Order Execution                                              │
│  • Position Management                                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔐 Environment Variables & Secrets

### Frontend (App Hosting - apphosting.yaml)
```yaml
ANGELONE_TRADING_API_KEY          → Secret Manager
ANGELONE_TRADING_API_SECRET       → Secret Manager
ANGELONE_CLIENT_CODE              → Secret Manager
ANGELONE_PASSWORD                 → Secret Manager
ANGELONE_TOTP_SECRET              → Secret Manager
FIREBASE_WEBAPP_CONFIG            → Secret Manager
NEXT_PUBLIC_FIREBASE_API_KEY      → Secret Manager (build-time)
NEXT_PUBLIC_FIREBASE_APP_ID       → Secret Manager (build-time)
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN  → Secret Manager (build-time)
NEXT_PUBLIC_FIREBASE_PROJECT_ID   → Secret Manager (build-time)
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET → Secret Manager (build-time)
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID → Secret Manager (build-time)
NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID → Secret Manager (build-time)
```

### Backend - Cloud Run (trading-bot-service)
```yaml
ANGELONE_TRADING_API_KEY    → Secret Manager
ANGELONE_TRADING_SECRET     → Secret Manager
ANGELONE_CLIENT_CODE        → Secret Manager
ANGELONE_PASSWORD           → Secret Manager
ANGELONE_TOTP_SECRET        → Secret Manager
GOOGLE_CLOUD_PROJECT=tbsignalstream
```

---

## 📁 Directory Structure

```
tbsignalstream_backup/
├── src/                          # Frontend source
│   ├── app/                      # Next.js App Router pages
│   ├── components/               # React components
│   └── lib/                      # Utilities & API clients
│       ├── firebase.ts           # Firebase SDK init
│       ├── trading-api.ts        # ⚠️ MUST use correct Cloud Run URL
│       └── stores.ts             # Nanostores state
│
├── trading_bot_service/          # Backend Python service
│   ├── main.py                   # Flask server
│   ├── realtime_bot_engine.py    # Bot logic
│   ├── websocket_manager_v2.py   # Angel One WebSocket
│   ├── Dockerfile                # Cloud Run container
│   └── requirements.txt          # Python dependencies
│
├── functions/                    # Firebase Functions
│   ├── main.py                   # Cloud Functions (Python)
│   └── requirements.txt
│
├── apphosting.yaml               # ⚠️ App Hosting config (CRITICAL)
├── firebase.json                 # Firebase project config
├── package.json                  # Frontend dependencies
└── next.config.js                # Next.js config
```

---

## 🚀 Deployment Commands

### Deploy Frontend (App Hosting)
```bash
# AUTO-DEPLOYS on git push to master!
git add .
git commit -m "Update"
git push origin master

# OR manually trigger:
firebase apphosting:rollouts:create studio
```

### Deploy Backend (Cloud Run)
```bash
cd trading_bot_service
gcloud run deploy trading-bot-service \
  --source . \
  --region asia-south1 \
  --allow-unauthenticated
```

### Deploy Firebase Functions
```bash
firebase deploy --only functions
# OR specific function:
firebase deploy --only functions:directAngelLogin
```

---

## ⚠️ CRITICAL CONFIGURATION FILES

### 1. src/lib/trading-api.ts
**MUST ALWAYS USE THIS URL:**
```typescript
const TRADING_BOT_SERVICE_URL = 'https://trading-bot-service-vmxfbt7qiq-el.a.run.app';
```

**NEVER USE:**
- ❌ `https://trading-bot-service-818546654122.asia-south1.run.app` (OLD)
- ❌ Any other URL

### 2. apphosting.yaml
This file controls Firebase App Hosting deployment:
- Build command: `npm run build`
- Static directory: `.next`
- All environment variables/secrets

### 3. Dockerfile (trading_bot_service/)
Cloud Run container configuration:
- Base image: Python 3.11 slim
- Port: 8080
- Server: Gunicorn with 4 workers

---

## 🔍 How to Verify Everything is Working

### 1. Check Frontend Deployment
```bash
firebase apphosting:backends:list
# Should show: studio | TroubleshooterTB-tbsignalstream | https://studio--tbsignalstream.us-central1.hosted.app
```

### 2. Check Backend Deployment
```bash
gcloud run services describe trading-bot-service --region asia-south1 --format="value(status.url)"
# Should output: https://trading-bot-service-vmxfbt7qiq-el.a.run.app
```

### 3. Check Backend Logs
```bash
gcloud run services logs read trading-bot-service --region asia-south1 --limit 50
```

### 4. Test Frontend → Backend Connection
1. Open: https://studio--tbsignalstream.us-central1.hosted.app
2. Login
3. Start bot
4. Check logs for activity with current timestamp

---

## 🐛 Common Issues & Solutions

### Issue: "Frontend not connecting to backend"
**Cause:** Wrong URL in `trading-api.ts`
**Fix:** Update to `https://trading-bot-service-vmxfbt7qiq-el.a.run.app`

### Issue: "No logs appearing when starting bot"
**Cause 1:** Using wrong frontend URL (static hosting instead of App Hosting)
**Fix:** Use https://studio--tbsignalstream.us-central1.hosted.app

**Cause 2:** Cloud Run URL mismatch
**Fix:** Verify URL in trading-api.ts matches actual Cloud Run service

### Issue: "Bot crashes silently"
**Cause:** Empty symbol list causing WebSocket subscription failure
**Fix:** Already fixed - bot now skips subscription if no symbols

---

## 📝 Development Workflow

1. **Make code changes** in local environment
2. **Test locally** (optional): `npm run dev` for frontend
3. **Commit to GitHub**: 
   ```bash
   git add .
   git commit -m "Description"
   git push origin master
   ```
4. **App Hosting auto-deploys** frontend in ~2-3 minutes
5. **For backend changes**: 
   ```bash
   cd trading_bot_service
   gcloud run deploy trading-bot-service --source . --region asia-south1
   ```
6. **Verify deployment**: Check logs and test in browser

---

## 🎯 Quick Reference

| What | Where | URL/Command |
|------|-------|-------------|
| **Access Live App** | Browser | https://studio--tbsignalstream.us-central1.hosted.app |
| **Backend API** | Cloud Run | https://trading-bot-service-vmxfbt7qiq-el.a.run.app |
| **Firebase Console** | Web | https://console.firebase.google.com/project/tbsignalstream |
| **Cloud Run Console** | Web | https://console.cloud.google.com/run?project=tbsignalstream |
| **Deploy Frontend** | Terminal | `git push origin master` (auto) |
| **Deploy Backend** | Terminal | `cd trading_bot_service && gcloud run deploy...` |
| **View Logs** | Terminal | `gcloud run services logs read trading-bot-service --region asia-south1` |
| **Secrets** | Console | https://console.cloud.google.com/security/secret-manager?project=tbsignalstream |

---

**REMEMBER:**
1. ✅ Frontend: Firebase App Hosting (auto-deploy from GitHub)
2. ✅ Backend: Google Cloud Run (manual deploy)
3. ✅ Always use: https://studio--tbsignalstream.us-central1.hosted.app
4. ✅ Backend URL in code: https://trading-bot-service-vmxfbt7qiq-el.a.run.app
5. ✅ Check logs with current timestamp to verify activity
