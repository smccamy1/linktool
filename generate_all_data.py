#!/usr/bin/env python3
"""
Combined Data Generator
Generates both IDV data and insurance data in one script, ensuring all users have complete profiles.
"""

import argparse
import sys
from generate_idv_data import IDVDataGenerator, DataIngestor as IDVIngestor
from generate_insurance_data import InsuranceDataGenerator, DataIngestor as InsuranceIngestor


def main():
    parser = argparse.ArgumentParser(
        description='Generate complete dataset with IDV and insurance data'
    )
    parser.add_argument(
        '--num-users',
        type=int,
        default=50,
        help='Number of IDV users to generate (default: 50)'
    )
    parser.add_argument(
        '--mongo-uri',
        default='mongodb://localhost:27017/',
        help='MongoDB connection URI (default: mongodb://localhost:27017/)'
    )
    parser.add_argument(
        '--postgres-uri',
        default='postgresql://admin:postgrespass123@localhost:5432/insurance_db',
        help='PostgreSQL connection URI'
    )
    parser.add_argument(
        '--opensearch-host',
        default='localhost',
        help='OpenSearch host (default: localhost)'
    )
    parser.add_argument(
        '--opensearch-port',
        type=int,
        default=9200,
        help='OpenSearch port (default: 9200)'
    )
    parser.add_argument(
        '--opensearch-user',
        default='admin',
        help='OpenSearch username (default: admin)'
    )
    parser.add_argument(
        '--opensearch-password',
        default='admin',
        help='OpenSearch password (default: admin)'
    )
    parser.add_argument(
        '--skip-opensearch',
        action='store_true',
        help='Skip OpenSearch data ingestion'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("STEP 1: Generating IDV Data")
    print("=" * 60)
    
    # Generate IDV data
    try:
        idv_generator = IDVDataGenerator()
        print(f"Generating {args.num_users} IDV users with verifications and attempts...")
        data = idv_generator.generate_batch(args.num_users)
        
        print(f"Generated:")
        print(f"  - {len(data['user_profiles'])} users")
        print(f"  - {len(data['verifications'])} verifications")
        print(f"  - {len(data['attempts'])} attempts")
        
        # Ingest to MongoDB (and optionally OpenSearch)
        print("\nIngesting IDV data to MongoDB...")
        if args.skip_opensearch:
            # Connect to MongoDB only
            from pymongo import MongoClient
            mongo_client = MongoClient(args.mongo_uri)
            db = mongo_client['idv_data']
            
            # Clear existing data
            db.user_profiles.delete_many({})
            db.identity_verifications.delete_many({})
            db.verification_attempts.delete_many({})
            
            # Insert new data
            db.user_profiles.insert_many(data['user_profiles'])
            db.identity_verifications.insert_many(data['verifications'])
            db.verification_attempts.insert_many(data['attempts'])
            
            mongo_client.close()
            print("✓ IDV data ingested to MongoDB")
        else:
            idv_ingestor = IDVIngestor(
                args.mongo_uri,
                args.opensearch_host,
                args.opensearch_port,
                args.opensearch_user,
                args.opensearch_password
            )
            idv_ingestor.ingest_data(data)
            print("✓ IDV data ingested to MongoDB and OpenSearch")
        
    except Exception as e:
        print(f"✗ Error generating IDV data: {e}")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("STEP 2: Generating Insurance Data")
    print("=" * 60)
    
    # Generate insurance data for all IDV users
    try:
        print("Connecting to databases...")
        insurance_ingestor = InsuranceIngestor(args.mongo_uri, args.postgres_uri)
        
        # Clear existing insurance data
        print("Clearing existing insurance data from PostgreSQL...")
        cursor = insurance_ingestor.pg_conn.cursor()
        cursor.execute("TRUNCATE TABLE payments, dependents, claims, policies, customers RESTART IDENTITY CASCADE")
        insurance_ingestor.pg_conn.commit()
        cursor.close()
        print("✓ PostgreSQL cleared")
        
        print(f"Generating insurance data for all {args.num_users} IDV users...")
        insurance_ingestor.generate_and_insert_all(max_customers=None)
        
        insurance_ingestor.close()
        print("✓ Insurance data generation complete")
        
    except Exception as e:
        print(f"✗ Error generating insurance data: {e}")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✓ ALL DATA GENERATION COMPLETE")
    print("=" * 60)
    print(f"\nGenerated {args.num_users} complete user profiles with:")
    print("  - IDV verification data")
    print("  - Insurance customer records")
    print("  - Insurance policies")
    print("  - Claims history")
    print("  - Payment records")
    print("  - Dependent information")
    print("\nYou can now access the visualization at: http://localhost:5050")


if __name__ == '__main__':
    main()
