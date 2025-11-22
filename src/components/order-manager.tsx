"use client";

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Loader2, TrendingUp, TrendingDown } from 'lucide-react';
import { orderApi } from '@/lib/trading-api';
import { useToast } from '@/hooks/use-toast';

export function OrderManager() {
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();
  
  const [formData, setFormData] = useState({
    symbol: '',
    quantity: '',
    orderType: 'LIMIT' as 'MARKET' | 'LIMIT' | 'STOPLOSS_LIMIT' | 'STOPLOSS_MARKET',
    transactionType: 'BUY' as 'BUY' | 'SELL',
    price: '',
    triggerPrice: '',
    productType: 'INTRADAY' as 'INTRADAY' | 'DELIVERY',
  });

  const handlePlaceOrder = async () => {
    if (!formData.symbol || !formData.quantity) {
      toast({
        title: 'Validation Error',
        description: 'Please fill in symbol and quantity',
        variant: 'destructive',
      });
      return;
    }

    setIsLoading(true);
    try {
      const orderData: any = {
        symbol: formData.symbol.toUpperCase(),
        quantity: parseInt(formData.quantity),
        orderType: formData.orderType,
        transactionType: formData.transactionType,
        productType: formData.productType,
      };

      if (formData.orderType !== 'MARKET' && formData.price) {
        orderData.price = parseFloat(formData.price);
      }

      if (formData.orderType.includes('STOPLOSS') && formData.triggerPrice) {
        orderData.triggerPrice = parseFloat(formData.triggerPrice);
      }

      const result = await orderApi.place(orderData);
      
      toast({
        title: 'Order Placed Successfully',
        description: `Order ID: ${result.orderId || 'N/A'}`,
      });

      // Reset form
      setFormData({
        ...formData,
        symbol: '',
        quantity: '',
        price: '',
        triggerPrice: '',
      });
    } catch (error: any) {
      toast({
        title: 'Order Failed',
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
        <CardTitle>Place Order</CardTitle>
        <CardDescription>Execute trades with Angel One broker</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="symbol">Symbol</Label>
            <Input
              id="symbol"
              placeholder="SBIN-EQ"
              value={formData.symbol}
              onChange={(e) => setFormData({ ...formData, symbol: e.target.value })}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="quantity">Quantity</Label>
            <Input
              id="quantity"
              type="number"
              placeholder="1"
              value={formData.quantity}
              onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="orderType">Order Type</Label>
            <Select
              value={formData.orderType}
              onValueChange={(value: any) => setFormData({ ...formData, orderType: value })}
            >
              <SelectTrigger id="orderType">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="MARKET">Market</SelectItem>
                <SelectItem value="LIMIT">Limit</SelectItem>
                <SelectItem value="STOPLOSS_LIMIT">Stop Loss Limit</SelectItem>
                <SelectItem value="STOPLOSS_MARKET">Stop Loss Market</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="productType">Product Type</Label>
            <Select
              value={formData.productType}
              onValueChange={(value: any) => setFormData({ ...formData, productType: value })}
            >
              <SelectTrigger id="productType">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="INTRADAY">Intraday</SelectItem>
                <SelectItem value="DELIVERY">Delivery</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {formData.orderType !== 'MARKET' && (
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="price">Price</Label>
              <Input
                id="price"
                type="number"
                step="0.05"
                placeholder="0.00"
                value={formData.price}
                onChange={(e) => setFormData({ ...formData, price: e.target.value })}
              />
            </div>
            {formData.orderType.includes('STOPLOSS') && (
              <div className="space-y-2">
                <Label htmlFor="triggerPrice">Trigger Price</Label>
                <Input
                  id="triggerPrice"
                  type="number"
                  step="0.05"
                  placeholder="0.00"
                  value={formData.triggerPrice}
                  onChange={(e) => setFormData({ ...formData, triggerPrice: e.target.value })}
                />
              </div>
            )}
          </div>
        )}

        <div className="flex gap-2 pt-2">
          <Button
            onClick={() => {
              setFormData({ ...formData, transactionType: 'BUY' });
              setTimeout(handlePlaceOrder, 0);
            }}
            disabled={isLoading}
            className="flex-1 bg-green-600 hover:bg-green-700"
          >
            {isLoading && formData.transactionType === 'BUY' ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Placing...
              </>
            ) : (
              <>
                <TrendingUp className="mr-2 h-4 w-4" />
                Buy
              </>
            )}
          </Button>
          <Button
            onClick={() => {
              setFormData({ ...formData, transactionType: 'SELL' });
              setTimeout(handlePlaceOrder, 0);
            }}
            disabled={isLoading}
            variant="destructive"
            className="flex-1"
          >
            {isLoading && formData.transactionType === 'SELL' ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Placing...
              </>
            ) : (
              <>
                <TrendingDown className="mr-2 h-4 w-4" />
                Sell
              </>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
