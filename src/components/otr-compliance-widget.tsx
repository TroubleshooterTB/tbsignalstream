"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { AlertCircle, CheckCircle, TrendingUp } from "lucide-react";
import { useAuth } from "@/context/auth-context";
import { db } from "@/lib/firebase";
import { doc, onSnapshot } from "firebase/firestore";

interface OTRData {
  otr_ratio: number;
  otr_threshold: number;
  orders_placed_today: number;
  orders_executed_today: number;
  otr_compliant: boolean;
  last_updated?: Date;
}

export function OTRComplianceWidget() {
  const { firebaseUser } = useAuth();
  const [otrData, setOtrData] = useState<OTRData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!firebaseUser?.uid) {
      setIsLoading(false);
      return;
    }

    const botStatusRef = doc(db, "bot_status", firebaseUser.uid);
    
    const unsubscribe = onSnapshot(
      botStatusRef,
      (snapshot) => {
        if (snapshot.exists()) {
          const data = snapshot.data();
          setOtrData({
            otr_ratio: data.otr_ratio || 0,
            otr_threshold: data.otr_threshold || 20.0,
            orders_placed_today: data.orders_placed_today || 0,
            orders_executed_today: data.orders_executed_today || 0,
            otr_compliant: data.otr_compliant !== false, // Default to compliant
            last_updated: data.last_updated?.toDate()
          });
        }
        setIsLoading(false);
      },
      (error) => {
        console.error("Error fetching OTR data:", error);
        setIsLoading(false);
      }
    );

    return () => unsubscribe();
  }, [firebaseUser]);

  if (!firebaseUser) {
    return null;
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">OTR Compliance (SEBI)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-muted-foreground">Loading...</div>
        </CardContent>
      </Card>
    );
  }

  if (!otrData) {
    return null;
  }

  const percentOfLimit = (otrData.otr_ratio / otrData.otr_threshold) * 100;
  const isHealthy = percentOfLimit < 60;
  const isWarning = percentOfLimit >= 60 && percentOfLimit < 80;
  const isCritical = percentOfLimit >= 80;

  return (
    <Card className="border-l-4" style={{
      borderLeftColor: isCritical ? '#ef4444' : isWarning ? '#f59e0b' : '#10b981'
    }}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">📊 OTR Compliance (SEBI)</CardTitle>
          {otrData.otr_compliant ? (
            <Badge variant="default" className="bg-green-500">
              <CheckCircle className="h-3 w-3 mr-1" />
              Compliant
            </Badge>
          ) : (
            <Badge variant="destructive">
              <AlertCircle className="h-3 w-3 mr-1" />
              Throttled
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="space-y-1">
          <div className="flex items-baseline justify-between">
            <span className="text-2xl font-bold">
              {otrData.otr_ratio.toFixed(1)}:1
            </span>
            <span className="text-sm text-muted-foreground">
              Limit: {otrData.otr_threshold}:1
            </span>
          </div>
          <Progress 
            value={Math.min(percentOfLimit, 100)} 
            className="h-2"
            style={{
              backgroundColor: isCritical ? '#fecaca' : isWarning ? '#fed7aa' : '#d1fae5'
            }}
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>
              {isHealthy && "Healthy"}
              {isWarning && "Approaching Limit"}
              {isCritical && "Critical"}
            </span>
            <span>{percentOfLimit.toFixed(0)}% of limit</span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2 pt-2 border-t">
          <div>
            <div className="text-xs text-muted-foreground">Orders Placed</div>
            <div className="text-lg font-semibold">{otrData.orders_placed_today}</div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground">Orders Executed</div>
            <div className="text-lg font-semibold">{otrData.orders_executed_today}</div>
          </div>
        </div>

        {otrData.orders_placed_today > 0 && (
          <div className="pt-2 border-t">
            <div className="flex items-center text-xs text-muted-foreground">
              <TrendingUp className="h-3 w-3 mr-1" />
              Execution Rate: {((otrData.orders_executed_today / otrData.orders_placed_today) * 100).toFixed(0)}%
            </div>
          </div>
        )}

        {!otrData.otr_compliant && (
          <div className="pt-2 border-t">
            <div className="text-xs text-destructive font-medium">
              ⚠️ Bot is throttled due to high OTR ratio. New orders will be blocked until ratio improves.
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
