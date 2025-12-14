"use client";

import React, { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";
import { format } from "date-fns";
import { Calendar as CalendarIcon, TrendingUp, TrendingDown, Loader2, BarChart3, Play } from "lucide-react";
import { useTradingContext } from "@/context/trading-context";

type BacktestResult = {
  symbol: string;
  entry_time: string;
  entry_price: number;
  exit_time: string;
  exit_price: number;
  direction: "BUY" | "SELL";
  pnl: number;
  pnl_pct: number;
  win: boolean;
  reason: string;
};

type BacktestSummary = {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_pnl: number;
  pnl_percentage?: number;
  avg_win: number;
  avg_loss: number;
  max_win: number;
  max_loss: number;
  profit_factor: number;
};

export function StrategyBacktester() {
  const { botConfig } = useTradingContext();
  const [isBacktesting, setIsBacktesting] = useState(false);
  const [backtestEnabled, setBacktestEnabled] = useState(false);
  const [startDate, setStartDate] = useState<Date>();
  const [endDate, setEndDate] = useState<Date>();
  const [selectedStrategy, setSelectedStrategy] = useState<string>("defining");
  const [capital, setCapital] = useState<string>("100000");
  const [results, setResults] = useState<BacktestResult[]>([]);
  const [summary, setSummary] = useState<BacktestSummary | null>(null);
  const [error, setError] = useState<string>("");

  const runBacktest = async () => {
    if (!startDate || !endDate) {
      setError("Please select both start and end dates");
      return;
    }

    if (startDate >= endDate) {
      setError("Start date must be before end date");
      return;
    }

    const capitalAmount = parseFloat(capital);
    if (isNaN(capitalAmount) || capitalAmount <= 0) {
      setError("Please enter a valid capital amount");
      return;
    }

    setIsBacktesting(true);
    setError("");
    setResults([]);
    setSummary(null);

    try {
      const response = await fetch("/api/backtest", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          strategy: selectedStrategy,
          start_date: format(startDate, "yyyy-MM-dd"),
          end_date: format(endDate, "yyyy-MM-dd"),
          symbols: botConfig.symbols || "NIFTY50",
          capital: capitalAmount,
        }),
      });

      if (!response.ok) {
        throw new Error(`Backtest failed: ${response.statusText}`);
      }

      const data = await response.json();
      setResults(data.trades || []);
      setSummary(data.summary || null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Backtest failed");
      console.error("Backtest error:", err);
    } finally {
      setIsBacktesting(false);
    }
  };

  if (!backtestEnabled) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Strategy Backtesting
          </CardTitle>
          <CardDescription>
            Test strategy performance on historical data
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Enable Backtesting</Label>
              <p className="text-sm text-muted-foreground">
                Run strategy tests on past data while bot trades live
              </p>
            </div>
            <Switch
              checked={backtestEnabled}
              onCheckedChange={setBacktestEnabled}
            />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5" />
          Strategy Backtesting
        </CardTitle>
        <CardDescription>
          Test strategy performance on historical data (independent of live trading)
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Controls */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Strategy Selection */}
          <div className="space-y-2">
            <Label>Strategy</Label>
            <Select
              value={selectedStrategy}
              onValueChange={setSelectedStrategy}
              disabled={isBacktesting}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="defining">The Defining Order v3.2</SelectItem>
                <SelectItem value="pattern">Pattern Detector</SelectItem>
                <SelectItem value="ironclad">Ironclad Strategy</SelectItem>
                <SelectItem value="both">Both (Dual Confirmation)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Capital Amount */}
          <div className="space-y-2">
            <Label htmlFor="capital">Capital Amount (₹)</Label>
            <Input
              id="capital"
              type="number"
              placeholder="100000"
              value={capital}
              onChange={(e) => setCapital(e.target.value)}
              disabled={isBacktesting}
              min="1000"
              step="1000"
            />
            <p className="text-xs text-muted-foreground">
              Starting capital for backtest
            </p>
          </div>

          {/* Date Range */}
          <div className="space-y-2">
            <Label>Date Range</Label>
            <div className="flex gap-2">
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className={cn(
                      "flex-1 justify-start text-left font-normal",
                      !startDate && "text-muted-foreground"
                    )}
                    disabled={isBacktesting}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {startDate ? format(startDate, "PPP") : "Start date"}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0">
                  <Calendar
                    mode="single"
                    selected={startDate}
                    onSelect={setStartDate}
                    initialFocus
                  />
                </PopoverContent>
              </Popover>

              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className={cn(
                      "flex-1 justify-start text-left font-normal",
                      !endDate && "text-muted-foreground"
                    )}
                    disabled={isBacktesting}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {endDate ? format(endDate, "PPP") : "End date"}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0">
                  <Calendar
                    mode="single"
                    selected={endDate}
                    onSelect={setEndDate}
                    initialFocus
                  />
                </PopoverContent>
              </Popover>
            </div>
          </div>
        </div>

        {/* Quick Presets */}
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCapital("50000")}
            disabled={isBacktesting}
          >
            ₹50K Capital
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCapital("100000")}
            disabled={isBacktesting}
          >
            ₹1L Capital
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCapital("200000")}
            disabled={isBacktesting}
          >
            ₹2L Capital
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCapital("500000")}
            disabled={isBacktesting}
          >
            ₹5L Capital
          </Button>
        </div>

        {/* Quick Date Presets */}
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              const end = new Date();
              const start = new Date();
              start.setDate(start.getDate() - 7);
              setStartDate(start);
              setEndDate(end);
            }}
            disabled={isBacktesting}
          >
            Last 7 Days
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              const end = new Date();
              const start = new Date();
              start.setMonth(start.getMonth() - 1);
              setStartDate(start);
              setEndDate(end);
            }}
            disabled={isBacktesting}
          >
            Last Month
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              const end = new Date();
              const start = new Date(2025, 11, 1); // Dec 1, 2025
              setStartDate(start);
              setEndDate(end);
            }}
            disabled={isBacktesting}
          >
            December 2025
          </Button>
        </div>

        {/* Run Button */}
        <Button
          onClick={runBacktest}
          disabled={isBacktesting || !startDate || !endDate}
          className="w-full"
        >
          {isBacktesting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Running Backtest...
            </>
          ) : (
            <>
              <Play className="mr-2 h-4 w-4" />
              Run Backtest
            </>
          )}
        </Button>

        {/* Error Message */}
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Summary Results */}
        {summary && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">Backtest Results</h3>
              <Badge variant={summary.win_rate >= 50 ? "default" : "destructive"}>
                {summary.win_rate.toFixed(2)}% Win Rate
              </Badge>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Total Trades</p>
                <p className="text-2xl font-bold">{summary.total_trades}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Win/Loss</p>
                <p className="text-2xl font-bold">
                  <span className="text-green-600">{summary.winning_trades}</span>
                  /
                  <span className="text-red-600">{summary.losing_trades}</span>
                </p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Total P&L</p>
                <p className={cn(
                  "text-2xl font-bold",
                  summary.total_pnl >= 0 ? "text-green-600" : "text-red-600"
                )}>
                  ₹{summary.total_pnl.toLocaleString()}
                </p>
                {summary.pnl_percentage !== undefined && (
                  <p className={cn(
                    "text-xs font-medium",
                    summary.pnl_percentage >= 0 ? "text-green-600" : "text-red-600"
                  )}>
                    {summary.pnl_percentage >= 0 ? '+' : ''}{summary.pnl_percentage}% returns
                  </p>
                )}
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Profit Factor</p>
                <p className="text-2xl font-bold">{summary.profit_factor.toFixed(2)}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-muted-foreground">Avg Win</p>
                <p className="font-semibold text-green-600">₹{summary.avg_win.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Avg Loss</p>
                <p className="font-semibold text-red-600">₹{summary.avg_loss.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Max Win</p>
                <p className="font-semibold text-green-600">₹{summary.max_win.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Max Loss</p>
                <p className="font-semibold text-red-600">₹{summary.max_loss.toLocaleString()}</p>
              </div>
            </div>
          </div>
        )}

        {/* Trade List */}
        {results.length > 0 && (
          <div className="space-y-2">
            <h3 className="text-sm font-semibold">Trade History ({results.length} trades)</h3>
            <div className="border rounded-md max-h-96 overflow-y-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Symbol</TableHead>
                    <TableHead>Direction</TableHead>
                    <TableHead>Entry</TableHead>
                    <TableHead>Exit</TableHead>
                    <TableHead>P&L</TableHead>
                    <TableHead>Reason</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {results.map((trade, index) => (
                    <TableRow key={index}>
                      <TableCell className="font-medium">{trade.symbol}</TableCell>
                      <TableCell>
                        <Badge variant={trade.direction === "BUY" ? "default" : "secondary"}>
                          {trade.direction}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm">
                        <div>{format(new Date(trade.entry_time), "MMM dd, HH:mm")}</div>
                        <div className="text-muted-foreground">₹{trade.entry_price.toFixed(2)}</div>
                      </TableCell>
                      <TableCell className="text-sm">
                        <div>{format(new Date(trade.exit_time), "MMM dd, HH:mm")}</div>
                        <div className="text-muted-foreground">₹{trade.exit_price.toFixed(2)}</div>
                      </TableCell>
                      <TableCell>
                        <div className={cn(
                          "flex items-center gap-1 font-semibold",
                          trade.win ? "text-green-600" : "text-red-600"
                        )}>
                          {trade.win ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                          ₹{trade.pnl.toFixed(0)} ({trade.pnl_pct.toFixed(2)}%)
                        </div>
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground max-w-xs truncate">
                        {trade.reason}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>
        )}

        {/* Toggle Off */}
        <div className="pt-4 border-t">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              Disable backtesting to hide this panel
            </p>
            <Switch
              checked={backtestEnabled}
              onCheckedChange={setBacktestEnabled}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
