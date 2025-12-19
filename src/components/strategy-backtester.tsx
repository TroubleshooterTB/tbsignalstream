"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";
import { format } from "date-fns";
import { Calendar as CalendarIcon, TrendingUp, TrendingDown, Loader2, BarChart3, Play, History, Save } from "lucide-react";
import { useTradingContext } from "@/context/trading-context";
import { db } from "@/lib/firebase";
import { collection, addDoc, query, orderBy, limit, getDocs, Timestamp } from "firebase/firestore";

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
  const [dateMode, setDateMode] = useState<"single" | "range">("range");
  const [singleDate, setSingleDate] = useState<Date>();
  const [startDate, setStartDate] = useState<Date>();
  const [endDate, setEndDate] = useState<Date>();
  const [selectedStrategy, setSelectedStrategy] = useState<string>("alpha-ensemble");
  const [capital, setCapital] = useState<string>("100000");
  const [results, setResults] = useState<BacktestResult[]>([]);
  const [summary, setSummary] = useState<BacktestSummary | null>(null);
  const [error, setError] = useState<string>("");
  const [savedResults, setSavedResults] = useState<any[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState<string>("");
  const [isSaving, setIsSaving] = useState(false);

  // Strategy Parameters
  const [adxThreshold, setAdxThreshold] = useState(25);
  const [rsiOversold, setRsiOversold] = useState(35);
  const [rsiOverbought, setRsiOverbought] = useState(65);
  const [volumeMultiplier, setVolumeMultiplier] = useState(2.5);
  const [riskReward, setRiskReward] = useState(2.5);
  const [timeframeAlignment, setTimeframeAlignment] = useState("2TF");
  const [tradingStartTime, setTradingStartTime] = useState("09:30");
  const [tradingEndTime, setTradingEndTime] = useState("15:15");
  const [positionSize, setPositionSize] = useState(2.0);
  const [maxPositions, setMaxPositions] = useState(3);
  const [niftyAlignment, setNiftyAlignment] = useState("same");
  const [symbolUniverse, setSymbolUniverse] = useState("NIFTY50");
  const [useCustomParams, setUseCustomParams] = useState(false);

  // Load saved backtest history
  const loadBacktestHistory = async () => {
    setLoadingHistory(true);
    try {
      const q = query(
        collection(db, 'backtest_results'),
        orderBy('timestamp', 'desc'),
        limit(20)
      );
      const querySnapshot = await getDocs(q);
      const history = querySnapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));
      setSavedResults(history);
    } catch (err) {
      console.error('Error loading backtest history:', err);
    } finally {
      setLoadingHistory(false);
    }
  };

  // Load history on component mount
  useEffect(() => {
    loadBacktestHistory();
  }, []);

  // Save backtest results to Firestore
  const saveBacktestResults = async (backtestData: any) => {
    setIsSaving(true);
    setSaveError("");
    try {
      console.log('Attempting to save backtest results...', {
        strategy: selectedStrategy,
        start_date: format(backtestData.start_date, "yyyy-MM-dd"),
        end_date: format(backtestData.end_date, "yyyy-MM-dd"),
        trades: backtestData.trades?.length || 0
      });
      
      const docData: any = {
        strategy: selectedStrategy,
        start_date: format(backtestData.start_date, "yyyy-MM-dd"),
        end_date: format(backtestData.end_date, "yyyy-MM-dd"),
        capital: parseFloat(capital),
        summary: backtestData.summary,
        trades: backtestData.trades,
        timestamp: Timestamp.now(),
        user: 'local_bot_user',
        created_at: new Date().toISOString()
      };
      
      // Include custom parameters if used
      if (useCustomParams) {
        docData.custom_params = {
          adx_threshold: adxThreshold,
          rsi_oversold: rsiOversold,
          rsi_overbought: rsiOverbought,
          volume_multiplier: volumeMultiplier,
          risk_reward: riskReward,
          timeframe_alignment: timeframeAlignment,
          trading_start_time: tradingStartTime,
          trading_end_time: tradingEndTime,
          position_size_pct: positionSize,
          max_positions: maxPositions,
          nifty_alignment: niftyAlignment,
          symbol_universe: symbolUniverse
        };
        docData.used_custom_params = true;
      } else {
        docData.used_custom_params = false;
      }
      
      const docRef = await addDoc(collection(db, 'backtest_results'), docData);
      
      console.log('✅ Backtest results saved with ID:', docRef.id);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
      
      // Reload history to show new result
      await loadBacktestHistory();
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to save results';
      console.error('❌ Error saving backtest results:', err);
      setSaveError(errorMsg);
    } finally {
      setIsSaving(false);
    }
  };

  const runBacktest = async () => {
    // Validate based on mode
    if (dateMode === "single") {
      if (!singleDate) {
        setError("Please select a date");
        return;
      }
    } else {
      if (!startDate || !endDate) {
        setError("Please select both start and end dates");
        return;
      }

      if (startDate >= endDate) {
        setError("Start date must be before end date");
        return;
      }
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
      // Use single date for both start/end if in single day mode
      const backtestStartDate = dateMode === "single" ? singleDate! : startDate!;
      const backtestEndDate = dateMode === "single" ? singleDate! : endDate!;
      
      const requestBody: any = {
        strategy: selectedStrategy,
        start_date: format(backtestStartDate, "yyyy-MM-dd"),
        end_date: format(backtestEndDate, "yyyy-MM-dd"),
        symbols: symbolUniverse,
        capital: capitalAmount,
      };

      // Include custom parameters if enabled
      if (useCustomParams) {
        requestBody.custom_params = {
          adx_threshold: adxThreshold,
          rsi_oversold: rsiOversold,
          rsi_overbought: rsiOverbought,
          volume_multiplier: volumeMultiplier,
          risk_reward: riskReward,
          timeframe_alignment: timeframeAlignment,
          trading_hours: {
            start: tradingStartTime,
            end: tradingEndTime
          },
          position_size_pct: positionSize,
          max_positions: maxPositions,
          nifty_alignment: niftyAlignment
        };
      }

      const response = await fetch("/api/backtest", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        try {
          const errorData = await response.json();
          errorMessage = errorData.error || errorMessage;
        } catch (e) {
          // If can't parse JSON, use status text
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      
      if (!data.trades || data.trades.length === 0) {
        setError("No trades found for the selected period. Try a different date range or strategy.");
      }
      
      setResults(data.trades || []);
      setSummary(data.summary || null);
      
      // Auto-save results to Firestore
      if (data.summary && data.trades) {
        await saveBacktestResults({
          start_date: backtestStartDate,
          end_date: backtestEndDate,
          summary: data.summary,
          trades: data.trades
        });
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Backtest failed";
      setError(errorMessage);
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
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Strategy Backtesting
            </CardTitle>
            <CardDescription>
              Test strategy performance on historical data (independent of live trading)
            </CardDescription>
          </div>
          {saveSuccess && (
            <Badge variant="default" className="flex items-center gap-1">
              <Save className="h-3 w-3" />
              Saved!
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <Tabs defaultValue="backtest" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="backtest">
              <Play className="h-4 w-4 mr-2" />
              Run Backtest
            </TabsTrigger>
            <TabsTrigger value="history">
              <History className="h-4 w-4 mr-2" />
              History ({savedResults.length})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="backtest" className="space-y-6 mt-6">
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
                <SelectItem value="alpha-ensemble">⭐ Alpha-Ensemble (NEW)</SelectItem>
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

          {/* Date Mode Selector */}
          <div className="space-y-2">
            <Label>Backtest Period</Label>
            <div className="flex gap-2">
              <Button
                variant={dateMode === "single" ? "default" : "outline"}
                size="sm"
                onClick={() => setDateMode("single")}
                disabled={isBacktesting}
                className="flex-1"
              >
                Single Day
              </Button>
              <Button
                variant={dateMode === "range" ? "default" : "outline"}
                size="sm"
                onClick={() => setDateMode("range")}
                disabled={isBacktesting}
                className="flex-1"
              >
                Date Range
              </Button>
            </div>
          </div>
        </div>

        {/* Date Selection - Full Width Row */}
        <div className="grid grid-cols-1 gap-4">
          {/* Single Date Picker */}
          {dateMode === "single" && (
            <div className="space-y-2">
              <Label>Select Date</Label>
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className={cn(
                      "w-full justify-start text-left font-normal",
                      !singleDate && "text-muted-foreground"
                    )}
                    disabled={isBacktesting}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {singleDate ? format(singleDate, "PPP") : "Pick a date"}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar
                    mode="single"
                    selected={singleDate}
                    onSelect={setSingleDate}
                    disabled={(date) => date > new Date() || date < new Date("2020-01-01")}
                  />
                </PopoverContent>
              </Popover>
            </div>
          )}

          {/* Date Range Pickers */}
          {dateMode === "range" && (
            <div className="space-y-2">
              <Label>Date Range</Label>
              <div className="grid grid-cols-2 gap-2">
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className={cn(
                      "w-full justify-start text-left font-normal",
                      !startDate && "text-muted-foreground"
                    )}
                    disabled={isBacktesting}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {startDate ? format(startDate, "PPP") : "Start date"}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
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
                      "w-full justify-start text-left font-normal",
                      !endDate && "text-muted-foreground"
                    )}
                    disabled={isBacktesting}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {endDate ? format(endDate, "PPP") : "End date"}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
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
          )}
        </div>

        {/* Capital Quick Presets */}
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

        {/* Quick Date Presets - Only show for range mode */}
        {dateMode === "range" && (
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
        )}

        {/* Advanced Parameter Controls */}
        <div className="border rounded-lg p-4 space-y-4 bg-muted/30">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label className="text-base font-semibold">Advanced Parameters</Label>
              <p className="text-xs text-muted-foreground">
                Fine-tune strategy settings for optimization testing
              </p>
            </div>
            <Switch
              checked={useCustomParams}
              onCheckedChange={setUseCustomParams}
              disabled={isBacktesting}
            />
          </div>

          {useCustomParams && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4">
              {/* Symbol Universe */}
              <div className="space-y-2">
                <Label>Symbol Universe</Label>
                <Select
                  value={symbolUniverse}
                  onValueChange={setSymbolUniverse}
                  disabled={isBacktesting}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="NIFTY50">Nifty 50 (50 symbols)</SelectItem>
                    <SelectItem value="NIFTY100">Nifty 100 (100 symbols)</SelectItem>
                    <SelectItem value="NIFTY200">Nifty 200 (200+ symbols)</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  Select the stock universe for backtesting
                </p>
              </div>

              {/* ADX Threshold */}
              <div className="space-y-2">
                <Label className="flex items-center justify-between">
                  <span>ADX Threshold</span>
                  <Badge variant="outline">{adxThreshold}</Badge>
                </Label>
                <Slider
                  value={[adxThreshold]}
                  onValueChange={(v) => setAdxThreshold(v[0])}
                  min={15}
                  max={35}
                  step={1}
                  disabled={isBacktesting}
                  className="w-full"
                />
                <p className="text-xs text-muted-foreground">
                  Minimum ADX for trend strength (15=weak, 35=very strong)
                </p>
              </div>

              {/* RSI Oversold */}
              <div className="space-y-2">
                <Label>RSI Oversold (Long Entry)</Label>
                <Input
                  type="number"
                  value={rsiOversold}
                  onChange={(e) => setRsiOversold(parseFloat(e.target.value))}
                  min={20}
                  max={45}
                  step={1}
                  disabled={isBacktesting}
                />
                <p className="text-xs text-muted-foreground">
                  Lower bound for long entries (20-45)
                </p>
              </div>

              {/* RSI Overbought */}
              <div className="space-y-2">
                <Label>RSI Overbought (Short Entry)</Label>
                <Input
                  type="number"
                  value={rsiOverbought}
                  onChange={(e) => setRsiOverbought(parseFloat(e.target.value))}
                  min={55}
                  max={80}
                  step={1}
                  disabled={isBacktesting}
                />
                <p className="text-xs text-muted-foreground">
                  Upper bound for short entries (55-80)
                </p>
              </div>

              {/* Volume Multiplier */}
              <div className="space-y-2">
                <Label className="flex items-center justify-between">
                  <span>Volume Multiplier</span>
                  <Badge variant="outline">{volumeMultiplier.toFixed(1)}x</Badge>
                </Label>
                <Slider
                  value={[volumeMultiplier]}
                  onValueChange={(v) => setVolumeMultiplier(v[0])}
                  min={1.0}
                  max={3.5}
                  step={0.1}
                  disabled={isBacktesting}
                  className="w-full"
                />
                <p className="text-xs text-muted-foreground">
                  Required volume vs 20-day average (1.0=low, 3.5=very high)
                </p>
              </div>

              {/* Risk:Reward Ratio */}
              <div className="space-y-2">
                <Label className="flex items-center justify-between">
                  <span>Risk:Reward Ratio</span>
                  <Badge variant="outline">{riskReward.toFixed(1)}:1</Badge>
                </Label>
                <Slider
                  value={[riskReward]}
                  onValueChange={(v) => setRiskReward(v[0])}
                  min={2.0}
                  max={4.0}
                  step={0.5}
                  disabled={isBacktesting}
                  className="w-full"
                />
                <p className="text-xs text-muted-foreground">
                  Target profit relative to risk (2.0=conservative, 4.0=aggressive)
                </p>
              </div>

              {/* Timeframe Alignment */}
              <div className="space-y-2">
                <Label>Timeframe Alignment</Label>
                <Select
                  value={timeframeAlignment}
                  onValueChange={setTimeframeAlignment}
                  disabled={isBacktesting}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1TF">1 Timeframe (5min only)</SelectItem>
                    <SelectItem value="2TF">2 Timeframes (5min + 15min)</SelectItem>
                    <SelectItem value="3TF">3 Timeframes (5min + 15min + hourly)</SelectItem>
                    <SelectItem value="4TF">All 4 Timeframes aligned</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  More timeframes = higher quality but fewer trades
                </p>
              </div>

              {/* Trading Hours Start */}
              <div className="space-y-2">
                <Label>Trading Start Time</Label>
                <Input
                  type="time"
                  value={tradingStartTime}
                  onChange={(e) => setTradingStartTime(e.target.value)}
                  disabled={isBacktesting}
                />
                <p className="text-xs text-muted-foreground">
                  Earliest entry time (Market opens: 09:15)
                </p>
              </div>

              {/* Trading Hours End */}
              <div className="space-y-2">
                <Label>Trading End Time</Label>
                <Input
                  type="time"
                  value={tradingEndTime}
                  onChange={(e) => setTradingEndTime(e.target.value)}
                  disabled={isBacktesting}
                />
                <p className="text-xs text-muted-foreground">
                  Latest entry time (Market closes: 15:30)
                </p>
              </div>

              {/* Position Size */}
              <div className="space-y-2">
                <Label className="flex items-center justify-between">
                  <span>Position Size</span>
                  <Badge variant="outline">{positionSize.toFixed(1)}%</Badge>
                </Label>
                <Slider
                  value={[positionSize]}
                  onValueChange={(v) => setPositionSize(v[0])}
                  min={1.0}
                  max={5.0}
                  step={0.5}
                  disabled={isBacktesting}
                  className="w-full"
                />
                <p className="text-xs text-muted-foreground">
                  Capital allocated per trade (1%=conservative, 5%=aggressive)
                </p>
              </div>

              {/* Max Positions */}
              <div className="space-y-2">
                <Label>Max Concurrent Positions</Label>
                <Input
                  type="number"
                  value={maxPositions}
                  onChange={(e) => setMaxPositions(parseInt(e.target.value))}
                  min={1}
                  max={10}
                  step={1}
                  disabled={isBacktesting}
                />
                <p className="text-xs text-muted-foreground">
                  Maximum simultaneous trades (1-10)
                </p>
              </div>

              {/* Nifty Alignment */}
              <div className="space-y-2">
                <Label>Nifty Alignment</Label>
                <Select
                  value={niftyAlignment}
                  onValueChange={setNiftyAlignment}
                  disabled={isBacktesting}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">None Required</SelectItem>
                    <SelectItem value="same">Same Direction</SelectItem>
                    <SelectItem value="strong">Strong ({'>'}0.3%)</SelectItem>
                    <SelectItem value="very_strong">Very Strong ({'>'}0.5%)</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  Require Nifty index trend confirmation
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Run Button */}
        <Button
          onClick={runBacktest}
          disabled={isBacktesting || (dateMode === "single" ? !singleDate : (!startDate || !endDate))}
          className="w-full"
          size="lg"
        >
          {isBacktesting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Running Backtest...
            </>
          ) : (
            <>
              <Play className="mr-2 h-4 w-4" />
              Run Backtest {useCustomParams && "(Custom Parameters)"}
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
              <div className="flex items-center gap-2">
                <Badge variant={summary.win_rate >= 50 ? "default" : "destructive"}>
                  {summary.win_rate.toFixed(2)}% Win Rate
                </Badge>
                <Button
                  size="sm"
                  onClick={() => {
                    const backtestStartDate = dateMode === "single" ? singleDate! : startDate!;
                    const backtestEndDate = dateMode === "single" ? singleDate! : endDate!;
                    saveBacktestResults({
                      start_date: backtestStartDate,
                      end_date: backtestEndDate,
                      summary: summary,
                      trades: results,
                      custom_params_used: useCustomParams
                    });
                  }}
                  disabled={isSaving}
                  variant="outline"
                >
                  {isSaving ? (
                    <>
                      <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save className="h-3 w-3 mr-1" />
                      Save Results
                    </>
                  )}
                </Button>
              </div>
            </div>
            
            {saveError && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-sm text-red-800">Save Error: {saveError}</p>
              </div>
            )}
            
            {saveSuccess && (
              <div className="p-3 bg-green-50 border border-green-200 rounded-md">
                <p className="text-sm text-green-800">✅ Results saved successfully!</p>
              </div>
            )}

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

          </TabsContent>

          <TabsContent value="history" className="space-y-4 mt-6">
            {loadingHistory ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            ) : savedResults.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <History className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>No saved backtest results yet</p>
                <p className="text-sm">Run a backtest to save results automatically</p>
              </div>
            ) : (
              <div className="space-y-4">
                <h3 className="font-semibold">Recent Backtest Results</h3>
                <div className="space-y-2">
                  {savedResults.map((result) => (
                    <Card key={result.id} className="p-4">
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <div>
                            <Badge variant="outline">{result.strategy}</Badge>
                            {result.used_custom_params && (
                              <Badge variant="secondary" className="ml-2">Custom Params</Badge>
                            )}
                            <span className="text-sm text-muted-foreground ml-2">
                              {result.start_date} to {result.end_date}
                            </span>
                          </div>
                          <Badge variant={result.summary?.win_rate >= 50 ? "default" : "destructive"}>
                            {result.summary?.win_rate?.toFixed(1)}% WR
                          </Badge>
                        </div>
                        
                        {/* Show custom parameters if used */}
                        {result.used_custom_params && result.custom_params && (
                          <div className="grid grid-cols-3 gap-2 p-3 bg-muted/50 rounded-md text-xs">
                            <div>
                              <span className="text-muted-foreground">ADX:</span>{' '}
                              <span className="font-medium">{result.custom_params.adx_threshold}</span>
                            </div>
                            <div>
                              <span className="text-muted-foreground">RSI:</span>{' '}
                              <span className="font-medium">{result.custom_params.rsi_oversold}-{result.custom_params.rsi_overbought}</span>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Volume:</span>{' '}
                              <span className="font-medium">{result.custom_params.volume_multiplier}x</span>
                            </div>
                            <div>
                              <span className="text-muted-foreground">R:R:</span>{' '}
                              <span className="font-medium">1:{result.custom_params.risk_reward}</span>
                            </div>
                            <div>
                              <span className="text-muted-foreground">TF:</span>{' '}
                              <span className="font-medium">{result.custom_params.timeframe_alignment}</span>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Universe:</span>{' '}
                              <span className="font-medium">{result.custom_params.symbol_universe}</span>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Hours:</span>{' '}
                              <span className="font-medium">{result.custom_params.trading_start_time}-{result.custom_params.trading_end_time}</span>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Size:</span>{' '}
                              <span className="font-medium">{result.custom_params.position_size_pct}%</span>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Max Pos:</span>{' '}
                              <span className="font-medium">{result.custom_params.max_positions}</span>
                            </div>
                          </div>
                        )}
                        
                        <div className="grid grid-cols-5 gap-4 text-sm">
                          <div>
                            <div className="text-muted-foreground">Trades</div>
                            <div className="font-medium">{result.summary?.total_trades || 0}</div>
                          </div>
                          <div>
                            <div className="text-muted-foreground">P&L</div>
                            <div className={cn("font-medium", result.summary?.total_pnl >= 0 ? "text-green-600" : "text-red-600")}>
                              ₹{result.summary?.total_pnl?.toFixed(0) || 0}
                            </div>
                          </div>
                          <div>
                            <div className="text-muted-foreground">Profit Factor</div>
                            <div className="font-medium">{result.summary?.profit_factor?.toFixed(2) || 0}</div>
                          </div>
                          <div>
                            <div className="text-muted-foreground">Avg Win</div>
                            <div className="font-medium text-green-600">₹{result.summary?.avg_win?.toFixed(0) || 0}</div>
                          </div>
                          <div>
                            <div className="text-muted-foreground">Avg Loss</div>
                            <div className="font-medium text-red-600">₹{result.summary?.avg_loss?.toFixed(0) || 0}</div>
                          </div>
                        </div>
                        <div className="text-xs text-muted-foreground">
                          Saved: {result.created_at || result.timestamp?.toDate?.()?.toLocaleString?.() || 'Unknown'}
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
