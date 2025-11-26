"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Loader2, Power, PowerOff, Wifi, WifiOff } from 'lucide-react';
import { useTradingContext } from '@/context/trading-context';

export function WebSocketControls() {
  const {
    isWebSocketConnected,
    isWebSocketLoading,
    connectWebSocket,
    disconnectWebSocket
  } = useTradingContext();

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              {isWebSocketConnected ? (
                <Wifi className="h-5 w-5 text-green-500" />
              ) : (
                <WifiOff className="h-5 w-5 text-gray-400" />
              )}
              Live Market Data
            </CardTitle>
            <CardDescription>WebSocket connection for real-time quotes</CardDescription>
          </div>
          <Badge variant={isWebSocketConnected ? 'default' : 'secondary'}>
            {isWebSocketConnected ? 'Connected' : 'Disconnected'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="flex gap-2">
        {!isWebSocketConnected ? (
          <Button
            onClick={connectWebSocket}
            disabled={isWebSocketLoading}
            className="flex-1"
          >
            {isWebSocketLoading ? (
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
            onClick={disconnectWebSocket}
            disabled={isWebSocketLoading}
            variant="destructive"
            className="flex-1"
          >
            {isWebSocketLoading ? (
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
