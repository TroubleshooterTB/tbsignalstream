/**
 * Nifty 50 Stock Symbols for Trading
 * Complete list of all 50 stocks in the Nifty 50 index
 */

export const NIFTY_50_SYMBOLS = [
  'ADANIENT-EQ',    // Adani Enterprises
  'ADANIPORTS-EQ',  // Adani Ports
  'APOLLOHOSP-EQ',  // Apollo Hospitals
  'ASIANPAINT-EQ',  // Asian Paints
  'AXISBANK-EQ',    // Axis Bank
  'BAJAJ-AUTO-EQ',  // Bajaj Auto
  'BAJFINANCE-EQ',  // Bajaj Finance
  'BAJAJFINSV-EQ',  // Bajaj Finserv
  'BPCL-EQ',        // BPCL
  'BHARTIARTL-EQ',  // Bharti Airtel
  'BRITANNIA-EQ',   // Britannia
  'CIPLA-EQ',       // Cipla
  'COALINDIA-EQ',   // Coal India
  'DIVISLAB-EQ',    // Divi's Lab
  'DRREDDY-EQ',     // Dr Reddy's
  'EICHERMOT-EQ',   // Eicher Motors
  'GRASIM-EQ',      // Grasim
  'HCLTECH-EQ',     // HCL Tech
  'HDFCBANK-EQ',    // HDFC Bank
  'HDFCLIFE-EQ',    // HDFC Life
  'HEROMOTOCO-EQ',  // Hero MotoCorp
  'HINDALCO-EQ',    // Hindalco
  'HINDUNILVR-EQ',  // Hindustan Unilever
  'ICICIBANK-EQ',   // ICICI Bank
  'ITC-EQ',         // ITC
  'INDUSINDBK-EQ',  // IndusInd Bank
  'INFY-EQ',        // Infosys
  'JSWSTEEL-EQ',    // JSW Steel
  'KOTAKBANK-EQ',   // Kotak Bank
  'LT-EQ',          // L&T
  'M&M-EQ',         // M&M
  'MARUTI-EQ',      // Maruti Suzuki
  'NTPC-EQ',        // NTPC
  'NESTLEIND-EQ',   // Nestle India
  'ONGC-EQ',        // ONGC
  'POWERGRID-EQ',   // Power Grid
  'RELIANCE-EQ',    // Reliance
  'SBILIFE-EQ',     // SBI Life
  'SBIN-EQ',        // SBI
  'SUNPHARMA-EQ',   // Sun Pharma
  'TCS-EQ',         // TCS
  'TATACONSUM-EQ',  // Tata Consumer
  'TATAMOTORS-EQ',  // Tata Motors
  'TATASTEEL-EQ',   // Tata Steel
  'TECHM-EQ',       // Tech Mahindra
  'TITAN-EQ',       // Titan
  'ULTRACEMCO-EQ',  // UltraTech Cement
  'UPL-EQ',         // UPL
  'WIPRO-EQ',       // Wipro
];

export const NIFTY_50_SYMBOLS_STRING = NIFTY_50_SYMBOLS.join(',');

// Categorized by sector for advanced filtering
export const NIFTY_50_BY_SECTOR = {
  'Banking & Finance': [
    'AXISBANK-EQ',
    'BAJFINANCE-EQ',
    'BAJAJFINSV-EQ',
    'HDFCBANK-EQ',
    'HDFCLIFE-EQ',
    'ICICIBANK-EQ',
    'INDUSINDBK-EQ',
    'KOTAKBANK-EQ',
    'SBILIFE-EQ',
    'SBIN-EQ',
  ],
  'IT & Technology': [
    'HCLTECH-EQ',
    'INFY-EQ',
    'TCS-EQ',
    'TECHM-EQ',
    'WIPRO-EQ',
  ],
  'Auto & Auto Components': [
    'BAJAJ-AUTO-EQ',
    'EICHERMOT-EQ',
    'HEROMOTOCO-EQ',
    'M&M-EQ',
    'MARUTI-EQ',
    'TATAMOTORS-EQ',
  ],
  'Pharma & Healthcare': [
    'APOLLOHOSP-EQ',
    'CIPLA-EQ',
    'DIVISLAB-EQ',
    'DRREDDY-EQ',
    'SUNPHARMA-EQ',
  ],
  'Energy & Power': [
    'BPCL-EQ',
    'COALINDIA-EQ',
    'NTPC-EQ',
    'ONGC-EQ',
    'POWERGRID-EQ',
    'RELIANCE-EQ',
  ],
  'Metals & Mining': [
    'HINDALCO-EQ',
    'JSWSTEEL-EQ',
    'TATASTEEL-EQ',
  ],
  'FMCG & Consumer': [
    'ASIANPAINT-EQ',
    'BRITANNIA-EQ',
    'HINDUNILVR-EQ',
    'ITC-EQ',
    'NESTLEIND-EQ',
    'TATACONSUM-EQ',
    'TITAN-EQ',
  ],
  'Infrastructure & Construction': [
    'ADANIENT-EQ',
    'ADANIPORTS-EQ',
    'GRASIM-EQ',
    'LT-EQ',
    'ULTRACEMCO-EQ',
  ],
  'Telecom': [
    'BHARTIARTL-EQ',
  ],
  'Chemicals': [
    'UPL-EQ',
  ],
};

export function getSymbolsBySector(sector: keyof typeof NIFTY_50_BY_SECTOR): string[] {
  return NIFTY_50_BY_SECTOR[sector] || [];
}

export function getAllNifty50Symbols(): string[] {
  return NIFTY_50_SYMBOLS;
}
