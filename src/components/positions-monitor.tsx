"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Loader2, RefreshCw, TrendingUp, TrendingDown } from 'lucide-react';
import { orderApi } from '@/lib/trading-api';
import { useToast } from '@/hooks/use-toast';

interface Position {
  symbol: string;
  quantity: number;
  averagePrice: number;
  currentPrice: number;
  pnl: number;
  pnlPercent: number;
}

export function PositionsMonitor() {
  const [positions, setPositions] = useState<Position[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  const loadPositions = async () => {
    setIsLoading(true);
    try {
      const result = await orderApi.getPositions();
      setPositions(result.positions || []);
    } catch (error: any) {
      toast({
        title: 'Failed to Load Positions',
        description: error.message,
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadPositions();
    
    // Auto-refresh every 3 seconds for real-time P&L updates
    const interval = setInterval(() => {
      loadPositions();
    }, 3000);
    
    return () => clearInterval(interval);
  }, []);

  const totalPnl = positions.reduce((sum, pos) => sum + pos.pnl, 0);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Open Positions</CardTitle>
            <CardDescription>Current holdings and P&L</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={totalPnl >= 0 ? 'default' : 'destructive'} className="text-lg px-3 py-1">
              {totalPnl >= 0 ? '+' : ''}₹{totalPnl.toFixed(2)}
            </Badge>
            <Button
              variant="outline"
              size="icon"
              onClick={loadPositions}
              disabled={isLoading}
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {positions.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            No open positions
          </div>
        ) : (
          <div className="space-y-3">
            {positions.map((position, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-4 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
              >
                <div className="flex-1">
                  <div className="font-semibold">{position.symbol}</div>
                  <div className="text-sm text-muted-foreground">
                    Qty: {position.quantity} @ ₹{position.averagePrice.toFixed(2)}
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <div className="font-semibold">₹{position.currentPrice.toFixed(2)}</div>
                    <div className={`text-sm flex items-center gap-1 ${
                      position.pnl >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {position.pnl >= 0 ? (
                        <TrendingUp className="h-3 w-3" />
                      ) : (
                        <TrendingDown className="h-3 w-3" />
                      )}
                      {position.pnl >= 0 ? '+' : ''}₹{position.pnl.toFixed(2)}
                      <span className="text-xs">
                        ({position.pnlPercent >= 0 ? '+' : ''}{position.pnlPercent.toFixed(2)}%)
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
