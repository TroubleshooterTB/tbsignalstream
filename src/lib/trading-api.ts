// API client for trading Cloud Functions
import { auth } from '@/lib/firebase';

const CLOUD_FUNCTIONS_BASE = 'https://us-central1-tbsignalstream.cloudfunctions.net';

async function callCloudFunction(functionName: string, data: any = {}) {
  const user = auth.currentUser;
  if (!user) {
    throw new Error('User not authenticated');
  }

  const idToken = await user.getIdToken();

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
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: response.statusText }));
    throw new Error(error.error || error.message || 'API call failed');
  }

  return response.json();
}

// WebSocket Functions
export const websocketApi = {
  initialize: () => callCloudFunction('initializeWebSocket'),
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
    maxPositions?: number;
    positionSize?: number;
  }) => callCloudFunction('startLiveTradingBot', config),
  
  stop: () => callCloudFunction('stopLiveTradingBot'),
};

// Market Data Function
export const marketDataApi = {
  get: (symbols: string[], interval: string = '5min') => 
    callCloudFunction('getMarketData', { symbols, interval }),
};
