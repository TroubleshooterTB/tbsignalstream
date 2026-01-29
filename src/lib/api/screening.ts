/**
 * Screening API Client
 * Manages screening modes and presets
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://trading-bot-service-818546654122.us-central1.run.app';

export interface ScreeningMode {
  name: 'RELAXED' | 'MEDIUM' | 'STRICT';
  description: string;
  expected_signals_per_day: number;
  expected_pass_rate: string;
  risk_level: {
    max_position: string;
    max_var: string;
  };
}

export interface ScreeningModesResponse {
  modes: ScreeningMode[];
}

export interface SetModeRequest {
  user_id: string;
  mode: 'RELAXED' | 'MEDIUM' | 'STRICT';
}

export interface CurrentModeResponse {
  user_id: string;
  current_mode: 'RELAXED' | 'MEDIUM' | 'STRICT';
  updated_at: string;
}

/**
 * Get all available screening modes
 */
export async function getScreeningModes(): Promise<ScreeningMode[]> {
  const response = await fetch(`${API_BASE}/api/screening/modes`);
  
  if (!response.ok) {
    throw new Error(`Failed to get screening modes: ${response.statusText}`);
  }
  
  const data: ScreeningModesResponse = await response.json();
  return data.modes;
}

/**
 * Set screening mode for user
 */
export async function setScreeningMode(userId: string, mode: 'RELAXED' | 'MEDIUM' | 'STRICT'): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`${API_BASE}/api/screening/set-mode`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user_id: userId,
      mode: mode,
    }),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to set screening mode: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Get current screening mode for user
 */
export async function getCurrentMode(userId: string): Promise<CurrentModeResponse> {
  const response = await fetch(`${API_BASE}/api/screening/current-mode?user_id=${userId}`);
  
  if (!response.ok) {
    throw new Error(`Failed to get current mode: ${response.statusText}`);
  }
  
  return response.json();
}
