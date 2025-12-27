"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { db } from '@/lib/firebase';
import { collection, query, where, onSnapshot, orderBy, Timestamp, doc } from 'firebase/firestore';
import { useAuth } from '@/context/auth-context';
import { Clock, TrendingUp, TrendingDown, Target, AlertCircle, CheckCircle, XCircle, Calendar } from 'lucide-react';

interface ReplaySignal {
  id: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  entry_price: number;
  exit_price?: number;
  stop_loss: number;
  target: number;
  confidence: number;
  timestamp: Date;
  outcome?: 'hit_target' | 'hit_sl' | 'open';
  pnl?: number;
  pnl_percent?: number;
  pattern?: string;
}

interface ReplayStats {
  totalSignals: number;
  winners: number;
  losers: number;
  open: number;
  winRate: number;
  totalPnL: number;
  avgWin: number;
  avgLoss: number;
  profitFactor: number;
}

export function ReplayResultsPanel() {
  const { firebaseUser } = useAuth();
  const [replaySignals, setReplaySignals] = useState<ReplaySignal[]>([]);
  const [replayDate, setReplayDate] = useState<string | null>(null);
  const [isReplayActive, setIsReplayActive] = useState(false);
  const [stats, setStats] = useState<ReplayStats>({
    totalSignals: 0,
    winners: 0,
    losers: 0,
    open: 0,
    winRate: 0,
    totalPnL: 0,
    avgWin: 0,
    avgLoss: 0,
    profitFactor: 0
  });

  useEffect(() => {
    if (!firebaseUser?.uid) return;

    // Listen to bot config to check if replay mode is active
    const configUnsubscribe = onSnapshot(
      doc(db, 'bot_configs', firebaseUser.uid),
      (docSnap) => {
        if (docSnap.exists()) {
          const data = docSnap.data();
          setIsReplayActive(data.replay_mode === true);
          setReplayDate(data.replay_date || null);
        }
      },
      (error) => {
        console.warn('[ReplayResults] Config listener error:', error.message);
      }
    );

    // Listen to replay signals
    const signalsQuery = query(
      collection(db, 'signals'),
      where('userId', '==', firebaseUser.uid),
      where('replay_mode', '==', true),
      orderBy('timestamp', 'desc')
    );

    const signalsUnsubscribe = onSnapshot(
      signalsQuery, 
      (snapshot) => {
        const signals: ReplaySignal[] = [];
        
        snapshot.forEach((doc) => {
        const data = doc.data();
        signals.push({
          id: doc.id,
          symbol: data.symbol,
          side: data.side,
          entry_price: data.entry_price,
          exit_price: data.exit_price,
          stop_loss: data.stop_loss,
          target: data.target,
          confidence: data.confidence || 0,
          timestamp: data.timestamp?.toDate() || new Date(),
          outcome: data.outcome,
          pnl: data.pnl,
          pnl_percent: data.pnl_percent,
          pattern: data.pattern
        });
      });

      setReplaySignals(signals);
      calculateStats(signals);
    },
    (error) => {
      console.warn('[ReplayResults] Signals listener error:', error.message);
      setReplaySignals([]);
    }
    );

    return () => {
      configUnsubscribe();
      signalsUnsubscribe();
    };
  }, [firebaseUser?.uid]);

  const calculateStats = (signals: ReplaySignal[]) => {
    const totalSignals = signals.length;
    const winners = signals.filter(s => s.outcome === 'hit_target').length;
    const losers = signals.filter(s => s.outcome === 'hit_sl').length;
    const open = signals.filter(s => !s.outcome || s.outcome === 'open').length;
    
    const winRate = totalSignals > 0 ? (winners / totalSignals) * 100 : 0;
    
    const totalPnL = signals.reduce((sum, s) => sum + (s.pnl || 0), 0);
    
    const wins = signals.filter(s => s.outcome === 'hit_target' && s.pnl);
    const losses = signals.filter(s => s.outcome === 'hit_sl' && s.pnl);
    
    const avgWin = wins.length > 0 
      ? wins.reduce((sum, s) => sum + (s.pnl || 0), 0) / wins.length 
      : 0;
    
    const avgLoss = losses.length > 0
      ? Math.abs(losses.reduce((sum, s) => sum + (s.pnl || 0), 0) / losses.length)
      : 0;
    
    const totalWinAmount = wins.reduce((sum, s) => sum + (s.pnl || 0), 0);
    const totalLossAmount = Math.abs(losses.reduce((sum, s) => sum + (s.pnl || 0), 0));
    
    const profitFactor = totalLossAmount > 0 ? totalWinAmount / totalLossAmount : 0;

    setStats({
      totalSignals,
      winners,
      losers,
      open,
      winRate,
      totalPnL,
      avgWin,
      avgLoss,
      profitFactor
    });
  };

  if (!isReplayActive && replaySignals.length === 0) {
    return null; // Don't show if not in replay mode and no replay data
  }

  return (
    <Card className="border-blue-200 bg-blue-50/50 dark:bg-blue-950/20">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5 text-blue-600" />
              🔄 Replay Mode Results
            </CardTitle>
            <CardDescription>
              {replayDate ? `Testing bot on ${replayDate}` : 'Historical replay results'}
            </CardDescription>
          </div>
          {isReplayActive && (
            <Badge variant="outline" className="bg-blue-100 text-blue-700 border-blue-300">
              REPLAY ACTIVE
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Performance Summary */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 bg-white dark:bg-gray-800 rounded-lg border">
            <div className="text-sm text-muted-foreground mb-1">Total Signals</div>
            <div className="text-2xl font-bold">{stats.totalSignals}</div>
          </div>
          
          <div className="p-4 bg-white dark:bg-gray-800 rounded-lg border">
            <div className="text-sm text-muted-foreground mb-1">Win Rate</div>
            <div className={`text-2xl font-bold ${stats.winRate >= 50 ? 'text-green-600' : 'text-red-600'}`}>
              {stats.winRate.toFixed(1)}%
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              {stats.winners}W / {stats.losers}L / {stats.open}Open
            </div>
          </div>
          
          <div className="p-4 bg-white dark:bg-gray-800 rounded-lg border">
            <div className="text-sm text-muted-foreground mb-1">Total P&L</div>
            <div className={`text-2xl font-bold ${stats.totalPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              ₹{stats.totalPnL.toFixed(0)}
            </div>
          </div>
          
          <div className="p-4 bg-white dark:bg-gray-800 rounded-lg border">
            <div className="text-sm text-muted-foreground mb-1">Profit Factor</div>
            <div className={`text-2xl font-bold ${stats.profitFactor >= 1 ? 'text-green-600' : 'text-red-600'}`}>
              {stats.profitFactor.toFixed(2)}
            </div>
          </div>
        </div>

        {/* Signals List */}
        <div>
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <Target className="h-4 w-4" />
            Replay Signals ({replaySignals.length})
          </h3>
          
          {replaySignals.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <AlertCircle className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>No signals generated yet in replay mode</p>
              <p className="text-sm mt-1">Bot is analyzing historical data...</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {replaySignals.map((signal) => (
                <div
                  key={signal.id}
                  className="p-4 bg-white dark:bg-gray-800 rounded-lg border flex items-center justify-between hover:shadow-md transition-shadow"
                >
                  <div className="flex items-center gap-4">
                    {/* Outcome Icon */}
                    {signal.outcome === 'hit_target' && (
                      <CheckCircle className="h-8 w-8 text-green-600 flex-shrink-0" />
                    )}
                    {signal.outcome === 'hit_sl' && (
                      <XCircle className="h-8 w-8 text-red-600 flex-shrink-0" />
                    )}
                    {(!signal.outcome || signal.outcome === 'open') && (
                      <Clock className="h-8 w-8 text-gray-400 flex-shrink-0" />
                    )}
                    
                    {/* Signal Details */}
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-bold text-lg">{signal.symbol}</span>
                        <Badge variant={signal.side === 'BUY' ? 'default' : 'destructive'}>
                          {signal.side}
                        </Badge>
                        {signal.pattern && (
                          <Badge variant="outline" className="text-xs">
                            {signal.pattern}
                          </Badge>
                        )}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        Entry: ₹{signal.entry_price.toFixed(2)} | 
                        Target: ₹{signal.target.toFixed(2)} | 
                        SL: ₹{signal.stop_loss.toFixed(2)}
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        {signal.timestamp.toLocaleTimeString()} | Confidence: {(signal.confidence * 100).toFixed(0)}%
                      </div>
                    </div>
                  </div>

                  {/* P&L */}
                  {signal.pnl !== undefined && (
                    <div className="text-right">
                      <div className={`text-xl font-bold ${signal.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {signal.pnl >= 0 ? '+' : ''}₹{signal.pnl.toFixed(0)}
                      </div>
                      {signal.pnl_percent !== undefined && (
                        <div className={`text-sm ${signal.pnl_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {signal.pnl_percent >= 0 ? '+' : ''}{signal.pnl_percent.toFixed(2)}%
                        </div>
                      )}
                    </div>
                  )}
                  
                  {(!signal.pnl && signal.outcome === 'open') && (
                    <Badge variant="outline">Open</Badge>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Performance Details */}
        {stats.totalSignals > 0 && (
          <div className="grid grid-cols-2 gap-4 pt-4 border-t">
            <div className="p-3 bg-green-50 dark:bg-green-950/20 rounded-lg">
              <div className="flex items-center gap-2 text-green-700 dark:text-green-400 mb-1">
                <TrendingUp className="h-4 w-4" />
                <span className="text-sm font-medium">Avg Win</span>
              </div>
              <div className="text-xl font-bold text-green-600">
                ₹{stats.avgWin.toFixed(0)}
              </div>
            </div>
            
            <div className="p-3 bg-red-50 dark:bg-red-950/20 rounded-lg">
              <div className="flex items-center gap-2 text-red-700 dark:text-red-400 mb-1">
                <TrendingDown className="h-4 w-4" />
                <span className="text-sm font-medium">Avg Loss</span>
              </div>
              <div className="text-xl font-bold text-red-600">
                ₹{stats.avgLoss.toFixed(0)}
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
