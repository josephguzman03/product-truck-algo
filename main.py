from dotenv import load_dotenv
import os
from azure_ocr import AzureReceiptParser
from database import ReceiptDatabase
import json

load_dotenv()

def main():
    # Get Azure credentials
    api_key = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_KEY')
    endpoint = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT')
    
    if not api_key or not endpoint:
        print("ERROR: Missing Azure credentials in .env")
        return
    
    # Get database credentials
    db_name = os.getenv('DB_NAME', 'receipt_inventory')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = int(os.getenv('DB_PORT', 5432))
    
    if not db_password:
        print("ERROR: Missing DB_PASSWORD in .env")
        return
    
    # Initialize parser and database
    parser = AzureReceiptParser(api_key=api_key, endpoint=endpoint)
    db = ReceiptDatabase(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port
    )
    
    # Connect to database
    db.connect()
    
    try:
        # Process receipts
        receipt_paths = [
            'data/receipts/0.jpg',
            'data/receipts/1.jpg',
            # Add more receipt paths as needed
        ]
        
        print("\n=== PROCESSING RECEIPTS ===\n")
        
        for receipt_path in receipt_paths:
            if not os.path.exists(receipt_path):
                print(f"⚠ File not found: {receipt_path}")
                continue
            
            print(f"Processing: {receipt_path}")
            
            # Parse receipt
            receipt_data = parser.process_receipt(receipt_path)
            
            # Save to JSON for inspection
            json_output = receipt_path.replace('.jpg', '_output.json')
            parser.save_to_json(receipt_data, json_output)
            print(f"  ✓ Saved JSON: {json_output}")
            
            # Insert into database
            if db.insert_receipt(receipt_data):
                print(f"  ✓ Successfully inserted to database")
            else:
                print(f"  ✗ Failed to insert to database")
            
            print()
        
        # Print summaries
        print("\n=== MERCHANT SUMMARY ===\n")
        merchants = db.get_merchant_summary()
        for merchant, num_receipts, total_spent in merchants:
            print(f"{merchant:20} | {num_receipts:3} receipts | ${total_spent:8.2f}")
        
        print("\n=== TOP PRODUCTS ===\n")
        products = db.get_product_summary()
        for product, purchases, total_spent in products:
            print(f"{product[:40]:40} | {purchases:2} purchases | ${total_spent:7.2f}")
    
    finally:
        db.close()

if __name__ == "__main__":
    main()