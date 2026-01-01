/**
 * Environment variable validation and type-safe access
 * Client-safe implementation - only validates on server side
 */

const isServer = typeof window === 'undefined';

function getEnvVar(key: string, required: boolean = true): string {
  // On client, only NEXT_PUBLIC_ prefixed vars are available
  const value = process.env[key];
  
  if (required && !value) {
    // Only throw during server-side/build time
    if (isServer) {
      throw new Error(`Missing required environment variable: ${key}`);
    }
    // Silently return empty string on client to prevent crashes
    return '';
  }
  
  return value || '';
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
    console.warn(`Invalid URL for ${name}: ${url}`);
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
  nodeEnv: getEnvVar('NODE_ENV', false) || 'development',
  isDevelopment: process.env.NODE_ENV === 'development',
  isProduction: process.env.NODE_ENV === 'production',

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
