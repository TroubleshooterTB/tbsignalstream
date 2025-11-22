import pandas as pd
from typing import Dict, Any

class PriceActionEngine:
    """
    Analyzes price action patterns, bar microstructure, and market context
    based on the principles described by Al Brooks.
    """
    def __init__(self, data: pd.DataFrame):
        """
        Initializes the PriceActionEngine with price data.

        Args:
            data: A pandas DataFrame with columns 'Open', 'High', 'Low', 'Close', 'Volume'.
        """
        self.data = data

    def analyze_bar_microstructure(self, index: int):
        """
        Analyzes the microstructure of a specific price bar.

        Args:
            index: The index of the bar to analyze.

        Returns:
            A dictionary containing microstructure details.
        """
        if index < 0 or index >= len(self.data):
            return {"error": "Invalid index"}

        bar = self.data.iloc[index]
        bar_range = bar['High'] - bar['Low']
        body_range = abs(bar['Close'] - bar['Open'])
        upper_shadow = bar['High'] - max(bar['Open'], bar['Close'])
        lower_shadow = min(bar['Open'], bar['Close']) - bar['Low']

        microstructure = {
            "range": bar_range,
            "body_range": body_range,
            "upper_shadow": upper_shadow,
            "lower_shadow": lower_shadow,
            "is_bullish_bar": bar['Close'] > bar['Open'],
            "is_bearish_bar": bar['Close'] < bar['Open'],
            "is_doji": body_range < bar_range * 0.1,  # Example threshold for a doji
            "body_to_range_ratio": body_range / bar_range if bar_range > 0 else 0,
            "upper_shadow_to_range_ratio": upper_shadow / bar_range if bar_range > 0 else 0,
            "lower_shadow_to_range_ratio": lower_shadow / bar_range if bar_range > 0 else 0,
        }
        return microstructure

    def analyze_consolidation_health(self, start_index: int, end_index: int):
        """
        Analyzes the health of a consolidation phase.

        Args:
            start_index: The starting index of the consolidation.
            end_index: The ending index of the consolidation.

        Returns:
            A dictionary containing consolidation health metrics.
        """
        if start_index < 0 or end_index >= len(self.data) or start_index >= end_index:
            return {"error": "Invalid indices"}

        consolidation_data = self.data.iloc[start_index:end_index + 1]
        high_of_consolidation = consolidation_data['High'].max()
        low_of_consolidation = consolidation_data['Low'].min()
        range_of_consolidation = high_of_consolidation - low_of_consolidation
        average_bar_range = consolidation_data.apply(lambda x: x['High'] - x['Low'], axis=1).mean()
        volume_during_consolidation = consolidation_data['Volume'].sum()

        # Simple checks for health (these can be expanded based on Brooks' criteria)
        is_tight_consolidation = range_of_consolidation / self.data['Close'].mean() < 0.05 # Example threshold
        is_low_volume_consolidation = volume_during_consolidation < self.data['Volume'].mean() * (end_index - start_index + 1) # Example check

        consolidation_health = {
            "range": range_of_consolidation,
            "high": high_of_consolidation,
            "low": low_of_consolidation,
            "duration": end_index - start_index + 1,
            "average_bar_range": average_bar_range,
            "total_volume": volume_during_consolidation,
            "is_tight": is_tight_consolidation,
            "is_low_volume": is_low_volume_consolidation,
            # Add more metrics like number of overlapping bars, presence of breakout attempts, etc.
        }
        return consolidation_health

    def determine_always_in_direction(self, lookback_period: int = 20):
        """
        Determines the "always in" direction based on price action over a lookback period.
        This is a simplified approach based on Brooks' concept.

        Args:
            lookback_period: The number of bars to consider for determining direction.

        Returns:
            "Bullish", "Bearish", or "Trading Range".
        """
        if lookback_period > len(self.data):
            lookback_period = len(self.data)

        recent_data = self.data.iloc[-lookback_period:]
        high_of_period = recent_data['High'].max()
        low_of_period = recent_data['Low'].min()
        current_price = self.data.iloc[-1]['Close']

        # Simple logic: if price is near the high of the period, assume bullish, and vice versa.
        # A more sophisticated approach would involve trend lines, moving averages, etc.
        range_of_period = high_of_period - low_of_period
        bullish_threshold = high_of_period - range_of_period * 0.2
        bearish_threshold = low_of_period + range_of_period * 0.2

        if current_price > bullish_threshold:
            return "Bullish"
        elif current_price < bearish_threshold:
            return "Bearish"
        else:
            return "Trading Range"

    def is_spike_or_channel(self, index: int, lookback_period: int = 10):
        """
        Determines if the recent price action leading up to the index is a spike or a channel.
        This is a simplified check.

        Args:
            index: The index of the current bar.
            lookback_period: The number of previous bars to consider.

        Returns:
            "Spike", "Channel", or "Other".
        """
        if index < lookback_period or index >= len(self.data):
            return "Other"

        recent_data = self.data.iloc[index - lookback_period:index + 1]
        high_of_period = recent_data['High'].max()
        low_of_period = recent_data['Low'].min()
        range_of_period = high_of_period - low_of_period

        # Spike indication: a large range bar or a few large range bars in a short period
        average_recent_bar_range = recent_data.apply(lambda x: x['High'] - x['Low'], axis=1).mean()
        average_overall_bar_range = self.data.apply(lambda x: x['High'] - x['Low'], axis=1).mean()

        if average_recent_bar_range > average_overall_bar_range * 1.5: # Example threshold for spike
            return "Spike"

        # Channel indication: series of overlapping bars, potentially with shallow angles
        # A more robust check would involve linear regression or angle analysis
        overlaps = 0
        for i in range(1, len(recent_data)):
            if max(recent_data.iloc[i]['Low'], recent_data.iloc[i-1]['Low']) < min(recent_data.iloc[i]['High'], recent_data.iloc[i-1]['High']):
                overlaps += 1

        if overlaps / lookback_period > 0.7: # Example threshold for significant overlap
             return "Channel"

        return "Other"

if __name__ == '__main__':
    # Example Usage
    # Create a sample DataFrame
    data = {
        'Open': [10, 11, 12, 11, 13, 14, 15, 14, 13, 12, 11, 10, 9, 10, 11],
        'High': [12, 13, 14, 12, 15, 16, 17, 15, 14, 13, 12, 11, 10, 11, 12],
        'Low': [9, 10, 11, 10, 12, 13, 14, 13, 12, 11, 10, 9, 8, 9, 10],
        'Close': [11, 12, 11, 13, 14, 15, 14, 13, 12, 11, 10, 9, 10, 11, 12],
        'Volume': [100, 120, 110, 130, 150, 160, 140, 130, 120, 110, 100, 90, 80, 90, 100]
    }
    df = pd.DataFrame(data)

    engine = PriceActionEngine(df)

    # Analyze bar microstructure
    bar_index_to_analyze = 5
    microstructure = engine.analyze_bar_microstructure(bar_index_to_analyze)
    print(f"Microstructure of bar {bar_index_to_analyze}: {microstructure}")

    # Analyze consolidation health
    consolidation_start = 7
    consolidation_end = 11
    consolidation_health = engine.analyze_consolidation_health(consolidation_start, consolidation_end)
    print(f"Consolidation health from index {consolidation_start} to {consolidation_end}: {consolidation_health}")

    # Determine always in direction
    always_in = engine.determine_always_in_direction()
    print(f"Always in direction: {always_in}")

    # Determine if spike or channel
    bar_index_for_pattern = 6
    pattern = engine.is_spike_or_channel(bar_index_for_pattern)
    print(f"Pattern around bar {bar_index_for_pattern}: {pattern}")
