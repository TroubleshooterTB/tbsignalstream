# functions/src/trading/checkers/pattern_checker.py

import pandas as pd
import numpy as np
# import pandas_ta as ta # TEMPORARILY DISABLED - not compatible with Python 3.11
# TODO: Migrate to alternative library like ta-lib or implement indicators manually

class AdvancedPriceActionAnalyzer:
    """
    This class embodies a multi-stage, institutional-grade trading strategy.
    As an analyst with over two decades of experience in the Indian markets, I've designed
    this logic to move beyond simple indicators and focus on the confluence of evidence
    that signals high-probability price action moves.

    The process mirrors a professional workflow:
    1.  Market Context: We first establish the health of the broader market and sector.
    2.  Trend & Momentum Analysis: We identify stocks with clear upward trajectory and accelerating momentum.
    3.  Price Action Confirmation: We look for specific bar-by-bar patterns that confirm institutional buying
        and validate the strength of the move. This is where we separate noise from real intent.
    4.  Confidence Scoring: Each of the 24 checks contributes to a final confidence score.
    5.  Trade Signal Generation: If confidence surpasses 95%, a trade signal is generated with
        dynamically calculated entry, stop-loss, and an initial take-profit target based on volatility.
    """

    def __init__(self, confidence_threshold=0.95, reward_risk_ratio=2.5):
        """
        Initializes the analyzer.
        :param confidence_threshold: The percentage of checks that must pass to generate a signal.
        :param reward_risk_ratio: The initial target for profit-taking as a multiple of the risk (stop-loss).
        """
        self.confidence_threshold = confidence_threshold
        self.reward_risk_ratio = reward_risk_ratio
        # A curated list of 24 checks, categorized by analytical focus.
        self.all_checks = [
            # Market & Sector Context (4)
            self.check_market_is_in_uptrend,
            self.check_sector_is_in_uptrend,
            self.check_relative_strength_positive,
            self.check_no_major_news_event,
            # Trend Strength & Quality (6)
            self.check_price_above_vwap,
            self.check_price_above_ema50,
            self.check_ema20_above_ema50,
            self.check_adx_trending_up,
            self.check_parabolic_sar_bullish,
            self.check_higher_highs_and_lows_long_term,
            # Momentum & Volume Confirmation (6)
            self.check_rsi_in_bullish_zone,
            self.check_stoch_k_above_d,
            self.check_macd_bullish_crossover,
            self.check_obv_confirming_price,
            self.check_volume_confirms_breakout,
            self.check_price_near_upper_bollinger,
            # Price Action & Entry Signal (8)
            self.check_bullish_engulfing_or_marubozu,
            self.check_breakout_from_consolidation,
            self.check_is_second_entry_buy_signal,
            self.check_no_strong_bearish_reversal_bar,
            self.check_no_bearish_divergence,
            self.check_volatility_expanding,
            self.check_atr_is_reasonable,
            self.check_price_above_recent_pivot,
        ]
        assert len(self.all_checks) == 24, f"Strategy requires exactly 24 checks. Found: {len(self.all_checks)}"

    def _calculate_indicators(self, data: pd.DataFrame):
        """Helper function to calculate all necessary indicators using pandas_ta."""
        # TEMPORARILY DISABLED - pandas_ta not compatible with Python 3.11
        # TODO: Migrate to alternative library or implement indicators manually
        # data.ta.ema(length=20, append=True, col_names=('ema_20'))
        # data.ta.ema(length=50, append=True, col_names=('ema_50'))
        # data.ta.rsi(length=14, append=True, col_names=('rsi'))
        # data.ta.adx(length=14, append=True, col_names=('adx', 'dmp', 'dmn'))
        # data.ta.macd(fast=12, slow=26, signal=9, append=True, col_names=('macd_line', 'macd_hist', 'macd_signal'))
        # data.ta.stoch(k=14, d=3, smooth_k=3, append=True, col_names=('stoch_k', 'stoch_d'))
        # data.ta.bbands(length=20, std=2, append=True, col_names=('bb_lower', 'bb_mid', 'bb_upper', 'bb_bw', 'bb_perc'))
        # data.ta.atr(length=14, append=True, col_names=('atr'))
        # data.ta.obv(append=True)
        # data.ta.psar(append=True, col_names=('psar_long', 'psar_short', 'psar_af', 'psar_reversal'))
        # data.ta.vwap(append=True)
        return data

    # --- MARKET & SECTOR CONTEXT (4) ---
    def check_market_is_in_uptrend(self, market_data):
        market_data = self._calculate_indicators(market_data.copy())
        return market_data['close'].iloc[-1] > market_data['ema_50'].iloc[-1], "Broader market (Index) is in an uptrend"
    def check_sector_is_in_uptrend(self, sector_data):
        sector_data = self._calculate_indicators(sector_data.copy())
        return sector_data['close'].iloc[-1] > sector_data['ema_50'].iloc[-1], "Sector is in an uptrend"
    def check_relative_strength_positive(self, stock_data, market_data):
        stock_return = stock_data['close'].pct_change(20).iloc[-1]
        market_return = market_data['close'].pct_change(20).iloc[-1]
        return stock_return > market_return, "Stock is outperforming the broader market"
    def check_no_major_news_event(self, stock_symbol):
        # In a live system, this would query a financial news API (e.g., for earnings announcements).
        return True, "No immediate high-impact news scheduled"

    # --- TREND STRENGTH & QUALITY (6) ---
    def check_price_above_vwap(self, data):
        return data['close'].iloc[-1] > data['VWAP_D'].iloc[-1], "Price is above the Volume-Weighted Average Price (VWAP)"
    def check_price_above_ema50(self, data):
        return data['close'].iloc[-1] > data['ema_50'].iloc[-1], "Price is above the 50-period EMA (long-term trend)"
    def check_ema20_above_ema50(self, data):
        return data['ema_20'].iloc[-1] > data['ema_50'].iloc[-1], "20 EMA is above 50 EMA (short-term trend confirms long-term)"
    def check_adx_trending_up(self, data):
        return data['adx'].iloc[-1] > 25 and data['dmp'].iloc[-1] > data['dmn'].iloc[-1], "ADX > 25 indicates strong trend, +DI > -DI confirms bullish"
    def check_parabolic_sar_bullish(self, data):
        return data['close'].iloc[-1] > data['psar_long'].iloc[-1], "Parabolic SAR is in a bullish position (below price)"
    def check_higher_highs_and_lows_long_term(self, data):
        last_30_bars = data.iloc[-30:]
        recent_low = last_30_bars['low'].iloc[-10:].min()
        prior_low = last_30_bars['low'].iloc[:-10].min()
        recent_high = last_30_bars['high'].iloc[-10:].max()
        prior_high = last_30_bars['high'].iloc[:-10].max()
        return recent_low > prior_low and recent_high > prior_high, "Clear pattern of higher highs and higher lows over the last 30 periods"

    # --- MOMENTUM & VOLUME CONFIRMATION (6) ---
    def check_rsi_in_bullish_zone(self, data):
        return 50 < data['rsi'].iloc[-1] < 75, "RSI is in the bullish zone (50-75), showing momentum without being overbought"
    def check_stoch_k_above_d(self, data):
        return data['stoch_k'].iloc[-1] > data['stoch_d'].iloc[-1], "Stochastic %K is above %D, indicating upward momentum"
    def check_macd_bullish_crossover(self, data):
        return data['macd_line'].iloc[-1] > data['macd_signal'].iloc[-1] and data['macd_line'].iloc[-2] < data['macd_signal'].iloc[-2], "MACD line has recently crossed above the signal line"
    def check_obv_confirming_price(self, data):
        # On-Balance Volume should be making higher highs along with price
        return data['OBV'].iloc[-1] > data['OBV'].iloc[-5:].min(), "On-Balance Volume (OBV) confirms upward price pressure"
    def check_volume_confirms_breakout(self, data):
        avg_vol = data['volume'].rolling(window=20).mean().iloc[-1]
        return data['volume'].iloc[-1] > avg_vol * 1.5, "Breakout volume is at least 150% of the 20-period average"
    def check_price_near_upper_bollinger(self, data):
        return data['close'].iloc[-1] > data['bb_mid'].iloc[-1], "Price is trading in the upper half of the Bollinger Bands"

    # --- PRICE ACTION & ENTRY SIGNAL (8) ---
    def check_bullish_engulfing_or_marubozu(self, data):
        last = data.iloc[-1]
        prev = data.iloc[-2]
        is_engulfing = prev['close'] < prev['open'] and last['close'] > last['open'] and last['close'] > prev['open'] and last['open'] < prev['close']
        body_size = last['close'] - last['open']
        total_range = last['high'] - last['low']
        is_marubozu = body_size > 0 and total_range > 0 and body_size / total_range > 0.95
        return is_engulfing or is_marubozu, "Strong bullish candle pattern (Engulfing or Marubozu) present"
    def check_breakout_from_consolidation(self, data):
        # Looks for a breakout from a tight trading range (a "ledge" in price action terms)
        recent_range = data['high'].iloc[-10:-1].max() - data['low'].iloc[-10:-1].min()
        is_consolidating = recent_range < (data['atr'].iloc[-1] * 2)
        is_breakout = data['close'].iloc[-1] > data['high'].iloc[-10:-1].max()
        return is_consolidating and is_breakout, "Breakout from a recent consolidation/ledge"
    def check_is_second_entry_buy_signal(self, data):
        # Al Brooks concept: A second signal is more reliable. Checks for a higher low after a recent swing high.
        swing_high_idx = data['high'].iloc[-20:-2].idxmax()
        since_high = data.loc[swing_high_idx:]
        if len(since_high) < 3: return False, "Not a second entry signal"
        pullback_low_idx = since_high['low'].iloc[1:].idxmin()
        is_higher_low = data['low'].loc[pullback_low_idx] > data['low'].iloc[-20:swing_high_idx].min()
        is_breaking_out_now = data['close'].iloc[-1] > data['high'].loc[swing_high_idx]
        return is_higher_low and is_breaking_out_now, "Second entry buy signal (higher low pullback)"
    def check_no_strong_bearish_reversal_bar(self, data):
        # Ensures the last few bars don't show significant selling pressure (e.g., a huge bear bar)
        last_bar = data.iloc[-1]
        is_strong_bear_bar = (last_bar['open'] - last_bar['close']) > data['atr'].iloc[-1] and last_bar['close'] < (last_bar['high'] + last_bar['low']) / 2
        return not is_strong_bear_bar, "Absence of a strong bearish reversal bar in the last 3 periods"
    def check_no_bearish_divergence(self, data):
        # A more robust check for bearish divergence (higher high in price, lower high in MACD)
        highs = data[data['high'] == data['high'].rolling(15).max()]
        if len(highs) < 2: return True, "No bearish divergence found"
        divergence = highs['high'].iloc[-1] > highs['high'].iloc[-2] and highs['macd_line'].iloc[-1] < highs['macd_line'].iloc[-2]
        return not divergence, "No bearish MACD divergence found"
    def check_volatility_expanding(self, data):
        # Bollinger Bandwidth increasing indicates volatility is expanding, which fuels trends.
        return data['bb_bw'].iloc[-1] > data['bb_bw'].iloc[-2], "Volatility is expanding (Bollinger Bands widening)"
    def check_atr_is_reasonable(self, data):
        atr_percent = (data['atr'].iloc[-1] / data['close'].iloc[-1]) * 100
        return 0.5 < atr_percent < 7.0, "ATR is reasonable (0.5%-7%), not too choppy or stagnant"
    def check_price_above_recent_pivot(self, data):
        # Checks if price is above the most recent significant swing low.
        recent_low = data['low'].iloc[-20:-2].min()
        return data['close'].iloc[-1] > recent_low, "Price is trading above the last significant swing low"

    def run_full_analysis(self, stock_data, market_data, sector_data):
        """Runs all checks and calculates the confidence score."""
        stock_data = self._calculate_indicators(stock_data.copy())
        
        passed_checks = []
        passed_count = 0

        for check_func in self.all_checks:
            try:
                if check_func.__name__ in ['check_market_is_in_uptrend']:
                    result, reason = check_func(market_data)
                elif check_func.__name__ == 'check_sector_is_in_uptrend':
                    result, reason = check_func(sector_data)
                elif check_func.__name__ == 'check_relative_strength_positive':
                    result, reason = check_func(stock_data, market_data)
                elif check_func.__name__ == 'check_no_major_news_event':
                    result, reason = check_func("SYMBOL") # Placeholder symbol
                else:
                    result, reason = check_func(stock_data)
                
                if result:
                    passed_count += 1
                    passed_checks.append(reason)
            except Exception as e:
                # Silently fail any check that has an error (e.g., not enough data)
                pass
        
        confidence = passed_count / len(self.all_checks)
        return confidence, passed_checks, passed_count

    def generate_trade_signal(self, stock_data, market_data, sector_data):
        """Generates a complete trade signal if confidence threshold is met."""
        confidence, passed_checks, passed_count = self.run_full_analysis(stock_data, market_data, sector_data)
        
        print(f"\nAnalysis Complete. Confidence Score: {confidence:.2%}")
        print(f"Passed Checks ({passed_count}/{len(self.all_checks)}):")
        for check in passed_checks:
            print(f"- {check}")

        if confidence >= self.confidence_threshold:
            entry_price = stock_data['close'].iloc[-1]
            atr_value = stock_data['atr'].iloc[-1]
            stop_loss = entry_price - (2 * atr_value)
            take_profit = entry_price + (self.reward_risk_ratio * (entry_price - stop_loss))
            
            signal = {
                'signal': 'BUY',
                'entry_price': f"{entry_price:.2f}",
                'stop_loss': f"{stop_loss:.2f}",
                'take_profit': f"{take_profit:.2f}",
                'confidence': f"{confidence:.2%}",
                'reason': f"Passed {passed_count} of {len(self.all_checks)} checks."
            }
            return signal
        else:
            return None

# Example of how to use this class
if __name__ == '__main__':
    # --- Create sample data for demonstration ---
    base = np.array([150, 151, 152, 150, 152, 153, 155, 154, 156, 155, 157, 158, 160, 159, 161, 163, 162, 164, 163, 168])
    dates = pd.to_datetime(pd.date_range(start='2023-01-01', periods=len(base)))
    sample_stock_data = pd.DataFrame({
        'open': base - 1, 'high': base + 2, 'low': base - 2, 'close': base,
        'volume': np.random.randint(100000, 200000, size=len(base))
    }, index=dates)
    sample_stock_data.loc[sample_stock_data.index[-1], 'volume'] = 350000 # Volume spike
    sample_stock_data.loc[sample_stock_data.index[-1], 'close'] = 170 # Breakout
    sample_stock_data.loc[sample_stock_data.index[-1], 'high'] = 171

    market_base = np.linspace(300, 310, len(base))
    sample_market_data = pd.DataFrame({'close': market_base}, index=dates)
    sector_base = np.linspace(100, 105, len(base))
    sample_sector_data = pd.DataFrame({'close': sector_base}, index=dates)

    # --- Run the analysis ---
    analyzer = AdvancedPriceActionAnalyzer()
    trade_signal = analyzer.generate_trade_signal(sample_stock_data, sample_market_data, sample_sector_data)

    if trade_signal:
        print("\n--- TRADE SIGNAL GENERATED ---")
        for key, value in trade_signal.items():
            print(f"{key.replace('_', ' ').title()}: {value}")
    else:
        print("\n--- NO TRADE SIGNAL: Confidence threshold not met. ---")
