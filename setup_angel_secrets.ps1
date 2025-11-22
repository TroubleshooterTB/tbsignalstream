# PowerShell Script to create Google Cloud Secret Manager secrets for Angel Broking API
# Run this script using: .\setup_angel_secrets.ps1
# Make sure you have gcloud CLI installed and authenticated

$PROJECT_ID = "tbsignalstream"
Write-Host "Setting up Angel Broking secrets for project: $PROJECT_ID" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# Function to create or update a secret
function Create-Secret {
    param(
        [string]$SecretName,
        [string]$SecretValue
    )
    
    Write-Host "Creating secret: $SecretName" -ForegroundColor Yellow
    
    # Check if secret already exists
    $exists = gcloud secrets describe $SecretName --project=$PROJECT_ID 2>$null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Secret $SecretName already exists, adding new version..." -ForegroundColor Gray
        $SecretValue | gcloud secrets versions add $SecretName --data-file=- --project=$PROJECT_ID
    } else {
        Write-Host "  Creating new secret $SecretName..." -ForegroundColor Gray
        $SecretValue | gcloud secrets create $SecretName --data-file=- --project=$PROJECT_ID
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Success: $SecretName" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Failed: $SecretName" -ForegroundColor Red
    }
    Write-Host ""
}

# Trading API Credentials
Write-Host "1. Trading API Credentials" -ForegroundColor Cyan
Create-Secret "angelone-trading-api-key" "6TilvLvs"
Create-Secret "angelone-trading-api-secret" "e3b8bf3c-38bf-4379-bece-bc7883e983d2"

# Historical Data API Credentials
Write-Host "2. Historical Data API Credentials" -ForegroundColor Cyan
Create-Secret "angelone-historical-api-key" "dQMZzCQF"
Create-Secret "angelone-historical-api-secret" "65c7e839-6c1f-4688-9302-b13d4600b2e9"

# Market API Credentials
Write-Host "3. Market API Credentials" -ForegroundColor Cyan
Create-Secret "angelone-market-api-key" "X1iLPhdi"
Create-Secret "angelone-market-api-secret" "043de84f-f078-440f-a8a4-ef703d342579"

# Publisher API Credentials
Write-Host "4. Publisher API Credentials" -ForegroundColor Cyan
Create-Secret "angelone-publisher-api-key" "rYFg7mmT"
Create-Secret "angelone-publisher-api-secret" "257d1489-6fdd-465f-b13d-a0d9d0c58dce"

# Account Credentials
Write-Host "5. Account Credentials" -ForegroundColor Cyan
Create-Secret "angelone-client-code" "AABL713311"
Create-Secret "angelone-password" "1012"
Create-Secret "angelone-totp-secret" "AGODKRXZZH6FHMYWMSBIK6KDXQ"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "All secrets created/updated!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Grant access to App Hosting backend using grant_secrets.ps1"
Write-Host "2. Verify secrets in Google Cloud Console:"
Write-Host "   https://console.cloud.google.com/security/secret-manager?project=$PROJECT_ID"
Write-Host ""
Write-Host "⚠️  SECURITY WARNING:" -ForegroundColor Red
Write-Host "After confirming secrets are created, DELETE the functions/.env.local file"
Write-Host "containing plaintext credentials!"
