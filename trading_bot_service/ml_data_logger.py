"""
ML Data Logger - Collects historical trade data for ML model training

This module logs every trading signal (whether taken or not) along with:
- All technical indicators and features
- Trade outcome (win/loss/breakeven)
- Entry/exit prices and P&L
- Holding duration

After 100+ trades are collected, this data can be used to train a Random Forest
model that predicts trade success probability (Level 23).
"""

import logging
import pandas as pd
from datetime import datetime
from typing import Dict, Optional
from google.cloud import firestore

logger = logging.getLogger(__name__)


class MLDataLogger:
    """
    Logs every trade signal with features and outcomes for ML training.
    
    Data Collection Flow:
    1. log_signal() - Called when signal is generated (before entry)
    2. update_outcome() - Called when trade closes (with P&L)
    3. get_training_data() - Retrieve completed trades for model training
    """
    
    def __init__(self, db_client: Optional[firestore.Client] = None):
        """
        Initialize ML Data Logger
        
        Args:
            db_client: Firestore client (optional, creates new if None)
        """
        self.db = db_client
        self.enabled = True
        
        if self.db:
            logger.info("✅ MLDataLogger initialized with Firestore")
        else:
            logger.warning("⚠️ MLDataLogger initialized without Firestore - logging disabled")
            self.enabled = False
    
    def log_signal(self, signal_data: Dict) -> Optional[str]:
        """
        Log a trading signal with all features.
        
        Call this when a signal is generated (before order placement).
        
        Args:
            signal_data: Dictionary containing:
                Required:
                - symbol: Stock symbol
                - action: 'BUY' or 'SELL'
                - entry_price: Entry price
                - stop_loss: Stop loss price
                - target: Target price
                - was_taken: True if order was placed, False if rejected
                
                Optional (technical indicators):
                - rsi, macd, adx, bb_width, volume_ratio, etc.
                - pattern_name, confidence, score
                - Any other features you want ML to learn from
                
        Returns:
            Document ID if successful, None otherwise
        """
        if not self.enabled or not self.db:
            return None
        
        try:
            # Add timestamp and outcome placeholders
            log_entry = signal_data.copy()
            log_entry['logged_at'] = datetime.now()
            log_entry['outcome'] = None  # Will be updated when trade closes
            log_entry['pnl'] = None
            log_entry['pnl_percent'] = None
            log_entry['exit_price'] = None
            log_entry['exit_time'] = None
            log_entry['holding_duration_minutes'] = None
            log_entry['exit_reason'] = None
            
            # Calculate derived features
            if all(k in log_entry for k in ['entry_price', 'stop_loss', 'target']):
                entry = log_entry['entry_price']
                stop = log_entry['stop_loss']
                target = log_entry['target']
                
                risk = abs(entry - stop)
                reward = abs(target - entry)
                
                log_entry['risk_amount'] = risk
                log_entry['reward_amount'] = reward
                log_entry['risk_reward_ratio'] = reward / risk if risk > 0 else 0
                log_entry['stop_distance_percent'] = (risk / entry) * 100
                log_entry['target_distance_percent'] = (reward / entry) * 100
            
            # Store in Firestore
            doc_ref = self.db.collection('ml_training_data').document()
            doc_ref.set(log_entry)
            
            signal_id = doc_ref.id
            logger.debug(f"📊 Logged signal {signal_id}: {log_entry.get('symbol')} "
                        f"{log_entry.get('action')} @ ₹{log_entry.get('entry_price'):.2f} "
                        f"(Taken: {log_entry.get('was_taken')})")
            
            return signal_id
            
        except Exception as e:
            logger.error(f"Error logging signal to ML database: {e}", exc_info=True)
            return None
    
    def update_outcome(self, signal_id: str, outcome_data: Dict):
        """
        Update a logged signal with actual trade outcome.
        
        Call this when a trade closes (stop hit, target hit, or manual exit).
        
        Args:
            signal_id: Document ID returned from log_signal()
            outcome_data: Dictionary containing:
                Required:
                - outcome: 'WIN', 'LOSS', or 'BREAKEVEN'
                - exit_price: Actual exit price
                - pnl: Profit/loss amount in rupees
                - pnl_percent: Profit/loss percentage
                
                Optional:
                - exit_time: Timestamp of exit
                - holding_duration_minutes: How long position was held
                - exit_reason: 'STOP_LOSS', 'TARGET', 'TRAILING_STOP', 'EOD_CLOSE', 'MANUAL'
        """
        if not self.enabled or not self.db:
            return
        
        try:
            doc_ref = self.db.collection('ml_training_data').document(signal_id)
            
            # Add exit timestamp if not provided
            if 'exit_time' not in outcome_data:
                outcome_data['exit_time'] = datetime.now()
            
            # Update document
            doc_ref.update(outcome_data)
            
            logger.info(f"✅ Updated ML data {signal_id}: {outcome_data.get('outcome')} "
                       f"(P&L: {outcome_data.get('pnl_percent', 0):.2f}%)")
            
        except Exception as e:
            logger.error(f"Error updating outcome for signal {signal_id}: {e}", exc_info=True)
    
    def log_rejected_signal(self, signal_data: Dict, rejection_reason: str):
        """
        Log a signal that was rejected (not taken).
        
        This is valuable for ML training - knowing which signals were filtered out.
        
        Args:
            signal_data: Signal data (same format as log_signal)
            rejection_reason: Why the signal was rejected (e.g., "30-Point Checklist Failed")
        """
        if not self.enabled or not self.db:
            return
        
        signal_data['was_taken'] = False
        signal_data['rejection_reason'] = rejection_reason
        signal_data['outcome'] = 'REJECTED'
        
        return self.log_signal(signal_data)
    
    def get_training_data(self, min_samples: int = 100, 
                         only_completed: bool = True) -> pd.DataFrame:
        """
        Retrieve trade data for ML model training.
        
        Args:
            min_samples: Minimum number of samples required
            only_completed: If True, only return trades with outcomes (not pending)
            
        Returns:
            DataFrame with all logged signals and outcomes
        """
        if not self.enabled or not self.db:
            logger.warning("MLDataLogger not enabled or no Firestore client")
            return pd.DataFrame()
        
        try:
            # Query Firestore
            collection_ref = self.db.collection('ml_training_data')
            
            if only_completed:
                # Only get signals with outcomes (completed trades)
                query = collection_ref.where('outcome', 'in', ['WIN', 'LOSS', 'BREAKEVEN'])
            else:
                # Get all signals
                query = collection_ref
            
            # Retrieve documents
            docs = query.stream()
            data = [doc.to_dict() for doc in docs]
            
            if len(data) == 0:
                logger.warning("No training data available yet")
                return pd.DataFrame()
            
            df = pd.DataFrame(data)
            
            logger.info(f"📊 Retrieved {len(df)} training samples from Firestore")
            
            # Check if enough samples
            if len(df) < min_samples:
                logger.warning(f"⚠️ Only {len(df)} samples available, need {min_samples} "
                             f"for reliable model training. Continue trading to collect more data.")
            
            # Data quality report
            if not df.empty and 'outcome' in df.columns:
                outcome_counts = df['outcome'].value_counts()
                logger.info(f"Outcome distribution:\n{outcome_counts}")
                
                if 'was_taken' in df.columns:
                    taken_count = df['was_taken'].sum()
                    logger.info(f"Signals taken: {taken_count} / {len(df)} "
                               f"({taken_count/len(df)*100:.1f}%)")
            
            return df
            
        except Exception as e:
            logger.error(f"Error retrieving training data: {e}", exc_info=True)
            return pd.DataFrame()
    
    def get_statistics(self) -> Dict:
        """
        Get statistics about logged data.
        
        Returns:
            Dictionary with data collection statistics
        """
        if not self.enabled or not self.db:
            return {'enabled': False, 'total_signals': 0}
        
        try:
            # Count total signals
            total_docs = len(list(self.db.collection('ml_training_data').stream()))
            
            # Count completed trades
            completed_query = self.db.collection('ml_training_data').where(
                'outcome', 'in', ['WIN', 'LOSS', 'BREAKEVEN']
            )
            completed_docs = len(list(completed_query.stream()))
            
            return {
                'enabled': True,
                'total_signals': total_docs,
                'completed_trades': completed_docs,
                'pending_trades': total_docs - completed_docs,
                'ready_for_training': completed_docs >= 100
            }
            
        except Exception as e:
            logger.error(f"Error getting ML statistics: {e}")
            return {'enabled': True, 'error': str(e)}
    
    def cleanup_old_data(self, days_old: int = 90):
        """
        Remove training data older than specified days.
        
        Args:
            days_old: Delete data older than this many days
        """
        if not self.enabled or not self.db:
            return
        
        try:
            from datetime import timedelta
            
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            # Query old documents
            old_docs = self.db.collection('ml_training_data').where(
                'logged_at', '<', cutoff_date
            ).stream()
            
            count = 0
            for doc in old_docs:
                doc.reference.delete()
                count += 1
            
            logger.info(f"🗑️ Cleaned up {count} training samples older than {days_old} days")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")


# Example usage for testing
if __name__ == '__main__':
    # Test without Firestore (logging disabled)
    logger_test = MLDataLogger(db_client=None)
    
    print(f"Logger enabled: {logger_test.enabled}")
    
    # Would need actual Firestore client to test fully
    print("MLDataLogger created successfully!")
