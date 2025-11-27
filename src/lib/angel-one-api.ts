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
 * All Nifty 50 NSE symbols with their tokens
 */
export const POPULAR_SYMBOLS = {
  // Banking & Finance
  AXISBANK: { exchange: 'NSE', symboltoken: '5900', tradingsymbol: 'AXISBANK-EQ' },
  BAJFINANCE: { exchange: 'NSE', symboltoken: '317', tradingsymbol: 'BAJFINANCE-EQ' },
  BAJAJFINSV: { exchange: 'NSE', symboltoken: '16675', tradingsymbol: 'BAJAJFINSV-EQ' },
  HDFCBANK: { exchange: 'NSE', symboltoken: '1333', tradingsymbol: 'HDFCBANK-EQ' },
  HDFCLIFE: { exchange: 'NSE', symboltoken: '467', tradingsymbol: 'HDFCLIFE-EQ' },
  ICICIBANK: { exchange: 'NSE', symboltoken: '1330', tradingsymbol: 'ICICIBANK-EQ' },
  INDUSINDBK: { exchange: 'NSE', symboltoken: '5258', tradingsymbol: 'INDUSINDBK-EQ' },
  KOTAKBANK: { exchange: 'NSE', symboltoken: '1922', tradingsymbol: 'KOTAKBANK-EQ' },
  SBILIFE: { exchange: 'NSE', symboltoken: '21808', tradingsymbol: 'SBILIFE-EQ' },
  SBIN: { exchange: 'NSE', symboltoken: '3045', tradingsymbol: 'SBIN-EQ' },
  
  // IT & Technology
  HCLTECH: { exchange: 'NSE', symboltoken: '7229', tradingsymbol: 'HCLTECH-EQ' },
  INFY: { exchange: 'NSE', symboltoken: '1594', tradingsymbol: 'INFY-EQ' },
  TCS: { exchange: 'NSE', symboltoken: '11536', tradingsymbol: 'TCS-EQ' },
  TECHM: { exchange: 'NSE', symboltoken: '13538', tradingsymbol: 'TECHM-EQ' },
  WIPRO: { exchange: 'NSE', symboltoken: '3787', tradingsymbol: 'WIPRO-EQ' },
  
  // Auto & Auto Components
  BAJAJ_AUTO: { exchange: 'NSE', symboltoken: '16669', tradingsymbol: 'BAJAJ-AUTO-EQ' },
  EICHERMOT: { exchange: 'NSE', symboltoken: '910', tradingsymbol: 'EICHERMOT-EQ' },
  HEROMOTOCO: { exchange: 'NSE', symboltoken: '1348', tradingsymbol: 'HEROMOTOCO-EQ' },
  M_M: { exchange: 'NSE', symboltoken: '10999', tradingsymbol: 'M&M-EQ' },
  MARUTI: { exchange: 'NSE', symboltoken: '10999', tradingsymbol: 'MARUTI-EQ' },
  TATAMOTORS: { exchange: 'NSE', symboltoken: '3456', tradingsymbol: 'TATAMOTORS-EQ' },
  
  // Pharma & Healthcare
  APOLLOHOSP: { exchange: 'NSE', symboltoken: '157', tradingsymbol: 'APOLLOHOSP-EQ' },
  CIPLA: { exchange: 'NSE', symboltoken: '694', tradingsymbol: 'CIPLA-EQ' },
  DIVISLAB: { exchange: 'NSE', symboltoken: '10940', tradingsymbol: 'DIVISLAB-EQ' },
  DRREDDY: { exchange: 'NSE', symboltoken: '881', tradingsymbol: 'DRREDDY-EQ' },
  SUNPHARMA: { exchange: 'NSE', symboltoken: '3351', tradingsymbol: 'SUNPHARMA-EQ' },
  
  // Energy & Power
  BPCL: { exchange: 'NSE', symboltoken: '526', tradingsymbol: 'BPCL-EQ' },
  COALINDIA: { exchange: 'NSE', symboltoken: '20374', tradingsymbol: 'COALINDIA-EQ' },
  NTPC: { exchange: 'NSE', symboltoken: '11630', tradingsymbol: 'NTPC-EQ' },
  ONGC: { exchange: 'NSE', symboltoken: '2475', tradingsymbol: 'ONGC-EQ' },
  POWERGRID: { exchange: 'NSE', symboltoken: '14977', tradingsymbol: 'POWERGRID-EQ' },
  RELIANCE: { exchange: 'NSE', symboltoken: '2885', tradingsymbol: 'RELIANCE-EQ' },
  
  // Metals & Mining
  HINDALCO: { exchange: 'NSE', symboltoken: '1363', tradingsymbol: 'HINDALCO-EQ' },
  JSWSTEEL: { exchange: 'NSE', symboltoken: '11723', tradingsymbol: 'JSWSTEEL-EQ' },
  TATASTEEL: { exchange: 'NSE', symboltoken: '3499', tradingsymbol: 'TATASTEEL-EQ' },
  
  // FMCG & Consumer
  ASIANPAINT: { exchange: 'NSE', symboltoken: '236', tradingsymbol: 'ASIANPAINT-EQ' },
  BRITANNIA: { exchange: 'NSE', symboltoken: '547', tradingsymbol: 'BRITANNIA-EQ' },
  HINDUNILVR: { exchange: 'NSE', symboltoken: '1394', tradingsymbol: 'HINDUNILVR-EQ' },
  ITC: { exchange: 'NSE', symboltoken: '1660', tradingsymbol: 'ITC-EQ' },
  NESTLEIND: { exchange: 'NSE', symboltoken: '17963', tradingsymbol: 'NESTLEIND-EQ' },
  TATACONSUM: { exchange: 'NSE', symboltoken: '3432', tradingsymbol: 'TATACONSUM-EQ' },
  TITAN: { exchange: 'NSE', symboltoken: '3506', tradingsymbol: 'TITAN-EQ' },
  
  // Infrastructure & Construction
  ADANIENT: { exchange: 'NSE', symboltoken: '25', tradingsymbol: 'ADANIENT-EQ' },
  ADANIPORTS: { exchange: 'NSE', symboltoken: '15083', tradingsymbol: 'ADANIPORTS-EQ' },
  GRASIM: { exchange: 'NSE', symboltoken: '1232', tradingsymbol: 'GRASIM-EQ' },
  LT: { exchange: 'NSE', symboltoken: '11483', tradingsymbol: 'LT-EQ' },
  ULTRACEMCO: { exchange: 'NSE', symboltoken: '11532', tradingsymbol: 'ULTRACEMCO-EQ' },
  
  // Telecom
  BHARTIARTL: { exchange: 'NSE', symboltoken: '10604', tradingsymbol: 'BHARTIARTL-EQ' },
  
  // Chemicals
  UPL: { exchange: 'NSE', symboltoken: '2889', tradingsymbol: 'UPL-EQ' },
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
