# product-truck-algo
# Receipt Inventory System

Automated receipt parsing and inventory database system using Azure Document Intelligence and PostgreSQL.

## Setup

### 1. Install Dependencies
```bash
pip install psycopg2-binary python-dotenv azure-ai-documentintelligence
```

### 2. Setup PostgreSQL
```bash
psql -U postgres
CREATE DATABASE receipt_inventory;
CREATE USER receipt_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE receipt_inventory TO receipt_user;
\q

psql -U receipt_user -d receipt_inventory -f schema_oltp.sql
```

### 3. Configure .env
```
AZURE_DOCUMENT_INTELLIGENCE_KEY=your_key
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=your_endpoint
DB_NAME=receipt_inventory
DB_USER=receipt_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

### 4. Run
```bash
python main_with_db.py
```

## Usage

Place receipt images in `data/receipts/` and run the script. It will:
- Parse receipts via Azure Document Intelligence
- Normalize data (prices, quantities, dates)
- Insert into PostgreSQL with validation
- Print merchant and product summaries

## Query Examples
```bash
# Most purchased items
psql -U receipt_user -d receipt_inventory -c "SELECT * FROM vw_product_frequency LIMIT 10;"

# Monthly spending by merchant
psql -U receipt_user -d receipt_inventory -c "SELECT * FROM vw_monthly_merchant_spending;"
```

## Files

- `azure_ocr.py` - Receipt parsing
- `database.py` - Database operations
- `main_with_db.py` - Main pipeline
- `schema_oltp.sql` - Database schema