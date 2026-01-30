import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Play, Square, TrendingUp, TrendingDown, Activity, DollarSign, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';

const CryptoBotDashboard = ({ userId = 'default_user' }) => {
  const [status, setStatus] = useState(null);
  const [activity, setActivity] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  // Fetch bot status
  const fetchStatus = async () => {
    try {
      const response = await fetch(`/api/crypto/status?user_id=${userId}`);
      const data = await response.json();
      if (data.success) {
        setStatus(data);
      }
    } catch (error) {
      console.error('Error fetching status:', error);
    }
  };

  // Fetch activity feed
  const fetchActivity = async () => {
    try {
      const response = await fetch(`/api/crypto/activity?user_id=${userId}&limit=20`);
      const data = await response.json();
      if (data.success) {
        setActivity(data.activities);
      }
    } catch (error) {
      console.error('Error fetching activity:', error);
    }
  };

  // Fetch statistics
  const fetchStats = async () => {
    try {
      const response = await fetch(`/api/crypto/stats?user_id=${userId}&days=7`);
      const data = await response.json();
      if (data.success) {
        setStats(data.stats);
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  // Load all data
  const loadData = async () => {
    setLoading(true);
    await Promise.all([fetchStatus(), fetchActivity(), fetchStats()]);
    setLoading(false);
  };

  // Auto-refresh every 10 seconds
  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, [userId]);

  // Start bot
  const handleStart = async () => {
    setActionLoading(true);
    try {
      const response = await fetch('/api/crypto/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          pair: status?.active_pair || 'BTC'
        })
      });
      const data = await response.json();
      
      if (data.success) {
        toast.success(data.message);
        await loadData();
      } else {
        toast.error(data.error || 'Failed to start bot');
      }
    } catch (error) {
      toast.error('Error starting bot');
      console.error(error);
    } finally {
      setActionLoading(false);
    }
  };

  // Stop bot
  const handleStop = async () => {
    setActionLoading(true);
    try {
      const response = await fetch('/api/crypto/stop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId })
      });
      const data = await response.json();
      
      if (data.success) {
        toast.success(data.message);
        await loadData();
      } else {
        toast.error(data.error || 'Failed to stop bot');
      }
    } catch (error) {
      toast.error('Error stopping bot');
      console.error(error);
    } finally {
      setActionLoading(false);
    }
  };

  // Switch pair
  const handleSwitchPair = async (newPair) => {
    setActionLoading(true);
    try {
      const response = await fetch('/api/crypto/switch-pair', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          pair: newPair
        })
      });
      const data = await response.json();
      
      if (data.success) {
        toast.success(data.message);
        await loadData();
      } else {
        toast.error(data.error || 'Failed to switch pair');
      }
    } catch (error) {
      toast.error('Error switching pair');
      console.error(error);
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-gray-400" />
      </div>
    );
  }

  const isRunning = status?.is_running;
  const activePair = status?.active_pair || 'BTC';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Crypto Trading Bot</h1>
          <p className="text-gray-500 mt-1">24/7 BTC & ETH Trading on CoinDCX</p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant={isRunning ? 'success' : 'secondary'}>
            {isRunning ? '● RUNNING' : '○ STOPPED'}
          </Badge>
          <Button
            onClick={loadData}
            variant="outline"
            size="icon"
            disabled={actionLoading}
          >
            <RefreshCw className={`w-4 h-4 ${actionLoading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>

      {/* Main Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="w-5 h-5" />
            Bot Controls
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Start/Stop */}
          <div className="flex items-center gap-3">
            {!isRunning ? (
              <Button
                onClick={handleStart}
                disabled={actionLoading}
                className="bg-green-600 hover:bg-green-700"
              >
                <Play className="w-4 h-4 mr-2" />
                Start Bot
              </Button>
            ) : (
              <Button
                onClick={handleStop}
                disabled={actionLoading}
                variant="destructive"
              >
                <Square className="w-4 h-4 mr-2" />
                Stop Bot
              </Button>
            )}
            
            <Badge variant="outline">
              {status?.mode === 'paper' ? '📄 Paper Trading' : '💰 Live Trading'}
            </Badge>
          </div>

          {/* Pair Selector */}
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium">Active Pair:</span>
            <div className="flex gap-2">
              <Button
                onClick={() => handleSwitchPair('BTC')}
                disabled={actionLoading || activePair === 'BTC'}
                variant={activePair === 'BTC' ? 'default' : 'outline'}
                size="sm"
              >
                BTC/USDT
              </Button>
              <Button
                onClick={() => handleSwitchPair('ETH')}
                disabled={actionLoading || activePair === 'ETH'}
                variant={activePair === 'ETH' ? 'default' : 'outline'}
                size="sm"
              >
                ETH/USDT
              </Button>
            </div>
          </div>

          {/* Strategies */}
          <div className="grid grid-cols-2 gap-4 pt-4 border-t">
            <div>
              <div className="text-sm font-medium mb-1">Day Strategy (9AM-9PM)</div>
              <Badge variant="outline">Momentum Scalping</Badge>
              <p className="text-xs text-gray-500 mt-1">Triple EMA + RSI on 5m candles</p>
            </div>
            <div>
              <div className="text-sm font-medium mb-1">Night Strategy (9PM-9AM)</div>
              <Badge variant="outline">Mean Reversion</Badge>
              <p className="text-xs text-gray-500 mt-1">Bollinger Bands + RSI on 1h candles</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Daily P&L</p>
                <p className={`text-2xl font-bold ${
                  (stats?.daily_pnl || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  ${(stats?.daily_pnl || 0).toFixed(2)}
                </p>
              </div>
              {(stats?.daily_pnl || 0) >= 0 ? (
                <TrendingUp className="w-8 h-8 text-green-600" />
              ) : (
                <TrendingDown className="w-8 h-8 text-red-600" />
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Total P&L</p>
                <p className={`text-2xl font-bold ${
                  (stats?.total_pnl || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  ${(stats?.total_pnl || 0).toFixed(2)}
                </p>
              </div>
              <DollarSign className="w-8 h-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div>
              <p className="text-sm text-gray-500">Win Rate (7d)</p>
              <p className="text-2xl font-bold">
                {stats?.win_rate || 0}%
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {stats?.winning_trades || 0} / {stats?.total_trades || 0} trades
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div>
              <p className="text-sm text-gray-500">Open Positions</p>
              <p className="text-2xl font-bold">
                {status?.open_positions || 0}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {activePair}/USDT
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Activity Feed */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {activity.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No activity yet</p>
            ) : (
              activity.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-xs">
                        {item.type}
                      </Badge>
                      <span className="text-sm">{item.message}</span>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(item.timestamp).toLocaleString()}
                    </p>
                  </div>
                  {item.pnl !== undefined && (
                    <div className={`text-sm font-medium ${
                      item.pnl >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {item.pnl >= 0 ? '+' : ''}{item.pnl.toFixed(2)} USDT
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default CryptoBotDashboard;
