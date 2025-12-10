"use client";

import React, { useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface MarketHeatmapProps {
  prices: Map<string, number>;
  previousPrices?: Map<string, number>;
}

export function MarketHeatmap({ prices, previousPrices }: MarketHeatmapProps) {
  const stocksWithChanges = useMemo(() => {
    const stocks: Array<{
      symbol: string;
      price: number;
      change: number;
      changePercent: number;
    }> = [];

    prices.forEach((price, symbol) => {
      // Calculate change (if we have previous price, otherwise assume 0)
      const prevPrice = previousPrices?.get(symbol) || price;
      const change = price - prevPrice;
      const changePercent = prevPrice > 0 ? (change / prevPrice) * 100 : 0;

      stocks.push({
        symbol: symbol.replace('-EQ', ''),
        price,
        change,
        changePercent,
      });
    });

    // Sort by change percent (biggest movers first)
    return stocks.sort((a, b) => Math.abs(b.changePercent) - Math.abs(a.changePercent));
  }, [prices, previousPrices]);

  const getColorClass = (changePercent: number) => {
    if (changePercent > 1.5) return "bg-green-600 text-white";
    if (changePercent > 0.5) return "bg-green-500 text-white";
    if (changePercent > 0) return "bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-200";
    if (changePercent < -1.5) return "bg-red-600 text-white";
    if (changePercent < -0.5) return "bg-red-500 text-white";
    if (changePercent < 0) return "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-200";
    return "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200";
  };

  const getIcon = (changePercent: number) => {
    if (changePercent > 0.1) return <TrendingUp className="h-3 w-3" />;
    if (changePercent < -0.1) return <TrendingDown className="h-3 w-3" />;
    return <Minus className="h-3 w-3" />;
  };

  // Market statistics
  const stats = useMemo(() => {
    let bullish = 0;
    let bearish = 0;
    let neutral = 0;

    stocksWithChanges.forEach(({ changePercent }) => {
      if (changePercent > 0.3) bullish++;
      else if (changePercent < -0.3) bearish++;
      else neutral++;
    });

    return { bullish, bearish, neutral, total: stocksWithChanges.length };
  }, [stocksWithChanges]);

  if (prices.size === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Market Heatmap</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center text-muted-foreground py-8">
            Loading market data...
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Market Heatmap - Live Movers</CardTitle>
          <div className="flex gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-green-500"></div>
              <span className="text-muted-foreground">Bullish: {stats.bullish}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-gray-400"></div>
              <span className="text-muted-foreground">Neutral: {stats.neutral}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-red-500"></div>
              <span className="text-muted-foreground">Bearish: {stats.bearish}</span>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-5 sm:grid-cols-6 md:grid-cols-8 lg:grid-cols-10 gap-2">
          {stocksWithChanges.slice(0, 50).map(({ symbol, price, changePercent }) => (
            <div
              key={symbol}
              className={cn(
                "p-2 rounded-lg transition-all hover:scale-105 cursor-pointer",
                getColorClass(changePercent)
              )}
              title={`${symbol}: ₹${price.toFixed(2)} (${changePercent > 0 ? '+' : ''}${changePercent.toFixed(2)}%)`}
            >
              <div className="flex flex-col items-center justify-center space-y-1">
                <div className="text-xs font-bold truncate w-full text-center">
                  {symbol}
                </div>
                <div className="flex items-center gap-1">
                  {getIcon(changePercent)}
                  <div className="text-xs font-semibold">
                    {changePercent > 0 ? '+' : ''}{changePercent.toFixed(1)}%
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Market Sentiment Bar */}
        <div className="mt-4 space-y-2">
          <div className="flex justify-between text-sm text-muted-foreground">
            <span>Market Sentiment</span>
            <span>
              {stats.bullish > stats.bearish ? '📈 Bullish' : 
               stats.bearish > stats.bullish ? '📉 Bearish' : 
               '➡️ Neutral'}
            </span>
          </div>
          <div className="w-full h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden flex">
            <div 
              className="bg-green-500 transition-all duration-500" 
              style={{ width: `${(stats.bullish / stats.total) * 100}%` }}
            />
            <div 
              className="bg-gray-400 transition-all duration-500" 
              style={{ width: `${(stats.neutral / stats.total) * 100}%` }}
            />
            <div 
              className="bg-red-500 transition-all duration-500" 
              style={{ width: `${(stats.bearish / stats.total) * 100}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>{stats.bullish} bullish ({((stats.bullish / stats.total) * 100).toFixed(0)}%)</span>
            <span>{stats.neutral} neutral ({((stats.neutral / stats.total) * 100).toFixed(0)}%)</span>
            <span>{stats.bearish} bearish ({((stats.bearish / stats.total) * 100).toFixed(0)}%)</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
