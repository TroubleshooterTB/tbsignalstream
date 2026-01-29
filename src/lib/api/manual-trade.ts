/**
 * Manual Trade API Client
 * Allows placing trades manually, bypassing screening
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://trading-bot-service-818546654122.us-central1.run.app';

export interface ManualTradeRequest {
  user_id: string;
  symbol: string;
  action: 'BUY' | 'SELL';
  quantity?: number;
  stop_loss_pct: number;
  target_pct: number;
  price?: number;
}

export interface QuickCloseRequest {
  user_id: string;
  symbol: string;
}

export interface CloseAllRequest {
  user_id: string;
  reason?: string;
}

/**
 * Place manual trade bypassing all screening
 */
export async function placeTrade(trade: ManualTradeRequest): Promise<{ success: boolean; message: string; signal_id?: string }> {
  const response = await fetch(`${API_BASE}/api/manual/place-trade`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(trade),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || `Failed to place trade: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Quick close specific position
 */
export async function quickClose(request: QuickCloseRequest): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`${API_BASE}/api/manual/quick-close`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || `Failed to close position: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Emergency close all positions
 */
export async function closeAll(request: CloseAllRequest): Promise<{ success: boolean; message: string; closed_count?: number }> {
  const response = await fetch(`${API_BASE}/api/manual/close-all`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || `Failed to close all positions: ${response.statusText}`);
  }
  
  return response.json();
}
