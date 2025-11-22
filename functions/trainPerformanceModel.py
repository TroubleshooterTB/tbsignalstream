import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta

# Initialize Firebase Admin SDK (ensure you have configured your credentials)
try:
    firebase_admin.get_app()
except ValueError:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred)

db = firestore.client()

def trainPerformanceModel(event, context):
    """
    Cloud Function to analyze trade performance data and update weekly bias.

    Args:
        event: The Cloud Functions event object.
        context: The Cloud Functions context object.
    """
    print("Starting trainPerformanceModel function...")

    # Define the time range for the past week
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)

    # Reference to the trade performance log collection
    trade_log_ref = db.collection('trade_performance_log')

    # Query for documents within the past week
    docs = trade_log_ref.where('timestamp', '>=', start_date).where('timestamp', '<=', end_date).stream()

    trade_data = []
    for doc in docs:
        trade_data.append(doc.to_dict())

    if not trade_data:
        print("No trade data found for the past week.")
        # Optionally, save an empty or default weekly bias
        weekly_bias_ref = db.collection('market_analysis').document('weekly_bias')
        weekly_bias_ref.set({'message': 'No trade data available for analysis this week.'})
        return

    # Convert trade data to a pandas DataFrame for analysis
    df = pd.DataFrame(trade_data)

    # --- Perform Analysis ---
    # This is a placeholder for sophisticated analysis.
    # You would add logic here to analyze columns like:
    # 'pattern_name', 'sector', 'time_of_day', 'result' (win/loss), 'profit_loss', etc.

    # Example Analysis: Find best performing pattern
    best_performing_pattern = None
    if 'pattern_name' in df.columns and 'result' in df.columns:
        win_rates = df.groupby('pattern_name')['result'].apply(lambda x: (x == 'win').sum() / len(x) if len(x) > 0 else 0)
        if not win_rates.empty:
            best_performing_pattern = win_rates.idxmax()

    # Example Analysis: Find best performing sector
    best_sector = None
    if 'sector' in df.columns and 'result' in df.columns:
         sector_win_rates = df.groupby('sector')['result'].apply(lambda x: (x == 'win').sum() / len(x) if len(x) > 0 else 0)
         if not sector_win_rates.empty:
             best_sector = sector_win_rates.idxmax()

    # Example Analysis: Calculate overall win rate bias
    win_rate_bias = 0.0
    if 'result' in df.columns:
        total_trades = len(df)
        if total_trades > 0:
            winning_trades = (df['result'] == 'win').sum()
            win_rate_bias = (winning_trades / total_trades) - 0.5 # Simple bias around 50%

    # Add more analysis as needed (e.g., time of day, specific indicators)

    # --- Prepare and Save Weekly Bias ---
    weekly_bias_data = {
        'analysis_date': datetime.utcnow(),
        'best_performing_pattern': best_performing_pattern,
        'best_sector': best_sector,
        'win_rate_bias': win_rate_bias,
        # Add other insights here
        'total_trades_analyzed': len(df),
        'analysis_period_start': start_date,
        'analysis_period_end': end_date
    }

    weekly_bias_ref = db.collection('market_analysis').document('weekly_bias')

    try:
        weekly_bias_ref.set(weekly_bias_data)
        print(f"Weekly bias updated successfully: {weekly_bias_data}")
    except Exception as e:
        print(f"Error writing weekly bias to Firestore: {e}")

    print("trainPerformanceModel function finished.")
