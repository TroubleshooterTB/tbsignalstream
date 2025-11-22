import pandas as pd

class TrendFollowerPersona:
    """
    Trading persona focused on trending markets.
    """
    def __init__(self):
        self.name = "TrendFollower"
        self.activation_condition = "Market Health Index is strongly Bullish or Bearish"
        self.pattern_priority = ["Head and Shoulders", "Triangles", "Rounding Bottom (Cup and Handle)", "Rectangles", "Flags and Pennants"]
        self.stop_loss_strategy = "Wider, volatility-based Trailing Stop-Loss"
        self.risk_reward_ratio = None # Not fixed, aims to ride the trend

    def get_trading_behavior(self):
        return {
            "pattern_priority": self.pattern_priority,
            "stop_loss_strategy": self.stop_loss_strategy,
            "risk_reward_ratio": self.risk_reward_ratio
        }

class ScalperPersona:
    """
    Trading persona focused on volatile, choppy markets with quick trades.
    """
    def __init__(self):
        self.name = "Scalper"
        self.activation_condition = "Market Health Index is Neutral and India VIX is high"
        self.pattern_priority = ["Flags and Pennants", "Triangles", "Rectangles"] # Prioritize short-term patterns
        self.stop_loss_strategy = "Very tight stop-losses"
        self.risk_reward_ratio = 1.5 # Example fixed Risk/Reward ratio

    def get_trading_behavior(self):
        return {
            "pattern_priority": self.pattern_priority,
            "stop_loss_strategy": self.stop_loss_strategy,
            "risk_reward_ratio": self.risk_reward_ratio
        }

class RangeTraderPersona:
    """
    Trading persona focused on sideways markets, buying at support and selling at resistance.
    """
    def __init__(self):
        self.name = "RangeTrader"
        self.activation_condition = "Market Health Index is Neutral and India VIX is low"
        self.pattern_priority = ["Double Top", "Double Bottom", "Triple Top", "Triple Bottom", "Rectangles", "Rounding Bottom (Cup and Handle)"] # Prioritize reversal/boundary patterns
        self.stop_loss_strategy = "Stop-losses outside of clear boundaries"
        self.risk_reward_ratio = None # Depends on range width

    def get_trading_behavior(self):
        return {
            "pattern_priority": self.pattern_priority,
            "stop_loss_strategy": self.stop_loss_strategy,
            "risk_reward_ratio": self.risk_reward_ratio
        }

# Placeholder function to determine the active persona (will be called by Cloud Function)
def determine_active_persona(market_health_index: str, india_vix: float):
    """
    Determines the active trading persona based on market conditions.

    Args:
        market_health_index: Current market health (\"Bullish\", \"Bearish\", \"Neutral\").
        india_vix: Current India VIX value.

    Returns:
        An instance of the active persona class.
    """
    # This is placeholder logic. Actual implementation will need to be more sophisticated.
    if market_health_index in ["Bullish", "Bearish"]:
        return TrendFollowerPersona()
    elif market_health_index == "Neutral" and india_vix > 20: # Example VIX threshold
        return ScalperPersona()
    elif market_health_index == "Neutral" and india_vix <= 20: # Example VIX threshold
        return RangeTraderPersona()
    else:
        # Default or error case
        return TrendFollowerPersona() # Default to trend following
import pandas as pd

class TrendFollowerPersona:
    """
    Trading persona focused on trending markets.
    """
    def __init__(self):
        self.name = "TrendFollower"
        self.activation_condition = "Market Health Index is strongly Bullish or Bearish"
        self.pattern_priority = ["Head and Shoulders", "Triangles", "Rounding Bottom (Cup and Handle)", "Rectangles", "Flags and Pennants"]
        self.stop_loss_strategy = "Wider, volatility-based Trailing Stop-Loss"
        self.risk_reward_ratio = None # Not fixed, aims to ride the trend

    def get_trading_behavior(self):
        return {
            "pattern_priority": self.pattern_priority,
            "stop_loss_strategy": self.stop_loss_strategy,
            "risk_reward_ratio": self.risk_reward_ratio
        }

class ScalperPersona:
    """
    Trading persona focused on volatile, choppy markets with quick trades.
    """
    def __init__(self):
        self.name = "Scalper"
        self.activation_condition = "Market Health Index is Neutral and India VIX is high"
        self.pattern_priority = ["Flags and Pennants", "Triangles", "Rectangles"] # Prioritize short-term patterns
        self.stop_loss_strategy = "Very tight stop-losses"
        self.risk_reward_ratio = 1.5 # Example fixed Risk/Reward ratio

    def get_trading_behavior(self):
        return {
            "pattern_priority": self.pattern_priority,
            "stop_loss_strategy": self.stop_loss_strategy,
            "risk_reward_ratio": self.risk_reward_ratio
        }

class RangeTraderPersona:
    """
    Trading persona focused on sideways markets, buying at support and selling at resistance.
    """
    def __init__(self):
        self.name = "RangeTrader"
        self.activation_condition = "Market Health Index is Neutral and India VIX is low"
        self.pattern_priority = ["Double Top", "Double Bottom", "Triple Top", "Triple Bottom", "Rectangles", "Rounding Bottom (Cup and Handle)"] # Prioritize reversal/boundary patterns
        self.stop_loss_strategy = "Stop-losses outside of clear boundaries"
        self.risk_reward_ratio = None # Depends on range width

    def get_trading_behavior(self):
        return {
            "pattern_priority": self.pattern_priority,
            "stop_loss_strategy": self.stop_loss_strategy,
            "risk_reward_ratio": self.risk_reward_ratio
        }

# Placeholder function to determine the active persona (will be called by Cloud Function)
def determine_active_persona(market_health_index: str, india_vix: float):
    """
    Determines the active trading persona based on market conditions.

    Args:
        market_health_index: Current market health ("Bullish", "Bearish", "Neutral").
        india_vix: Current India VIX value.

    Returns:
        An instance of the active persona class.
    """
    # This is placeholder logic. Actual implementation will need to be more sophisticated.
    if market_health_index in ["Bullish", "Bearish"]:
        return TrendFollowerPersona()
    elif market_health_index == "Neutral" and india_vix > 20: # Example VIX threshold
        return ScalperPersona()
    elif market_health_index == "Neutral" and india_vix <= 20: # Example VIX threshold
        return RangeTraderPersona()
    else:
        # Default or error case
        return TrendFollowerPersona() # Default to trend following


if __name__ == '__main__':
    # Example usage:
    market_health = "Bullish"
    vix_value = 15.0

    active_persona = determine_active_persona(market_health, vix_value)
    print(f"Active Persona: {active_persona.name}")
    print("Trading Behavior:")
    print(active_persona.get_trading_behavior())

    market_health = "Neutral"
    vix_value = 25.0
    active_persona = determine_active_persona(market_health, vix_value)
    print(f"\nActive Persona: {active_persona.name}")
    print("Trading Behavior:")
    print(active_persona.get_trading_behavior())

    market_health = "Neutral"
    vix_value = 12.0
    active_persona = determine_active_persona(market_health, vix_value)
    print(f"\nActive Persona: {active_persona.name}")
    print("Trading Behavior:")
    print(active_persona.get_trading_behavior())