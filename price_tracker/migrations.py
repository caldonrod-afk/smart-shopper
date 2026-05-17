"""
Database Migration Script for Real-Time Price Tracking
Adds new tables: monitoring_config and updates existing tables
"""

import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager


class DatabaseMigration:
    """Handles database schema migrations"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            home = os.path.expanduser("~")
            data_dir = os.path.join(home, 'price-tracker', 'data')
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, 'price_tracker.db')
        
        self.db_path = db_path
        self.backup_path = db_path + '.backup'
    
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
    
    def backup_database(self) -> bool:
        """Create backup of database before migration"""
        try:
            import shutil
            if os.path.exists(self.db_path):
                shutil.copy2(self.db_path, self.backup_path)
                print(f"Database backed up to: {self.backup_path}")
                return True
            return False
        except Exception as e:
            print(f"Failed to backup database: {e}")
            return False
    
    def table_exists(self, conn, table_name: str) -> bool:
        """Check if a table exists"""
        cursor = conn.cursor()
        cursor.execute('''
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        ''', (table_name,))
        return cursor.fetchone() is not None
    
    def index_exists(self, conn, index_name: str) -> bool:
        """Check if an index exists"""
        cursor = conn.cursor()
        cursor.execute('''
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name=?
        ''', (index_name,))
        return cursor.fetchone() is not None
    
    def migrate(self) -> bool:
        """Run all migrations"""
        print("Starting database migration...")
        
        # Create backup
        if not self.backup_database():
            print("Warning: Could not create backup, proceeding anyway...")
        
        try:
            with self.get_connection() as conn:
                # Add monitoring_config table
                if not self.table_exists(conn, 'monitoring_config'):
                    self._create_monitoring_config_table(conn)
                else:
                    print("Table 'monitoring_config' already exists, skipping...")
                
                # Update price_history table if needed
                self._update_price_history_table(conn)
                
                # Update alerts table if needed
                self._update_alerts_table(conn)
                
                # Create indexes
                self._create_indexes(conn)
                
                print("Migration completed successfully!")
                return True
                
        except Exception as e:
            print(f"Migration failed: {e}")
            print("You can restore from backup if needed")
            return False
    
    def _create_monitoring_config_table(self, conn):
        """Create monitoring_config table"""
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE monitoring_config (
                product_id INTEGER PRIMARY KEY,
                interval_minutes INTEGER NOT NULL DEFAULT 60,
                last_check DATETIME,
                next_check DATETIME,
                status TEXT DEFAULT 'active',
                failure_count INTEGER DEFAULT 0,
                backoff_until DATETIME,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            )
        ''')
        
        print("Created table: monitoring_config")
        
        # Initialize monitoring config for existing products
        cursor.execute('''
            INSERT INTO monitoring_config (product_id, interval_minutes, status)
            SELECT id, 60, 'active' FROM products WHERE active = 1
        ''')
        
        print(f"Initialized monitoring config for {cursor.rowcount} products")
    
    def _update_price_history_table(self, conn):
        """Update price_history table if needed"""
        cursor = conn.cursor()
        
        # Check if source column exists
        cursor.execute("PRAGMA table_info(price_history)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'source' not in columns:
            # SQLite doesn't support ADD COLUMN with constraints easily
            # So we'll create a new table and migrate data
            print("Updating price_history table...")
            
            cursor.execute('''
                CREATE TABLE price_history_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    price REAL NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    source TEXT,
                    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
                )
            ''')
            
            cursor.execute('''
                INSERT INTO price_history_new (id, product_id, price, timestamp, source)
                SELECT id, product_id, price, timestamp, NULL FROM price_history
            ''')
            
            cursor.execute('DROP TABLE price_history')
            cursor.execute('ALTER TABLE price_history_new RENAME TO price_history')
            
            print("Updated price_history table")
        else:
            print("price_history table already up to date")
    
    def _update_alerts_table(self, conn):
        """Update alerts table if needed"""
        cursor = conn.cursor()
        
        # Check current columns
        cursor.execute("PRAGMA table_info(alerts)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Check if we need to update the table structure
        required_columns = ['id', 'product_id', 'alert_type', 'old_price', 
                          'new_price', 'timestamp', 'notified']
        
        if 'timestamp' not in columns or 'notified' not in columns:
            print("Updating alerts table...")
            
            # Create new table with updated schema
            cursor.execute('''
                CREATE TABLE alerts_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    alert_type TEXT NOT NULL,
                    old_price REAL,
                    new_price REAL,
                    message TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    notified BOOLEAN DEFAULT 0,
                    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
                )
            ''')
            
            # Migrate existing data
            cursor.execute('''
                INSERT INTO alerts_new (id, product_id, alert_type, old_price, 
                                       new_price, message, timestamp, notified)
                SELECT id, product_id, alert_type, old_price, new_price, 
                       message, sent_at, email_sent
                FROM alerts
            ''')
            
            cursor.execute('DROP TABLE alerts')
            cursor.execute('ALTER TABLE alerts_new RENAME TO alerts')
            
            print("Updated alerts table")
        else:
            print("alerts table already up to date")
    
    def _create_indexes(self, conn):
        """Create performance indexes"""
        cursor = conn.cursor()
        
        indexes = [
            ('idx_price_history_product_time', 
             'CREATE INDEX IF NOT EXISTS idx_price_history_product_time ON price_history(product_id, timestamp DESC)'),
            ('idx_monitoring_config_status', 
             'CREATE INDEX IF NOT EXISTS idx_monitoring_config_status ON monitoring_config(status)'),
            ('idx_alerts_product_time', 
             'CREATE INDEX IF NOT EXISTS idx_alerts_product_time ON alerts(product_id, timestamp DESC)'),
            ('idx_alerts_notified', 
             'CREATE INDEX IF NOT EXISTS idx_alerts_notified ON alerts(notified)'),
        ]
        
        for index_name, sql in indexes:
            if not self.index_exists(conn, index_name):
                cursor.execute(sql)
                print(f"Created index: {index_name}")
            else:
                print(f"Index '{index_name}' already exists")
    
    def rollback(self) -> bool:
        """Rollback to backup database"""
        try:
            if os.path.exists(self.backup_path):
                import shutil
                shutil.copy2(self.backup_path, self.db_path)
                print(f"Database restored from backup: {self.backup_path}")
                return True
            else:
                print("No backup file found")
                return False
        except Exception as e:
            print(f"Failed to rollback: {e}")
            return False


if __name__ == '__main__':
    # Run migration
    migration = DatabaseMigration()
    success = migration.migrate()
    
    if success:
        print("\n✓ Migration completed successfully!")
    else:
        print("\n✗ Migration failed!")
        print("To rollback, run: migration.rollback()")
