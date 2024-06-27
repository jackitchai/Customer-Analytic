CREATE SCHEMA IF NOT EXISTS customer_schema;

DROP TABLE IF EXISTS customer_schema.customer_table;

CREATE TABLE customer_schema.customer_table (
    InvoiceNo TEXT,
    StockCode TEXT,
    "Description" TEXT,
    Quantity INT,
    InvoiceDate TIMESTAMP,
    UnitPrice FLOAT,
    CustomerID TEXT,
    Country TEXT
);

-- COPY customer_schema.customer_table
-- FROM '/data/cleaned_data.csv' DELIMITER ',' CSV HEADER;