# Receipt Inventory - OLTP Schema Design

## Why OLTP (not OLAP)?

The system is primarily **transactional**:
- **Real-time inserts**: Scan a receipt, save it immediately
- **Corrections needed**: "Oops, that price was wrong, fix it"
- **Ad-hoc queries**: "What did I buy last week?"
- **Speed matters**: Process a receipt in milliseconds

Analytics are secondary—nice to have, but not the bottleneck.

## Schema Design (3NF - Third Normal Form)

```
┌──────────────┐
│   MERCHANT   │
├──────────────┤
│ merchant_id  │
│ name (UK)    │
│ address      │
│ phone        │
└──────┬───────┘
       │ 1..∞
       │
       ├─────────────┬─────────────┐
       │             │             │
     (FK)          (FK)          (FK)
       │             │             │
┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
│   RECEIPT   │  │   PRODUCT   │  │ RECEIPT_ITEM│
├─────────────┤  ├─────────────┤  ├─────────────┤
│receipt_id   │  │product_id   │  │receipt_item_│
│merchant_id  │  │description  │  │receipt_id   │
│date         │  │category     │  │product_id   │
│subtotal     │  │created_at   │  │quantity     │
│tax          │  │updated_at   │  │unit_price   │
│total        │  └─────────────┘  │total_price  │
└─────────────┘                     └─────────────┘
```

## Table Relationships

| Table | Role | Relationships |
|-------|------|--------------|
| **MERCHANT** | Reference data (vendors) | 1 merchant → ∞ receipts |
| **PRODUCT** | Reference data (items) | 1 product → ∞ receipt items |
| **RECEIPT** | Transaction header | 1 receipt → ∞ line items |
| **RECEIPT_ITEM** | Transactional fact | Many-to-many join |

## Why This Design is Better for OLTP

### 1. **Normalized (3NF) = Safe Updates**

If you fix a merchant's phone number, it changes in ONE place:
```sql
UPDATE merchant SET phone_number = '555-1234' WHERE merchant_id = 1;
```

Without normalization (snowflake with denormalized dim), you'd have to update hundreds of receipt rows.

### 2. **Fast Inserts**
```sql
-- Insert receipt: 1 row
INSERT INTO receipt (merchant_id, transaction_date, total) 
VALUES (1, '2024-12-07', 45.99);

-- Insert 18 items: 18 rows (no complex joins)
INSERT INTO receipt_item (receipt_id, product_id, quantity, unit_price, total_price) 
VALUES (1, 5, 1, 2.49, 2.49);
```

No pre-aggregations needed. Just insert and move on.

### 3. **Referential Integrity**
```sql
-- Can't insert a receipt for a merchant that doesn't exist
INSERT INTO receipt (merchant_id, ...) VALUES (999, ...);
-- ERROR: foreign key constraint violated

-- Can't delete a merchant with active receipts
DELETE FROM merchant WHERE merchant_id = 1;
-- ERROR: update or delete on table "receipt" violates foreign key
```

### 4. **Easy to Modify**
New requirement: "Add a category field to merchants"
```sql
ALTER TABLE merchant ADD COLUMN category VARCHAR(100);
```

With denormalized snowflake, you'd have to update every row in the fact table.

### 5. **Analytics Still Work**
You're not sacrificing analytical power—you just calculate on the fly:
```sql
-- What's the most popular item?
SELECT product_description, COUNT(*) as purchases
FROM receipt_item ri
JOIN product p ON ri.product_id = p.product_id
GROUP BY product_description
ORDER BY purchases DESC;
```

This query is fast because:
- RECEIPT_ITEM is indexed on product_id
- PRODUCT is indexed on product_id
- Only a simple join, no complex dimensions

## Key Differences from Snowflake

| Aspect | OLTP (This Design) | Snowflake (Previous) |
|--------|-------------------|---------------------|
| **Normalization** | 3NF (normalized) | Denormalized |
| **Duplicate data** | None | Many (denormalized dims) |
| **Update speed** | Fast (change one row) | Slow (change many rows) |
| **Insert speed** | Fast (simple) | Moderate (dimension lookups) |
| **Query complexity** | Join on-the-fly | Pre-aggregated tables |
| **Best for** | OLTP + light analytics | Heavy analytics |

## Indexes

Created for common access patterns:
- **Merchant lookups**: `merchant_name`
- **Receipt queries**: `transaction_date`, `merchant_id`
- **Product analytics**: `product_description`, `category`
- **Join efficiency**: All foreign keys indexed

## Views (Pre-built Analytical Queries)

Even though it's 3NF, I included views for quick analytics:

**vw_receipt_details** - See full receipt breakdown
```sql
SELECT * FROM vw_receipt_details 
WHERE merchant_name = 'TRADER JOES' AND transaction_date >= '2024-01-01';
```

**vw_product_frequency** - Which items purchased most
```sql
SELECT * FROM vw_product_frequency ORDER BY num_purchases DESC LIMIT 10;
```

**vw_monthly_merchant_spending** - Spending by vendor over time
```sql
SELECT * FROM vw_monthly_merchant_spending 
WHERE merchant_name = 'WALMART' ORDER BY month DESC;
```

## Summary

This OLTP design is:
- Fast for inserts/updates
- Safe (no anomalies)
- Easy to maintain
- Simple analytical queries still work
- Right-sized for your actual use case