import { initializeApp, getApps, getApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";
import { getFunctions } from "firebase/functions";

// Read the firebase webapp config from runtime env, with sensible fallbacks.
// During App Hosting builds the variable may be provided as `FIREBASE_WEBAPP_CONFIG` (BUILD/RUNTIME),
// while local dev often uses `NEXT_PUBLIC_FIREBASE_WEBAPP_CONFIG` (client-side). Support both.
function rawFirebaseConfig(): string | undefined {
  // Prefer explicit runtime var first, then public client-side var.
  const candidates = [
    process.env.FIREBASE_WEBAPP_CONFIG,
    process.env.FIREBASE_CONFIG,
    process.env.NEXT_PUBLIC_FIREBASE_WEBAPP_CONFIG,
    process.env.NEXT_PUBLIC_FIREBASE_CONFIG,
  ];
  for (let c of candidates) {
    if (typeof c === "string" && c.length) {
      // strip surrounding single or double quotes which sometimes appear in .env files
      let cleaned = c.replace(/^['\"]|['\"]$/g, "");
      return cleaned;
    }
  }
  return undefined;
}

let firebaseConfig: any = {};
const raw = rawFirebaseConfig();
if (raw) {
  // Try several parsing strategies to handle values that may be
  // - a raw JSON object string: {"apiKey":...}
  // - a quoted JSON string: "{\"apiKey\":...}"
  // - double-encoded / escaped JSON (common when inlined into client bundles)
  let parsed: any = undefined;

  function tryParse(s: string) {
    if (!s || typeof s !== 'string') return undefined;
    // quick trim
    let t = s.trim();
    // strip surrounding single or double quotes
    t = t.replace(/^['"]|['"]$/g, '');
    try {
      const p = JSON.parse(t);
      if (typeof p === 'string') return tryParse(p);
      return p;
    } catch (e) {
      // try unescaping common escape sequences then parse
      try {
        const unescaped = t.replace(/\\"/g, '"').replace(/\\\\/g, '\\');
        const p2 = JSON.parse(unescaped);
        if (typeof p2 === 'string') return tryParse(p2);
        return p2;
      } catch (e2) {
        return undefined;
      }
    }
  }

  // 1) Try straightforward parsing attempts
  parsed = tryParse(raw);

  // 2) If that failed, attempt to extract a balanced JSON object from the string
  if (!parsed && typeof raw === 'string') {
    const s = raw;
    const first = s.indexOf('{');
    if (first !== -1) {
      // find matching closing brace by counting
      let depth = 0;
      let end = -1;
      for (let i = first; i < s.length; i++) {
        const ch = s[i];
        if (ch === '{') depth++;
        else if (ch === '}') {
          depth--;
          if (depth === 0) { end = i; break; }
        }
      }
      if (end !== -1) {
        const candidate = s.substring(first, end + 1);
        parsed = tryParse(candidate);
      }
    }
  }

  if (!parsed) {
    console.error("Failed to parse Firebase webapp config JSON from env. Raw value (first 200 chars):", raw?.substring(0, 200));
  }

  if (parsed && typeof parsed === 'object') {
    firebaseConfig = parsed;
    if (!firebaseConfig.apiKey) {
      console.warn("Firebase config parsed but missing apiKey. Config keys:", Object.keys(firebaseConfig));
    }
  } else {
    firebaseConfig = {};
  }
} else {
  firebaseConfig = {};
}

// Fallback: construct config from individual NEXT_PUBLIC_* or FIREBASE_* env vars
if ((!firebaseConfig || !firebaseConfig.apiKey)) {
  // Trim and normalize individual env vars to avoid stray CR/LF or whitespace
  function trimEnvVal(v?: string) {
    if (typeof v !== 'string' || !v.length) return undefined;
    // remove common CR/LF and surrounding whitespace
    const cleaned = v.replace(/\r?\n/g, '').trim();
    return cleaned.length ? cleaned : undefined;
  }

  const fallback = {
    apiKey: trimEnvVal(process.env.NEXT_PUBLIC_FIREBASE_API_KEY) || trimEnvVal(process.env.FIREBASE_API_KEY) || undefined,
    authDomain: trimEnvVal(process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN) || trimEnvVal(process.env.FIREBASE_AUTH_DOMAIN) || undefined,
    projectId: trimEnvVal(process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID) || trimEnvVal(process.env.FIREBASE_PROJECT_ID) || undefined,
    storageBucket: trimEnvVal(process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET) || trimEnvVal(process.env.FIREBASE_STORAGE_BUCKET) || undefined,
    messagingSenderId: trimEnvVal(process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID) || trimEnvVal(process.env.FIREBASE_MESSAGING_SENDER_ID) || undefined,
    appId: trimEnvVal(process.env.NEXT_PUBLIC_FIREBASE_APP_ID) || trimEnvVal(process.env.FIREBASE_APP_ID) || undefined,
    measurementId: trimEnvVal(process.env.NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID) || trimEnvVal(process.env.FIREBASE_MEASUREMENT_ID) || undefined,
  } as any;
  // If we found an apiKey in individual vars, use this fallback
  if (fallback.apiKey) {
    firebaseConfig = fallback;
    console.info('Using individual NEXT_PUBLIC_FIREBASE_* env vars to initialize Firebase client.');
  }
}

// If the config is missing an apiKey, initialization of the client SDK may fail with
// a generic "auth/invalid-api-key" error. Surface a clearer message to help debugging.
if (!firebaseConfig || !firebaseConfig.apiKey) {
  // If running in the browser, fall back to letting client code use `NEXT_PUBLIC_*`.
  if (typeof window !== "undefined") {
    console.warn("Firebase webapp config missing at runtime; client-side may still initialize from NEXT_PUBLIC env.");
  } else {
    // Server-side: log and provide guidance. We avoid initializing with an empty config.
    console.error("Missing Firebase webapp config (apiKey). Ensure FIREBASE_WEBAPP_CONFIG or NEXT_PUBLIC_FIREBASE_WEBAPP_CONFIG is provided at runtime and exposed in App Hosting with availability 'RUNTIME'.");
  }
}

// Initialize Firebase only when we have a valid-looking config to avoid obscure errors.
const app = (firebaseConfig && firebaseConfig.apiKey)
  ? (!getApps().length ? initializeApp(firebaseConfig) : getApp())
  : undefined;

export const auth = app ? getAuth(app) : undefined as any;
export const db = app ? getFirestore(app) : undefined as any;
export const functions = app ? getFunctions(app, 'us-central1') : undefined as any;
export default app;
