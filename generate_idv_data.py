#!/usr/bin/env python3
"""
IDV (Identity Verification) Data Generator
Generates realistic fake identity verification data for testing purposes.
"""

import json
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List
import argparse

# Try to import faker, provide installation instructions if not available
try:
    from faker import Faker
except ImportError:
    print("Error: 'faker' library is required. Install it with:")
    print("  pip install faker")
    exit(1)

# Try to import pymongo, provide installation instructions if not available
try:
    from pymongo import MongoClient
except ImportError:
    print("Error: 'pymongo' library is required. Install it with:")
    print("  pip install pymongo")
    exit(1)

# Try to import opensearch-py
try:
    from opensearchpy import OpenSearch
except ImportError:
    print("Error: 'opensearch-py' library is required. Install it with:")
    print("  pip install opensearch-py")
    exit(1)


class IDVDataGenerator:
    """Generate fake identity verification data."""
    
    def __init__(self, locale='en_US'):
        self.faker = Faker(locale)
        self.verification_statuses = [
            'pending', 'approved', 'rejected', 'under_review', 
            'needs_additional_info', 'expired', 'cancelled'
        ]
        self.document_types = [
            'passport', 'drivers_license', 'national_id', 
            'residence_permit', 'voter_id'
        ]
        self.verification_methods = [
            'manual_review', 'automated', 'hybrid', 'video_call'
        ]
        self.rejection_reasons = [
            'document_expired', 'poor_image_quality', 'document_mismatch',
            'fraudulent_document', 'underage', 'sanctions_list_match',
            'incomplete_information'
        ]
        self.risk_levels = ['low', 'medium', 'high', 'critical']
        
    def generate_user_profile(self) -> Dict:
        """Generate a fake user profile."""
        user_id = str(uuid.uuid4())
        return {
            'userId': user_id,
            'email': self.faker.email(),
            'firstName': self.faker.first_name(),
            'lastName': self.faker.last_name(),
            'dateOfBirth': self.faker.date_of_birth(minimum_age=18, maximum_age=80).isoformat(),
            'phone': self.faker.phone_number(),
            'address': {
                'street': self.faker.street_address(),
                'city': self.faker.city(),
                'state': self.faker.state(),
                'zipCode': self.faker.zipcode(),
                'country': self.faker.country_code()
            },
            'createdAt': self.faker.date_time_between(start_date='-2y', end_date='now').isoformat(),
            'lastUpdated': datetime.utcnow().isoformat()
        }
    
    def generate_verification_attempt(self, verification_id: str, attempt_number: int) -> Dict:
        """Generate a verification attempt record."""
        return {
            'attemptId': str(uuid.uuid4()),
            'verificationId': verification_id,
            'attemptNumber': attempt_number,
            'timestamp': self.faker.date_time_between(start_date='-30d', end_date='now').isoformat(),
            'ipAddress': self.faker.ipv4(),
            'userAgent': self.faker.user_agent(),
            'location': {
                'latitude': float(self.faker.latitude()),
                'longitude': float(self.faker.longitude()),
                'city': self.faker.city(),
                'country': self.faker.country_code()
            },
            'deviceFingerprint': self.faker.sha256(),
            'duration': random.randint(30, 600)  # seconds
        }
    
    def generate_identity_verification(self, user_id: str = None) -> Dict:
        """Generate a complete identity verification record."""
        if user_id is None:
            user_id = str(uuid.uuid4())
        
        verification_id = str(uuid.uuid4())
        status = random.choice(self.verification_statuses)
        document_type = random.choice(self.document_types)
        method = random.choice(self.verification_methods)
        
        # Generate base verification data
        verification = {
            'verificationId': verification_id,
            'userId': user_id,
            'status': status,
            'riskLevel': random.choice(self.risk_levels),
            'verificationMethod': method,
            'documentType': document_type,
            'documentNumber': self.faker.bothify(text='??########'),
            'documentIssuingCountry': self.faker.country_code(),
            'documentExpiryDate': self.faker.date_between(start_date='today', end_date='+10y').isoformat(),
            'submittedAt': self.faker.date_time_between(start_date='-60d', end_date='now').isoformat(),
            'reviewedAt': None,
            'reviewedBy': None,
            'processingTime': None,
            'confidence_score': round(random.uniform(0.0, 1.0), 3),
            'biometric_match_score': round(random.uniform(0.5, 1.0), 3) if random.random() > 0.3 else None,
            'liveness_check_passed': random.choice([True, False, None]),
            'sanctions_check_passed': random.choice([True, False]),
            'pep_check_passed': random.choice([True, False]),
            'aml_check_passed': random.choice([True, False]),
            'metadata': {
                'frontImageQuality': round(random.uniform(0.5, 1.0), 2),
                'backImageQuality': round(random.uniform(0.5, 1.0), 2),
                'selfieImageQuality': round(random.uniform(0.5, 1.0), 2) if random.random() > 0.2 else None,
                'ocrConfidence': round(random.uniform(0.7, 1.0), 2),
                'documentAuthenticity': round(random.uniform(0.6, 1.0), 2)
            },
            'flags': []
        }
        
        # Add status-specific fields
        if status in ['approved', 'rejected', 'expired']:
            verification['reviewedAt'] = (
                datetime.fromisoformat(verification['submittedAt']) + 
                timedelta(minutes=random.randint(5, 4320))
            ).isoformat()
            verification['reviewedBy'] = f"reviewer_{random.randint(1, 50)}"
            submitted_time = datetime.fromisoformat(verification['submittedAt'])
            reviewed_time = datetime.fromisoformat(verification['reviewedAt'])
            verification['processingTime'] = int((reviewed_time - submitted_time).total_seconds())
        
        if status == 'rejected':
            verification['rejectionReason'] = random.choice(self.rejection_reasons)
            verification['rejectionDetails'] = self.faker.sentence()
        
        # Add random flags
        possible_flags = [
            'age_mismatch', 'address_mismatch', 'name_mismatch',
            'expired_document', 'low_quality_image', 'multiple_attempts',
            'suspicious_activity', 'proxy_detected'
        ]
        if random.random() > 0.7:
            verification['flags'] = random.sample(possible_flags, random.randint(1, 3))
        
        return verification
    
    def generate_batch(self, count: int) -> Dict[str, List]:
        """Generate a batch of related IDV data."""
        user_profiles = []
        verifications = []
        attempts = []
        
        for _ in range(count):
            # Generate user profile
            user_profile = self.generate_user_profile()
            user_profiles.append(user_profile)
            
            # Generate 1-3 verifications per user
            num_verifications = random.randint(1, 3)
            for _ in range(num_verifications):
                verification = self.generate_identity_verification(user_profile['userId'])
                verifications.append(verification)
                
                # Generate 1-5 attempts per verification
                num_attempts = random.randint(1, 5)
                for attempt_num in range(1, num_attempts + 1):
                    attempt = self.generate_verification_attempt(
                        verification['verificationId'], 
                        attempt_num
                    )
                    attempts.append(attempt)
        
        return {
            'user_profiles': user_profiles,
            'verifications': verifications,
            'attempts': attempts
        }


class DataIngestor:
    """Ingest generated data into MongoDB and OpenSearch."""
    
    def __init__(self, mongo_uri: str, opensearch_host: str, opensearch_port: int,
                 opensearch_user: str, opensearch_password: str):
        # MongoDB connection
        self.mongo_client = MongoClient(mongo_uri)
        self.db = self.mongo_client['idv_data']
        
        # OpenSearch connection
        self.opensearch = OpenSearch(
            hosts=[{'host': opensearch_host, 'port': opensearch_port}],
            http_auth=(opensearch_user, opensearch_password),
            use_ssl=True,
            verify_certs=False,
            ssl_show_warn=False
        )
        
        # Create OpenSearch indices if they don't exist
        self._setup_opensearch_indices()
    
    def _setup_opensearch_indices(self):
        """Create OpenSearch indices with appropriate mappings."""
        verification_mapping = {
            "mappings": {
                "properties": {
                    "verificationId": {"type": "keyword"},
                    "userId": {"type": "keyword"},
                    "status": {"type": "keyword"},
                    "riskLevel": {"type": "keyword"},
                    "verificationMethod": {"type": "keyword"},
                    "documentType": {"type": "keyword"},
                    "submittedAt": {"type": "date"},
                    "reviewedAt": {"type": "date"},
                    "confidence_score": {"type": "float"},
                    "biometric_match_score": {"type": "float"},
                    "processingTime": {"type": "integer"},
                    "flags": {"type": "keyword"}
                }
            }
        }
        
        if not self.opensearch.indices.exists(index='idv_verifications'):
            self.opensearch.indices.create(index='idv_verifications', body=verification_mapping)
            print("Created OpenSearch index: idv_verifications")
    
    def ingest_data(self, data: Dict[str, List]):
        """Ingest data into MongoDB and OpenSearch."""
        # Insert into MongoDB
        if data['user_profiles']:
            self.db.user_profiles.insert_many(data['user_profiles'])
            print(f"Inserted {len(data['user_profiles'])} user profiles into MongoDB")
        
        if data['verifications']:
            self.db.identity_verifications.insert_many(data['verifications'])
            print(f"Inserted {len(data['verifications'])} verifications into MongoDB")
            
            # Also index verifications in OpenSearch
            for verification in data['verifications']:
                self.opensearch.index(
                    index='idv_verifications',
                    id=verification['verificationId'],
                    body=verification
                )
            print(f"Indexed {len(data['verifications'])} verifications in OpenSearch")
        
        if data['attempts']:
            self.db.verification_attempts.insert_many(data['attempts'])
            print(f"Inserted {len(data['attempts'])} verification attempts into MongoDB")
    
    def close(self):
        """Close database connections."""
        self.mongo_client.close()


def main():
    parser = argparse.ArgumentParser(
        description='Generate fake IDV (Identity Verification) data'
    )
    parser.add_argument(
        '-n', '--num-users',
        type=int,
        default=100,
        help='Number of users to generate (default: 100)'
    )
    parser.add_argument(
        '--mongo-uri',
        default='mongodb://admin:mongopass123@localhost:27017/',
        help='MongoDB connection URI'
    )
    parser.add_argument(
        '--opensearch-host',
        default='localhost',
        help='OpenSearch host'
    )
    parser.add_argument(
        '--opensearch-port',
        type=int,
        default=9200,
        help='OpenSearch port'
    )
    parser.add_argument(
        '--opensearch-user',
        default='admin',
        help='OpenSearch username'
    )
    parser.add_argument(
        '--opensearch-password',
        default='Admin123!',
        help='OpenSearch password'
    )
    parser.add_argument(
        '--json-output',
        type=str,
        help='Output data to JSON file instead of database'
    )
    
    args = parser.parse_args()
    
    print(f"Generating IDV data for {args.num_users} users...")
    generator = IDVDataGenerator()
    data = generator.generate_batch(args.num_users)
    
    print(f"Generated:")
    print(f"  - {len(data['user_profiles'])} user profiles")
    print(f"  - {len(data['verifications'])} verifications")
    print(f"  - {len(data['attempts'])} verification attempts")
    
    if args.json_output:
        # Save to JSON file
        with open(args.json_output, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\nData saved to {args.json_output}")
    else:
        # Ingest into databases
        print("\nIngesting data into databases...")
        ingestor = DataIngestor(
            args.mongo_uri,
            args.opensearch_host,
            args.opensearch_port,
            args.opensearch_user,
            args.opensearch_password
        )
        ingestor.ingest_data(data)
        ingestor.close()
        print("\nData ingestion completed successfully!")


if __name__ == '__main__':
    main()
