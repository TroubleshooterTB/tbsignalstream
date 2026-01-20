"use client";

import React, { useState, useEffect } from "react";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, Activity } from "lucide-react";
import { useAuth } from "@/context/auth-context";
import { db } from "@/lib/firebase";
import { doc, onSnapshot } from "firebase/firestore";

interface RegimeData {
  current_regime: "trending" | "sideways";
  adx_value: number;
  regime_since?: Date;
  active_strategy: string;
  strategy_reason?: string;
}

export function RegimeIndicator() {
  const { firebaseUser } = useAuth();
  const [regimeData, setRegimeData] = useState<RegimeData | null>(null);

  useEffect(() => {
    if (!firebaseUser?.uid) {
      return;
    }

    const botStatusRef = doc(db, "bot_status", firebaseUser.uid);
    
    const unsubscribe = onSnapshot(
      botStatusRef,
      (snapshot) => {
        if (snapshot.exists()) {
          const data = snapshot.data();
          setRegimeData({
            current_regime: data.current_regime || "trending",
            adx_value: data.adx_value || 25,
            regime_since: data.regime_since?.toDate(),
            active_strategy: data.active_strategy || "pattern_detection",
            strategy_reason: data.strategy_reason
          });
        }
      },
      (error) => {
        console.error("Error fetching regime data:", error);
      }
    );

    return () => unsubscribe();
  }, [firebaseUser]);

  if (!firebaseUser || !regimeData) {
    return null;
  }

  const isTrending = regimeData.current_regime === "trending";
  const Icon = isTrending ? TrendingUp : Activity;

  return (
    <div className="flex items-center gap-2">
      <Badge 
        variant={isTrending ? "default" : "secondary"}
        className="flex items-center gap-1 px-3 py-1"
      >
        <Icon className="h-3 w-3" />
        {isTrending ? "🎯 TRENDING" : "🔄 SIDEWAYS"}
      </Badge>
      <div className="text-xs text-muted-foreground">
        ADX: {regimeData.adx_value.toFixed(1)}
      </div>
      {regimeData.active_strategy && (
        <div className="text-xs text-muted-foreground">
          {regimeData.active_strategy === "mean_reversion" ? "Mean Reversion" : "Trend Following"}
        </div>
      )}
    </div>
  );
}
