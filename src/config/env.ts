/**
 * Environment variable validation and type-safe access
 * Validates all required environment variables at startup
 */

function getEnvVar(key: string, required: boolean = true): string {
  const value = process.env[key];
  
  if (required && !value) {
    throw new Error(`Missing required environment variable: ${key}`);
  }
  
  return value || '';
}

function validateUrl(url: string, name: string): string {
  try {
    new URL(url);
    return url;
  } catch {
    throw new Error(`Invalid URL for ${name}: ${url}`);
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
  nodeEnv: getEnvVar('NODE_ENV', false) || 'development',
  isDevelopment: process.env.NODE_ENV === 'development',
  isProduction: process.env.NODE_ENV === 'production',

  // Optional - Error Tracking
  sentryDsn: getEnvVar('NEXT_PUBLIC_SENTRY_DSN', false),
} as const;

// Validate on import (fail fast)
if (typeof window === 'undefined') {
  console.log('✅ Environment variables validated successfully');
  console.log(`   Environment: ${env.nodeEnv}`);
  console.log(`   Firebase Project: ${env.firebase.projectId}`);
  console.log(`   Backend URL: ${env.backendUrl}`);
}
