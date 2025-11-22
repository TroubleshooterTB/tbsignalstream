// Forcing a rebuild to clear any potential caching issues.
"use client";

import dynamic from "next/dynamic";
import { Skeleton } from "@/components/ui/skeleton";

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
  return <LiveAlertsDashboard />;
}
