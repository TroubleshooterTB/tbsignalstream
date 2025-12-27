// Forcing a rebuild to clear any potential caching issues.
// Version: 2.3 - System Health Monitoring
"use client";

import dynamic from "next/dynamic";
import { Skeleton } from "@/components/ui/skeleton";
import { useEffect } from "react";
import SystemHealthMonitor from "@/components/system-health-monitor";

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
    console.log('[App] Page mounted - v2.3 - HEALTH MONITORING');
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
      <LiveAlertsDashboard />
    </>
  );
}
