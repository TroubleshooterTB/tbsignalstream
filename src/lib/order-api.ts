/**
 * Order Management API for Frontend
 * Provides functions to place, modify, and track orders
 */

import { auth } from './firebase';

export interface PlaceOrderRequest {
  symbol: string;
  token: string;
  exchange: string;
  transactionType: 'BUY' | 'SELL';
  orderType: 'MARKET' | 'LIMIT' | 'STOPLOSS_LIMIT' | 'STOPLOSS_MARKET';
  quantity: number;
  productType?: 'DELIVERY' | 'INTRADAY' | 'MARGIN';
  price?: number;
  triggerPrice?: number;
}

export interface OrderResponse {
  status: string;
  data?: {
    orderid: string;
    [key: string]: any;
  };
  error?: string;
}

/**
 * Place a new order
 */
export async function placeOrder(orderRequest: PlaceOrderRequest): Promise<OrderResponse> {
  const user = auth.currentUser;
  if (!user) {
    throw new Error('User not authenticated');
  }

  const idToken = await user.getIdToken();

  const response = await fetch('/api/placeOrder', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${idToken}`,
    },
    body: JSON.stringify(orderRequest),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to place order');
  }

  return response.json();
}

/**
 * Modify an existing order
 */
export async function modifyOrder(
  orderId: string,
  orderType: string,
  quantity: number,
  price?: number,
  triggerPrice?: number
): Promise<{status: string}> {
  const user = auth.currentUser;
  if (!user) {
    throw new Error('User not authenticated');
  }

  const idToken = await user.getIdToken();

  const response = await fetch('/api/modifyOrder', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${idToken}`,
    },
    body: JSON.stringify({
      orderId,
      orderType,
      quantity,
      price,
      triggerPrice
    }),
  });

  return response.json();
}

/**
 * Cancel an order
 */
export async function cancelOrder(orderId: string): Promise<{status: string}> {
  const user = auth.currentUser;
  if (!user) {
    throw new Error('User not authenticated');
  }

  const idToken = await user.getIdToken();

  const response = await fetch('/api/cancelOrder', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${idToken}`,
    },
    body: JSON.stringify({ orderId }),
  });

  return response.json();
}

/**
 * Get order book
 */
export async function getOrderBook(): Promise<any[]> {
  const user = auth.currentUser;
  if (!user) {
    throw new Error('User not authenticated');
  }

  const idToken = await user.getIdToken();

  const response = await fetch('/api/getOrderBook', {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${idToken}`,
    },
  });

  const result = await response.json();
  return result.data || [];
}

/**
 * Get current positions
 */
export async function getPositions(): Promise<any> {
  const user = auth.currentUser;
  if (!user) {
    throw new Error('User not authenticated');
  }

  const idToken = await user.getIdToken();

  const response = await fetch('/api/getPositions', {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${idToken}`,
    },
  });

  const result = await response.json();
  return result.data || {};
}

/**
 * Initialize WebSocket for live data streaming
 */
export async function initializeWebSocket(tokens: any[], mode: number = 1): Promise<any> {
  const user = auth.currentUser;
  if (!user) {
    throw new Error('User not authenticated');
  }

  const idToken = await user.getIdToken();

  const response = await fetch('/api/initializeWebSocket', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${idToken}`,
    },
    body: JSON.stringify({ tokens, mode }),
  });

  return response.json();
}

/**
 * Subscribe to WebSocket tokens
 */
export async function subscribeWebSocket(tokens: any[], mode: number = 1): Promise<any> {
  const user = auth.currentUser;
  if (!user) {
    throw new Error('User not authenticated');
  }

  const idToken = await user.getIdToken();

  const response = await fetch('/api/subscribeWebSocket', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${idToken}`,
    },
    body: JSON.stringify({ tokens, mode }),
  });

  return response.json();
}

/**
 * Close WebSocket connection
 */
export async function closeWebSocket(): Promise<any> {
  const user = auth.currentUser;
  if (!user) {
    throw new Error('User not authenticated');
  }

  const idToken = await user.getIdToken();

  const response = await fetch('/api/closeWebSocket', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${idToken}`,
    },
  });

  return response.json();
}

/**
 * Start live trading bot with real-time execution
 * @param symbols - Array of symbol tokens to trade
 * @param interval - Candle interval (e.g., '5minute', '15minute')
 */
export async function startLiveTradingBot(symbols: string[], interval: string = '5minute'): Promise<any> {
  const user = auth.currentUser;
  if (!user) {
    throw new Error('User not authenticated');
  }

  const idToken = await user.getIdToken();

  const response = await fetch('/api/startLiveTradingBot', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${idToken}`,
    },
    body: JSON.stringify({ symbols, interval }),
  });

  return response.json();
}

/**
 * Stop live trading bot
 */
export async function stopLiveTradingBot(): Promise<any> {
  const user = auth.currentUser;
  if (!user) {
    throw new Error('User not authenticated');
  }

  const idToken = await user.getIdToken();

  const response = await fetch('/api/stopLiveTradingBot', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${idToken}`,
    },
  });

  return response.json();
}
