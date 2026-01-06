"use client";

import { useEffect, useState } from 'react';
import { AlertCircle, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import { env } from '@/config/env';
import { TIMEOUTS } from '@/config/constants';
import { fetchWithTimeout } from '@/lib/fetch-with-timeout';

interface SystemError {
  type: string;
  severity: 'CRITICAL' | 'WARNING' | 'INFO';
  message: string;
  impact?: string;
  resolution?: string;
}

interface SystemStatus {
  timestamp: string;
  backend_operational: boolean;
  firestore_connected: boolean;
  errors: SystemError[];
  warnings: SystemError[];
}

export default function SystemHealthMonitor() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const checkSystemHealth = async () => {
      try {
        const response = await fetchWithTimeout(
          `${env.backendUrl}/health`,
          {},
          TIMEOUTS.HEALTH_CHECK
        );
        const data = await response.json();
        setStatus(data);
        setIsLoading(false);
      } catch (error) {
        console.error('Failed to check system health:', error);
        // If we can't reach backend, show critical error
        setStatus({
          timestamp: new Date().toISOString(),
          backend_operational: false,
          firestore_connected: false,
          errors: [{
            type: 'BACKEND_UNREACHABLE',
            severity: 'CRITICAL',
            message: 'Cannot connect to trading backend',
            impact: 'All bot operations unavailable',
            resolution: 'Check if backend service is running or refresh the page'
          }],
          warnings: []
        });
        setIsLoading(false);
      }
    };

    // Check immediately
    checkSystemHealth();

    // Check every 30 seconds
    const interval = setInterval(checkSystemHealth, TIMEOUTS.HEALTH_CHECK);

    return () => clearInterval(interval);
  }, []);

  if (isLoading) {
    return null; // Don't show anything while loading
  }

  // If everything is healthy, show minimal indicator
  if (status?.errors?.length === 0 && status?.warnings?.length === 0 && status?.backend_operational) {
    return (
      <div className="fixed top-4 right-4 z-50 bg-green-50 border border-green-200 rounded-lg px-3 py-2 flex items-center gap-2 shadow-sm">
        <CheckCircle className="h-4 w-4 text-green-600" />
        <span className="text-sm text-green-700 font-medium">System Healthy</span>
      </div>
    );
  }

  // Critical errors - show prominent banner
  const hasCriticalErrors = status?.errors?.some(e => e.severity === 'CRITICAL');

  return (
    <div className="fixed top-0 left-0 right-0 z-50">
      {/* Critical Error Banner */}
      {hasCriticalErrors && status && (
        <div className="bg-red-600 text-white px-4 py-3 shadow-lg">
          <div className="max-w-7xl mx-auto flex items-start justify-between gap-4">
            <div className="flex items-start gap-3 flex-1">
              <XCircle className="h-6 w-6 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h3 className="font-bold text-lg mb-1">System Error - Bot Operations Unavailable</h3>
                {status.errors.map((error, idx) => (
                  <div key={idx} className="mb-2">
                    <p className="font-medium">{error.message}</p>
                    {error.impact && (
                      <p className="text-sm text-red-100 mt-1">Impact: {error.impact}</p>
                    )}
                    {showDetails && error.resolution && (
                      <p className="text-sm text-red-100 mt-1 bg-red-700 rounded px-2 py-1">
                        💡 Solution: {error.resolution}
                      </p>
                    )}
                  </div>
                ))}
                <button
                  onClick={() => setShowDetails(!showDetails)}
                  className="text-sm underline hover:no-underline mt-2"
                >
                  {showDetails ? 'Hide Details' : 'Show Resolution Steps'}
                </button>
              </div>
            </div>
            <button
              onClick={() => window.location.reload()}
              className="bg-white text-red-600 px-4 py-2 rounded font-medium hover:bg-red-50 transition-colors flex-shrink-0"
            >
              Refresh Page
            </button>
          </div>
        </div>
      )}

      {/* Warnings Banner */}
      {!hasCriticalErrors && status && status.warnings && status.warnings.length > 0 && (
        <div className="bg-yellow-50 border-b border-yellow-200 px-4 py-3">
          <div className="max-w-7xl mx-auto flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-yellow-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h4 className="font-semibold text-yellow-800 mb-1">System Warnings</h4>
              {status.warnings.map((warning, idx) => (
                <p key={idx} className="text-sm text-yellow-700">
                  {warning.message}
                  {warning.impact && ` - ${warning.impact}`}
                </p>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Backend Unreachable */}
      {!status?.backend_operational && !hasCriticalErrors && (
        <div className="bg-orange-600 text-white px-4 py-3 shadow-lg">
          <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <AlertCircle className="h-6 w-6" />
              <div>
                <h3 className="font-bold">Backend Connection Lost</h3>
                <p className="text-sm text-orange-100">Unable to communicate with trading backend. Retrying...</p>
              </div>
            </div>
            <button
              onClick={() => window.location.reload()}
              className="bg-white text-orange-600 px-4 py-2 rounded font-medium hover:bg-orange-50"
            >
              Refresh
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
