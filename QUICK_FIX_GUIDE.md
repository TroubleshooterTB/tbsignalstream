# Angel Broking Integration - Quick Fix Guide

## 🚨 Critical Issues Fixed

This guide shows what was fixed and what you need to do next to complete the integration.

---

## ✅ What Was Fixed Automatically

### 1. Fixed apphosting.yaml
- ❌ **Before**: Used incorrect variable names (`ANGEL_ONE_API_KEY`, `ANGEL_ONE_CLIENT_ID`)
- ✅ **After**: Now uses correct names matching the code (`ANGELONE_TRADING_API_KEY`, `ANGELONE_CLIENT_CODE`)
- ✅ **After**: Added all 11 required environment variables for complete Angel Broking integration

### 2. Fixed functions/requirements.txt
- ❌ **Before**: Missing `smartapi-python` and `pyotp` packages
- ✅ **After**: Added both required packages for Angel Broking API integration

### 3. Created Setup Scripts
- ✅ Created `setup_angel_secrets.ps1` - Automated secret creation
- ✅ Created `setup_angel_secrets.sh` - Bash version for Linux/Mac
- ✅ Updated `grant_secrets.ps1` - Grants access to all 11 secrets

---

## 🔧 What You Need to Do Next

### Step 1: Install Google Cloud SDK (if not already installed)

**Windows:**
```powershell
# Download and install from: https://cloud.google.com/sdk/docs/install
# Or use Chocolatey:
choco install google-cloud-sdk
```

**After installation, authenticate:**
```powershell
gcloud auth login
gcloud config set project tbsignalstream
```

### Step 2: Create Google Cloud Secrets

Run the automated setup script:

```powershell
# In PowerShell (Windows)
cd "d:\Tushar 2.0\tbsignalstream_backup\tbsignalstream_backup"
.\setup_angel_secrets.ps1
```

OR manually create each secret:

```powershell
# Trading API
echo -n "6TilvLvs" | gcloud secrets create angelone-trading-api-key --data-file=- --project=tbsignalstream
echo -n "e3b8bf3c-38bf-4379-bece-bc7883e983d2" | gcloud secrets create angelone-trading-api-secret --data-file=- --project=tbsignalstream

# Historical API
echo -n "dQMZzCQF" | gcloud secrets create angelone-historical-api-key --data-file=- --project=tbsignalstream
echo -n "65c7e839-6c1f-4688-9302-b13d4600b2e9" | gcloud secrets create angelone-historical-api-secret --data-file=- --project=tbsignalstream

# Market API
echo -n "X1iLPhdi" | gcloud secrets create angelone-market-api-key --data-file=- --project=tbsignalstream
echo -n "043de84f-f078-440f-a8a4-ef703d342579" | gcloud secrets create angelone-market-api-secret --data-file=- --project=tbsignalstream

# Publisher API
echo -n "rYFg7mmT" | gcloud secrets create angelone-publisher-api-key --data-file=- --project=tbsignalstream
echo -n "257d1489-6fdd-465f-b13d-a0d9d0c58dce" | gcloud secrets create angelone-publisher-api-secret --data-file=- --project=tbsignalstream

# Account Credentials
echo -n "AABL713311" | gcloud secrets create angelone-client-code --data-file=- --project=tbsignalstream
echo -n "1012" | gcloud secrets create angelone-password --data-file=- --project=tbsignalstream
echo -n "AGODKRXZZH6FHMYWMSBIK6KDXQ" | gcloud secrets create angelone-totp-secret --data-file=- --project=tbsignalstream
```

### Step 3: Grant Access to App Hosting Backend

```powershell
# Automated way:
.\grant_secrets.ps1

# OR manually for each secret:
firebase apphosting:secrets:grantaccess angelone-trading-api-key --backend=studio
firebase apphosting:secrets:grantaccess angelone-trading-api-secret --backend=studio
firebase apphosting:secrets:grantaccess angelone-historical-api-key --backend=studio
firebase apphosting:secrets:grantaccess angelone-historical-api-secret --backend=studio
firebase apphosting:secrets:grantaccess angelone-market-api-key --backend=studio
firebase apphosting:secrets:grantaccess angelone-market-api-secret --backend=studio
firebase apphosting:secrets:grantaccess angelone-publisher-api-key --backend=studio
firebase apphosting:secrets:grantaccess angelone-publisher-api-secret --backend=studio
firebase apphosting:secrets:grantaccess angelone-client-code --backend=studio
firebase apphosting:secrets:grantaccess angelone-password --backend=studio
firebase apphosting:secrets:grantaccess angelone-totp-secret --backend=studio
```

### Step 4: Verify Secrets in Google Cloud Console

Visit: https://console.cloud.google.com/security/secret-manager?project=tbsignalstream

You should see all 11 secrets:
- ✅ angelone-trading-api-key
- ✅ angelone-trading-api-secret
- ✅ angelone-historical-api-key
- ✅ angelone-historical-api-secret
- ✅ angelone-market-api-key
- ✅ angelone-market-api-secret
- ✅ angelone-publisher-api-key
- ✅ angelone-publisher-api-secret
- ✅ angelone-client-code
- ✅ angelone-password
- ✅ angelone-totp-secret

### Step 5: Deploy or Rebuild

Trigger a new build to pick up the fixed configuration:

**Option A: Git Push**
```bash
git add apphosting.yaml functions/requirements.txt
git commit -m "Fix Angel Broking API integration environment variables"
git push
```

**Option B: Manual Deploy**
```bash
firebase deploy --only apphosting:studio
```

**Option C: Firebase Console**
Go to Firebase Console → App Hosting → Trigger new build

---

## 🔐 Critical Security Steps

### ⚠️ After Confirming Everything Works:

1. **Delete the plaintext credentials file:**
   ```powershell
   Remove-Item "d:\Tushar 2.0\tbsignalstream_backup\tbsignalstream_backup\functions\.env.local"
   ```

2. **Verify .gitignore includes:**
   ```
   .env
   .env.local
   functions/.env.local
   *.secret
   ```

3. **Consider rotating your API keys** since they were exposed in the codebase:
   - Log in to Angel Broking SmartAPI portal
   - Generate new API keys
   - Update the secrets in Google Cloud Secret Manager

---

## 📋 Verification Checklist

After deployment, verify:

- [ ] Build completes without "Misconfigured Secret" errors
- [ ] All 11 environment variables are accessible in the app
- [ ] Angel Broking login function works (test via API endpoint)
- [ ] Tokens are stored correctly in Firestore
- [ ] No plaintext credentials remain in the repository

---

## 🐛 Troubleshooting

### Error: "Secret not found"
- Run `gcloud secrets list --project=tbsignalstream` to verify secrets exist
- Ensure secret names match exactly (case-sensitive)

### Error: "Permission denied" when creating secrets
- Ensure you're authenticated: `gcloud auth login`
- Verify you have Secret Manager Admin role
- Check project ID is correct: `gcloud config get-value project`

### Error: "Backend not found" when granting access
- List backends: `firebase apphosting:backends:list`
- Update `$BACKEND_ID` in `grant_secrets.ps1` if different from "studio"

### Build still failing after fixes
- Clear build cache in Firebase Console
- Verify all secrets have been granted access
- Check build logs for specific error messages

---

## 📚 Next Development Steps

After the integration is working:

1. **Complete Trading Bot Implementation**
   - Implement order placement functions
   - Add historical data fetching
   - Integrate WebSocket for live data

2. **Add Error Handling**
   - Token refresh logic
   - API rate limiting
   - Connection retry mechanisms

3. **Testing**
   - Test login flow end-to-end
   - Verify token storage and retrieval
   - Test with real market data

4. **Monitoring**
   - Set up logging for API calls
   - Monitor token expiration
   - Track API usage and limits

---

## 📞 Support Resources

- **Angel Broking SmartAPI Docs**: https://smartapi.angelbroking.com/docs
- **SmartAPI Python SDK**: https://github.com/angelbroking-github/smartapi-python
- **Google Cloud Secret Manager**: https://cloud.google.com/secret-manager/docs
- **Firebase App Hosting**: https://firebase.google.com/docs/app-hosting

---

**Last Updated**: 2025-11-16  
**Status**: Ready for deployment after completing Steps 1-5
