/**
 * Centralized notification helpers
 * Provides consistent toast notifications across the app
 */

import { toast } from 'sonner';

export const notify = {
  /**
   * Show success notification
   */
  success: (title: string, description?: string) => {
    toast.success(title, { description });
  },

  /**
   * Show error notification with longer duration
   */
  error: (title: string, description?: string) => {
    toast.error(title, { 
      description,
      duration: 10000, // 10 seconds for errors
    });
  },

  /**
   * Show warning notification
   */
  warning: (title: string, description?: string) => {
    toast.warning(title, { description });
  },

  /**
   * Show info notification
   */
  info: (title: string, description?: string) => {
    toast.info(title, { description });
  },

  /**
   * Show bot error with standard formatting
   */
  botError: (errorMessage: string) => {
    toast.error('❌ Bot Error', {
      description: errorMessage,
      duration: 10000,
    });
  },

  /**
   * Show bot started notification
   */
  botStarted: (mode: 'paper' | 'live' | 'replay', strategy: string) => {
    toast.success('🤖 Bot Started', {
      description: `Mode: ${mode.toUpperCase()} | Strategy: ${strategy}`,
    });
  },

  /**
   * Show bot stopped notification
   */
  botStopped: () => {
    toast.info('Bot Stopped', {
      description: 'Trading bot has been stopped',
    });
  },

  /**
   * Show WebSocket connection status
   */
  wsConnected: () => {
    toast.success('WebSocket Connected', {
      description: 'Live market data streaming active',
    });
  },

  wsDisconnected: () => {
    toast.info('WebSocket Disconnected', {
      description: 'Live market data stopped',
    });
  },

  /**
   * Show market closed notification (info, not error)
   */
  marketClosed: () => {
    toast.info('Market Closed', {
      description: 'Trading unavailable outside market hours',
    });
  },
};
