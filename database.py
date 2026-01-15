import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
import re

class ReceiptDatabase:
    def __init__(self, dbname, user, password, host='localhost', port=5432):
        """Initialize database connection"""
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.conn = None
    
    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
            print(f"✓ Connected to {self.dbname}")
        except psycopg2.Error as e:
            print(f"✗ Failed to connect: {e}")
            raise
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("✓ Connection closed")
    
    def parse_date(self, date_str):
        """
        Convert date string to YYYY-MM-DD format
        Handles: MM-DD-YYYY, DD-MM-YYYY, YYYY-MM-DD, etc.
        """
        if not date_str:
            return None
        
        try:
            # Try common formats
            for fmt in ['%m-%d-%Y', '%m-%d-%y', '%Y-%m-%d', '%d-%m-%Y']:
                try:
                    date_obj = datetime.strptime(date_str.strip(), fmt)
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
            print(f"⚠ Could not parse date: {date_str}")
            return None
        except Exception as e:
            print(f"⚠ Date parsing error: {e}")
            return None
    
    def parse_quantity(self, quantity_str):
        """
        Extract numeric quantity from strings like "3EA", "2", "0.41 lb"
        Returns: float or None
        """
        if not quantity_str:
            return None
        
        try:
            # Remove units like 'EA', 'lb', etc and extract number
            match = re.search(r'[\d.]+', str(quantity_str))
            if match:
                return float(match.group())
            return None
        except Exception as e:
            print(f"⚠ Quantity parsing error: {e}")
            return None
    
    def parse_price(self, price_str):
        """
        Extract numeric price from strings like "$1.29", "0.29/EA", "1.29"
        Returns: float or None
        """
        if not price_str:
            return None
        
        try:
            # Remove currency symbols and units, extract number
            match = re.search(r'[\d.]+', str(price_str))
            if match:
                return float(match.group())
            return None
        except Exception as e:
            print(f"⚠ Price parsing error: {e}")
            return None
    
    def insert_or_get_merchant(self, merchant_name, address=None, phone=None):
        """
        Insert merchant if not exists, return merchant_id
        """
        if not merchant_name:
            return None
        
        cur = self.conn.cursor()
        try:
            # Try to get existing merchant
            cur.execute(
                "SELECT merchant_id FROM merchant WHERE merchant_name = %s",
                (merchant_name,)
            )
            result = cur.fetchone()
            
            if result:
                return result[0]
            
            # Insert new merchant
            cur.execute(
                """INSERT INTO merchant (merchant_name, address, phone_number)
                   VALUES (%s, %s, %s) RETURNING merchant_id""",
                (merchant_name, address, phone)
            )
            merchant_id = cur.fetchone()[0]
            print(f"  ✓ Created merchant: {merchant_name}")
            return merchant_id
        except psycopg2.Error as e:
            print(f"  ✗ Error inserting merchant: {e}")
            return None
        finally:
            cur.close()
    
    def insert_or_get_product(self, product_description, category=None):
        """
        Insert product if not exists, return product_id
        """
        if not product_description:
            return None
        
        cur = self.conn.cursor()
        try:
            # Try to get existing product
            cur.execute(
                "SELECT product_id FROM product WHERE product_description = %s",
                (product_description,)
            )
            result = cur.fetchone()
            
            if result:
                return result[0]
            
            # Insert new product
            cur.execute(
                """INSERT INTO product (product_description, category)
                   VALUES (%s, %s) RETURNING product_id""",
                (product_description, category)
            )
            product_id = cur.fetchone()[0]
            return product_id
        except psycopg2.Error as e:
            print(f"  ✗ Error inserting product: {e}")
            return None
        finally:
            cur.close()
    
    def insert_receipt(self, receipt_data):
        """
        Insert a complete receipt (header + line items) into the database.
        
        receipt_data format:
        {
            'merchant': 'TRADER JOE\'S',
            'date': '06-28-2014',
            'items': [
                {'Description': 'BANANAS', 'TotalPrice': '0.99'},
                ...
            ],
            'subtotal': '$38.68',
            'tax': None,
            'total': '$38.68'
        }
        """
        cur = self.conn.cursor()
        
        try:
            # Parse and validate required fields
            merchant_name = receipt_data.get('merchant')
            transaction_date = self.parse_date(receipt_data.get('date'))
            subtotal = self.parse_price(receipt_data.get('subtotal'))
            tax = self.parse_price(receipt_data.get('tax'))
            total = self.parse_price(receipt_data.get('total'))
            items = receipt_data.get('items', [])
            
            if not merchant_name:
                print("✗ Receipt missing merchant name")
                return False
            
            if not transaction_date:
                print("✗ Receipt missing valid date")
                return False
            
            if not total:
                print("✗ Receipt missing total")
                return False
            
            # Insert merchant (or get existing)
            merchant_id = self.insert_or_get_merchant(merchant_name)
            if not merchant_id:
                print("✗ Failed to get/create merchant")
                return False
            
            # Insert receipt header
            cur.execute(
                """INSERT INTO receipt (merchant_id, transaction_date, subtotal, tax, total)
                   VALUES (%s, %s, %s, %s, %s) RETURNING receipt_id""",
                (merchant_id, transaction_date, subtotal, tax, total)
            )
            receipt_id = cur.fetchone()[0]
            print(f"✓ Created receipt #{receipt_id} from {merchant_name} on {transaction_date}")
            
            # Insert receipt items
            if not items:
                print("  ⚠ Receipt has no items")
                self.conn.commit()
                return True
            
            for item in items:
                description = item.get('Description')
                if not description:
                    continue
                
                # Parse item data
                quantity = self.parse_quantity(item.get('Quantity'))
                unit_price = self.parse_price(item.get('Price'))
                total_price = self.parse_price(item.get('TotalPrice'))
                
                if not total_price:
                    continue
                
                # If unit_price not available, calculate from total
                if not unit_price and quantity:
                    unit_price = total_price / quantity
                
                # If quantity not available, assume 1
                if not quantity:
                    quantity = 1
                
                # Get or create product
                product_id = self.insert_or_get_product(description)
                if not product_id:
                    print(f"  ⚠ Failed to insert product: {description}")
                    continue
                
                # Insert receipt item
                cur.execute(
                    """INSERT INTO receipt_item (receipt_id, product_id, quantity, unit_price, total_price)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (receipt_id, product_id, quantity, unit_price, total_price)
                )
            
            self.conn.commit()
            print(f"  ✓ Inserted {len(items)} items")
            return True
        
        except psycopg2.Error as e:
            self.conn.rollback()
            print(f"✗ Database error: {e}")
            return False
        except Exception as e:
            self.conn.rollback()
            print(f"✗ Unexpected error: {e}")
            return False
        finally:
            cur.close()
    
    def get_merchant_summary(self):
        """Get summary of merchants and spending"""
        cur = self.conn.cursor()
        try:
            cur.execute(
                """SELECT m.merchant_name, COUNT(r.receipt_id) as num_receipts, SUM(r.total) as total_spent
                   FROM receipt r
                   JOIN merchant m ON r.merchant_id = m.merchant_id
                   GROUP BY m.merchant_name
                   ORDER BY total_spent DESC"""
            )
            return cur.fetchall()
        finally:
            cur.close()
    
    def get_product_summary(self):
        """Get summary of most purchased products"""
        cur = self.conn.cursor()
        try:
            cur.execute(
                """SELECT p.product_description, COUNT(ri.receipt_item_id) as purchases, 
                          SUM(ri.total_price) as total_spent
                   FROM receipt_item ri
                   JOIN product p ON ri.product_id = p.product_id
                   GROUP BY p.product_description
                   ORDER BY purchases DESC
                   LIMIT 20"""
            )
            return cur.fetchall()
        finally:
            cur.close()