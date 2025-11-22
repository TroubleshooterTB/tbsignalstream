
"use client";

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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AnimatePresence, motion } from "framer-motion";
import { useToast } from "@/hooks/use-toast";
import { Bell, ArrowUp, ArrowDown } from "lucide-react";
import { fetchPopularStocksLTP, POPULAR_SYMBOLS } from "@/lib/angel-one-api";
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

const initialBuySignals: Omit<Alert, 'id' | 'timestamp' | 'type' | 'pnl'>[] = [
  { ticker: "RELIANCE", price: 2850.50, confidence: 0.95, signal_type: "Breakout", rationale: "Volume spike, opening range breakout." },
  { ticker: "HDFCBANK", price: 1520.00, confidence: 0.92, signal_type: "Momentum", rationale: "Strong relative strength vs NIFTY." },
  { ticker: "INFY", price: 1610.75, confidence: 0.98, signal_type: "Breakout", rationale: "News catalyst and high volume." },
  { ticker: "TCS", price: 3900.00, confidence: 0.91, signal_type: "Reversal", rationale: "RSI divergence, MACD crossover." },
  { ticker: "ICICIBANK", price: 1105.20, confidence: 0.93, signal_type: "Momentum", rationale: "Sustained trend, low volatility." },
];

let alertCounter = 0;
let tradeLogForPerformance: any[] = [];

export function LiveAlertsDashboard() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [openPositions, setOpenPositions] = useState<Map<string, OpenPosition>>(new Map());
  const [livePrices, setLivePrices] = useState<Map<string, number>>(new Map());
  const [isLoadingPrices, setIsLoadingPrices] = useState(true);
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

  useEffect(() => {
    // Generate BUY signals using REAL live prices
    const signalGeneratorInterval = setInterval(() => {
      if (alertCounter < initialBuySignals.length && openPositions.size < 3 && livePrices.size > 0) {
        const newAlertData = initialBuySignals[alertCounter];
        
        // Use REAL live price from Angel One instead of hardcoded price
        const realPrice = livePrices.get(newAlertData.ticker) || newAlertData.price;
        
        const signalId = (alertCounter + 1).toString();
        
        if (newAlertData.confidence && newAlertData.confidence > 0.90) {
            const newAlert: Alert = {
                ...newAlertData,
                price: realPrice, // REAL LIVE PRICE
                id: signalId,
                timestamp: new Date(),
                type: "BUY",
            };
            
            addAlert(newAlert);
    
            const risk_amount = realPrice * 0.015; // 1.5% risk
            const newPosition: OpenPosition = {
                signal_id: signalId,
                ticker: newAlert.ticker,
                entry_timestamp: newAlert.timestamp,
                entry_price: realPrice, // REAL LIVE PRICE
                initial_stop_loss: realPrice - risk_amount,
                profit_target: realPrice + (risk_amount * 2),
                current_trailing_stop: realPrice - risk_amount,
                status: "open",
            };
    
            setOpenPositions(prev => new Map(prev).set(newPosition.ticker, newPosition));
        }
        alertCounter++;
      } else if (alertCounter >= initialBuySignals.length) {
        clearInterval(signalGeneratorInterval);
      }
    }, 8000); // New BUY signal every 8 seconds

    return () => clearInterval(signalGeneratorInterval);
  }, [addAlert, openPositions.size, livePrices]);


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
      
      <Tabs defaultValue="trading" className="space-y-4">
        <TabsList>
          <TabsTrigger value="trading">Trading</TabsTrigger>
          <TabsTrigger value="positions">Positions</TabsTrigger>
          <TabsTrigger value="orders">Orders</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
        </TabsList>

        <TabsContent value="trading" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <WebSocketControls />
            <TradingBotControls />
          </div>
          <OrderManager />
        </TabsContent>

        <TabsContent value="positions">
          <PositionsMonitor />
        </TabsContent>

        <TabsContent value="orders">
          <OrderBook />
        </TabsContent>

        <TabsContent value="alerts">
          <Card>
            <CardHeader>
              <CardTitle>Triggered Signals</CardTitle>
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
        </TabsContent>
      </Tabs>
    </div>
  );
}
