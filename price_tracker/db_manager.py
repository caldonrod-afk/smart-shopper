"""
Database Manager Utility Functions
Provides common database operations for real-time price tracking
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager
import os


class DatabaseManager:
    """Utility class for common database operations"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            home = os.path.expanduser("~")
            data_dir = os.path.join(home, 'price-tracker', 'data')
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, 'price_tracker.db')
        
        self.db_path = db_path
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    # Monitoring Configuration Operations
    
    def get_monitoring_config(self, product_id: int) -> Optional[Dict]:
        """Get monitoring configuration for a product"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM monitoring_config WHERE product_id = ?
            ''', (product_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def set_monitoring_interval(self, product_id: int, interval_minutes: int) -> bool:
        """Set monitoring interval for a product"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if config exists
            cursor.execute('''
                SELECT product_id FROM monitoring_config WHERE product_id = ?
            ''', (product_id,))
            
            if cursor.fetchone():
                # Update existing
                cursor.execute('''
                    UPDATE monitoring_config 
                    SET interval_minutes = ?
                    WHERE product_id = ?
                ''', (interval_minutes, product_id))
            else:
                # Insert new
                cursor.execute('''
                    INSERT INTO monitoring_config (product_id, interval_minutes, status)
                    VALUES (?, ?, 'active')
                ''', (product_id, interval_minutes))
            
            return cursor.rowcount > 0
    
    def update_monitoring_status(self, product_id: int, status: str) -> bool:
        """Update monitoring status (active, paused, error)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE monitoring_config 
                SET status = ?
                WHERE product_id = ?
            ''', (status, product_id))
            return cursor.rowcount > 0
    
    def update_check_times(self, product_id: int, 
                          last_check: datetime = None,
                          next_check: datetime = None) -> bool:
        """Update last and next check times"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if last_check and next_check:
                cursor.execute('''
                    UPDATE monitoring_config 
                    SET last_check = ?, next_check = ?
                    WHERE product_id = ?
                ''', (last_check, next_check, product_id))
            elif last_check:
                cursor.execute('''
                    UPDATE monitoring_config 
                    SET last_check = ?
                    WHERE product_id = ?
                ''', (last_check, product_id))
            elif next_check:
                cursor.execute('''
                    UPDATE monitoring_config 
                    SET next_check = ?
                    WHERE product_id = ?
                ''', (next_check, product_id))
            
            return cursor.rowcount > 0
    
    def increment_failure_count(self, product_id: int) -> int:
        """Increment failure count and return new count"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE monitoring_config 
                SET failure_count = failure_count + 1
                WHERE product_id = ?
            ''', (product_id,))
            
            cursor.execute('''
                SELECT failure_count FROM monitoring_config WHERE product_id = ?
            ''', (product_id,))
            
            row = cursor.fetchone()
            return row[0] if row else 0
    
    def reset_failure_count(self, product_id: int) -> bool:
        """Reset failure count to 0"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE monitoring_config 
                SET failure_count = 0, backoff_until = NULL
                WHERE product_id = ?
            ''', (product_id,))
            return cursor.rowcount > 0
    
    def set_backoff(self, product_id: int, backoff_until: datetime) -> bool:
        """Set backoff time for a product"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE monitoring_config 
                SET backoff_until = ?
                WHERE product_id = ?
            ''', (backoff_until, product_id))
            return cursor.rowcount > 0
    
    def get_products_ready_for_check(self) -> List[Dict]:
        """Get products that are ready to be checked"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now()
            
            cursor.execute('''
                SELECT p.*, mc.interval_minutes, mc.last_check, mc.next_check
                FROM products p
                JOIN monitoring_config mc ON p.id = mc.product_id
                WHERE p.active = 1 
                  AND mc.status = 'active'
                  AND (mc.next_check IS NULL OR mc.next_check <= ?)
                  AND (mc.backoff_until IS NULL OR mc.backoff_until <= ?)
            ''', (now, now))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # Price History Operations
    
    def record_price_check(self, product_id: int, price: float, 
                          timestamp: datetime = None, source: str = None) -> bool:
        """Record a price check with precise timestamp"""
        if timestamp is None:
            timestamp = datetime.now()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO price_history (product_id, price, timestamp, source)
                VALUES (?, ?, ?, ?)
            ''', (product_id, price, timestamp, source))
            return cursor.rowcount > 0
    
    def get_price_history(self, product_id: int, 
                         start_date: datetime = None,
                         end_date: datetime = None,
                         limit: int = None) -> List[Dict]:
        """Get price history for a product with optional date range"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = 'SELECT * FROM price_history WHERE product_id = ?'
            params = [product_id]
            
            if start_date:
                query += ' AND timestamp >= ?'
                params.append(start_date)
            
            if end_date:
                query += ' AND timestamp <= ?'
                params.append(end_date)
            
            query += ' ORDER BY timestamp DESC'
            
            if limit:
                query += ' LIMIT ?'
                params.append(limit)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_latest_price(self, product_id: int) -> Optional[float]:
        """Get the most recent price for a product"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT price FROM price_history 
                WHERE product_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            ''', (product_id,))
            
            row = cursor.fetchone()
            return row[0] if row else None
    
    def get_price_statistics(self, product_id: int, days: int = 30) -> Dict:
        """Get price statistics for a product"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cutoff_date = datetime.now() - timedelta(days=days)
            
            cursor.execute('''
                SELECT 
                    MIN(price) as min_price,
                    MAX(price) as max_price,
                    AVG(price) as avg_price,
                    COUNT(*) as check_count
                FROM price_history
                WHERE product_id = ? AND timestamp >= ?
            ''', (product_id, cutoff_date))
            
            row = cursor.fetchone()
            if row:
                return {
                    'min_price': row[0],
                    'max_price': row[1],
                    'avg_price': row[2],
                    'check_count': row[3],
                    'period_days': days
                }
            return {}
    
    # Alert Operations
    
    def create_alert(self, product_id: int, alert_type: str,
                    old_price: float = None, new_price: float = None,
                    message: str = None) -> int:
        """Create a new alert"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO alerts (product_id, alert_type, old_price, new_price, message)
                VALUES (?, ?, ?, ?, ?)
            ''', (product_id, alert_type, old_price, new_price, message))
            return cursor.lastrowid
    
    def get_unsent_alerts(self, limit: int = None) -> List[Dict]:
        """Get alerts that haven't been sent"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = '''
                SELECT a.*, p.name as product_name, p.url as product_url
                FROM alerts a
                JOIN products p ON a.product_id = p.id
                WHERE a.notified = 0
                ORDER BY a.timestamp DESC
            '''
            
            if limit:
                query += f' LIMIT {limit}'
            
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]
    
    def mark_alert_sent(self, alert_id: int) -> bool:
        """Mark an alert as sent"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE alerts SET notified = 1 WHERE id = ?
            ''', (alert_id,))
            return cursor.rowcount > 0
    
    def get_recent_alerts(self, product_id: int = None, 
                         days: int = 7, limit: int = 50) -> List[Dict]:
        """Get recent alerts"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cutoff_date = datetime.now() - timedelta(days=days)
            
            if product_id:
                cursor.execute('''
                    SELECT a.*, p.name as product_name, p.url as product_url
                    FROM alerts a
                    JOIN products p ON a.product_id = p.id
                    WHERE a.product_id = ? AND a.timestamp >= ?
                    ORDER BY a.timestamp DESC
                    LIMIT ?
                ''', (product_id, cutoff_date, limit))
            else:
                cursor.execute('''
                    SELECT a.*, p.name as product_name, p.url as product_url
                    FROM alerts a
                    JOIN products p ON a.product_id = p.id
                    WHERE a.timestamp >= ?
                    ORDER BY a.timestamp DESC
                    LIMIT ?
                ''', (cutoff_date, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # Cleanup Operations
    
    def cleanup_old_price_history(self, days: int = 90) -> int:
        """Delete price history older than specified days"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cutoff_date = datetime.now() - timedelta(days=days)
            
            cursor.execute('''
                DELETE FROM price_history WHERE timestamp < ?
            ''', (cutoff_date,))
            
            deleted_count = cursor.rowcount
            print(f"Deleted {deleted_count} old price history records")
            return deleted_count
    
    def cleanup_old_alerts(self, days: int = 30) -> int:
        """Delete alerts older than specified days"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cutoff_date = datetime.now() - timedelta(days=days)
            
            cursor.execute('''
                DELETE FROM alerts WHERE timestamp < ? AND notified = 1
            ''', (cutoff_date,))
            
            deleted_count = cursor.rowcount
            print(f"Deleted {deleted_count} old alerts")
            return deleted_count
    
    # Dashboard and Statistics
    
    def get_monitoring_summary(self) -> Dict:
        """Get summary of monitoring status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total active products
            cursor.execute('''
                SELECT COUNT(*) FROM products WHERE active = 1
            ''')
            total_products = cursor.fetchone()[0]
            
            # Products by status
            cursor.execute('''
                SELECT mc.status, COUNT(*) as count
                FROM monitoring_config mc
                JOIN products p ON mc.product_id = p.id
                WHERE p.active = 1
                GROUP BY mc.status
            ''')
            status_counts = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Recent alerts (last 24 hours)
            cursor.execute('''
                SELECT COUNT(*) FROM alerts 
                WHERE timestamp >= datetime('now', '-1 day')
            ''')
            recent_alerts = cursor.fetchone()[0]
            
            # Products with failures
            cursor.execute('''
                SELECT COUNT(*) FROM monitoring_config 
                WHERE failure_count > 0
            ''')
            products_with_failures = cursor.fetchone()[0]
            
            return {
                'total_products': total_products,
                'status_counts': status_counts,
                'recent_alerts_24h': recent_alerts,
                'products_with_failures': products_with_failures
            }


if __name__ == '__main__':
    # Test database manager
    db_manager = DatabaseManager()
    
    # Get monitoring summary
    summary = db_manager.get_monitoring_summary()
    print("Monitoring Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
