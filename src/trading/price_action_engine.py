import pandas as pd
from typing import Dict, Any, List
import numpy as np

class PriceActionEngine:
    """
    Analyzes bar-by-bar price action and market micro-structure.
    """

    def __init__(self):
        """Initializes the PriceActionEngine."""
        pass

    def analyze_bar_microstructure(self, bar_data: pd.Series, breakout_direction: str) -> bool:
        """
        Analyzes the characteristics of a single bar (range, close location within the bar, wicks)
        to determine if it shows strength or weakness in the direction of the potential trade.

        Args:
            bar_data: A pandas Series containing OHLCV data for a single bar.
            breakout_direction: The direction of the potential breakout (\'up\' or \'down\').

        Returns:
            True if the bar microstructure confirms the breakout direction, False otherwise.
        """
        bar_range = bar_data[\'High\'] - bar_data[\'Low\']
        if bar_range == 0:
            return False

        close_location = (bar_data[\'Close\'] - bar_data[\'Low\']) / bar_range

        if breakout_direction == \'up\':
            if close_location > 0.75:
                upper_wick_size = bar_data[\'High\'] - bar_data[\'Close\']
                if upper_wick_size / bar_range < 0.3:
                    body_size = abs(bar_data[\'Close\'] - bar_data[\'Open\'])
                    if body_size / bar_range > 0.5:
                        return True
            return False

        elif breakout_direction == \'down\':
            if close_location < 0.25:
                lower_wick_size = bar_data[\'Open\'] - bar_data[\'Low\'] if bar_data[\'Open\'] > bar_data[\'Low\'] else bar_data[\'Close\'] - bar_data[\'Low\']
                if lower_wick_size / bar_range < 0.3:
                    body_size = abs(bar_data[\'Close\'] - bar_data[\'Open\'])
                    if body_size / bar_range > 0.5:
                        return True
            return False
        else:
            return False

    def analyze_consolidation_health(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyzes a consolidation period to determine its health and potential for a breakout.
        Looks for signs of accumulation or distribution, decreasing volume, and tightening price range.

        Args:
            data: DataFrame of price data covering the consolidation period.

        Returns:
            A dictionary containing analysis results.
        """
        if data.empty or len(data) < 10:
            return {\'healthy\': False, \'reason\': \'Insufficient data\'}

        volume_series = data[\'Volume\']
        if len(volume_series) > 5:
            volume_indices = np.arange(len(volume_series))
            volume_slope = np.polyfit(volume_indices, volume_series, 1)[0]
            decreasing_volume = volume_slope < 0
        else:
            decreasing_volume = False

        if len(data) > 1:
            high_low = data[\'High\'] - data[\'Low\']
            high_close = (data[\'High\'] - data[\'Close\'].shift()).abs().fillna(0)
            low_close = (data[\'Low\'] - data[\'Close\'].shift()).abs().fillna(0)
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = true_range.ewm(alpha=1/len(data), adjust=False).mean().iloc[-1]

            if len(data) > 10:
                recent_atr = true_range.iloc[-5:].mean()
                earlier_atr = true_range.iloc[:5:].mean()
                tightening_range_factor = 1.0 - (recent_atr / earlier_atr if earlier_atr > 0 else 0)
                tightening_range = tightening_range_factor if tightening_range_factor > 0 else 0
            else:
                tightening_range = 0.0
        else:
            atr = 0
            tightening_range = 0.0

        up_bars = data[data[\'Close\'] > data[\'Open\']]
        down_bars = data[data[\'Close\'] < data[\'Open\']]

        if not up_bars.empty and not down_bars.empty:
            avg_volume_up_bars = up_bars[\'Volume\'].mean()
            avg_volume_down_bars = down_bars[\'Volume\'].mean()
            accumulation_sign = avg_volume_up_bars > avg_volume_down_bars * 1.1 if avg_volume_down_bars > 0 else False
            distribution_sign = avg_volume_down_bars > avg_volume_up_bars * 1.1 if avg_volume_up_bars > 0 else False
        else:
            accumulation_sign = False
            distribution_sign = False

        is_healthy = decreasing_volume and tightening_range > 0.5
        health_reason = []
        if not decreasing_volume: health_reason.append("Volume not decreasing")
        if tightening_range <= 0.5: health_reason.append("Range not tightening sufficiently")
        if distribution_sign: health_reason.append("Signs of distribution")

        return {
            \'healthy\': is_healthy,
            \'decreasing_volume\': decreasing_volume,
            \'tightening_range_factor\': round(tightening_range, 2),
            \'accumulation_sign\': accumulation_sign,
            \'distribution_sign\': distribution_sign,
            \'reason\': ", ".join(health_reason) if health_reason else "Healthy"
        }

    def determine_always_in_direction(self, data: pd.DataFrame) -> str:
        """
        Determines the prevailing "always in" direction of the market.
        """
        if data.empty or len(data) < 50:
            return \'neutral\'

        short_ma_period = 20
        long_ma_period = 50

        if len(data) < long_ma_period:
            return \'neutral\'

        data[\'Short_MA\'] = data[\'Close\'].rolling(window=short_ma_period).mean()
        data[\'Long_MA\'] = data[\'Close\'].rolling(window=long_ma_period).mean()

        latest_short_ma = data[\'Short_MA\'].iloc[-1]
        latest_long_ma = data[\'Long_MA\'].iloc[-1]
        latest_close = data[\'Close\'].iloc[-1]

        if latest_close > latest_short_ma and latest_short_ma > latest_long_ma:
            recent_trend = data[\'Close\'].iloc[-5:].mean() - data[\'Close\'].iloc[-10:-5].mean()
            if recent_trend > 0:
                return \'long\'

        elif latest_close < latest_short_ma and latest_short_ma < latest_long_ma:
            recent_trend = data[\'Close\'].iloc[-5:].mean() - data[\'Close\'].iloc[-10:-5].mean()
            if recent_trend < 0:
                return \'short\'

        return \'neutral\'

    def is_spike_or_channel(self, data: pd.DataFrame) -> str:
        """
        Identifies if the market is currently in a "spike" or a "channel".
        """
        if data.empty or len(data) < 20:
            return \'range\'

        recent_data = data.iloc[-20:]
        price_change_recent = recent_data[\'Close\'].iloc[-1] - recent_data[\'Open\'].iloc[0]
        range_recent = recent_data[\'High\'].max() - recent_data[\'Low\'].min()

        if range_recent > 0 and abs(price_change_recent) / range_recent > 0.7 and len(recent_data[recent_data[\'Close\'].diff().fillna(0).abs() > recent_data[\'Close\'].std() * 0.5]) > 5:
            if price_change_recent > 0:
                return \'spike_up\'
            else:
                return \'spike_down\'

        if len(data) > 14:
            atr = self._calculate_atr(data.iloc[-14:])
            if atr is not None and atr > 0:
                latest_close = data[\'Close\'].iloc[-1]
                recent_high = data[\'High\'].iloc[-10:].max()
                recent_low = data[\'Low\'].iloc[-10:].min()

                if abs(latest_close - recent_high) > atr * 1.5 and abs(latest_close - recent_low) > atr * 1.5:
                    return \'channel\'

        return \'range\'

    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> float:
        """Calculates the Average True Range (ATR)."""
        if len(data) < period:
            return None
        high_low = data[\'High\'] - data[\'Low\']
        high_close = (data[\'High\'] - data[\'Close\'].shift()).abs().fillna(0)
        low_close = (data[\'Low\'] - data[\'Close\'].shift()).abs().fillna(0)
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr = true_range.ewm(alpha=1/period, adjust=False).mean()
        return atr.iloc[-1]


if __name__ == \'__main__\':
    data = pd.DataFrame({
        \'Open\': [100, 101, 102, 101, 103, 104, 103, 105, 106, 105, 107, 108, 107, 109, 110, 115, 120, 118, 122, 125],
        \'High\': [102, 103, 104, 102, 105, 106, 104, 107, 108, 107, 109, 110, 109, 111, 112, 118, 123, 120, 124, 127],
        \'Low\': [99, 100, 101, 100, 102, 103, 102, 104, 105, 104, 106, 107, 106, 108, 109, 114, 119, 117, 121, 124],
        \'Close\': [101, 102, 103, 102, 104, 105, 103, 106, 107, 105, 108, 109, 108, 110, 111, 117, 122, 119, 123, 126],
        \'Volume\': [1000, 1100, 900, 1200, 1300, 1100, 1000, 1400, 1500, 1300, 1600, 1700, 1500, 1800, 1900, 3000, 3500, 2500, 2800, 3200]
    })

    pa_engine = PriceActionEngine()

    latest_bar = data.iloc[-1]
    print(f"Microstructure of latest bar (bullish): {pa_engine.analyze_bar_microstructure(latest_bar, \'up\')}")
    print(f"Microstructure of latest bar (bearish): {pa_engine.analyze_bar_microstructure(latest_bar, \'down\')}")

    consolidation_data = data.iloc[5:15]
    print(f"\nConsolidation health: {pa_engine.analyze_consolidation_health(consolidation_data)}")

    longer_data = pd.DataFrame({
        \'Open\': np.arange(100, 200, 1).tolist() + np.arange(200, 150, -1).tolist(),
        \'High\': np.arange(101, 201, 1).tolist() + np.arange(201, 151, -1).tolist(),
        \'Low\': np.arange(99, 199, 1).tolist() + np.arange(199, 149, -1).tolist(),
        \'Close\': np.arange(100.5, 200.5, 1).tolist() + np.arange(200.5, 150.5, -1).tolist(),
        \'Volume\': np.random.randint(500, 3000, 150).tolist()
    })
    print(f"\nAlways In Direction: {pa_engine.determine_always_in_direction(longer_data)}")

    print(f"\nSpike or Channel: {pa_engine.is_spike_or_channel(data)}")
