#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scripts/deploy-cloudbuild.sh [PROJECT_ID]
# If PROJECT_ID is omitted, defaults to 'tbsignalstream'.

PROJECT_ID=${1:-tbsignalstream}

echo "Submitting Cloud Build to build & deploy to Firebase project: ${PROJECT_ID}"

gcloud builds submit --config=cloudbuild.yaml --substitutions=_FIREBASE_PROJECT=${PROJECT_ID} .

echo "Build submitted. Check Cloud Build history in GCP console for logs."
