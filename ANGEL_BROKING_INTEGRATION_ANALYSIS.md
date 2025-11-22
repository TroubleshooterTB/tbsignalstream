# Angel Broking SmartAPI Integration Analysis

## Executive Summary
✅ **Overall Status**: Partially Integrated with Critical Issues

The project has Angel Broking SmartAPI integration implemented but has **critical environment variable mismatches** and **missing secret configurations** that are preventing successful deployment.

---

## ✅ What's Working

### 1. Python SDK Integration
- ✅ `smartapi-python` package included in `requirements.txt`
- ✅ `DataHandler` class properly implements SmartConnect SDK
- ✅ TOTP-based authentication implemented with `pyotp`
- ✅ Session management with JWT, refresh, and feed tokens

### 2. Firebase Cloud Function (Login Endpoint)
- ✅ `directAngelLogin` function in `functions/main.py`
- ✅ Proper API endpoint: `https://apiconnect.angelone.in/rest/auth/angelbroking/user/v1/loginByPassword`
- ✅ Correct headers implementation (X-PrivateKey, X-UserType, etc.)
- ✅ Token storage in Firestore under `angel_one_credentials` collection
- ✅ Firebase Auth integration for user-specific credential management

### 3. Configuration Files
- ✅ Multiple API key types configured in `config.py` (Historical, Trading, Publisher, Market)
- ✅ Environment-based credential management
- ✅ Risk management and position management parameters defined

### 4. Credentials Present
- ✅ All 4 API keys with secrets stored in `functions/.env.local`:
  - ANGELONE_HISTORICAL_API_KEY
  - ANGELONE_MARKET_API_KEY
  - ANGELONE_PUBLISHER_API_KEY
  - ANGELONE_TRADING_API_KEY
- ✅ Client code, password, and TOTP secret configured

---

## ❌ Critical Issues Found

### Issue #1: Environment Variable Name Mismatch 🔴 CRITICAL

**Problem**: Inconsistent environment variable naming across files

| File | Variable Name |
|------|--------------|
| `apphosting.yaml` | `ANGEL_ONE_API_KEY` |
| `functions/main.py` | `ANGELONE_TRADING_API_KEY` |
| `functions/.env.local` | `ANGELONE_TRADING_API_KEY` |
| `data_handler.py` | `ANGELONE_TRADING_API_KEY` |

**Impact**: The Cloud Build fails with "Misconfigured Secret" error because `angelone-api-key` secret is referenced in `apphosting.yaml`, but the code expects `ANGELONE_TRADING_API_KEY`.

**Solution Required**: 
1. Update `apphosting.yaml` to use correct secret names matching Google Cloud Secret Manager
2. Ensure all secret names use underscores consistently

---

### Issue #2: Incomplete Secret Manager Configuration 🔴 CRITICAL

**Current State in apphosting.yaml**:
```yaml
env:
  - variable: ANGEL_ONE_API_KEY
    secret: angelone-api-key
  - variable: ANGEL_ONE_CLIENT_ID
    secret: angelone-client-id
  - variable: ANGEL_ONE_PASSWORD
    secret: angelone-password
  - variable: ANGEL_ONE_TOTP_SECRET
    secret: angelone-totp-secret
```

**What's Missing**:
- No secrets for the 4 different API key types (Historical, Market, Publisher, Trading)
- Variable name `ANGEL_ONE_CLIENT_ID` should be `ANGELONE_CLIENT_CODE`
- Missing all API secrets (only keys are configured)

**Required Secret Manager Secrets**:
```
angelone-trading-api-key
angelone-trading-api-secret
angelone-historical-api-key
angelone-historical-api-secret
angelone-market-api-key
angelone-market-api-secret
angelone-publisher-api-key
angelone-publisher-api-secret
angelone-client-code
angelone-password
angelone-totp-secret
```

---

### Issue #3: Missing Dependencies in Functions

**Problem**: `functions/requirements.txt` doesn't include `smartapi-python` or `pyotp`

**Current functions/requirements.txt**:
```
firebase-admin==6.5.0
firebase-functions==0.2.0
requests==2.31.0
google-cloud-secret-manager==2.19.0
```

**Missing**:
- `smartapi-python` (for SmartConnect SDK)
- `pyotp` (for TOTP generation)

---

### Issue #4: Unused API Keys/Secrets 🟡 WARNING

The project has API **keys** but the Angel Broking SmartAPI also requires corresponding API **secrets** for each key type. The `.env.local` file has these secrets, but they're not being used anywhere in the code.

---

## 📋 Recommended Fixes (Priority Order)

### Priority 1: Fix apphosting.yaml (CRITICAL)

Update the file to properly map all required environment variables:

```yaml
run: npm run build
staticDirectory: .next

env:
  # Trading API Credentials
  - variable: ANGELONE_TRADING_API_KEY
    secret: angelone-trading-api-key
  - variable: ANGELONE_TRADING_API_SECRET
    secret: angelone-trading-api-secret
  
  # Historical Data API Credentials
  - variable: ANGELONE_HISTORICAL_API_KEY
    secret: angelone-historical-api-key
  - variable: ANGELONE_HISTORICAL_API_SECRET
    secret: angelone-historical-api-secret
  
  # Market API Credentials
  - variable: ANGELONE_MARKET_API_KEY
    secret: angelone-market-api-key
  - variable: ANGELONE_MARKET_API_SECRET
    secret: angelone-market-api-secret
  
  # Publisher API Credentials
  - variable: ANGELONE_PUBLISHER_API_KEY
    secret: angelone-publisher-api-key
  - variable: ANGELONE_PUBLISHER_API_SECRET
    secret: angelone-publisher-api-secret
  
  # Account Credentials
  - variable: ANGELONE_CLIENT_CODE
    secret: angelone-client-code
  - variable: ANGELONE_PASSWORD
    secret: angelone-password
  - variable: ANGELONE_TOTP_SECRET
    secret: angelone-totp-secret
```

### Priority 2: Create Google Cloud Secrets

Run these commands to create all required secrets in Google Cloud Secret Manager:

```bash
# Trading API
echo -n "6TilvLvs" | gcloud secrets create angelone-trading-api-key --data-file=-
echo -n "e3b8bf3c-38bf-4379-bece-bc7883e983d2" | gcloud secrets create angelone-trading-api-secret --data-file=-

# Historical API
echo -n "dQMZzCQF" | gcloud secrets create angelone-historical-api-key --data-file=-
echo -n "65c7e839-6c1f-4688-9302-b13d4600b2e9" | gcloud secrets create angelone-historical-api-secret --data-file=-

# Market API
echo -n "X1iLPhdi" | gcloud secrets create angelone-market-api-key --data-file=-
echo -n "043de84f-f078-440f-a8a4-ef703d342579" | gcloud secrets create angelone-market-api-secret --data-file=-

# Publisher API
echo -n "rYFg7mmT" | gcloud secrets create angelone-publisher-api-key --data-file=-
echo -n "257d1489-6fdd-465f-b13d-a0d9d0c58dce" | gcloud secrets create angelone-publisher-api-secret --data-file=-

# Account Credentials
echo -n "AABL713311" | gcloud secrets create angelone-client-code --data-file=-
echo -n "1012" | gcloud secrets create angelone-password --data-file=-
echo -n "AGODKRXZZH6FHMYWMSBIK6KDXQ" | gcloud secrets create angelone-totp-secret --data-file=-
```

### Priority 3: Update functions/requirements.txt

Add missing dependencies:

```txt
firebase-admin==6.5.0
firebase-functions==0.2.0
requests==2.31.0
google-cloud-secret-manager==2.19.0
google-api-core==2.19.0
google-cloud-firestore==2.16.0
grpcio==1.62.2
Flask-Cors==4.0.1
smartapi-python
pyotp
```

### Priority 4: Update main.py Environment Variable

Change line 52 in `functions/main.py`:
```python
# FROM:
api_key = os.environ.get("ANGELONE_TRADING_API_KEY")

# TO (if using unified key):
api_key = os.environ.get("ANGELONE_TRADING_API_KEY")
# This is already correct, just ensure the secret is properly named
```

---

## 🔍 Angel Broking SmartAPI Compliance Check

### Authentication ✅
- [x] Login endpoint implemented
- [x] TOTP-based 2FA
- [x] JWT token management
- [x] Feed token for WebSocket
- [x] Refresh token storage

### Required Headers ✅
- [x] X-PrivateKey (API Key)
- [x] X-UserType
- [x] X-SourceID
- [x] X-ClientLocalIP
- [x] X-ClientPublicIP
- [x] X-MACAddress

### Missing Implementations ⚠️
- [ ] Order placement functions
- [ ] Historical data fetching (placeholder exists)
- [ ] Market data APIs
- [ ] Portfolio management
- [ ] WebSocket live feed integration
- [ ] Order modification/cancellation
- [ ] Position management APIs

---

## 📁 File Structure Summary

```
tbsignalstream_backup/
├── apphosting.yaml                    # ❌ Needs fix (env vars)
├── functions/
│   ├── main.py                        # ✅ Login function working
│   ├── requirements.txt               # ❌ Missing smartapi-python, pyotp
│   ├── .env.local                     # ✅ All credentials present
│   └── src/
│       ├── config.py                  # ✅ Comprehensive config
│       └── trading/
│           ├── data_handler.py        # ✅ SmartAPI SDK integration
│           ├── trading_bot.py         # ⚠️ Placeholder implementation
│           └── execution_manager.py   # ⚠️ Not fully implemented
├── src/
│   └── app/
│       └── login/
│           └── page.tsx               # ℹ️ Firebase Auth (separate from Angel)
└── requirements.txt                   # ✅ smartapi-python included
```

---

## 🎯 Next Steps

1. **Immediate**: Fix `apphosting.yaml` environment variable names
2. **Immediate**: Create all Google Cloud secrets with correct values
3. **Immediate**: Update `functions/requirements.txt` to include missing packages
4. **Short-term**: Grant secret access permissions to App Hosting backend
5. **Medium-term**: Implement remaining Angel Broking API endpoints (orders, positions, etc.)
6. **Medium-term**: Add WebSocket integration for live market data
7. **Long-term**: Complete trading bot implementation with real API calls

---

## 🔐 Security Notes

⚠️ **CRITICAL SECURITY ISSUES**:

1. **Credentials in .env.local**: The `functions/.env.local` file contains **real API keys and secrets in plaintext**. These should:
   - Be removed from the repository
   - Only exist in Google Cloud Secret Manager
   - Never be committed to version control

2. **Add to .gitignore**:
   ```
   .env
   .env.local
   functions/.env.local
   ```

3. **Rotate Credentials**: Since credentials are exposed in the codebase, consider regenerating all API keys and secrets from the Angel Broking portal.

---

## 📚 References

- [Angel Broking SmartAPI Documentation](https://smartapi.angelbroking.com/docs)
- [SmartAPI Python SDK](https://github.com/angelbroking-github/smartapi-python)
- [Google Cloud Secret Manager](https://cloud.google.com/secret-manager/docs)
- [Firebase App Hosting Environment Variables](https://firebase.google.com/docs/app-hosting/configure-environment-variables)

---

**Generated**: 2025-11-16  
**Status**: Integration audit complete - Action required
