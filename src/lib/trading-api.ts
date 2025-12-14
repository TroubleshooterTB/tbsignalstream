// API client for trading Cloud Functions
import { auth } from '@/lib/firebase';

const CLOUD_FUNCTIONS_BASE = 'https://us-central1-tbsignalstream.cloudfunctions.net';

async function callCloudFunction(functionName: string, data: any = {}, timeoutMs: number = 30000) {
  const user = auth.currentUser;
  if (!user) {
    // Instead of throwing, log and return a rejected promise with better context
    const error = new Error('User not authenticated');
    console.log(`[${functionName}] Cannot call function - user not authenticated`);
    throw error;
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
  
  getBook: async () => {
    // Get orders from trading bot service
    const user = auth.currentUser;
    if (!user) {
      return { orders: [] };
    }
    
    const TRADING_BOT_SERVICE_URL = 'https://trading-bot-service-vmxfbt7qiq-el.a.run.app';
    const idToken = await user.getIdToken();
    
    try {
      const response = await fetch(`${TRADING_BOT_SERVICE_URL}/orders`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${idToken}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        console.error('Failed to fetch orders:', await response.text());
        return { orders: [] };
      }
      
      return response.json();
    } catch (error) {
      console.error('Error fetching orders:', error);
      return { orders: [] };
    }
  },
  
  getPositions: async () => {
    // Get positions from trading bot service
    const user = auth.currentUser;
    if (!user) {
      return { positions: [] };
    }
    
    const TRADING_BOT_SERVICE_URL = 'https://trading-bot-service-vmxfbt7qiq-el.a.run.app';
    const idToken = await user.getIdToken();
    
    try {
      const response = await fetch(`${TRADING_BOT_SERVICE_URL}/positions`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${idToken}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        console.error('Failed to fetch positions:', await response.text());
        return { positions: [] };
      }
      
      return response.json();
    } catch (error) {
      console.error('Error fetching positions:', error);
      return { positions: [] };
    }
  },
};

// Trading Bot Functions
export const tradingBotApi = {
  start: async (config: {
    symbols: string[];
    mode?: 'paper' | 'live';
    strategy?: 'pattern' | 'ironclad' | 'both' | 'defining';
    maxPositions?: number;
    positionSize?: number;
  }) => {
    const user = auth.currentUser;
    if (!user) {
      throw new Error('User not authenticated');
    }
    
    const TRADING_BOT_SERVICE_URL = 'https://trading-bot-service-vmxfbt7qiq-el.a.run.app';
    const idToken = await user.getIdToken();
    
    const response = await fetch(`${TRADING_BOT_SERVICE_URL}/start`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${idToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(config),
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Failed to start bot' }));
      throw new Error(error.error || 'Failed to start bot');
    }
    
    return response.json();
  },
  
  stop: async () => {
    const user = auth.currentUser;
    if (!user) {
      throw new Error('User not authenticated');
    }
    
    const TRADING_BOT_SERVICE_URL = 'https://trading-bot-service-vmxfbt7qiq-el.a.run.app';
    const idToken = await user.getIdToken();
    
    const response = await fetch(`${TRADING_BOT_SERVICE_URL}/stop`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${idToken}`,
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to stop bot');
    }
    
    return response.json();
  },
  
  status: async () => {
    // NEVER throw errors from status checks - always return gracefully
    try {
      const user = auth.currentUser;
      if (!user) {
        // Silently return stopped status if not authenticated
        console.log('[Bot Status] User not authenticated, returning stopped status');
        return { running: false, status: 'stopped' };
      }
      
      // Call Cloud Run service directly for status
      const TRADING_BOT_SERVICE_URL = 'https://trading-bot-service-vmxfbt7qiq-el.a.run.app';
      const idToken = await user.getIdToken();
      
      const response = await fetch(`${TRADING_BOT_SERVICE_URL}/status`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${idToken}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        console.warn(`[Bot Status] Check failed: ${response.statusText}`);
        return { running: false, status: 'stopped' };
      }
      
      const data = await response.json();
      console.log('[Bot Status] Received from server:', data);
      return data;
    } catch (error: any) {
      // Don't throw errors for status checks - just return stopped
      console.log('[Bot Status] Error fetching status, returning stopped:', error?.message || error);
      return { running: false, status: 'stopped' };
    }
  },
  
  healthCheck: async () => {
    const user = auth.currentUser;
    if (!user) {
      throw new Error('User not authenticated');
    }
    
    const TRADING_BOT_SERVICE_URL = 'https://trading-bot-service-vmxfbt7qiq-el.a.run.app';
    const idToken = await user.getIdToken();
    
    const response = await fetch(`${TRADING_BOT_SERVICE_URL}/health-check`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${idToken}`,
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Health check failed' }));
      throw new Error(error.error || 'Health check failed');
    }
    
    return response.json();
  },
};

// Market Data Function
export const marketDataApi = {
  get: (symbols: string[], interval: string = '5min') => 
    callCloudFunction('getMarketData', { symbols, interval }),
};

// Signals API
export const signalsApi = {
  getRecent: async () => {
    const user = auth.currentUser;
    if (!user) {
      return { signals: [] };
    }
    
    const TRADING_BOT_SERVICE_URL = 'https://trading-bot-service-vmxfbt7qiq-el.a.run.app';
    const idToken = await user.getIdToken();
    
    try {
      const response = await fetch(`${TRADING_BOT_SERVICE_URL}/signals`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${idToken}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        console.error('Failed to fetch signals:', await response.text());
        return { signals: [] };
      }
      
      return response.json();
    } catch (error) {
      console.error('Error fetching signals:', error);
      return { signals: [] };
    }
  },
};
