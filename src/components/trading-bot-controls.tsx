"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Loader2, Play, Square, Bot, AlertCircle } from 'lucide-react';
import { useTradingContext } from '@/context/trading-context';

export function TradingBotControls() {
  const {
    isBotRunning,
    isBotLoading,
    botError,
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
        {/* Error Display */}
        {botError && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Bot Error</AlertTitle>
            <AlertDescription>{botError}</AlertDescription>
          </Alert>
        )}

        <div className="space-y-2">
          <Label htmlFor="symbols">Symbol Universe</Label>
          <Select
            value={botConfig.symbols || "NIFTY50"}
            onValueChange={(value) => updateBotConfig({ symbols: value })}
            disabled={isBotRunning}
          >
            <SelectTrigger id="symbols">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="NIFTY50">Nifty 50 (Recommended)</SelectItem>
              <SelectItem value="NIFTY100">Nifty 100 (More opportunities)</SelectItem>
              <SelectItem value="NIFTY200">Nifty 200 (Maximum coverage)</SelectItem>
            </SelectContent>
          </Select>
          <p className="text-xs text-muted-foreground">
            {botConfig.strategy === 'alpha-ensemble' 
              ? 'Alpha-Ensemble applies intelligent screening (EMA200, ADX, RSI, Volume) to find best opportunities'
              : 'Bot scans all symbols and selects trades with highest confidence scores'}
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
              {botConfig.mode === 'live' ? '🔴 LIVE TRADING MODE' : botConfig.mode === 'replay' ? '🔄 REPLAY MODE' : '📄 Paper Trading Mode'}
            </Label>
            <span className="text-sm text-muted-foreground">
              {botConfig.mode === 'live' 
                ? 'Real money will be used. Trades will be executed on your broker account.' 
                : botConfig.mode === 'replay'
                ? 'Test bot on historical date. No real trades.'
                : 'Simulated trading. No real money will be used.'}
            </span>
          </div>
          <Switch
            id="liveMode"
            checked={botConfig.mode === 'live'}
            onCheckedChange={(checked) => updateBotConfig({ mode: checked ? 'live' : 'paper' })}
            disabled={isBotRunning || botConfig.mode === 'replay'}
          />
        </div>

        {/* Phase 3: Replay Mode Option */}
        <div className="p-4 bg-blue-50 dark:bg-blue-950 rounded-lg border border-blue-200 dark:border-blue-800 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex flex-col gap-1">
              <Label htmlFor="replayMode" className="cursor-pointer font-semibold">
                🔄 Replay Mode (Historical Testing)
              </Label>
              <span className="text-sm text-muted-foreground">
                Test your live bot on a past date to see how it would have performed
              </span>
            </div>
            <Switch
              id="replayMode"
              checked={botConfig.mode === 'replay'}
              onCheckedChange={(checked) => updateBotConfig({ mode: checked ? 'replay' : 'paper' })}
              disabled={isBotRunning}
            />
          </div>
          
          {botConfig.mode === 'replay' && (
            <div className="space-y-2 pt-2 border-t border-blue-200 dark:border-blue-800">
              <Label htmlFor="replayDate">Select Historical Date</Label>
              <Input
                id="replayDate"
                type="date"
                value={botConfig.replayDate || ''}
                onChange={(e) => updateBotConfig({ replayDate: e.target.value })}
                disabled={isBotRunning}
                max={new Date().toISOString().split('T')[0]}
                min={new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]} // Last 90 days
              />
              <p className="text-xs text-blue-600 dark:text-blue-400">
                ⚡ Bot will replay the entire trading day at accelerated speed
              </p>
            </div>
          )}
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
