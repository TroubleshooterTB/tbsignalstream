"use client";

import React from "react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Badge } from "@/components/ui/badge";
import { HelpCircle } from "lucide-react";

interface PatternTooltipProps {
  pattern: string;
  children?: React.ReactNode;
}

const PATTERN_EXPLANATIONS: Record<string, {
  title: string;
  description: string;
  indication: string;
  emoji: string;
}> = {
  "Bullish Engulfing": {
    title: "Bullish Engulfing Pattern",
    description: "A large green candle completely engulfs the previous red candle, with the body of the green candle covering the entire body of the red candle.",
    indication: "Strong reversal signal. Indicates buyers have taken control after a downtrend. High probability of upward movement.",
    emoji: "🟢",
  },
  "Bearish Engulfing": {
    title: "Bearish Engulfing Pattern",
    description: "A large red candle completely engulfs the previous green candle, covering its entire body.",
    indication: "Strong reversal signal. Indicates sellers have taken control after an uptrend. Suggests downward movement ahead.",
    emoji: "🔴",
  },
  "Morning Star": {
    title: "Morning Star Pattern",
    description: "A three-candle pattern: red candle, small-bodied candle (doji/spinning top), then large green candle.",
    indication: "Bullish reversal pattern. Signals the end of a downtrend. Bot looks for this at support levels.",
    emoji: "⭐",
  },
  "Evening Star": {
    title: "Evening Star Pattern",
    description: "A three-candle pattern: green candle, small-bodied candle, then large red candle.",
    indication: "Bearish reversal pattern. Signals the end of an uptrend. Suggests profit-taking time.",
    emoji: "🌙",
  },
  "Hammer": {
    title: "Hammer Pattern",
    description: "Small body at the top with a long lower wick (at least 2x the body). Appears after a downtrend.",
    indication: "Bullish reversal. Shows buyers rejected lower prices. Bot combines with RSI oversold for confirmation.",
    emoji: "🔨",
  },
  "Shooting Star": {
    title: "Shooting Star Pattern",
    description: "Small body at the bottom with a long upper wick. Appears after an uptrend.",
    indication: "Bearish reversal. Shows sellers rejected higher prices. Suggests resistance level.",
    emoji: "💫",
  },
  "Doji": {
    title: "Doji Pattern",
    description: "Open and close prices are nearly identical, creating a cross or plus sign shape.",
    indication: "Indecision in the market. Can signal reversal when combined with other indicators. Bot uses for context.",
    emoji: "➕",
  },
  "Breakout": {
    title: "Breakout Signal",
    description: "Price breaks above a significant resistance level with strong volume.",
    indication: "Bullish momentum. Bot looks for clean breakouts above consolidation zones with volume confirmation.",
    emoji: "🚀",
  },
  "Momentum": {
    title: "Momentum Signal",
    description: "Strong directional movement confirmed by multiple indicators (MACD, RSI, volume).",
    indication: "Trend continuation. Bot detects when all indicators align in the same direction.",
    emoji: "📈",
  },
  "Reversal": {
    title: "Reversal Signal",
    description: "Multiple indicators suggest trend change: RSI divergence, MACD crossover, pattern formation.",
    indication: "Trend reversal expected. Bot combines technical analysis with candlestick patterns.",
    emoji: "🔄",
  },
  "Profit Target": {
    title: "Profit Target Hit",
    description: "Price reached the predetermined profit target calculated at entry.",
    indication: "Exit signal. Bot's position management system triggered automatic exit to lock in gains.",
    emoji: "🎯",
  },
  "Stop Loss": {
    title: "Stop Loss Triggered",
    description: "Price fell below the trailing stop loss level.",
    indication: "Risk management exit. Bot protects capital by cutting losses early. Trailing stop adjusts as price moves up.",
    emoji: "🛡️",
  },
  "Technical Exit": {
    title: "Technical Exit Signal",
    description: "Technical indicators suggest weakening momentum or trend exhaustion.",
    indication: "Bot detected adverse technical conditions: RSI overbought, MACD bearish crossover, or pattern breakdown.",
    emoji: "⚠️",
  },
  "EOD": {
    title: "End of Day Exit",
    description: "Market closing time (3:20 PM). Bot squares off all intraday positions.",
    indication: "Mandatory exit. Bot closes all positions 10 minutes before market close to avoid overnight risk.",
    emoji: "🌅",
  },
};

export function PatternTooltip({ pattern, children }: PatternTooltipProps) {
  const patternInfo = PATTERN_EXPLANATIONS[pattern];

  if (!patternInfo) {
    return children || <Badge variant="outline">{pattern}</Badge>;
  }

  return (
    <TooltipProvider delayDuration={200}>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="cursor-help inline-flex items-center gap-1">
            {children || <Badge variant="outline">{pattern}</Badge>}
            <HelpCircle className="h-3 w-3 text-muted-foreground" />
          </div>
        </TooltipTrigger>
        <TooltipContent side="bottom" className="max-w-sm p-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-lg">{patternInfo.emoji}</span>
              <h4 className="font-bold text-sm">{patternInfo.title}</h4>
            </div>
            <div className="space-y-1 text-xs">
              <div>
                <span className="font-semibold">What it is: </span>
                <span className="text-muted-foreground">{patternInfo.description}</span>
              </div>
              <div>
                <span className="font-semibold">What it means: </span>
                <span className="text-muted-foreground">{patternInfo.indication}</span>
              </div>
            </div>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

// Helper component for signal type badges with tooltips
export function PatternBadge({ pattern, variant }: { pattern: string; variant?: "default" | "secondary" | "destructive" | "outline" }) {
  return (
    <PatternTooltip pattern={pattern}>
      <Badge variant={variant || "outline"}>{pattern}</Badge>
    </PatternTooltip>
  );
}
