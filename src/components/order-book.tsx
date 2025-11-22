"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Loader2, RefreshCw, X } from 'lucide-react';
import { orderApi } from '@/lib/trading-api';
import { useToast } from '@/hooks/use-toast';

interface Order {
  orderId: string;
  symbol: string;
  quantity: number;
  price: number;
  orderType: string;
  transactionType: 'BUY' | 'SELL';
  status: string;
  timestamp: string;
}

export function OrderBook() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [cancellingOrderId, setCancellingOrderId] = useState<string | null>(null);
  const { toast } = useToast();

  const loadOrders = async () => {
    setIsLoading(true);
    try {
      const result = await orderApi.getBook();
      setOrders(result.orders || []);
    } catch (error: any) {
      toast({
        title: 'Failed to Load Orders',
        description: error.message,
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadOrders();
  }, []);

  const handleCancelOrder = async (orderId: string) => {
    setCancellingOrderId(orderId);
    try {
      await orderApi.cancel(orderId);
      toast({
        title: 'Order Cancelled',
        description: `Order ${orderId} has been cancelled`,
      });
      loadOrders();
    } catch (error: any) {
      toast({
        title: 'Cancellation Failed',
        description: error.message,
        variant: 'destructive',
      });
    } finally {
      setCancellingOrderId(null);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'complete':
      case 'executed':
        return 'default';
      case 'open':
      case 'pending':
        return 'secondary';
      case 'cancelled':
      case 'rejected':
        return 'destructive';
      default:
        return 'outline';
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Order Book</CardTitle>
            <CardDescription>Order history and status</CardDescription>
          </div>
          <Button
            variant="outline"
            size="icon"
            onClick={loadOrders}
            disabled={isLoading}
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {orders.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            No orders yet
          </div>
        ) : (
          <div className="space-y-2">
            {orders.map((order) => (
              <div
                key={order.orderId}
                className="flex items-center justify-between p-4 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
              >
                <div className="flex-1 space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold">{order.symbol}</span>
                    <Badge variant={order.transactionType === 'BUY' ? 'default' : 'destructive'}>
                      {order.transactionType}
                    </Badge>
                    <Badge variant={getStatusColor(order.status)}>
                      {order.status}
                    </Badge>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Qty: {order.quantity} @ ₹{order.price.toFixed(2)} | {order.orderType}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    ID: {order.orderId} | {new Date(order.timestamp).toLocaleString()}
                  </div>
                </div>
                {(order.status.toLowerCase() === 'open' || order.status.toLowerCase() === 'pending') && (
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleCancelOrder(order.orderId)}
                    disabled={cancellingOrderId === order.orderId}
                  >
                    {cancellingOrderId === order.orderId ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <X className="h-4 w-4" />
                    )}
                  </Button>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
