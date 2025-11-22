
"use client";

import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import {
  BarChart,
  DollarSign,
  TrendingDown,
  TrendingUp,
  Percent,
  RefreshCw,
} from "lucide-react";
import {
  Bar,
  BarChart as RechartsBarChart,
  ResponsiveContainer,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  Line,
  LineChart,
} from "recharts";
import { ChartContainer, ChartTooltipContent } from "./ui/chart";
import { Button } from './ui/button';

type TradeLog = {
  id: string;
  ticker: string;
  entry_price: number;
  exit_price: number;
  outcome: "Profit Target" | "Stop Loss" | "Expired" | "EOD" | "Technical Exit";
  pnl_points: number;
  pnl_percent: number;
  entry_timestamp: string;
  exit_timestamp: string;
};

const calculateMetrics = (logs: TradeLog[]) => {
  const totalTrades = logs.length;
  if (totalTrades === 0) {
    return { winRate: 0, totalPnl: 0, avgGain: 0, avgLoss: 0, pnlOverTime: [], totalTrades: 0, winningTrades: 0, losingTrades: 0, payoffRatio: 0 };
  }

  const winningTrades = logs.filter((log) => log.pnl_points > 0);
  const losingTrades = logs.filter((log) => log.pnl_points < 0);
  
  const winRate = (winningTrades.length / totalTrades) * 100;
  const totalPnl = logs.reduce((acc, log) => acc + log.pnl_points, 0);
  
  const totalGain = winningTrades.reduce((acc, log) => acc + log.pnl_percent, 0);
  const totalLoss = losingTrades.reduce((acc, log) => acc + Math.abs(log.pnl_percent), 0);

  const avgGain = winningTrades.length > 0 ? totalGain / winningTrades.length : 0;
  const avgLoss = losingTrades.length > 0 ? totalLoss / losingTrades.length : 0;
  
  const payoffRatio = avgLoss > 0 ? avgGain / avgLoss : 0;

  const pnlOverTime = logs
    .slice()
    .sort((a,b) => new Date(a.exit_timestamp).getTime() - new Date(b.exit_timestamp).getTime())
    .reduce((acc, log, index) => {
      const lastPnl = acc.length > 0 ? acc[acc.length - 1].cumulativePnl : 0;
      acc.push({
        name: `Trade ${index + 1}`,
        pnl: log.pnl_points,
        cumulativePnl: lastPnl + log.pnl_points,
      });
      return acc;
    }, [] as { name: string; pnl: number; cumulativePnl: number }[]);

  return { winRate, totalPnl, avgGain, avgLoss, pnlOverTime, totalTrades, winningTrades: winningTrades.length, losingTrades: losingTrades.length, payoffRatio };
};

export function PerformanceDashboard() {
  const [tradeLogs, setTradeLogs] = useState<TradeLog[]>([]);

  const refreshData = () => {
    const storedLogs = localStorage.getItem('tradeLog');
    if (storedLogs) {
      setTradeLogs(JSON.parse(storedLogs));
    }
  };

  useEffect(() => {
    refreshData();
    
    const interval = setInterval(refreshData, 5000); // Poll for new trades
    
    return () => clearInterval(interval);
  }, []);

  const { winRate, totalPnl, avgGain, avgLoss, pnlOverTime, totalTrades, winningTrades, losingTrades, payoffRatio } =
    calculateMetrics(tradeLogs);

  return (
    <div className="space-y-6">
      <header className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            Performance Analytics
          </h1>
          <p className="text-muted-foreground">
            Reviewing the historical performance of trade signals.
          </p>
        </div>
        <Button onClick={refreshData} variant="outline" size="sm">
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
        </Button>
      </header>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Win/Loss Rate</CardTitle>
            <Percent className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{winRate.toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">
              {winningTrades} wins / {losingTrades} losses from {totalTrades} trades
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Average % Gain
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              +{avgGain.toFixed(2)}%
            </div>
            <p className="text-xs text-muted-foreground">On winning trades.</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Average % Loss
            </CardTitle>
            <TrendingDown className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              -{avgLoss.toFixed(2)}%
            </div>
            <p className="text-xs text-muted-foreground">On losing trades.</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Payoff Ratio
            </CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div
              className={`text-2xl font-bold ${
                payoffRatio >= 1 ? "text-green-600" : "text-red-600"
              }`}
            >
              {payoffRatio.toFixed(2)}
            </div>
            <p className="text-xs text-muted-foreground">
              Avg Gain / Avg Loss
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart className="text-muted-foreground" />
            P&L Over Time
          </CardTitle>
          <CardDescription>
            Cumulative profit and loss from signals (in points).
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ChartContainer
            config={{
              cumulativePnl: {
                label: 'Cumulative P&L',
                color: 'hsl(var(--primary))',
              },
            }}
            className="h-[300px] w-full"
            >
            <LineChart data={pnlOverTime}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis
                stroke="#888888"
                fontSize={12}
                tickFormatter={(value) => `${value}`}
                tickLine={false}
                axisLine={false}
                domain={['auto', 'auto']}
              />
              <Tooltip
                content={<ChartTooltipContent indicator="dot" />}
                cursor={{ fill: "hsl(var(--accent) / 0.1)" }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="cumulativePnl"
                name="Cumulative P&L (Points)"
                stroke="var(--color-cumulativePnl)"
                strokeWidth={2}
                dot={{ r: 4, fill: "var(--color-cumulativePnl)" }}
                connectNulls
              />
            </LineChart>
          </ChartContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Trade Performance Log</CardTitle>
          <CardDescription>
            A detailed record of all triggered signals and their outcomes.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-hidden rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Ticker</TableHead>
                  <TableHead>Outcome</TableHead>
                  <TableHead>Entry Price</TableHead>
                  <TableHead>Exit Price</TableHead>
                   <TableHead>Exit Time</TableHead>
                  <TableHead className="text-right">P&L (%)</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {tradeLogs.length > 0 ? tradeLogs.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell className="font-medium">{log.ticker}</TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          log.outcome === "Profit Target"
                            ? "default"
                            : log.outcome === "Stop Loss"
                            ? "destructive"
                            : "secondary"
                        }
                        className={
                          log.outcome === "Profit Target"
                            ? "bg-green-600/20 text-green-800 border-green-600/30 hover:bg-green-600/30"
                            : ""
                        }
                      >
                        {log.outcome}
                      </Badge>
                    </TableCell>
                    <TableCell>{log.entry_price.toFixed(2)}</TableCell>
                    <TableCell>{log.exit_price.toFixed(2)}</TableCell>
                    <TableCell>
                      {new Date(log.exit_timestamp).toLocaleString()}
                    </TableCell>
                    <TableCell
                      className={`text-right font-medium ${
                        log.pnl_percent >= 0
                          ? "text-green-600"
                          : "text-red-600"
                      }`}
                    >
                      {log.pnl_percent > 0 ? '+' : ''}{log.pnl_percent.toFixed(2)}%
                    </TableCell>
                  </TableRow>
                )) : (
                  <TableRow>
                    <TableCell colSpan={6} className="h-24 text-center">
                      No completed trades yet.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
