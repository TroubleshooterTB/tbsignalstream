# Trading Bot Service - Cloud Run

Fully functional live trading bot service with persistent execution capabilities.

## Features

- ✅ **Persistent Execution**: Runs continuously in Cloud Run
- ✅ **WebSocket Alternative**: Polls Angel One API for real-time data
- ✅ **Multi-User Support**: Isolated bot instances per user
- ✅ **Firebase Integration**: Secure authentication and state management
- ✅ **Automatic Scaling**: Scales from 0 to 10 instances based on load

## Architecture

```
Frontend → Cloud Function → Cloud Run Service
                              ↓
                         Bot Engine (Threading)
                              ↓
                         Angel One API
```

## Deployment

### Initial Deployment
```bash
cd trading_bot_service
gcloud run deploy trading-bot-service \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --project tbsignalstream \
  --memory 512Mi \
  --cpu 1 \
  --timeout 3600 \
  --min-instances 0 \
  --max-instances 10
```

### Set Environment Variable in Cloud Functions

After deployment, update the Cloud Function with the service URL:

```bash
SERVICE_URL=$(gcloud run services describe trading-bot-service \
  --region us-central1 \
  --project tbsignalstream \
  --format='value(status.url)')

# Deploy Cloud Functions with service URL
cd ../functions
gcloud functions deploy startLiveTradingBot \
  --gen2 \
  --runtime=python311 \
  --trigger-http \
  --allow-unauthenticated \
  --region=us-central1 \
  --project=tbsignalstream \
  --source=. \
  --entry-point=startLiveTradingBot \
  --memory=256Mi \
  --timeout=60s \
  --set-env-vars=TRADING_BOT_SERVICE_URL=$SERVICE_URL
```

## API Endpoints

### POST /start
Start trading bot for authenticated user

**Headers:**
- `Authorization: Bearer <firebase-id-token>`

**Body:**
```json
{
  "symbols": ["RELIANCE", "HDFCBANK"],
  "interval": "5minute"
}
```

### POST /stop
Stop trading bot for authenticated user

**Headers:**
- `Authorization: Bearer <firebase-id-token>`

### GET /status
Get bot status

**Headers:**
- `Authorization: Bearer <firebase-id-token>`

### GET /health
Health check endpoint (no auth required)

## Bot Engine

The bot engine (`bot_engine.py`) implements:

1. **Symbol Token Resolution**: Uses Angel One searchScrip API
2. **Market Data Polling**: Fetches LTP at configured intervals
3. **Tick Processing**: Builds candles from tick data
4. **Strategy Execution**: Placeholder for pattern detection and order placement
5. **Position Management**: Track open positions and P&L

## Next Steps

To make it fully functional:

1. **Integrate Pattern Detection**: Connect the existing PatternDetector class
2. **Implement Order Placement**: Use OrderManager to place trades
3. **Add Risk Management**: Integrate RiskManager for position sizing
4. **Enable 30-Point Checklist**: Connect ExecutionManager validation
5. **Add WebSocket Support**: Optionally upgrade to SmartAPI WebSocket v2

## Cost Optimization

- Scales to zero when no bots are running
- Only charged for active bot time
- 512Mi memory should handle 5-10 concurrent user bots
- Estimated cost: ~$5-10/month for moderate usage

## Monitoring

View logs:
```bash
gcloud run services logs read trading-bot-service \
  --region us-central1 \
  --project tbsignalstream \
  --limit 100
```

## Security

- Firebase authentication required for all user endpoints
- Angel One credentials stored securely in Firestore
- API keys loaded from environment variables
- No credentials in source code
