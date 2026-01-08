#!/bin/bash
#
# Fix PostgreSQL Schema - Expand VARCHAR columns
# Run this if you get "value too long for character varying" errors
#

echo "Fixing PostgreSQL schema column lengths..."

docker exec lynx-postgres psql -U admin -d insurance_db << 'EOF'
-- Expand state column from VARCHAR(2) to VARCHAR(50)
ALTER TABLE customers ALTER COLUMN state TYPE VARCHAR(50);

-- Expand customer_number from VARCHAR(20) to VARCHAR(50)
ALTER TABLE customers ALTER COLUMN customer_number TYPE VARCHAR(50);

-- Expand phone from VARCHAR(20) to VARCHAR(50)
ALTER TABLE customers ALTER COLUMN phone TYPE VARCHAR(50);

-- Verify changes
SELECT 
    column_name, 
    data_type, 
    character_maximum_length 
FROM information_schema.columns 
WHERE table_name = 'customers' 
    AND column_name IN ('state', 'customer_number', 'phone')
ORDER BY column_name;
EOF

echo ""
echo "✓ Schema updated successfully!"
echo ""
echo "Now regenerate insurance data:"
echo "  source venv/bin/activate"
echo "  python3 diagnose_insurance_generation.py"
echo "  deactivate"
