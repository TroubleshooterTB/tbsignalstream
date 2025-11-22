import pandas as pd
from typing import Dict, Any
import logging

class SentimentEngine:
    """
    Analyzes market psychology and narrative phases based on trading principles.
    """

    def __init__(self):
        """Initializes the SentimentEngine."""
        pass

    def get_narrative_phase(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Determines the current narrative phase of a stock based on price action and volume.

        This implementation uses simplified heuristics based on recent price action and volume
        spikes, aligning with the 'Buy The Rumor, Sell The Fact' principle.
        A more advanced version would integrate external news sentiment.

        Args:
            data: Historical price and volume data (pd.DataFrame).

        Returns:
            Dictionary containing 'phase' (e.g., 'rumor', 'fact', 'neutral', 'weakening', 'panic')
            and 'confidence' (float between 0 and 1).
        """
        if data.empty or len(data) < 20: # Need enough data for reasonable volume average and recent trend
            return {"phase": "neutral", "confidence": 0.0}

        recent_data = data.iloc[-20:] # Look at the last 20 bars for trend and volatility context
        recent_volume_avg = recent_data['Volume'].mean()
        last_bar = data.iloc[-1]
        
        # Simple trend analysis on the last few bars
        short_term_trend = "neutral"
        if recent_data['Close'].iloc[-5:].mean() > recent_data['Close'].iloc[-10:-5].mean():
            short_term_trend = "up"
        elif recent_data['Close'].iloc[-5:].mean() < recent_data['Close'].iloc[-10:-5].mean():
            short_term_trend = "down"

        # Simplified logic based on price movement and volume
        if short_term_trend == "up" and last_bar['Volume'] > recent_volume_avg * 1.8 and last_bar['Close'] > last_bar['Open']:
             # Strong upward momentum with confirming high volume bar
             return {"phase": "rumor", "confidence": 0.75}

        elif short_term_trend == "down" and last_bar['Volume'] > recent_volume_avg * 2.0 and last_bar['Close'] < last_bar['Open']:
            # Strong downward momentum with capitulatory volume spike
             return {"phase": "panic", "confidence": 0.8}

        elif short_term_trend == "up" and last_bar['Close'] < last_bar['Open'] and last_bar['Volume'] < recent_volume_avg * 0.8:
            # Weak pullback on low volume after an uptrend (potential buy the dip in 'rumor' phase)
             return {"phase": "rumor_consolidation", "confidence": 0.6}

        elif short_term_trend == "down" and last_bar['Close'] > last_bar['Open'] and last_bar['Volume'] < recent_volume_avg * 0.8:
             # Weak bounce on low volume after a downtrend (potential sell the bounce in 'fact' or 'disappointment' phase)
             return {"phase": "fact_bounce", "confidence": 0.5}

        elif short_term_trend == "down" and last_bar['Volume'] > recent_volume_avg * 1.5 and last_bar['Close'] < recent_data['Close'].iloc[-2]:
             # Significant down move on high volume, breaking recent support
             return {"phase": "disappointment", "confidence": 0.7}

        else:
            return {"phase": "neutral", "confidence": 0.3} # Default if no clear phase detected

    def check_for_contrarian_opportunity(self, data: pd.DataFrame) -> bool:
        """
        Checks for potential contrarian trading opportunities ('blood in the street').

        Looks for signs of extreme negative sentiment or capitulation in price action
        and volume, indicating a potential buying opportunity against the prevailing
        crowd psychology. Specifically looking for a potential bottom signal.

        Args:
            data: Historical price and volume data (pd.DataFrame).

        Returns:
            True if a contrarian opportunity is detected, False otherwise.
        """
        if data.empty or len(data) < 30: # Need enough data to see recent trend and potential capitulation
            return False

        recent_data = data.iloc[-30:] # Analyze the last 30 bars
        overall_volume_avg = data['Volume'].mean()

        # Signals for potential capitulation/contrarian buy opportunity:
        # 1. A sharp price drop (e.g., engulfing bearish bar or large range down bar)
        # 2. Accompanied by a significant volume spike (e.g., > 2x average volume)
        # 3. Price is testing a significant prior low or support level (requires swing point/support level data, not fully implemented here)
        # 4. A subsequent reversal attempt (e.g., a doji or bullish hammer on the next bar - requires looking at multiple bars)

        last_bar = data.iloc[-1]
        second_last_bar = data.iloc[-2] if len(data) >= 2 else None

        # Simplified check: Large range down bar on very high volume
        if last_bar['Close'] < last_bar['Open'] and \
           (last_bar['High'] - last_bar['Low']) > (recent_data['High'] - recent_data['Low']).mean() * 1.5 and \
           last_bar['Volume'] > overall_volume_avg * 2.5: # Volume spike is very high
             
             # Check if it's near a recent significant low (simplified check using recent minimum)
             recent_low = recent_data['Low'].min()
             if last_bar['Low'] <= recent_low * 1.01: # Current low is very close to recent lowest low
                logging.info("SENTIMENT_ENGINE: Potential contrarian opportunity: Large range down bar on extreme volume near recent low.")
                return True

        # Simplified check: Bearish engulfing or strong close near low, followed by low volume inside bar
        # This attempts to detect a potential stopping volume bar followed by indecision
        if second_last_bar is not None and \
           second_last_bar['Close'] < second_last_bar['Open'] and \
           second_last_bar['Volume'] > overall_volume_avg * 1.8 and \
           last_bar['High'] < second_last_bar['High'] and \
           last_bar['Low'] > second_last_bar['Low'] and \
           last_bar['Volume'] < overall_volume_avg * 0.8:
             
             logging.info("SENTIMENT_ENGINE: Potential contrarian opportunity: High volume down bar followed by low volume inside bar.")
             return True

        # More complex checks would involve analyzing sequences of bars and their relationship to support levels.

        return False

# Example Usage (for testing this module independently)
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    # Create a dummy DataFrame with some price and volume data
    # Data designed to potentially show a 'panic' followed by a low volume bounce
    dummy_data = pd.DataFrame({
        'Open': [100, 101, 102, 101, 98, 95, 92, 90, 91, 88, 85, 82, 80, 75, 78, 79, 78, 77, 76, 75, 74, 73, 72, 71, 70, 68, 65, 62, 60, 58, 60, 61, 60, 62, 63],
        'High': [102, 103, 104, 102, 99, 96, 93, 91, 92, 89, 86, 83, 81, 76, 79, 80, 79, 78, 77, 76, 75, 74, 73, 72, 71, 69, 66, 63, 61, 59, 61, 62, 61, 63, 64],
        'Low': [99, 100, 101, 97, 96, 93, 90, 88, 89, 86, 83, 80, 78, 74, 77, 78, 77, 76, 75, 74, 73, 72, 71, 70, 69, 67, 64, 61, 59, 57, 59, 60, 59, 61, 62],
        'Close': [101, 102, 101, 98, 95, 92, 90, 88, 90, 86, 83, 80, 79, 75, 78, 79, 78, 77, 76, 75, 74, 73, 72, 71, 70, 68, 65, 62, 60, 58, 60, 61, 60, 62, 63],
        'Volume': [1000, 1200, 800, 1500, 1800, 2000, 2500, 3000, 2800, 3500, 4000, 4500, 6000, 8000, 5000, 4800, 4500, 4000, 3800, 3500, 3200, 3000, 2800, 2500, 2200, 2000, 1800, 1500, 1200, 1000, 500, 600, 550, 700, 800]
    })

    sentiment_engine = SentimentEngine()

    # Test narrative phase detection
    narrative = sentiment_engine.get_narrative_phase(dummy_data)
    print(f"Detected Narrative Phase: {narrative}")

    # Test contrarian opportunity detection
    is_contrarian = sentiment_engine.check_for_contrarian_opportunity(dummy_data)
    print(f"Contrarian opportunity detected: {is_contrarian}")
