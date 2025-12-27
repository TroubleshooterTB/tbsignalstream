"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { db } from "@/lib/firebase";
import { collection, query, where, onSnapshot, orderBy } from "firebase/firestore";
import { useAuth } from "@/context/auth-context";
import { TrendingUp, TrendingDown, Target, AlertCircle, Activity, BarChart3 } from "lucide-react";

interface BotStats {
  signalsToday: number;
  buySignals: number;
  sellSignals: number;
  closedTrades: number;
  profitableTrades: number;
  losingTrades: number;
  winRate: number;
  totalPnL: number;
  avgPnL: number;
  bestTrade: { symbol: string; pnl: number } | null;
  worstTrade: { symbol: string; pnl: number } | null;
  lastSignalTime: Date | null;
}

export function BotPerformanceStats() {
  const [stats, setStats] = useState<BotStats>({
    signalsToday: 0,
    buySignals: 0,
    sellSignals: 0,
    closedTrades: 0,
    profitableTrades: 0,
    losingTrades: 0,
    winRate: 0,
    totalPnL: 0,
    avgPnL: 0,
    bestTrade: null,
    worstTrade: null,
    lastSignalTime: null,
  });
  const [isLoading, setIsLoading] = useState(true);
  const { firebaseUser } = useAuth();

  useEffect(() => {
    if (!firebaseUser) {
      setIsLoading(false);
      return;
    }

    // Get start of today (midnight)
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const signalsQuery = query(
      collection(db, 'trading_signals'),
      where('user_id', '==', firebaseUser.uid),
      where('timestamp', '>=', today),
      orderBy('timestamp', 'desc')
    );

    const unsubscribe = onSnapshot(
      signalsQuery, 
      (snapshot) => {
        console.log('[BotPerformance] Received signals:', snapshot.docs.length);

      let buySignals = 0;
      let sellSignals = 0;
      let closedTrades = 0;
      let profitableTrades = 0;
      let losingTrades = 0;
      let totalPnL = 0;
      let bestTrade: { symbol: string; pnl: number } | null = null;
      let worstTrade: { symbol: string; pnl: number } | null = null;
      let lastSignalTime: Date | null = null;

      snapshot.docs.forEach((doc) => {
        const data = doc.data();
        const timestamp = data.timestamp?.toDate();

        if (!lastSignalTime || (timestamp && timestamp > lastSignalTime)) {
          lastSignalTime = timestamp;
        }

        if (data.type === 'BUY') {
          buySignals++;
        } else if (data.type === 'SELL') {
          sellSignals++;
          closedTrades++;

          // Calculate P&L if we have entry and exit prices
          if (data.entry_price && data.exit_price) {
            const pnl = ((data.exit_price - data.entry_price) / data.entry_price) * 100;
            totalPnL += pnl;

            if (pnl > 0) {
              profitableTrades++;
            } else {
              losingTrades++;
            }

            // Track best and worst trades
            if (!bestTrade || pnl > bestTrade.pnl) {
              bestTrade = { symbol: data.symbol, pnl };
            }
            if (!worstTrade || pnl < worstTrade.pnl) {
              worstTrade = { symbol: data.symbol, pnl };
            }
          }
        }
      });

      const winRate = closedTrades > 0 ? (profitableTrades / closedTrades) * 100 : 0;
      const avgPnL = closedTrades > 0 ? totalPnL / closedTrades : 0;

      setStats({
        signalsToday: snapshot.docs.length,
        buySignals,
        sellSignals,
        closedTrades,
        profitableTrades,
        losingTrades,
        winRate,
        totalPnL,
        avgPnL,
        bestTrade,
        worstTrade,
        lastSignalTime,
      });

      setIsLoading(false);
    }, (error) => {
      console.error('[BotPerformance] Error:', error);
      setIsLoading(false);
    });

    return () => unsubscribe();
  }, [firebaseUser]);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Bot Performance Today</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-20" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Bot Performance Today
          </CardTitle>
          {stats.lastSignalTime && (
            <Badge variant="outline" className="text-xs">
              Last signal: {stats.lastSignalTime.toLocaleTimeString()}
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* Total Signals */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Activity className="h-4 w-4" />
              <span>Total Signals</span>
            </div>
            <div className="text-2xl font-bold">{stats.signalsToday}</div>
            <div className="flex gap-2 text-xs">
              <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                {stats.buySignals} BUY
              </Badge>
              <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">
                {stats.sellSignals} SELL
              </Badge>
            </div>
          </div>

          {/* Win Rate */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Target className="h-4 w-4" />
              <span>Win Rate</span>
            </div>
            <div className="text-2xl font-bold">
              {stats.closedTrades > 0 ? `${stats.winRate.toFixed(1)}%` : 'N/A'}
            </div>
            <div className="text-xs text-muted-foreground">
              {stats.profitableTrades}W / {stats.losingTrades}L
            </div>
          </div>

          {/* Average P&L */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              {stats.avgPnL >= 0 ? (
                <TrendingUp className="h-4 w-4 text-green-500" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-500" />
              )}
              <span>Avg P&L</span>
            </div>
            <div className={`text-2xl font-bold ${stats.avgPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {stats.closedTrades > 0 ? (
                <>
                  {stats.avgPnL >= 0 ? '+' : ''}{stats.avgPnL.toFixed(2)}%
                </>
              ) : (
                'N/A'
              )}
            </div>
            <div className="text-xs text-muted-foreground">
              {stats.closedTrades} closed trades
            </div>
          </div>

          {/* Total P&L */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <AlertCircle className="h-4 w-4" />
              <span>Total P&L</span>
            </div>
            <div className={`text-2xl font-bold ${stats.totalPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {stats.closedTrades > 0 ? (
                <>
                  {stats.totalPnL >= 0 ? '+' : ''}{stats.totalPnL.toFixed(2)}%
                </>
              ) : (
                'N/A'
              )}
            </div>
            <div className="text-xs text-muted-foreground">
              Cumulative return
            </div>
          </div>
        </div>

        {/* Best and Worst Trades */}
        {(stats.bestTrade || stats.worstTrade) && (
          <div className="mt-4 pt-4 border-t grid grid-cols-2 gap-4">
            {stats.bestTrade && (
              <div className="space-y-1">
                <div className="text-xs text-muted-foreground">Best Trade</div>
                <div className="flex items-center justify-between">
                  <span className="font-medium text-sm">{stats.bestTrade.symbol.replace('-EQ', '')}</span>
                  <span className="text-green-600 font-bold">
                    +{stats.bestTrade.pnl.toFixed(2)}%
                  </span>
                </div>
              </div>
            )}
            {stats.worstTrade && (
              <div className="space-y-1">
                <div className="text-xs text-muted-foreground">Worst Trade</div>
                <div className="flex items-center justify-between">
                  <span className="font-medium text-sm">{stats.worstTrade.symbol.replace('-EQ', '')}</span>
                  <span className="text-red-600 font-bold">
                    {stats.worstTrade.pnl.toFixed(2)}%
                  </span>
                </div>
              </div>
            )}
          </div>
        )}

        {stats.signalsToday === 0 && (
          <div className="mt-4 text-center text-sm text-muted-foreground py-4">
            No signals generated yet today. Bot is scanning for opportunities...
          </div>
        )}
      </CardContent>
    </Card>
  );
}
