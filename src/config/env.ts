/**
 * Environment variable validation and type-safe access
 * Client-safe implementation
 */

const isServer = typeof window === 'undefined';

// Direct access to avoid process.env issues on client
const getClientEnv = (key: string) => {
  if (isServer) {
    return process.env[key];
  }
  // On client, Next.js injects NEXT_PUBLIC_ vars as string literals during build
  // Access them directly to avoid process.env runtime issues
  switch(key) {
    case 'NEXT_PUBLIC_FIREBASE_API_KEY': return process.env.NEXT_PUBLIC_FIREBASE_API_KEY;
    case 'NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN': return process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN;
    case 'NEXT_PUBLIC_FIREBASE_PROJECT_ID': return process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID;
    case 'NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET': return process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET;
    case 'NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID': return process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID;
    case 'NEXT_PUBLIC_FIREBASE_APP_ID': return process.env.NEXT_PUBLIC_FIREBASE_APP_ID;
    case 'NEXT_PUBLIC_TRADING_BOT_URL': return process.env.NEXT_PUBLIC_TRADING_BOT_URL;
    case 'NEXT_PUBLIC_SENTRY_DSN': return process.env.NEXT_PUBLIC_SENTRY_DSN;
    case 'NODE_ENV': return process.env.NODE_ENV;
    default: return process.env[key];
  }
};

function getEnvVar(key: string, required: boolean = true): string {
  try {
    const value = getClientEnv(key);
    
    if (required && !value) {
      if (isServer) {
        throw new Error(`Missing required environment variable: ${key}`);
      }
      console.warn(`Missing environment variable on client: ${key}`);
      return '';
    }
    
    return value || '';
  } catch (error) {
    if (isServer) {
      throw error;
    }
    console.error(`Error accessing env var ${key}:`, error);
    return '';
  }
}

function validateUrl(url: string, name: string): string {
  if (!url) return '';
  
  try {
    new URL(url);
    return url;
  } catch {
    if (isServer) {
      throw new Error(`Invalid URL for ${name}: ${url}`);
    }
    return url; // Return as-is on client, don't crash
  }
}

/**
 * Validated and type-safe environment variables
 */
export const env = {
  // Firebase Configuration
  firebase: {
    apiKey: getEnvVar('NEXT_PUBLIC_FIREBASE_API_KEY'),
    authDomain: getEnvVar('NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN'),
    projectId: getEnvVar('NEXT_PUBLIC_FIREBASE_PROJECT_ID'),
    storageBucket: getEnvVar('NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET'),
    messagingSenderId: getEnvVar('NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID'),
    appId: getEnvVar('NEXT_PUBLIC_FIREBASE_APP_ID'),
  },

  // Backend URLs
  backendUrl: validateUrl(
    getEnvVar('NEXT_PUBLIC_TRADING_BOT_URL', false) || 
    'https://trading-bot-service-vmxfbt7qiq-el.a.run.app',
    'Backend URL'
  ),

  // Environment
  get nodeEnv() {
    try {
      return process.env.NODE_ENV || 'development';
    } catch {
      return 'development';
    }
  },
  get isDevelopment() {
    try {
      return process.env.NODE_ENV === 'development';
    } catch {
      return false;
    }
  },
  get isProduction() {
    try {
      return process.env.NODE_ENV === 'production';
    } catch {
      return true; // Assume production on client if we can't determine
    }
  },

  // Optional - Error Tracking
  sentryDsn: getEnvVar('NEXT_PUBLIC_SENTRY_DSN', false),
} as const;

// Validate on import (server-side only, fail fast during build)
if (isServer) {
  console.log('✅ Environment variables validated successfully');
  console.log(`   Environment: ${env.nodeEnv}`);
  console.log(`   Firebase Project: ${env.firebase.projectId}`);
  console.log(`   Backend URL: ${env.backendUrl}`);
}
