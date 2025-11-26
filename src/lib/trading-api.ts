// API client for trading Cloud Functions
import { auth } from '@/lib/firebase';

const CLOUD_FUNCTIONS_BASE = 'https://us-central1-tbsignalstream.cloudfunctions.net';

async function callCloudFunction(functionName: string, data: any = {}, timeoutMs: number = 30000) {
  const user = auth.currentUser;
  if (!user) {
    throw new Error('User not authenticated');
  }

  const idToken = await user.getIdToken();

  // Create abort controller for timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(`${CLOUD_FUNCTIONS_BASE}/${functionName}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${idToken}`,
      },
      body: JSON.stringify({
        ...data,
        userId: user.uid,
      }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: response.statusText }));
      throw new Error(error.error || error.message || 'API call failed');
    }

    return response.json();
  } catch (error: any) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new Error('Request timed out - market may be closed or connection unavailable');
    }
    throw error;
  }
}

// WebSocket Functions
export const websocketApi = {
  initialize: () => callCloudFunction('initializeWebSocket', {}, 60000), // 60 second timeout for WebSocket
  subscribe: (symbols: string[]) => callCloudFunction('subscribeWebSocket', { symbols }),
  close: () => callCloudFunction('closeWebSocket'),
};

// Order Management Functions
export const orderApi = {
  place: (order: {
    symbol: string;
    quantity: number;
    orderType: 'MARKET' | 'LIMIT' | 'STOPLOSS_LIMIT' | 'STOPLOSS_MARKET';
    transactionType: 'BUY' | 'SELL';
    price?: number;
    triggerPrice?: number;
    productType?: 'INTRADAY' | 'DELIVERY';
  }) => callCloudFunction('placeOrder', order),
  
  modify: (orderId: string, modifications: {
    quantity?: number;
    price?: number;
    triggerPrice?: number;
  }) => callCloudFunction('modifyOrder', { orderId, ...modifications }),
  
  cancel: (orderId: string) => callCloudFunction('cancelOrder', { orderId }),
  
  getBook: () => callCloudFunction('getOrderBook'),
  
  getPositions: () => callCloudFunction('getPositions'),
};

// Trading Bot Functions
export const tradingBotApi = {
  start: (config: {
    symbols: string[];
    mode?: 'paper' | 'live';
    strategy?: 'pattern' | 'ironclad' | 'both';
    maxPositions?: number;
    positionSize?: number;
  }) => callCloudFunction('startLiveTradingBot', config),
  
  stop: () => callCloudFunction('stopLiveTradingBot'),
  
  status: async () => {
    try {
      // Call Cloud Run service directly for status
      const TRADING_BOT_SERVICE_URL = 'https://trading-bot-service-818546654122.us-central1.run.app';
      const user = auth.currentUser;
      if (!user) {
        throw new Error('User not authenticated');
      }
      const idToken = await user.getIdToken();
      
      const response = await fetch(`${TRADING_BOT_SERVICE_URL}/status`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${idToken}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`Status check failed: ${response.statusText}`);
      }
      
      return response.json();
    } catch (error: any) {
      console.error('Error fetching bot status:', error);
      return { running: false };
    }
  },
};

// Market Data Function
export const marketDataApi = {
  get: (symbols: string[], interval: string = '5min') => 
    callCloudFunction('getMarketData', { symbols, interval }),
};
