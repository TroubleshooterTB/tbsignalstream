# ==============================================================================
# Arcane Nexus - Live Tactical Alert Engine
# Expert Module: Sentiment Engine (sentiment_engine.py)
#
# This module analyzes market psychology and narrative phases based on the
# "Buy The Rumor, Sell The Fact" PDF.
# ==============================================================================

import pandas as pd
from typing import Dict, Any

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
        """
        if data.empty or len(data) < 10:
            return {"phase": "neutral", "confidence": 0.0}

        recent_data = data.iloc[-10:]
        recent_volume_avg = recent_data[\'Volume\'].mean()
        last_bar = data.iloc[-1]

        if last_bar[\'Close\'] > last_bar[\'Open\'] and last_bar[\'Volume\'] > recent_volume_avg * 1.5:
            if len(recent_data) > 1 and recent_data[\'Close\'].iloc[-2] < recent_data[\'Close\'].iloc[-1]:
                return {"phase": "rumor", "confidence": 0.7}
            else:
                return {"phase": "fact", "confidence": 0.6}

        elif last_bar[\'Close\'] < last_bar[\'Open\'] and last_bar[\'Volume\'] > recent_volume_avg * 1.5:
            if len(recent_data) > 1 and recent_data[\'Close\'].iloc[-2] > recent_data[\'Close\'].iloc[-1]:
                return {"phase": "disappointment", "confidence": 0.7}
            else:
                return {"phase": "panic", "confidence": 0.6}

        elif recent_data[\'Close\'].mean() < data[\'Close\'].mean():
            return {"phase": "weakening", "confidence": 0.4}

        else:
            return {"phase": "neutral", "confidence": 0.3}

    def check_for_contrarian_opportunity(self, data: pd.DataFrame) -> bool:
        """
        Checks for potential contrarian trading opportunities (\'blood in the street\'s).
        """
        if data.empty or len(data) < 20:
            return False

        recent_data = data.iloc[-20:]
        lowest_close_recent = recent_data[\'Close\'].min()
        overall_volume_avg = data[\'Volume\'].mean()

        last_bar = data.iloc[-1]
        if last_bar[\'Close\'] < last_bar[\'Open\'] and overall_volume_avg > 0 and last_bar[\'Volume\'] > overall_volume_avg * 2.0:
            if last_bar[\'Close\'] <= lowest_close_recent * 1.02:
                print("SENTIMENT_ENGINE: Potential contrarian opportunity detected: Volume spike on down bar near recent low.")
                return True

        return False

if __name__ == \'__main__\':
    dummy_data = pd.DataFrame({
        \'Open\': [100, 101, 102, 101, 98, 95, 92, 90, 91, 88, 85, 82, 80, 81, 78],
        \'High\': [102, 103, 104, 102, 99, 96, 93, 91, 92, 89, 86, 83, 81, 82, 79],
        \'Low\': [99, 100, 101, 97, 96, 93, 90, 88, 89, 86, 83, 80, 78, 79, 76],
        \'Close\': [101, 102, 101, 98, 95, 92, 90, 88, 90, 86, 83.0, 80, 79, 80, 77],
        \'Volume\': [1000, 1200, 800, 1500, 1800, 2000, 2500, 3000, 2800, 3500, 4000, 4500, 6000, 5500, 7000]
    })

    sentiment_engine = SentimentEngine()

    narrative = sentiment_engine.get_narrative_phase(dummy_data)
    print(f"Detected Narrative Phase: {narrative}")

    is_contrarian = sentiment_engine.check_for_contrarian_opportunity(dummy_data)
    print(f"Contrarian opportunity detected: {is_contrarian}")
