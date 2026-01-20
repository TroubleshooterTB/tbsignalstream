// Forcing a rebuild to clear any potential caching issues.
// Version: 2.4 - Frontend Compatibility + OTR + Regime Indicator
"use client";

import dynamic from "next/dynamic";
import { Skeleton } from "@/components/ui/skeleton";
import { useEffect } from "react";
import SystemHealthMonitor from "@/components/system-health-monitor";
import { OTRComplianceWidget } from "@/components/otr-compliance-widget";
import { RegimeIndicator } from "@/components/regime-indicator";

// Dynamically import the dashboard to avoid SSR issues with Firebase
const LiveAlertsDashboard = dynamic(
  () => import("@/components/live-alerts-dashboard").then(mod => ({ default: mod.LiveAlertsDashboard })),
  {
    ssr: false,
    loading: () => (
      <div className="space-y-6 p-8">
        <div className="space-y-2">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-4 w-96" />
        </div>
        <Skeleton className="h-96 w-full" />
      </div>
    ),
  }
);

export default function Home() {
  // Force clear any stale data on mount
  useEffect(() => {
    console.log('[App] Page mounted - v2.4 - FRONTEND COMPATIBILITY FIX');
    // Clear any potential browser cache
    if (typeof window !== 'undefined') {
      localStorage.removeItem('cachedSignals');
      localStorage.removeItem('tradeLog');
      sessionStorage.removeItem('cachedSignals');
      console.log('[App] Cleared all cached data');
    }
  }, []);
  
  return (
    <>
      <SystemHealthMonitor />
      <div className="p-4 space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Trading Dashboard</h1>
          <RegimeIndicator />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-2">
            <LiveAlertsDashboard />
          </div>
          <div>
            <OTRComplianceWidget />
          </div>
        </div>
      </div>
    </>
  );
}
