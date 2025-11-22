# Grant Firebase App Hosting access to Angel Broking secrets
# Run this script after creating secrets with setup_angel_secrets.ps1

$PROJECT_ID = "tbsignalstream"
$BACKEND_ID = "studio"  # Update this if your backend ID is different

cd "d:\Tushar 2.0\tbsignalstream_backup\tbsignalstream_backup"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Granting App Hosting Backend Access to Secrets" -ForegroundColor Cyan
Write-Host "Project: $PROJECT_ID" -ForegroundColor Yellow
Write-Host "Backend: $BACKEND_ID" -ForegroundColor Yellow
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# List of all Angel Broking secrets
$secrets = @(
    "angelone-trading-api-key",
    "angelone-trading-api-secret",
    "angelone-historical-api-key",
    "angelone-historical-api-secret",
    "angelone-market-api-key",
    "angelone-market-api-secret",
    "angelone-publisher-api-key",
    "angelone-publisher-api-secret",
    "angelone-client-code",
    "angelone-password",
    "angelone-totp-secret"
)

Write-Host "Listing App Hosting backends..." -ForegroundColor Cyan
firebase apphosting:backends:list

Write-Host "`n`nGranting access to all secrets..." -ForegroundColor Cyan

$count = 0
foreach ($secret in $secrets) {
    $count++
    Write-Host "[$count/$($secrets.Count)] Granting access to: $secret" -ForegroundColor Yellow
    
    firebase apphosting:secrets:grantaccess $secret --backend=$BACKEND_ID
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Success: $secret" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Failed: $secret" -ForegroundColor Red
        Write-Host "  You may need to grant access manually using:" -ForegroundColor Gray
        Write-Host "  firebase apphosting:secrets:grantaccess $secret --backend=$BACKEND_ID" -ForegroundColor Gray
    }
    Write-Host ""
}

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Grant access complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Verify access in Firebase Console"
Write-Host "2. Deploy your app with: firebase deploy --only apphosting:studio"
Write-Host "3. Or trigger a rebuild through the Firebase Console"
Write-Host ""
Write-Host "⚠️  If any secrets failed, run the grant command manually" -ForegroundColor Red
Write-Host "   firebase apphosting:secrets:grantaccess SECRET_NAME --backend=$BACKEND_ID" -ForegroundColor Gray
