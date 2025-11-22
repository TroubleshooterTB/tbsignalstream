"use client";

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Loader2, Play, Square, Bot } from 'lucide-react';
import { tradingBotApi } from '@/lib/trading-api';
import { useToast } from '@/hooks/use-toast';

export function TradingBotControls() {
  const [isRunning, setIsRunning] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();
  
  const [config, setConfig] = useState({
    symbols: 'SBIN-EQ,RELIANCE-EQ,TCS-EQ',
    mode: 'paper' as 'paper' | 'live',
    maxPositions: '3',
    positionSize: '1000',
  });

  const handleStart = async () => {
    setIsLoading(true);
    try {
      const symbols = config.symbols.split(',').map(s => s.trim()).filter(Boolean);
      
      if (symbols.length === 0) {
        toast({
          title: 'Validation Error',
          description: 'Please enter at least one symbol',
          variant: 'destructive',
        });
        return;
      }

      const result = await tradingBotApi.start({
        symbols,
        mode: config.mode,
        maxPositions: parseInt(config.maxPositions),
        positionSize: parseFloat(config.positionSize),
      });
      
      setIsRunning(true);
      toast({
        title: 'Trading Bot Started',
        description: `Bot is now ${config.mode === 'paper' ? 'paper trading' : 'live trading'} with ${symbols.length} symbols`,
      });
    } catch (error: any) {
      toast({
        title: 'Failed to Start Bot',
        description: error.message,
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleStop = async () => {
    setIsLoading(true);
    try {
      await tradingBotApi.stop();
      setIsRunning(false);
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
      setIsLoading(false);
    }
  };

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
          <Badge variant={isRunning ? 'default' : 'secondary'} className={isRunning ? 'bg-green-600' : ''}>
            {isRunning ? 'Running' : 'Stopped'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="symbols">Symbols (comma-separated)</Label>
          <Input
            id="symbols"
            placeholder="SBIN-EQ,RELIANCE-EQ,TCS-EQ"
            value={config.symbols}
            onChange={(e) => setConfig({ ...config, symbols: e.target.value })}
            disabled={isRunning}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="maxPositions">Max Positions</Label>
            <Input
              id="maxPositions"
              type="number"
              value={config.maxPositions}
              onChange={(e) => setConfig({ ...config, maxPositions: e.target.value })}
              disabled={isRunning}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="positionSize">Position Size (₹)</Label>
            <Input
              id="positionSize"
              type="number"
              value={config.positionSize}
              onChange={(e) => setConfig({ ...config, positionSize: e.target.value })}
              disabled={isRunning}
            />
          </div>
        </div>

        <div className="flex items-center justify-between p-4 bg-amber-50 dark:bg-amber-950 rounded-lg border border-amber-200 dark:border-amber-800">
          <div className="flex flex-col gap-1">
            <Label htmlFor="liveMode" className="cursor-pointer font-semibold">
              {config.mode === 'live' ? '🔴 LIVE TRADING MODE' : '📄 Paper Trading Mode'}
            </Label>
            <span className="text-sm text-muted-foreground">
              {config.mode === 'live' 
                ? 'Real money will be used. Trades will be executed on your broker account.' 
                : 'Simulated trading. No real money will be used.'}
            </span>
          </div>
          <Switch
            id="liveMode"
            checked={config.mode === 'live'}
            onCheckedChange={(checked) => setConfig({ ...config, mode: checked ? 'live' : 'paper' })}
            disabled={isRunning}
          />
        </div>

        <div className="flex gap-2 pt-2">
          {!isRunning ? (
            <Button
              onClick={handleStart}
              disabled={isLoading}
              className="flex-1"
              size="lg"
            >
              {isLoading ? (
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
              onClick={handleStop}
              disabled={isLoading}
              variant="destructive"
              className="flex-1"
              size="lg"
            >
              {isLoading ? (
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
