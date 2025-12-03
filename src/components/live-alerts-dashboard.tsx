
"use client";
// Unified Dashboard - No Tabs - v3.0

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { AnimatePresence, motion } from "framer-motion";
import { useToast } from "@/hooks/use-toast";
import { Bell, ArrowUp, ArrowDown } from "lucide-react";
import { fetchPopularStocksLTP, POPULAR_SYMBOLS } from "@/lib/angel-one-api";
import { NIFTY_50_SYMBOLS } from "@/lib/nifty50-symbols";
import { useAuth } from "@/context/auth-context";
import { useAngelOneStatus } from "@/hooks/use-angel-one-status";
import { WebSocketControls } from "@/components/websocket-controls";
import { OrderManager } from "@/components/order-manager";
import { TradingBotControls } from "@/components/trading-bot-controls";
import { PositionsMonitor } from "@/components/positions-monitor";
import { OrderBook } from "@/components/order-book";

type AlertType = "BUY" | "SELL";

type Alert = {
  id: string;
  ticker: string;
  price: number;
  confidence?: number;
  signal_type: "Breakout" | "Momentum" | "Reversal" | "Profit Target" | "Stop Loss" | "EOD" | "Technical Exit";
  rationale: string;
  timestamp: Date;
  type: AlertType;
  pnl?: number;
};

type OpenPosition = {
  signal_id: string;
  ticker: string;
  entry_timestamp: Date;
  entry_price: number;
  initial_stop_loss: number;
  profit_target: number;
  current_trailing_stop: number;
  status: "open";
};

// ⚠️ REMOVED: generateInitialSignals() - was causing ghost signals to appear
// All signals now ONLY come from Firestore (bot-generated) - no demo data

let alertCounter = 0;
let tradeLogForPerformance: any[] = [];

export function LiveAlertsDashboard() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [openPositions, setOpenPositions] = useState<Map<string, OpenPosition>>(new Map());
  const [livePrices, setLivePrices] = useState<Map<string, number>>(new Map());
  const [isLoadingPrices, setIsLoadingPrices] = useState(true);
  const [isMounted, setIsMounted] = useState(false);
  const { toast } = useToast();
  const { firebaseUser } = useAuth();
  const angelStatus = useAngelOneStatus();

  const addAlert = useCallback((alert: Alert) => {
      setAlerts((prevAlerts) => [alert, ...prevAlerts].slice(0, 20)); // Keep last 20 alerts
      toast({
        title: `${alert.type} Signal: ${alert.ticker}`,
        description: `${alert.signal_type} @ ₹${alert.price.toFixed(2)}`,
        action: alert.type === "BUY" ? <ArrowUp className="h-5 w-5 text-green-500" /> : <ArrowDown className="h-5 w-5 text-red-500" />,
      });
  }, [toast]);

  // 🧹 CLEANUP: Ensure fresh state on mount - no ghost signals
  useEffect(() => {
    console.log('[Dashboard] Component mounted - clearing any stale state');
    
    // Clear ALL potential sources of ghost signals
    setAlerts([]);
    setOpenPositions(new Map());
    
    // Clear localStorage that might contain old trade data
    if (typeof window !== 'undefined') {
      localStorage.removeItem('tradeLog');
      localStorage.removeItem('cachedSignals');
      sessionStorage.removeItem('cachedSignals');
      console.log('[Dashboard] Cleared localStorage/sessionStorage');
    }
    
    setIsMounted(true);
  }, []);

  // Fetch live prices from Angel One
  useEffect(() => {
    if (!firebaseUser) {
      setIsLoadingPrices(false);
      return;
    }

    const fetchPrices = async () => {
      try {
        console.log('[Dashboard] Fetching live prices from Angel One...');
        const prices = await fetchPopularStocksLTP();
        console.log('[Dashboard] Received live prices:', Object.fromEntries(prices));
        setLivePrices(prices);
        setIsLoadingPrices(false);
      } catch (error) {
        console.error('[Dashboard] Failed to fetch live prices:', error);
        setIsLoadingPrices(false);
        toast({
          title: "Market Data Error",
          description: "Using simulated data. Please connect your Angel One account.",
          variant: "destructive",
        });
      }
    };

    fetchPrices();
    const interval = setInterval(fetchPrices, 5000); // Update every 5 seconds

    return () => clearInterval(interval);
  }, [firebaseUser, toast]);


  useEffect(() => {
    // Position Manager - uses real live prices
    const positionManagerInterval = setInterval(() => {
      if (openPositions.size === 0 || livePrices.size === 0) return;

      const newPositions = new Map(openPositions);
      
      newPositions.forEach((position, ticker) => {
        // Get real live price from Angel One
        const live_price = livePrices.get(ticker) || position.entry_price;
        
        let exit_condition_met = false;
        let sell_alert_data: Partial<Alert> = {};

        // 1. Profit Target Hit
        if (live_price >= position.profit_target) {
          exit_condition_met = true;
          sell_alert_data = { price: live_price, signal_type: "Profit Target" };
        }
        // 2. Stop Loss Hit
        else if (live_price <= position.current_trailing_stop) {
           exit_condition_met = true;
           sell_alert_data = { price: live_price, signal_type: "Stop Loss" };
        }
        // 3. Dynamic Trailing Stop (Simplified)
        else {
            const price_gain_percent = (live_price - position.entry_price) / position.entry_price;
            if (price_gain_percent > 0.01) { // Every 1% gain
                position.current_trailing_stop = Math.max(position.current_trailing_stop, position.entry_price * (1 + (price_gain_percent - 0.01)));
            }
        }
        
        if (exit_condition_met) {
          const pnl = ((sell_alert_data.price! - position.entry_price) / position.entry_price) * 100;
          const outcome = pnl >= 0 ? "closed_profit" : "closed_loss";
          
          const sellAlert: Alert = {
            id: `sell-${position.signal_id}`,
            ticker: position.ticker,
            price: sell_alert_data.price!,
            signal_type: sell_alert_data.signal_type!,
            rationale: `Closing position. Outcome: ${pnl.toFixed(2)}% ${pnl >= 0 ? "Gain" : "Loss"}.`,
            timestamp: new Date(),
            type: "SELL",
            pnl: pnl,
          };

          addAlert(sellAlert);
          
          // Update performance log
          tradeLogForPerformance.push({
            id: position.signal_id,
            ticker: position.ticker,
            entry_price: position.entry_price,
            exit_price: sellAlert.price,
            outcome: sellAlert.signal_type,
            pnl_points: sellAlert.price - position.entry_price,
            pnl_percent: pnl,
            entry_timestamp: position.entry_timestamp.toISOString(),
            exit_timestamp: sellAlert.timestamp.toISOString()
          });
          if(typeof window !== "undefined") {
            localStorage.setItem('tradeLog', JSON.stringify(tradeLogForPerformance));
          }


          newPositions.delete(ticker);
        }
      });
      setOpenPositions(newPositions);

    }, 5000); // Check positions every 5 seconds

    return () => clearInterval(positionManagerInterval);
  }, [openPositions, addAlert, livePrices]);

  // 🔥 LISTEN TO REAL SIGNALS FROM FIRESTORE (bot-generated)
  useEffect(() => {
    if (!firebaseUser) return;

    const { onSnapshot, collection, query, where, orderBy, limit } = require('firebase/firestore');
    const { db } = require('@/lib/firebase');

    console.log('[Dashboard] Setting up real-time signal listener...');

    // Listen to trading signals from bot
    const signalsQuery = query(
      collection(db, 'trading_signals'),
      where('user_id', '==', firebaseUser.uid),
      where('status', '==', 'open'),
      orderBy('timestamp', 'desc'),
      limit(20)
    );

    const unsubscribe = onSnapshot(signalsQuery, (snapshot) => {
      snapshot.docChanges().forEach((change) => {
        if (change.type === 'added') {
          const data = change.doc.data();
          console.log('[Dashboard] New signal received:', data);

          const newAlert: Alert = {
            id: change.doc.id,
            ticker: data.symbol,
            price: data.price,
            confidence: data.confidence || 0.95,
            signal_type: data.signal_type as any,
            rationale: data.rationale || 'Trading bot signal',
            timestamp: data.timestamp?.toDate() || new Date(),
            type: data.type as AlertType,
          };

          addAlert(newAlert);

          // Create position if BUY signal
          if (data.type === 'BUY') {
            const newPosition: OpenPosition = {
              signal_id: change.doc.id,
              ticker: data.symbol,
              entry_timestamp: newAlert.timestamp,
              entry_price: data.price,
              initial_stop_loss: data.stop_loss,
              profit_target: data.target,
              current_trailing_stop: data.stop_loss,
              status: "open",
            };

            setOpenPositions(prev => new Map(prev).set(newPosition.ticker, newPosition));
          }
        }
      });
    }, (error) => {
      console.error('[Dashboard] Signal listener error:', error);
    });

    return () => {
      console.log('[Dashboard] Cleaning up signal listener');
      unsubscribe();
    };
  }, [firebaseUser, addAlert]);

  // Client-side mount guard
  useEffect(() => {
    setIsMounted(true);
  }, []);


  const getBadgeVariant = (signal: Alert["signal_type"]) => {
    switch (signal) {
      case "Breakout": return "default";
      case "Momentum": return "secondary";
      case "Reversal": return "destructive";
      case "Profit Target": return "default";
      case "Stop Loss": return "destructive";
      case "Technical Exit": return "destructive";
      case "EOD": return "secondary";
      default: return "outline";
    }
  };

  // Show skeleton loader until mounted on client side
  if (!isMounted) {
    return (
      <div className="space-y-6">
        <header>
          <Skeleton className="h-10 w-96" />
          <Skeleton className="h-4 w-[500px] mt-2" />
        </header>
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold tracking-tight">Live Trading Dashboard</h1>
        <p className="text-muted-foreground">Real-time trading controls, positions, and market signals.</p>
      </header>
      
      {/* Angel One Connection Status Banner */}
      {!angelStatus.isLoading && !angelStatus.isConnected && (
        <Card className="border-yellow-500 bg-yellow-50 dark:bg-yellow-950">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-yellow-800 dark:text-yellow-200">Angel One Not Connected</h3>
                <p className="text-sm text-yellow-700 dark:text-yellow-300">
                  Connect your Angel One account to enable live trading and see real market data.
                </p>
              </div>
              <Link href="/settings">
                <Button variant="default">Connect Now</Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      )}
      
      {angelStatus.isConnected && (
        <Card className="border-green-500 bg-green-50 dark:bg-green-950">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-green-800 dark:text-green-200">✓ Angel One Connected</h3>
                <p className="text-sm text-green-700 dark:text-green-300">
                  Live trading enabled for {angelStatus.clientCode}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
      
      {/* Control Panel - Always Visible */}
      <div className="grid gap-4 md:grid-cols-2">
        <WebSocketControls />
        <TradingBotControls />
      </div>
      
      {/* Unified Dashboard - All Sections Always Visible */}
      <div className="space-y-4">
        {/* Trading Controls */}
        <OrderManager />
        
        {/* Positions and Orders Side by Side */}
        <div className="grid gap-4 md:grid-cols-2">
          <PositionsMonitor />
          <OrderBook />
        </div>
        
        {/* Live Alerts/Signals Table */}
        <Card>
          <CardHeader>
            <CardTitle>Live Trading Signals</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-hidden rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Time</TableHead>
                    <TableHead>Ticker</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Signal</TableHead>
                    <TableHead>Price</TableHead>
                    <TableHead>Confidence/P&L</TableHead>
                    <TableHead>Rationale</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <AnimatePresence initial={false}>
                    {alerts.map((alert) => (
                      <motion.tr
                        key={alert.id}
                        layout
                        initial={{ opacity: 0, y: -20, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        transition={{ duration: 0.5, ease: "easeInOut" }}
                        className="hover:bg-muted/50"
                      >
                        <TableCell className="w-[120px]">
                          {alert.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                        </TableCell>
                        <TableCell className="font-medium">
                          <Link href={`/analysis/${alert.ticker}`} className="hover:underline text-primary">
                            {alert.ticker}
                          </Link>
                        </TableCell>
                        <TableCell>
                          <Badge variant={alert.type === "BUY" ? "outline" : "secondary"} className={alert.type === 'BUY' ? 'border-green-500 text-green-500' : 'border-red-500 text-red-500'}>
                            {alert.type}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant={getBadgeVariant(alert.signal_type)}
                            className={alert.signal_type === "Profit Target" ? "bg-green-600/20 text-green-800 border-green-600/30" : ""}
                          >{alert.signal_type}</Badge>
                        </TableCell>
                        <TableCell>{alert.price.toFixed(2)}</TableCell>
                        <TableCell>
                          {alert.type === 'BUY' && alert.confidence ? (
                             <span className="font-semibold text-green-600">{(alert.confidence * 100).toFixed(0)}%</span>
                          ) : alert.pnl ? (
                            <span className={`font-semibold ${alert.pnl > 0 ? 'text-green-600' : 'text-red-600'}`}>
                              {alert.pnl > 0 ? '+' : ''}{alert.pnl.toFixed(2)}%
                            </span>
                          ) : '-'}
                        </TableCell>
                        <TableCell className="max-w-sm truncate">{alert.rationale}</TableCell>
                      </motion.tr>
                    ))}
                  </AnimatePresence>
                  {alerts.length === 0 && (
                      <TableRow>
                          <TableCell colSpan={7} className="text-center h-24">
                              Waiting for market signals...
                          </TableCell>
                      </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
