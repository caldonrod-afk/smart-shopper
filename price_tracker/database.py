"""
Database Handler for Price Tracker
Manages product storage, price history, and alerts
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from contextlib import contextmanager
import os


class Database:
    """SQLite database handler for price tracking"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            home = os.path.expanduser("~")
            data_dir = os.path.join(home, 'price-tracker', 'data')
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, 'price_tracker.db')
        
        self.db_path = db_path
        self._init_database()
    
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
    
    def _init_database(self):
        """Create database tables if they don't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Products table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    name TEXT,
                    target_price REAL NOT NULL,
                    current_price REAL,
                    lowest_price REAL,
                    highest_price REAL,
                    last_checked TIMESTAMP,
                    alert_sent BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    active BOOLEAN DEFAULT 1,
                    website TEXT,
                    product_id TEXT,
                    currency TEXT DEFAULT 'INR'
                )
            ''')
            
            # Price history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    price REAL NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    source TEXT,
                    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
                )
            ''')
            
            # Alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    alert_type TEXT NOT NULL,
                    old_price REAL,
                    new_price REAL,
                    message TEXT,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    email_sent BOOLEAN DEFAULT 0,
                    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
                )
            ''')
            
            # Create indexes
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_products_url 
                ON products(url)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_price_history_product 
                ON price_history(product_id, timestamp DESC)
            ''')
            
            print("Database initialized successfully")
    
    def add_product(self, url: str, target_price: float, name: str = None,
                   website: str = None, product_id: str = None) -> int:
        """Add a new product to track"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT INTO products (url, name, target_price, website, product_id)
                    VALUES (?, ?, ?, ?, ?)
                ''', (url, name, target_price, website, product_id))
                
                product_id = cursor.lastrowid
                print(f"Product added: {name or url} (ID: {product_id})")
                return product_id
                
            except sqlite3.IntegrityError:
                print(f"Product already exists: {url}")
                cursor.execute('SELECT id FROM products WHERE url = ?', (url,))
                return cursor.fetchone()[0]
    
    def get_product(self, product_id: int) -> Optional[Dict]:
        """Get product by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_product_by_url(self, url: str) -> Optional[Dict]:
        """Get product by URL"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM products WHERE url = ?', (url,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_products(self, active_only: bool = True) -> List[Dict]:
        """Get all products"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if active_only:
                cursor.execute('SELECT * FROM products WHERE active = 1')
            else:
                cursor.execute('SELECT * FROM products')
            
            return [dict(row) for row in cursor.fetchall()]
    
    def update_product_price(self, product_id: int, price: float, 
                           source: str = None) -> bool:
        """Update product's current price and add to history"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get current product data
            cursor.execute('''
                SELECT current_price, lowest_price, highest_price, target_price, name
                FROM products WHERE id = ?
            ''', (product_id,))
            
            row = cursor.fetchone()
            if not row:
                return False
            
            current_price, lowest, highest, target, name = row
            
            # Update lowest and highest prices
            new_lowest = min(price, lowest) if lowest else price
            new_highest = max(price, highest) if highest else price
            
            # Update product
            cursor.execute('''
                UPDATE products 
                SET current_price = ?,
                    lowest_price = ?,
                    highest_price = ?,
                    last_checked = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (price, new_lowest, new_highest, product_id))
            
            # Add to price history
            cursor.execute('''
                INSERT INTO price_history (product_id, price, source)
                VALUES (?, ?, ?)
            ''', (product_id, price, source))
            
            # Check if alert should be sent
            if price <= target:
                if not current_price or price < current_price:
                    message = f"Price dropped to Rs.{price:.2f} (target: Rs.{target:.2f})"
                    cursor.execute('''
                        INSERT INTO alerts (product_id, alert_type, old_price, new_price, message)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (product_id, 'price_drop', current_price, price, message))
            
            print(f"Updated price for {name}: Rs.{price:.2f}")
            return True
    
    def update_product(self, product_id: int, **kwargs) -> bool:
        """Update product fields"""
        if not kwargs:
            return False
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            fields = ', '.join([f"{k} = ?" for k in kwargs.keys()])
            values = list(kwargs.values()) + [product_id]
            
            cursor.execute(f'''
                UPDATE products 
                SET {fields}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', values)
            
            return cursor.rowcount > 0
    
    def delete_product(self, product_id: int) -> bool:
        """Delete product"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
            return cursor.rowcount > 0
    
    def get_price_history(self, product_id: int, days: int = 30) -> List[Dict]:
        """Get price history for a product"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            cursor.execute('''
                SELECT * FROM price_history
                WHERE product_id = ? AND timestamp >= ?
                ORDER BY timestamp DESC
            ''', (product_id, cutoff_date))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_unsent_alerts(self) -> List[Dict]:
        """Get alerts that haven't been sent yet"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT a.*, p.name as product_name, p.url as product_url
                FROM alerts a
                JOIN products p ON a.product_id = p.id
                WHERE a.email_sent = 0
                ORDER BY a.sent_at DESC
            ''')
            
            return [dict(row) for row in cursor.fetchall()]
    
    def mark_alert_sent(self, alert_id: int) -> bool:
        """Mark alert as sent"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE alerts SET email_sent = 1 WHERE id = ?', (alert_id,))
            return cursor.rowcount > 0
    
    def get_dashboard_summary(self) -> Dict:
        """Get summary data for dashboard"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total products
            cursor.execute('SELECT COUNT(*) FROM products WHERE active = 1')
            total_products = cursor.fetchone()[0]
            
            # Products with price drops
            cursor.execute('''
                SELECT COUNT(*) FROM products 
                WHERE active = 1 AND current_price <= target_price
            ''')
            price_drops = cursor.fetchone()[0]
            
            # Recent alerts (last 7 days)
            cursor.execute('''
                SELECT COUNT(*) FROM alerts 
                WHERE sent_at >= datetime('now', '-7 days')
            ''')
            recent_alerts = cursor.fetchone()[0]
            
            return {
                'total_products': total_products,
                'price_drops': price_drops,
                'recent_alerts': recent_alerts
            }
    
    def export_to_json(self, filepath: str):
        """Export all products to JSON file"""
        products = self.get_all_products(active_only=False)
        
        with open(filepath, 'w') as f:
            json.dump(products, f, indent=2, default=str)
        
        print(f"Exported {len(products)} products to {filepath}")
    
    def import_from_json(self, filepath: str):
        """Import products from JSON file"""
        with open(filepath, 'r') as f:
            products = json.load(f)
        
        count = 0
        for product in products:
            try:
                self.add_product(
                    url=product['url'],
                    target_price=product.get('warn_price', product.get('target_price')),
                    name=product.get('name')
                )
                count += 1
            except Exception as e:
                print(f"Failed to import {product.get('url')}: {e}")
        
        print(f"Imported {count} products")


if __name__ == '__main__':
    # Test database
    db = Database()
    
    # Add sample product
    product_id = db.add_product(
        url='https://www.amazon.in/dp/B09G9HD6PD',
        target_price=25000,
        name='Sample Laptop'
    )
    
    # Get summary
    summary = db.get_dashboard_summary()
    print("\nDashboard Summary:")
    print(json.dumps(summary, indent=2))
