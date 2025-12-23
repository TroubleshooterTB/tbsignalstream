"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { websocketApi, tradingBotApi } from '@/lib/trading-api';
import { useToast } from '@/hooks/use-toast';
import { NIFTY_50_SYMBOLS_STRING } from '@/lib/nifty50-symbols';
import { auth } from '@/lib/firebase';
import { onAuthStateChanged } from 'firebase/auth';

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
    strategy: 'pattern' | 'ironclad' | 'both' | 'defining' | 'alpha-ensemble';
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
  const [isAuthReady, setIsAuthReady] = useState(false);
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
    strategy: 'alpha-ensemble' as 'pattern' | 'ironclad' | 'both' | 'defining' | 'alpha-ensemble', // NEW BEST: 36% WR, 2.64 PF, 250% returns
    maxPositions: '5', // Increased from 3 to allow more opportunities
    positionSize: '50000', // ₹50,000 total capital (bot manages sizing: 1% risk per trade)
  });

  useEffect(() => {
    setIsMounted(true);
  }, []);
  
  // Wait for auth state to be ready
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      setIsAuthReady(true);
      console.log('[TradingContext] Auth state ready, user:', user?.email || 'not signed in');
    });
    
    return () => unsubscribe();
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
      // Only check status if user is authenticated
      if (!auth.currentUser) {
        console.log('[TradingContext] Skipping bot status check - user not authenticated');
        setIsBotRunning(false);
        return;
      }
      
      const status = await tradingBotApi.status();
      const isRunning = status.running === true;
      console.log('[TradingContext] Bot status check:', { status, isRunning });
      setIsBotRunning(isRunning);
    } catch (error) {
      // If status check fails, assume bot is not running
      console.error('[TradingContext] Error fetching bot status:', error);
      setIsBotRunning(false);
    }
  }, []);
  
  // Trading bot methods
  const startTradingBot = useCallback(async () => {
    // REMOVED: Don't check state before calling backend - let backend decide
    // Always attempt to start, backend will return error if already running
    
    setIsBotLoading(true);
    try {
      // Don't split symbols - it's a universe name (NIFTY50/NIFTY100/NIFTY200)
      // Backend expects the universe string, not an array
      const symbols = botConfig.symbols; // Pass as-is: "NIFTY100"
      
      if (!symbols) {
        toast({
          title: 'Validation Error',
          description: 'Please select a symbol universe',
          variant: 'destructive',
        });
        return;
      }

      const result = await tradingBotApi.start({
        symbols, // Send "NIFTY100" not ["NIFTY100"]
        mode: botConfig.mode,
        strategy: botConfig.strategy,
        maxPositions: parseInt(botConfig.maxPositions),
        positionSize: parseFloat(botConfig.positionSize),
      });
      
      // Show starting message
      toast({
        title: 'Bot Starting...',
        description: 'Initializing WebSocket and loading data. Please wait 20 seconds...',
      });
      
      // Wait for bot to initialize
      await new Promise(resolve => setTimeout(resolve, 20000));
      
      // Check health after initialization
      try {
        const health = await tradingBotApi.healthCheck();
        
        if (health.overall_status === 'healthy') {
          setIsBotRunning(true);
          toast({
            title: 'Bot Started Successfully',
            description: `Trading with ${health.num_symbols} symbols. WebSocket connected.`,
          });
        } else if (health.overall_status === 'degraded') {
          setIsBotRunning(true);
          toast({
            title: '⚠️ Bot Started with Warnings',
            description: health.warnings?.join(', ') || 'Some systems may not be fully operational',
          });
        } else {
          setIsBotRunning(true);
          toast({
            title: '❌ Bot Started but Has Errors',
            description: health.errors?.join(', ') || 'Critical systems not working',
            variant: 'destructive',
          });
        }
      } catch (healthError) {
        console.error('[TradingContext] Health check failed:', healthError);
        // Bot started but couldn't verify health
        setIsBotRunning(true);
        toast({
          title: 'Bot Started',
          description: `Bot is now ${botConfig.mode === 'paper' ? 'paper trading' : 'live trading'} with ${symbols.length} symbols`,
        });
      }
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
  }, [botConfig, toast, refreshBotStatus]);
  
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
  
  // Poll bot status every 10 seconds (only when client-side and authenticated)
  useEffect(() => {
    if (!isMounted || !isAuthReady) return;
    
    // Only poll if user is authenticated
    if (!auth.currentUser) {
      console.log('[TradingContext] Skipping bot status polling - user not authenticated');
      setIsBotRunning(false);
      return;
    }
    
    // Initial status check after 2 seconds to ensure auth is fully ready
    const initialTimeout = setTimeout(() => {
      refreshBotStatus();
    }, 2000);
    
    // Poll every 10 seconds
    const interval = setInterval(() => {
      refreshBotStatus();
    }, 10000);
    
    return () => {
      clearTimeout(initialTimeout);
      clearInterval(interval);
    };
  }, [refreshBotStatus, isMounted, isAuthReady]);
  
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
