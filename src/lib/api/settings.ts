/**
 * Settings API Client
 * Manages user settings, API keys, and integrations
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://trading-bot-service-818546654122.us-central1.run.app';

export interface UserSettings {
  user_id: string;
  telegram_enabled?: boolean;
  telegram_bot_token?: string;
  telegram_chat_id?: string;
  tradingview_enabled?: boolean;
  tradingview_webhook_secret?: string;
  tradingview_bypass_screening?: boolean;
  screening_mode?: 'RELAXED' | 'MEDIUM' | 'STRICT';
  notifications_enabled?: boolean;
}

export interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  permissions: string[];
  created_at: string;
  last_used?: string;
}

export interface ApiKeyGenerateRequest {
  user_id: string;
  name: string;
  permissions: string[];
}

export interface ApiKeyGenerateResponse {
  success: boolean;
  api_key: string; // Full key - shown ONCE
  key_id: string;
  key_prefix: string;
}

/**
 * Get user settings
 */
export async function getUserSettings(userId: string): Promise<UserSettings> {
  const response = await fetch(`${API_BASE}/api/settings/user?user_id=${userId}`);
  
  if (!response.ok) {
    if (response.status === 404) {
      // User not found - return defaults
      return {
        user_id: userId,
        telegram_enabled: false,
        tradingview_enabled: false,
        screening_mode: 'RELAXED',
        notifications_enabled: true
      };
    }
    throw new Error(`Failed to get settings: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Update user settings
 */
export async function updateUserSettings(settings: UserSettings): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`${API_BASE}/api/settings/user`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(settings),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to update settings: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Generate new API key
 */
export async function generateApiKey(request: ApiKeyGenerateRequest): Promise<ApiKeyGenerateResponse> {
  const response = await fetch(`${API_BASE}/api/settings/api-key/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to generate API key: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Revoke API key
 */
export async function revokeApiKey(keyId: string): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`${API_BASE}/api/settings/api-key/${keyId}`, {
    method: 'DELETE',
  });
  
  if (!response.ok) {
    throw new Error(`Failed to revoke API key: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Test Telegram notification
 */
export async function testTelegramNotification(
  userId: string,
  botToken: string,
  chatId: string,
  message?: string
): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`${API_BASE}/api/settings/telegram/test`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user_id: userId,
      bot_token: botToken,
      chat_id: chatId,
      message: message || '🎉 SignalStream Bot Connected! Your trading notifications are now active.',
    }),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || `Failed to test Telegram: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Get webhook URL for TradingView
 */
export function getWebhookUrl(): string {
  return `${API_BASE}/webhook/tradingview`;
}
