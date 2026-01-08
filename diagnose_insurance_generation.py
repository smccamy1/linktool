#!/usr/bin/env python3
"""
Insurance Data Generation Diagnostic
Helps troubleshoot why insurance data isn't being generated.
"""

import sys

try:
    from generate_insurance_data import DataIngestor
except ImportError as e:
    print(f"Error: Cannot import required modules: {e}")
    sys.exit(1)

def main():
    print("=" * 60)
    print("Insurance Data Generation Diagnostic")
    print("=" * 60)
    print()
    
    try:
        print("[1/5] Connecting to databases...")
        ingestor = DataIngestor(
            'mongodb://localhost:27017/', 
            'postgresql://admin:postgrespass123@localhost:5432/insurance_db'
        )
        print("✓ Connected successfully")
        print()
        
        print("[2/5] Checking MongoDB for IDV users...")
        users = ingestor.get_idv_users()
        print(f"✓ Found {len(users)} IDV users")
        if users:
            print(f"  Sample user: {users[0].get('email', 'N/A')}")
        else:
            print("✗ ERROR: No IDV users found!")
            print("  Run: python3 generate_all_data.py --num-users 50")
            ingestor.close()
            sys.exit(1)
        print()
        
        print("[3/5] Checking PostgreSQL for insurance products...")
        products = ingestor.get_product_ids()
        print(f"✓ Found {len(products)} active products")
        if not products:
            print("✗ ERROR: No insurance products found!")
            print("  Products should be created by postgres-init.sql")
            print("  Check: docker exec lynx-postgres psql -U admin -d insurance_db -c 'SELECT COUNT(*) FROM products;'")
            ingestor.close()
            sys.exit(1)
        print()
        
        print("[4/5] Checking existing insurance data...")
        ingestor.pg_cursor.execute("SELECT COUNT(*) FROM customers")
        customer_count = ingestor.pg_cursor.fetchone()[0]
        print(f"  Current customers: {customer_count}")
        
        ingestor.pg_cursor.execute("SELECT COUNT(*) FROM policies")
        policy_count = ingestor.pg_cursor.fetchone()[0]
        print(f"  Current policies: {policy_count}")
        
        ingestor.pg_cursor.execute("SELECT COUNT(*) FROM claims")
        claim_count = ingestor.pg_cursor.fetchone()[0]
        print(f"  Current claims: {claim_count}")
        print()
        
        print("[5/5] Attempting to generate insurance data...")
        print(f"Processing {len(users)} users...")
        ingestor.generate_and_insert_all()
        print()
        
        print("=" * 60)
        print("✓ Insurance Data Generation Complete!")
        print("=" * 60)
        print()
        
        # Verify data was inserted
        ingestor.pg_cursor.execute("SELECT COUNT(*) FROM customers")
        new_customer_count = ingestor.pg_cursor.fetchone()[0]
        print(f"Customers in database: {new_customer_count}")
        
        ingestor.pg_cursor.execute("SELECT COUNT(*) FROM policies")
        new_policy_count = ingestor.pg_cursor.fetchone()[0]
        print(f"Policies in database: {new_policy_count}")
        
        ingestor.pg_cursor.execute("SELECT COUNT(*) FROM claims")
        new_claim_count = ingestor.pg_cursor.fetchone()[0]
        print(f"Claims in database: {new_claim_count}")
        
        ingestor.close()
        print()
        print("Next steps:")
        print("  1. Verify linkage: ./verify_data_linkage.sh")
        print("  2. Restart web UI: docker restart lynx-web-ui")
        print("  3. Access UI: http://localhost:5050")
        
    except Exception as e:
        print()
        print("=" * 60)
        print("✗ ERROR OCCURRED")
        print("=" * 60)
        print(f"Error: {e}")
        print()
        print("Full traceback:")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
