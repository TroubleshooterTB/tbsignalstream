"use client";

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Loader2, Power, PowerOff, Wifi, WifiOff } from 'lucide-react';
import { websocketApi } from '@/lib/trading-api';
import { useToast } from '@/hooks/use-toast';

export function WebSocketControls() {
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  const handleInitialize = async () => {
    setIsLoading(true);
    try {
      const result = await websocketApi.initialize();
      setIsConnected(true);
      toast({
        title: 'WebSocket Connected',
        description: result.message || 'Successfully connected to live market data',
      });
    } catch (error: any) {
      toast({
        title: 'Connection Failed',
        description: error.message,
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = async () => {
    setIsLoading(true);
    try {
      await websocketApi.close();
      setIsConnected(false);
      toast({
        title: 'WebSocket Disconnected',
        description: 'Successfully closed live market data connection',
      });
    } catch (error: any) {
      toast({
        title: 'Disconnect Failed',
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
              {isConnected ? (
                <Wifi className="h-5 w-5 text-green-500" />
              ) : (
                <WifiOff className="h-5 w-5 text-gray-400" />
              )}
              Live Market Data
            </CardTitle>
            <CardDescription>WebSocket connection for real-time quotes</CardDescription>
          </div>
          <Badge variant={isConnected ? 'default' : 'secondary'}>
            {isConnected ? 'Connected' : 'Disconnected'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="flex gap-2">
        {!isConnected ? (
          <Button
            onClick={handleInitialize}
            disabled={isLoading}
            className="flex-1"
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Connecting...
              </>
            ) : (
              <>
                <Power className="mr-2 h-4 w-4" />
                Connect WebSocket
              </>
            )}
          </Button>
        ) : (
          <Button
            onClick={handleClose}
            disabled={isLoading}
            variant="destructive"
            className="flex-1"
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Disconnecting...
              </>
            ) : (
              <>
                <PowerOff className="mr-2 h-4 w-4" />
                Disconnect
              </>
            )}
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
