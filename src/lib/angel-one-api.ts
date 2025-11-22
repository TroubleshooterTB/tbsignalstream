/**
 * Angel One API Client - Fetches live market data
 */

import { auth } from './firebase';

export interface MarketDataRequest {
  mode: 'LTP' | 'OHLC' | 'FULL';
  exchangeTokens: {
    [exchange: string]: string[];
  };
}

export interface MarketQuote {
  exchange: string;
  tradingSymbol: string;
  symbolToken: string;
  ltp: number;
  open?: number;
  high?: number;
  low?: number;
  close?: number;
  lastTradeQty?: number;
  exchFeedTime?: string;
  exchTradeTime?: string;
}

export interface MarketDataResponse {
  status: boolean;
  message: string;
  data: {
    fetched: MarketQuote[];
  };
}

/**
 * Fetch live market data from Angel One
 */
export async function fetchMarketData(request: MarketDataRequest): Promise<MarketDataResponse> {
  const user = auth.currentUser;
  if (!user) {
    throw new Error('User not authenticated');
  }

  const idToken = await user.getIdToken();

  const response = await fetch('/api/marketData', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${idToken}`,
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to fetch market data');
  }

  return response.json();
}

/**
 * Popular NSE symbols with their tokens
 */
export const POPULAR_SYMBOLS = {
  RELIANCE: { exchange: 'NSE', symboltoken: '2885', tradingsymbol: 'RELIANCE-EQ' },
  HDFCBANK: { exchange: 'NSE', symboltoken: '1333', tradingsymbol: 'HDFCBANK-EQ' },
  INFY: { exchange: 'NSE', symboltoken: '1594', tradingsymbol: 'INFY-EQ' },
  TCS: { exchange: 'NSE', symboltoken: '11536', tradingsymbol: 'TCS-EQ' },
  ICICIBANK: { exchange: 'NSE', symboltoken: '1330', tradingsymbol: 'ICICIBANK-EQ' },
  ITC: { exchange: 'NSE', symboltoken: '1660', tradingsymbol: 'ITC-EQ' },
  SBIN: { exchange: 'NSE', symboltoken: '3045', tradingsymbol: 'SBIN-EQ' },
  BHARTIARTL: { exchange: 'NSE', symboltoken: '10604', tradingsymbol: 'BHARTIARTL-EQ' },
  AXISBANK: { exchange: 'NSE', symboltoken: '5900', tradingsymbol: 'AXISBANK-EQ' },
  KOTAKBANK: { exchange: 'NSE', symboltoken: '1922', tradingsymbol: 'KOTAKBANK-EQ' },
};

/**
 * Fetch LTP for popular symbols
 */
export async function fetchPopularStocksLTP(): Promise<Map<string, number>> {
  const symbols = Object.values(POPULAR_SYMBOLS);
  
  // Group by exchange
  const exchangeTokens: { [key: string]: string[] } = {};
  symbols.forEach(symbol => {
    if (!exchangeTokens[symbol.exchange]) {
      exchangeTokens[symbol.exchange] = [];
    }
    exchangeTokens[symbol.exchange].push(symbol.symboltoken);
  });

  const response = await fetchMarketData({
    mode: 'LTP',
    exchangeTokens,
  });

  // Map symbol tokens to LTP
  const ltpMap = new Map<string, number>();
  
  if (response.status && response.data?.fetched) {
    response.data.fetched.forEach(quote => {
      // Find the symbol name by token
      const symbolEntry = Object.entries(POPULAR_SYMBOLS).find(
        ([_, data]) => data.symboltoken === quote.symbolToken
      );
      if (symbolEntry) {
        ltpMap.set(symbolEntry[0], quote.ltp);
      }
    });
  }

  return ltpMap;
}
