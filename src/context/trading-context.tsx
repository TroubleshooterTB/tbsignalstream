"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { websocketApi, tradingBotApi } from '@/lib/trading-api';
import { useToast } from '@/hooks/use-toast';
import { NIFTY_50_SYMBOLS_STRING } from '@/lib/nifty50-symbols';

interface TradingState {
  // WebSocket state
  isWebSocketConnected: boolean;
  isWebSocketLoading: boolean;
  
  // Trading bot state
  isBotRunning: boolean;
  isBotLoading: boolean;
  botConfig: {
    symbols: string;
    mode: 'paper' | 'live';
    strategy: 'pattern' | 'ironclad' | 'both';
    maxPositions: string;
    positionSize: string;
  };
}

interface TradingContextType extends TradingState {
  // WebSocket methods
  connectWebSocket: () => Promise<void>;
  disconnectWebSocket: () => Promise<void>;
  
  // Trading bot methods
  startTradingBot: () => Promise<void>;
  stopTradingBot: () => Promise<void>;
  updateBotConfig: (config: Partial<TradingState['botConfig']>) => void;
  
  // Polling for bot status
  refreshBotStatus: () => Promise<void>;
}

const TradingContext = createContext<TradingContextType | undefined>(undefined);

export function TradingProvider({ children }: { children: React.ReactNode }) {
  const [isMounted, setIsMounted] = useState(false);
  const { toast } = useToast();
  
  // WebSocket state
  const [isWebSocketConnected, setIsWebSocketConnected] = useState(false);
  const [isWebSocketLoading, setIsWebSocketLoading] = useState(false);
  
  // Trading bot state
  const [isBotRunning, setIsBotRunning] = useState(false);
  const [isBotLoading, setIsBotLoading] = useState(false);
  const [botConfig, setBotConfig] = useState({
    symbols: NIFTY_50_SYMBOLS_STRING, // All Nifty 50 stocks
    mode: 'paper' as 'paper' | 'live',
    strategy: 'pattern' as 'pattern' | 'ironclad' | 'both',
    maxPositions: '5', // Increased from 3 to allow more opportunities
    positionSize: '10000', // ₹10,000 per position
  });

  useEffect(() => {
    setIsMounted(true);
  }, []);
  
  // WebSocket methods
  const connectWebSocket = useCallback(async () => {
    setIsWebSocketLoading(true);
    try {
      const result = await websocketApi.initialize();
      setIsWebSocketConnected(true);
      toast({
        title: 'WebSocket Connected',
        description: result.message || 'Successfully connected to live market data',
      });
    } catch (error: any) {
      toast({
        title: 'Connection Failed',
        description: error.message,
        variant: 'destructive',
      });
    } finally {
      setIsWebSocketLoading(false);
    }
  }, [toast]);
  
  const disconnectWebSocket = useCallback(async () => {
    setIsWebSocketLoading(true);
    try {
      await websocketApi.close();
      setIsWebSocketConnected(false);
      toast({
        title: 'WebSocket Disconnected',
        description: 'Successfully closed live market data connection',
      });
    } catch (error: any) {
      toast({
        title: 'Disconnect Failed',
        description: error.message,
        variant: 'destructive',
      });
    } finally {
      setIsWebSocketLoading(false);
    }
  }, [toast]);
  
  // Poll bot status from backend
  const refreshBotStatus = useCallback(async () => {
    try {
      const status = await tradingBotApi.status();
      const isRunning = status.running === true;
      setIsBotRunning(isRunning);
    } catch (error) {
      // If status check fails, assume bot is not running
      console.error('Error fetching bot status:', error);
      setIsBotRunning(false);
    }
  }, []);
  
  // Trading bot methods
  const startTradingBot = useCallback(async () => {
    // Check if already running before making API call
    if (isBotRunning) {
      toast({
        title: 'Bot Already Running',
        description: 'Trading bot is already active',
      });
      return;
    }
    
    setIsBotLoading(true);
    try {
      const symbols = botConfig.symbols.split(',').map(s => s.trim()).filter(Boolean);
      
      if (symbols.length === 0) {
        toast({
          title: 'Validation Error',
          description: 'Please enter at least one symbol',
          variant: 'destructive',
        });
        return;
      }

      const result = await tradingBotApi.start({
        symbols,
        mode: botConfig.mode,
        strategy: botConfig.strategy,
        maxPositions: parseInt(botConfig.maxPositions),
        positionSize: parseFloat(botConfig.positionSize),
      });
      
      setIsBotRunning(true);
      toast({
        title: 'Trading Bot Started',
        description: `Bot is now ${botConfig.mode === 'paper' ? 'paper trading' : 'live trading'} with ${symbols.length} symbols`,
      });
    } catch (error: any) {
      // Check if bot is already running
      if (error.message?.includes('already running') || error.message?.includes('400')) {
        setIsBotRunning(true);
        // Refresh status to sync
        refreshBotStatus();
        toast({
          title: 'Bot Already Running',
          description: 'Trading bot is already active',
        });
      } else {
        toast({
          title: 'Failed to Start Bot',
          description: error.message,
          variant: 'destructive',
        });
      }
    } finally {
      setIsBotLoading(false);
    }
  }, [botConfig, toast, isBotRunning, refreshBotStatus]);
  
  const stopTradingBot = useCallback(async () => {
    setIsBotLoading(true);
    try {
      await tradingBotApi.stop();
      setIsBotRunning(false);
      toast({
        title: 'Trading Bot Stopped',
        description: 'Bot has been successfully stopped',
      });
    } catch (error: any) {
      toast({
        title: 'Failed to Stop Bot',
        description: error.message,
        variant: 'destructive',
      });
    } finally {
      setIsBotLoading(false);
    }
  }, [toast]);
  
  const updateBotConfig = useCallback((newConfig: Partial<typeof botConfig>) => {
    setBotConfig(prev => ({ ...prev, ...newConfig }));
  }, []);
  
  // Poll bot status every 10 seconds (only on client)
  useEffect(() => {
    if (!isMounted) return;
    
    const interval = setInterval(() => {
      refreshBotStatus();
    }, 10000);
    
    // Initial status check
    refreshBotStatus();
    
    return () => clearInterval(interval);
  }, [refreshBotStatus, isMounted]);
  
  const value: TradingContextType = {
    // State
    isWebSocketConnected,
    isWebSocketLoading,
    isBotRunning,
    isBotLoading,
    botConfig,
    
    // Methods
    connectWebSocket,
    disconnectWebSocket,
    startTradingBot,
    stopTradingBot,
    updateBotConfig,
    refreshBotStatus,
  };
  
  return (
    <TradingContext.Provider value={value}>
      {children}
    </TradingContext.Provider>
  );
}

export function useTradingContext() {
  const context = useContext(TradingContext);
  if (!context) {
    throw new Error('useTradingContext must be used within TradingProvider');
  }
  return context;
}
