"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { websocketApi, tradingBotApi } from '@/lib/trading-api';
import { useToast } from '@/hooks/use-toast';
import { notify } from '@/lib/notifications';
import { NIFTY_50_SYMBOLS_STRING } from '@/lib/nifty50-symbols';
import { BOT_DEFAULTS, COLLECTIONS } from '@/config/constants';
import { auth, db } from '@/lib/firebase';
import { onAuthStateChanged } from 'firebase/auth';
import { doc, updateDoc, onSnapshot } from 'firebase/firestore';

interface TradingState {
  // WebSocket state
  isWebSocketConnected: boolean;
  isWebSocketLoading: boolean;
  
  // Trading bot state
  isBotRunning: boolean;
  isBotLoading: boolean;
  botError: string | null;
  botConfig: {
    symbols: string;
    mode: 'paper' | 'live' | 'replay';
    strategy: 'pattern' | 'ironclad' | 'both' | 'defining' | 'alpha-ensemble';
    maxPositions: string;
    positionSize: string;
    replayDate?: string;  // Phase 3: Replay Mode
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
  const [botError, setBotError] = useState<string | null>(null);
  const [botConfig, setBotConfig] = useState({
    symbols: NIFTY_50_SYMBOLS_STRING, // All Nifty 50 stocks
    mode: BOT_DEFAULTS.MODE,
    strategy: BOT_DEFAULTS.STRATEGY,
    maxPositions: String(BOT_DEFAULTS.MAX_POSITIONS),
    positionSize: String(BOT_DEFAULTS.POSITION_SIZE),
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

  // Real-time listener for bot status and errors
  useEffect(() => {
    if (!auth.currentUser) return;

    const botConfigRef = doc(db, COLLECTIONS.BOT_CONFIGS, auth.currentUser.uid);
    const unsubscribe = onSnapshot(
      botConfigRef, 
      (docSnap) => {
        if (docSnap.exists()) {
          const data = docSnap.data();
          
          // Update bot status
          const isRunning = data.status === 'running';
          setIsBotRunning(isRunning);
          
          // Check for errors
          if (data.status === 'error' && data.error_message) {
            setBotError(data.error_message);
            
            // Show error toast using centralized notification
            notify.botError(data.error_message);
            
            console.error('[TradingContext] Bot error detected:', data.error_message);
          } else if (data.status !== 'error') {
            // Clear error when bot is running or stopped normally
            setBotError(null);
          }
        }
      },
      (error) => {
        // Handle permission denied and other errors silently
        console.warn('[TradingContext] Bot config listener error:', error.message);
        // Don't show error to user - they might not have set up bot yet
      }
    );

    return () => unsubscribe();
  }, [toast]);
  
  // WebSocket methods
  const connectWebSocket = useCallback(async () => {
    setIsWebSocketLoading(true);
    try {
      const result = await websocketApi.initialize();
      setIsWebSocketConnected(true);
      notify.wsConnected();
    } catch (error: any) {
      notify.error('Connection Failed', error.message);
    } finally {
      setIsWebSocketLoading(false);
    }
  }, [toast]);
  
  const disconnectWebSocket = useCallback(async () => {
    setIsWebSocketLoading(true);
    try {
      await websocketApi.close();
      setIsWebSocketConnected(false);
      notify.wsDisconnected();
    } catch (error: any) {
      notify.error('Disconnection Failed', error.message);
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
      // Clear replay mode flag if starting in paper/live mode
      if (auth.currentUser && botConfig.mode !== 'replay') {
        try {
          const botConfigRef = doc(db, 'bot_configs', auth.currentUser.uid);
          await updateDoc(botConfigRef, {
            replay_mode: false,
            replay_date: null
          });
        } catch (err) {
          console.error('Failed to clear replay mode:', err);
        }
      }
      
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

      // Phase 3: Validate replay mode
      if (botConfig.mode === 'replay' && !botConfig.replayDate) {
        toast({
          title: 'Replay Mode Error',
          description: 'Please select a historical date for replay mode',
          variant: 'destructive',
        });
        return;
      }

      const requestData: any = {
        symbols, // Send "NIFTY100" not ["NIFTY100"]
        mode: botConfig.mode,
        strategy: botConfig.strategy,
        maxPositions: parseInt(botConfig.maxPositions),
        positionSize: parseFloat(botConfig.positionSize),
      };
      
      // Add replay date if in replay mode
      if (botConfig.mode === 'replay' && botConfig.replayDate) {
        requestData.replay_date = botConfig.replayDate;
      }

      const result = await tradingBotApi.start(requestData);
      
      // Show starting message
      const modeText = botConfig.mode === 'replay' 
        ? `🔄 Replay Mode on ${botConfig.replayDate}` 
        : botConfig.mode === 'live' 
        ? '🔴 Live Trading' 
        : '📄 Paper Trading';
      
      toast({
        title: `Bot Starting... ${modeText}`,
        description: botConfig.mode === 'replay' 
          ? 'Loading historical data and replaying trading day...'
          : 'Initializing WebSocket and loading data. Please wait 20 seconds...',
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
          description: `Bot is now ${botConfig.mode === 'paper' ? 'paper trading' : 'live trading'} with ${botConfig.symbols?.split(',').length || 0} symbols`,
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
    botError,
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
