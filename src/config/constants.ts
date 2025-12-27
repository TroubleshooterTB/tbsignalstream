/**
 * Application configuration constants
 * Centralized place for all magic numbers and configuration values
 */

// API Timeouts
export const TIMEOUTS = {
  /** Default API request timeout */
  API_REQUEST: 5000,
  /** Health check interval */
  HEALTH_CHECK: 30000,
  /** Live price fetch interval */
  PRICE_FETCH: 5000,
  /** Bot status polling interval */
  BOT_STATUS_POLL: 10000,
} as const;

// Firestore Collection Names
export const COLLECTIONS = {
  BOT_CONFIGS: 'bot_configs',
  TRADING_SIGNALS: 'trading_signals',
  BOT_ACTIVITY: 'bot_activity',
  ANGEL_ONE_CREDS: 'angel_one_credentials',
  USER_CREDENTIALS: 'user_credentials',
  ORDERS: 'orders',
  POSITIONS: 'trading_positions',
  BACKTEST_RESULTS: 'backtest_results',
} as const;

// Bot Default Configuration
export const BOT_DEFAULTS = {
  /** Maximum number of concurrent positions */
  MAX_POSITIONS: 5,
  /** Default position size in INR */
  POSITION_SIZE: 50000,
  /** Default trading strategy */
  STRATEGY: 'alpha-ensemble' as const,
  /** Default trading mode */
  MODE: 'paper' as const,
} as const;

// Trading Strategies
export const STRATEGIES = {
  ALPHA_ENSEMBLE: 'alpha-ensemble',
  DEFINING_ORDER: 'defining',
  IRONCLAD: 'ironclad',
  PATTERN: 'pattern',
  BOTH: 'both',
} as const;

// Trading Modes
export const TRADING_MODES = {
  PAPER: 'paper',
  LIVE: 'live',
  REPLAY: 'replay',
} as const;

// Cache Configuration
export const CACHE = {
  /** Cache TTL for live prices (5 seconds) */
  LIVE_PRICES_TTL: 5000,
  /** Cache TTL for bot status (3 seconds) */
  BOT_STATUS_TTL: 3000,
} as const;

// UI Configuration
export const UI = {
  /** Maximum activity feed items */
  MAX_ACTIVITY_ITEMS: 50,
  /** Maximum alerts shown */
  MAX_ALERTS: 20,
  /** Toast notification duration for errors */
  ERROR_TOAST_DURATION: 10000,
  /** Toast notification duration for success */
  SUCCESS_TOAST_DURATION: 5000,
} as const;

// Angel One API Configuration
export const ANGEL_ONE = {
  /** Base URL for Angel One Smart API */
  BASE_URL: 'https://apiconnect.angelbroking.com',
  /** WebSocket URL for live data */
  WS_URL: 'wss://smartapisocket.angelone.in/smart-stream',
} as const;
