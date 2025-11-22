# **App Name**: SignalStream

## Core Features:

- AI-Powered News Catalyst: Catalyst Scoring: Uses generative AI to summarize news articles and assign a catalyst score based on sentiment analysis to help determine relevance as a tool.
- Live Alert Dashboard: Real-time Alerts View: Displays real-time alerts as they are triggered, updating dynamically.
- Deep Dive Analytics: Detailed Analysis View: Shows detailed data points from all layers that triggered an alert when the user clicks on it.
- Push Notification Alerts: Notification Handling: React app implementation to receive push notifications.
- Financial Data Integration: Connects to financial APIs for real-time and historical stock data, using provided API keys for services like TrueData or Polygon.io.
- Quantitative Analysis: Calculates advanced quantitative metrics: Relative Strength vs NIFTY 50, Volatility-Adjusted Momentum (Sharpe Ratio of daily returns over 60 days), and identifies stocks in a low-volatility consolidation regime.
- Confidence Calculation: Final function combines the Quant Score (from L2), Catalyst Score (L3), and Confirmation Score (L4) into a single confidence probability between 0 and 1.

## Style Guidelines:

- Primary color: Strong blue (#2962FF) to convey reliability and focus, reflecting the precision of financial data. 
- Background color: Light grayish-blue (#E5E9F2) for a clean, uncluttered backdrop.
- Accent color: Electric purple (#9D39C7) for interactive elements, inspired by the rapid shifts in market trends and advanced analytics.
- Body and headline font: 'Inter', a sans-serif (Note: currently only Google Fonts are supported.)
- Minimalist icons with a subtle outline style to represent different alert types and data points.
- Clean and structured layout to present complex financial data in an easily digestible format.
- Subtle animations for new alerts appearing in real-time and when navigating between different data views.