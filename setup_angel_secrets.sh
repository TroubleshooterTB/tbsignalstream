#!/bin/bash
# Script to create Google Cloud Secret Manager secrets for Angel Broking API
# Run this script using: bash setup_angel_secrets.sh
# Make sure you have gcloud CLI installed and authenticated

PROJECT_ID="tbsignalstream"
echo "Setting up Angel Broking secrets for project: $PROJECT_ID"
echo "================================================"

# Function to create or update a secret
create_secret() {
    local secret_name=$1
    local secret_value=$2
    
    echo "Creating secret: $secret_name"
    
    # Check if secret already exists
    if gcloud secrets describe $secret_name --project=$PROJECT_ID &> /dev/null; then
        echo "  Secret $secret_name already exists, adding new version..."
        echo -n "$secret_value" | gcloud secrets versions add $secret_name --data-file=- --project=$PROJECT_ID
    else
        echo "  Creating new secret $secret_name..."
        echo -n "$secret_value" | gcloud secrets create $secret_name --data-file=- --project=$PROJECT_ID
    fi
    
    if [ $? -eq 0 ]; then
        echo "  ✅ Success: $secret_name"
    else
        echo "  ❌ Failed: $secret_name"
    fi
    echo ""
}

# Trading API Credentials
echo "1. Trading API Credentials"
create_secret "angelone-trading-api-key" "6TilvLvs"
create_secret "angelone-trading-api-secret" "e3b8bf3c-38bf-4379-bece-bc7883e983d2"

# Historical Data API Credentials
echo "2. Historical Data API Credentials"
create_secret "angelone-historical-api-key" "dQMZzCQF"
create_secret "angelone-historical-api-secret" "65c7e839-6c1f-4688-9302-b13d4600b2e9"

# Market API Credentials
echo "3. Market API Credentials"
create_secret "angelone-market-api-key" "X1iLPhdi"
create_secret "angelone-market-api-secret" "043de84f-f078-440f-a8a4-ef703d342579"

# Publisher API Credentials
echo "4. Publisher API Credentials"
create_secret "angelone-publisher-api-key" "rYFg7mmT"
create_secret "angelone-publisher-api-secret" "257d1489-6fdd-465f-b13d-a0d9d0c58dce"

# Account Credentials
echo "5. Account Credentials"
create_secret "angelone-client-code" "AABL713311"
create_secret "angelone-password" "1012"
create_secret "angelone-totp-secret" "AGODKRXZZH6FHMYWMSBIK6KDXQ"

echo "================================================"
echo "All secrets created/updated!"
echo ""
echo "Next steps:"
echo "1. Grant access to App Hosting backend using grant_secrets.ps1"
echo "2. Verify secrets in Google Cloud Console:"
echo "   https://console.cloud.google.com/security/secret-manager?project=$PROJECT_ID"
echo ""
echo "⚠️  SECURITY WARNING:"
echo "After confirming secrets are created, DELETE the functions/.env.local file"
echo "containing plaintext credentials!"
