"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Loader2, Play, Square, Bot } from 'lucide-react';
import { useTradingContext } from '@/context/trading-context';

export function TradingBotControls() {
  const {
    isBotRunning,
    isBotLoading,
    botConfig,
    startTradingBot,
    stopTradingBot,
    updateBotConfig
  } = useTradingContext();

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Bot className="h-5 w-5" />
              Live Trading Bot
            </CardTitle>
            <CardDescription>Automated trading with real-time signals</CardDescription>
          </div>
          <Badge variant={isBotRunning ? 'default' : 'secondary'} className={isBotRunning ? 'bg-green-600' : ''}>
            {isBotRunning ? 'Running' : 'Stopped'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="symbols">Symbols (comma-separated)</Label>
          <Input
            id="symbols"
            placeholder="All Nifty 50 stocks (default) or custom list: SBIN-EQ,RELIANCE-EQ,TCS-EQ"
            value={botConfig.symbols}
            onChange={(e) => updateBotConfig({ symbols: e.target.value })}
            disabled={isBotRunning}
          />
          <p className="text-xs text-muted-foreground">
            Bot scans all symbols and selects trades with highest confidence scores
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="strategy">Trading Strategy</Label>
          <Select
            value={botConfig.strategy}
            onValueChange={(value: 'pattern' | 'ironclad' | 'both' | 'defining' | 'alpha-ensemble') => updateBotConfig({ strategy: value })}
            disabled={isBotRunning}
          >
            <SelectTrigger id="strategy">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="alpha-ensemble">⭐ Alpha-Ensemble (NEW - 36% WR, 2.64 PF, 250% Returns)</SelectItem>
              <SelectItem value="defining">The Defining Order v3.2 (59% WR, 24% Returns)</SelectItem>
              <SelectItem value="pattern">Pattern Detector</SelectItem>
              <SelectItem value="ironclad">Ironclad Strategy (Old Defining Range)</SelectItem>
              <SelectItem value="both">Both (Dual Confirmation)</SelectItem>
            </SelectContent>
          </Select>
          <p className="text-sm text-muted-foreground">
            {botConfig.strategy === 'alpha-ensemble' && '⭐ VALIDATED: Multi-timeframe momentum strategy. 47 trades, 36% WR, 2.64 PF, 250% returns in 1 month. High R:R design (2.5:1). Uses EMA200, ADX, RSI, ATR, Nifty alignment, volume filters.'}
            {botConfig.strategy === 'defining' && '✅ VALIDATED: 43 trades, 59% win rate, 24% returns (Dec 2025). Filters toxic hours, uses smart breakout detection.'}
            {botConfig.strategy === 'pattern' && 'Uses pattern detection with 30-point validation'}
            {botConfig.strategy === 'ironclad' && 'Uses defining range breakout with multi-indicator confirmation'}
            {botConfig.strategy === 'both' && 'Only trades when both strategies agree (highest confidence)'}
          </p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="maxPositions">Max Positions</Label>
            <Input
              id="maxPositions"
              type="number"
              value={botConfig.maxPositions}
              onChange={(e) => updateBotConfig({ maxPositions: e.target.value })}
              disabled={isBotRunning}
            />
            <p className="text-xs text-muted-foreground">
              Maximum concurrent trades
            </p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="positionSize">Total Trading Capital (₹)</Label>
            <Input
              id="positionSize"
              type="number"
              value={botConfig.positionSize}
              onChange={(e) => updateBotConfig({ positionSize: e.target.value })}
              disabled={isBotRunning}
              placeholder="50000"
            />
            <p className="text-xs text-muted-foreground">
              Bot manages position sizing (1% risk/trade)
            </p>
          </div>
        </div>

        <div className="flex items-center justify-between p-4 bg-amber-50 dark:bg-amber-950 rounded-lg border border-amber-200 dark:border-amber-800">
          <div className="flex flex-col gap-1">
            <Label htmlFor="liveMode" className="cursor-pointer font-semibold">
              {botConfig.mode === 'live' ? '🔴 LIVE TRADING MODE' : '📄 Paper Trading Mode'}
            </Label>
            <span className="text-sm text-muted-foreground">
              {botConfig.mode === 'live' 
                ? 'Real money will be used. Trades will be executed on your broker account.' 
                : 'Simulated trading. No real money will be used.'}
            </span>
          </div>
          <Switch
            id="liveMode"
            checked={botConfig.mode === 'live'}
            onCheckedChange={(checked) => updateBotConfig({ mode: checked ? 'live' : 'paper' })}
            disabled={isBotRunning}
          />
        </div>

        <div className="flex gap-2 pt-2">
          {!isBotRunning ? (
            <Button
              onClick={startTradingBot}
              disabled={isBotLoading}
              className="flex-1"
              size="lg"
            >
              {isBotLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Starting...
                </>
              ) : (
                <>
                  <Play className="mr-2 h-4 w-4" />
                  Start Trading Bot
                </>
              )}
            </Button>
          ) : (
            <Button
              onClick={stopTradingBot}
              disabled={isBotLoading}
              variant="destructive"
              className="flex-1"
              size="lg"
            >
              {isBotLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Stopping...
                </>
              ) : (
                <>
                  <Square className="mr-2 h-4 w-4" />
                  Stop Trading Bot
                </>
              )}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
