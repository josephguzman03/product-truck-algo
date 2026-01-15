import sqlite3
import os

'''
Creates the database file if it doesn't exist
Sets up tables with proper structure
Ensures data folder exists so the app doesn't crash
'''

class DatabaseConfig:
    def __init__(self, db_path="data/receipt_database.db"):
        self.db_path = db_path
        self.ensure_data_directory()
        self.init_database()
    
    def ensure_data_directory(self):
        """Create data directory if it doesn't exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def init_database(self):
        """Initialize database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create receipts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                raw_text TEXT,
                total_amount REAL,
                store_name TEXT
            )
        ''')
        
        # Create receipt_items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS receipt_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_id INTEGER,
                item_name TEXT,
                quantity REAL,
                price REAL,
                line_total REAL,
                FOREIGN KEY (receipt_id) REFERENCES receipts (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"Database initialized at: {self.db_path}")
