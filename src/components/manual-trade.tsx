'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle, CheckCircle2, Loader2, TrendingUp, TrendingDown } from 'lucide-react';
import { placeTrade, type ManualTradeRequest } from '@/lib/api/manual-trade';

interface ManualTradeProps {
  userId: string;
  watchlist?: string[];
  currentPrice?: number;
}

export function ManualTrade({ userId, watchlist = [], currentPrice }: ManualTradeProps) {
  const [symbol, setSymbol] = useState('');
  const [action, setAction] = useState<'BUY' | 'SELL'>('BUY');
  const [quantity, setQuantity] = useState(10);
  const [stopLossPct, setStopLossPct] = useState(2.0);
  const [targetPct, setTargetPct] = useState(5.0);
  const [price, setPrice] = useState(currentPrice || 0);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Calculate values
  const entryPrice = price || 0;
  const stopLossPrice = action === 'BUY' 
    ? entryPrice * (1 - stopLossPct / 100)
    : entryPrice * (1 + stopLossPct / 100);
  const targetPrice = action === 'BUY'
    ? entryPrice * (1 + targetPct / 100)
    : entryPrice * (1 - targetPct / 100);
  const riskRewardRatio = targetPct / stopLossPct;
  const totalValue = entryPrice * quantity;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setResult(null);
    setLoading(true);

    try {
      const trade: ManualTradeRequest = {
        user_id: userId,
        symbol,
        action,
        quantity,
        stop_loss_pct: stopLossPct,
        target_pct: targetPct,
        price: price || undefined,
      };

      const response = await placeTrade(trade);
      setResult({ type: 'success', text: response.message });
      
      // Reset form on success
      setSymbol('');
      setQuantity(10);
      setPrice(0);
    } catch (error) {
      setResult({
        type: 'error',
        text: error instanceof Error ? error.message : 'Failed to place trade',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Manual Trade</CardTitle>
        <CardDescription>
          Place trades manually, bypassing all screening filters. Use with caution.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Symbol Selection */}
          <div className="space-y-2">
            <Label htmlFor="symbol">Symbol</Label>
            {watchlist.length > 0 ? (
              <Select value={symbol} onValueChange={setSymbol}>
                <SelectTrigger id="symbol">
                  <SelectValue placeholder="Select symbol" />
                </SelectTrigger>
                <SelectContent>
                  {watchlist.map((sym) => (
                    <SelectItem key={sym} value={sym}>
                      {sym}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ) : (
              <Input
                id="symbol"
                placeholder="RELIANCE"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                required
              />
            )}
          </div>

          {/* Buy/Sell Toggle */}
          <div className="space-y-2">
            <Label>Action</Label>
            <div className="flex gap-2">
              <Button
                type="button"
                variant={action === 'BUY' ? 'default' : 'outline'}
                className="flex-1"
                onClick={() => setAction('BUY')}
              >
                <TrendingUp className="mr-2 h-4 w-4" />
                BUY
              </Button>
              <Button
                type="button"
                variant={action === 'SELL' ? 'destructive' : 'outline'}
                className="flex-1"
                onClick={() => setAction('SELL')}
              >
                <TrendingDown className="mr-2 h-4 w-4" />
                SELL
              </Button>
            </div>
          </div>

          {/* Quantity */}
          <div className="space-y-2">
            <Label htmlFor="quantity">Quantity</Label>
            <Input
              id="quantity"
              type="number"
              min={1}
              max={1000}
              value={quantity}
              onChange={(e) => setQuantity(parseInt(e.target.value) || 1)}
              required
            />
          </div>

          {/* Entry Price */}
          <div className="space-y-2">
            <Label htmlFor="price">Entry Price (₹)</Label>
            <Input
              id="price"
              type="number"
              step="0.05"
              min={0}
              value={price}
              onChange={(e) => setPrice(parseFloat(e.target.value) || 0)}
              placeholder="Leave empty for market price"
            />
          </div>

          {/* Stop Loss % */}
          <div className="space-y-2">
            <Label htmlFor="stop-loss">
              Stop Loss: {stopLossPct.toFixed(1)}% (₹{stopLossPrice.toFixed(2)})
            </Label>
            <Slider
              id="stop-loss"
              min={0.5}
              max={10}
              step={0.1}
              value={[stopLossPct]}
              onValueChange={([value]) => setStopLossPct(value)}
            />
            <p className="text-xs text-muted-foreground">Risk per share: ₹{Math.abs(entryPrice - stopLossPrice).toFixed(2)}</p>
          </div>

          {/* Target % */}
          <div className="space-y-2">
            <Label htmlFor="target">
              Target: {targetPct.toFixed(1)}% (₹{targetPrice.toFixed(2)})
            </Label>
            <Slider
              id="target"
              min={1}
              max={20}
              step={0.5}
              value={[targetPct]}
              onValueChange={([value]) => setTargetPct(value)}
            />
            <p className="text-xs text-muted-foreground">Reward per share: ₹{Math.abs(targetPrice - entryPrice).toFixed(2)}</p>
          </div>

          {/* Trade Summary */}
          <div className="rounded-lg border p-4 space-y-2 bg-muted/50">
            <h4 className="font-medium">Trade Summary</h4>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <span className="text-muted-foreground">Total Value:</span>
                <span className="ml-2 font-medium">₹{totalValue.toFixed(2)}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Risk/Reward:</span>
                <span className="ml-2 font-medium">1:{riskRewardRatio.toFixed(2)}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Max Loss:</span>
                <span className="ml-2 font-medium text-red-600">
                  ₹{(Math.abs(entryPrice - stopLossPrice) * quantity).toFixed(2)}
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">Max Profit:</span>
                <span className="ml-2 font-medium text-green-600">
                  ₹{(Math.abs(targetPrice - entryPrice) * quantity).toFixed(2)}
                </span>
              </div>
            </div>
          </div>

          {/* Result Message */}
          {result && (
            <Alert variant={result.type === 'error' ? 'destructive' : 'default'}>
              {result.type === 'success' ? (
                <CheckCircle2 className="h-4 w-4" />
              ) : (
                <AlertCircle className="h-4 w-4" />
              )}
              <AlertDescription>{result.text}</AlertDescription>
            </Alert>
          )}

          {/* Submit Button */}
          <Button type="submit" disabled={loading || !symbol || !price} className="w-full" size="lg">
            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Place {action} Order
          </Button>

          <p className="text-xs text-center text-muted-foreground">
            ⚠️ Manual trades bypass all screening. Ensure you've analyzed the setup carefully.
          </p>
        </form>
      </CardContent>
    </Card>
  );
}
