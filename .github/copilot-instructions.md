## Purpose
Give concise, repo-specific instructions so an AI coding agent can be productive immediately.

## Big Picture
- **Frontend**: A Next.js app in `src/app` (entry: `src/app/page.tsx`) that composes UI primitives from `src/components` (notably `src/components/ui/*`). The live demo component is `src/components/live-alerts-dashboard.tsx`.
- **Backend / Cloud Functions**: Python Cloud Functions live in `functions/` (entry examples: `functions/main.py`). They use the `firebase_functions` Python SDK and `firebase-admin` (see `functions/requirements.txt`).
- **Trading engines**: Core trading/analysis code exists as Python modules under `src/trading/` and also under `functions/src/trading/`. Treat these as the canonical algorithmic logic.
- **Persistence & Integration**: Firestore is the system-of-record; Cloud Functions read/write Firestore. Frontend reads Firestore and calls HTTPS functions. Secrets are provided via environment variables (see `ANGELONE_TRADING_API_KEY` used in `functions/main.py`).

## Key workflows (how to run / build / deploy)
- Install and run frontend locally:
  - `npm install`
  - `npm run dev` (dev server on port 9003 per `package.json` — `next dev -p 9003`).
- Build and start production:
  - `npm run build`
  - `npm start`
- GenKit (AI dev tools):
  - `npm run genkit:dev` and `npm run genkit:watch` run `src/ai/dev.ts` via `genkit`.
- Firebase hosting (App Hosting / backend named `studio`):
  - Deploy hosting only: `firebase deploy --only apphosting:studio --project=tbsignalstream`
  - Hosting config is in `firebase.json` (key: `apphosting` -> `backend: "studio"`).
- Cloud Functions (Python): deploy with your Firebase CLI using the functions directory; Python dependencies are listed in `functions/requirements.txt`.

## Project-specific conventions & patterns
- UI primitives live under `src/components/ui/` — prefer extending these rather than creating ad-hoc UI patterns.
- Client components explicitly include `"use client"` at the top (e.g., `live-alerts-dashboard.tsx`). Keep server-only code out of these files.
- Local simulation: Several components (e.g., `live-alerts-dashboard.tsx`) simulate trading behaviour and persist a `tradeLog` to `localStorage` — follow that convention when adding similar demos.
- Routing: Uses Next.js app-router conventions (`src/app/*`). Pages/route handlers go under `src/app`.
- AI features: `src/ai/` contains GenKit integrations and flows (e.g., `src/ai/dev.ts`, `src/ai/flows/*`). Prefer using existing GenKit helpers (`@genkit-ai/*`) for new AI features.

## Integration notes & gotchas for agents
- There are two distinct ecosystems: Node/Next (JS/TS) and Python Cloud Functions. When editing backend functions, modify files under `functions/` and update `functions/requirements.txt` for dependencies.
- `functions/main.py` expects production secrets in environment variables (example key: `ANGELONE_TRADING_API_KEY`). Do not hardcode secrets — use env vars or the Google Secret Manager (dependency present in `functions/requirements.txt`).
- Firestore collections referenced in the code:
  - `angel_one_credentials` — used by `functions/main.py` to store tokens.
- Be mindful of package boundaries: Node dependencies live in `package.json` (Next.js / GenKit), Python deps in `functions/requirements.txt`.

## Where to look for examples
- Frontend demo & patterns: `src/components/live-alerts-dashboard.tsx` (state, timers, UI primitives).
- Entry point: `src/app/page.tsx` (renders `LiveAlertsDashboard`).
- Cloud Function example: `functions/main.py` (https endpoint, token verification, Firestore writes, error handling).
- Python trading logic: `src/trading/*` and `functions/src/trading/*` — inspect both to understand duplication and sync needs.

## Practical guidance for edits and PRs
- Small UI changes: update `src/components/ui/*` primitives or the specific component file. Reuse variants and CSS classes from `tailwind.config.ts` and `globals.css`.
- Adding endpoints: add Python functions under `functions/`, update `requirements.txt`, and reference them from frontend via HTTPS calls (send Firebase ID token in `Authorization: Bearer <idToken>` as `functions/main.py` expects).
- Tests / linting: TypeScript typecheck via `npm run typecheck` and lint via `npm run lint`.
- Keep changes minimal and local: prefer adding a new UI primitive or function rather than large cross-cutting refactors without discussion.

## If you need more context
- Ask for clarifications about which Python module is canonical (`src/trading` vs `functions/src/trading`) before refactoring trading logic.
- If you plan to change deployment configuration, point to `firebase.json` and the `firebase` CLI commands shown above.

## Making deploys show in Cloud Build history
- Problem: `firebase deploy --only apphosting:studio` runs a local build and uploads artifacts, so GCP Cloud Build history may not show those builds.
- Workaround (recommended): Use the included Cloud Build pipeline which runs the build and deploy remotely so logs appear in Cloud Build history.
  - File: `cloudbuild.yaml` — runs `npm ci`, `npm run build`, installs `firebase-tools` and runs `firebase deploy --only apphosting:studio`.
  - Helper script: `./scripts/deploy-cloudbuild.sh [PROJECT_ID]` — submits the repo to Cloud Build and uses substitutions to set the Firebase project.
- Requirements: `gcloud` CLI authenticated (e.g. `gcloud auth login`) and Cloud Build API enabled for the project. Grant the Cloud Build service account the permissions needed to deploy to Firebase (e.g., `roles/firebasehosting.admin` or similar) if the deployment fails with permission errors.


---
If you'd like, I can refine any section, add examples for common tasks (e.g., add a new cloud function, or wire a new UI page), or generate PR templates that enforce these conventions.
