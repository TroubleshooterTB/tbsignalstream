"use client";

import React, { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  Activity, 
  CheckCircle2, 
  XCircle, 
  Search, 
  TrendingUp, 
  Shield, 
  Target,
  Clock,
  BarChart3
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/context/auth-context";
import { db } from "@/lib/firebase";
import { collection, query, where, orderBy, limit, Timestamp } from "firebase/firestore";
import { useFirestoreListener } from "@/hooks/use-firestore-listener";
import { COLLECTIONS, UI } from "@/config/constants";

type ActivityType = 
  | "scan_cycle_start"
  | "symbol_scanning"
  | "symbol_skipped"
  | "no_pattern"
  | "pattern_detected" 
  | "screening_started"
  | "screening_passed" 
  | "screening_failed"
  | "validation_started"
  | "validation_passed"
  | "validation_failed"
  | "signal_generated"
  | "signal_rejected";

type BotActivity = {
  id: string;
  timestamp: Date;
  type: ActivityType;
  symbol: string;
  pattern?: string;
  confidence?: number;
  rr_ratio?: number;
  reason?: string;
  level?: string;
  details?: Record<string, any>;
};

const activityConfig: Record<ActivityType, { 
  icon: React.ReactNode; 
  color: string; 
  label: string;
  bgColor: string;
}> = {
  scan_cycle_start: {
    icon: <BarChart3 className="h-4 w-4" />,
    color: "text-slate-600",
    bgColor: "bg-slate-50",
    label: "Scan Cycle Started"
  },
  symbol_scanning: {
    icon: <Search className="h-4 w-4" />,
    color: "text-gray-500",
    bgColor: "bg-gray-50",
    label: "Scanning"
  },
  symbol_skipped: {
    icon: <Clock className="h-4 w-4" />,
    color: "text-gray-400",
    bgColor: "bg-gray-50",
    label: "Skipped"
  },
  no_pattern: {
    icon: <TrendingUp className="h-4 w-4" />,
    color: "text-gray-400",
    bgColor: "bg-gray-50",
    label: "No Pattern"
  },
  pattern_detected: {
    icon: <Search className="h-4 w-4" />,
    color: "text-blue-600",
    bgColor: "bg-blue-50",
    label: "Pattern Detected"
  },
  screening_started: {
    icon: <Shield className="h-4 w-4" />,
    color: "text-purple-600",
    bgColor: "bg-purple-50",
    label: "Screening Started"
  },
  screening_passed: {
    icon: <CheckCircle2 className="h-4 w-4" />,
    color: "text-green-600",
    bgColor: "bg-green-50",
    label: "Screening Passed"
  },
  screening_failed: {
    icon: <XCircle className="h-4 w-4" />,
    color: "text-orange-600",
    bgColor: "bg-orange-50",
    label: "Screening Failed"
  },
  validation_started: {
    icon: <BarChart3 className="h-4 w-4" />,
    color: "text-indigo-600",
    bgColor: "bg-indigo-50",
    label: "Validation Started"
  },
  validation_passed: {
    icon: <CheckCircle2 className="h-4 w-4" />,
    color: "text-green-600",
    bgColor: "bg-green-50",
    label: "Validation Passed"
  },
  validation_failed: {
    icon: <XCircle className="h-4 w-4" />,
    color: "text-red-600",
    bgColor: "bg-red-50",
    label: "Validation Failed"
  },
  signal_generated: {
    icon: <Target className="h-4 w-4" />,
    color: "text-emerald-600",
    bgColor: "bg-emerald-50",
    label: "Signal Generated"
  },
  signal_rejected: {
    icon: <XCircle className="h-4 w-4" />,
    color: "text-gray-600",
    bgColor: "bg-gray-50",
    label: "Signal Rejected"
  }
};

export function BotActivityFeed() {
  const [activities, setActivities] = useState<BotActivity[]>([]);
  const [isLive, setIsLive] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);
  const [stats, setStats] = useState({
    patterns_detected: 0,
    screenings_passed: 0,
    screenings_failed: 0,
    signals_generated: 0
  });
  
  const { firebaseUser } = useAuth();

  // Auto-scroll to bottom when new activity arrives (if live mode is on)
  useEffect(() => {
    if (isLive && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [activities, isLive]);

  // Real-time listener for bot activity using custom hook
  useFirestoreListener<BotActivity>(
    COLLECTIONS.BOT_ACTIVITY,
    [
      where('user_id', '==', firebaseUser?.uid || ''),
      orderBy('timestamp', 'desc'),
      limit(UI.MAX_ACTIVITY_ITEMS)
    ],
    (fetchedActivities) => {
      console.log(`[BotActivity] Received ${fetchedActivities.length} activities`);
      
      // Process new activities
      fetchedActivities.forEach(activity => {
        // Convert Firestore timestamp to Date
        const timestamp = (activity.timestamp as any) instanceof Timestamp 
          ? (activity.timestamp as any).toDate() 
          : new Date();
        
        const processedActivity: BotActivity = {
          ...activity,
          timestamp,
        };
        
        setActivities(prev => {
          // Prevent duplicates
          if (prev.some(a => a.id === processedActivity.id)) return prev;
          return [processedActivity, ...prev].slice(0, UI.MAX_ACTIVITY_ITEMS);
        });
        
        // Update stats
        setStats(prev => {
          const newStats = { ...prev };
          if (activity.type === 'pattern_detected') newStats.patterns_detected++;
          if (activity.type === 'screening_passed') newStats.screenings_passed++;
          if (activity.type === 'screening_failed') newStats.screenings_failed++;
          if (activity.type === 'signal_generated') newStats.signals_generated++;
          return newStats;
        });
      });
    },
    { 
      enabled: !!firebaseUser,
      errorMessage: '[BotActivity]'
    }
  );

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-IN', { 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit',
      hour12: false 
    });
  };

  return (
    <Card className="h-[600px] flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-blue-600" />
            <CardTitle className="text-lg">Bot Activity Feed</CardTitle>
            <Badge variant={isLive ? "default" : "secondary"} className="ml-2">
              {isLive ? "LIVE" : "PAUSED"}
            </Badge>
          </div>
          <button
            onClick={() => setIsLive(!isLive)}
            className="text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            {isLive ? "Pause" : "Resume"}
          </button>
        </div>
        
        {/* Stats Summary */}
        <div className="grid grid-cols-4 gap-2 mt-4">
          <div className="bg-blue-50 rounded-lg p-2 text-center">
            <div className="text-xs text-blue-600 font-medium">Patterns</div>
            <div className="text-lg font-bold text-blue-700">{stats.patterns_detected}</div>
          </div>
          <div className="bg-green-50 rounded-lg p-2 text-center">
            <div className="text-xs text-green-600 font-medium">Passed</div>
            <div className="text-lg font-bold text-green-700">{stats.screenings_passed}</div>
          </div>
          <div className="bg-orange-50 rounded-lg p-2 text-center">
            <div className="text-xs text-orange-600 font-medium">Failed</div>
            <div className="text-lg font-bold text-orange-700">{stats.screenings_failed}</div>
          </div>
          <div className="bg-emerald-50 rounded-lg p-2 text-center">
            <div className="text-xs text-emerald-600 font-medium">Signals</div>
            <div className="text-lg font-bold text-emerald-700">{stats.signals_generated}</div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex-1 overflow-hidden p-0">
        <ScrollArea className="h-full px-4 pb-4" ref={scrollRef}>
          {activities.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
              <Activity className="h-12 w-12 mb-2 opacity-20" />
              <p className="text-sm">Waiting for bot activity...</p>
              <p className="text-xs mt-1">Pattern scanning runs every 1 second</p>
            </div>
          ) : (
            <div className="space-y-2">
              {activities.map((activity) => {
                const config = activityConfig[activity.type];
                
                return (
                  <div
                    key={activity.id}
                    className={cn(
                      "rounded-lg p-3 border transition-all hover:shadow-sm",
                      config.bgColor
                    )}
                  >
                    <div className="flex items-start gap-3">
                      <div className={cn("mt-0.5", config.color)}>
                        {config.icon}
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2 mb-1">
                          <div className="flex items-center gap-2">
                            <Badge variant="outline" className="font-mono text-xs">
                              {activity.symbol}
                            </Badge>
                            {activity.pattern && (
                              <span className="text-xs font-medium text-gray-700">
                                {activity.pattern}
                              </span>
                            )}
                          </div>
                          <span className="text-xs text-muted-foreground flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {formatTime(activity.timestamp)}
                          </span>
                        </div>
                        
                        <div className={cn("text-sm font-medium mb-1", config.color)}>
                          {config.label}
                        </div>
                        
                        {/* Confidence and R:R */}
                        {(activity.confidence || activity.rr_ratio) && (
                          <div className="flex items-center gap-3 text-xs text-gray-600 mb-1">
                            {activity.confidence && (
                              <span className="flex items-center gap-1">
                                <TrendingUp className="h-3 w-3" />
                                Confidence: {activity.confidence.toFixed(1)}%
                              </span>
                            )}
                            {activity.rr_ratio && (
                              <span>
                                R:R = 1:{activity.rr_ratio.toFixed(2)}
                              </span>
                            )}
                          </div>
                        )}
                        
                        {/* Reason/Details */}
                        {activity.reason && (
                          <div className="text-xs text-gray-600 mt-1 italic">
                            {activity.reason}
                          </div>
                        )}
                        
                        {/* Level info for screening/validation */}
                        {activity.level && (
                          <div className="text-xs text-gray-500 mt-1">
                            Level: {activity.level}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
