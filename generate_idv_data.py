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
            'failed_risk_rules', 'suspicious_ip', 'high_velocity_detected',
            'suspicious_user_agent', 'impossible_travel', 'multiple_failed_attempts',
            'blacklisted_ip'
        ]
        self.risk_levels = ['low', 'medium', 'high', 'critical']
        self.risk_rules = [
            'multiple_accounts_same_ip',
            'high_velocity_ip',
            'suspicious_user_agent',
            'impossible_travel',
            'unusual_login_time',
            'tor_exit_node',
            'proxy_detected',
            'vpn_detected',
            'multiple_failed_attempts',
            'account_age_mismatch',
            'behavior_anomaly'
        ]
        
        # IP velocity simulation - create pool of shared IPs
        self.shared_ip_pool = [self.faker.ipv4() for _ in range(50)]  # 50 shared IPs
        self.high_velocity_ips = random.sample(self.shared_ip_pool, 10)  # 10 IPs will have high velocity
        
        # User agent pools for realistic patterns
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15',
            'Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15',
            'Mozilla/5.0 (Android 11; Mobile) AppleWebKit/537.36',
        ]
        
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
    
    def generate_verification_attempt(self, verification_id: str, attempt_number: int, use_shared_ip: bool = False) -> Dict:
        """Generate a verification attempt record."""
        # Simulate IP velocity - 40% of attempts use shared IPs
        if use_shared_ip or random.random() < 0.4:
            ip_address = random.choice(self.shared_ip_pool)
        else:
            ip_address = self.faker.ipv4()
        
        # Mix of legitimate and bot-like user agents
        if random.random() < 0.85:
            user_agent = random.choice(self.user_agents)
        else:
            user_agent = self.faker.user_agent()  # Some suspicious patterns
        
        return {
            'attemptId': str(uuid.uuid4()),
            'verificationId': verification_id,
            'attemptNumber': attempt_number,
            'timestamp': self.faker.date_time_between(start_date='-30d', end_date='now').isoformat(),
            'ipAddress': ip_address,
            'userAgent': user_agent,
            'location': {
                'latitude': float(self.faker.latitude()),
                'longitude': float(self.faker.longitude()),
                'city': self.faker.city(),
                'country': self.faker.country_code()
            },
            'deviceFingerprint': self.faker.sha256(),
            'duration': random.randint(30, 600),  # seconds
            'isHighVelocityIP': ip_address in self.high_velocity_ips
        }
    
    def generate_identity_verification(self, user_id: str = None) -> Dict:
        """Generate a complete identity verification record."""
        if user_id is None:
            user_id = str(uuid.uuid4())
        
        verification_id = str(uuid.uuid4())
        status = random.choice(self.verification_statuses)
        method = random.choice(self.verification_methods)
        risk_level = random.choice(self.risk_levels)
        
        # Generate triggered risk rules based on risk level
        num_rules_triggered = 0
        if risk_level == 'low':
            num_rules_triggered = random.randint(0, 1)
        elif risk_level == 'medium':
            num_rules_triggered = random.randint(1, 3)
        elif risk_level == 'high':
            num_rules_triggered = random.randint(2, 5)
        elif risk_level == 'critical':
            num_rules_triggered = random.randint(4, 8)
        
        triggered_rules = random.sample(self.risk_rules, min(num_rules_triggered, len(self.risk_rules)))
        
        # Generate base verification data focused on login risk
        verification = {
            'verificationId': verification_id,
            'userId': user_id,
            'status': status,
            'riskLevel': risk_level,
            'verificationMethod': method,
            'submittedAt': self.faker.date_time_between(start_date='-60d', end_date='now').isoformat(),
            'reviewedAt': None,
            'reviewedBy': None,
            'processingTime': None,
            'riskScore': round(random.uniform(0.0, 1.0), 3),
            'triggeredRules': triggered_rules,
            'attemptCount': random.randint(1, 5),
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
        
        # Add random flags based on login patterns
        possible_flags = [
            'multiple_attempts', 'suspicious_activity', 'proxy_detected',
            'high_velocity_ip', 'unusual_location', 'suspicious_timing',
            'behavior_anomaly', 'device_mismatch'
        ]
        if random.random() > 0.7:
            verification['flags'] = random.sample(possible_flags, random.randint(1, 3))
        
        return verification
    
    def generate_login_sessions(self, user_id: str, num_sessions: int = None) -> List[Dict]:
        """Generate login sessions for a user to track IP velocity."""
        if num_sessions is None:
            num_sessions = random.randint(5, 30)
        
        sessions = []
        # Decide if this user exhibits high IP velocity (shared IP patterns)
        uses_shared_ips = random.random() < 0.3  # 30% of users show velocity patterns
        
        for i in range(num_sessions):
            # Generate session timestamp
            session_time = self.faker.date_time_between(start_date='-90d', end_date='now')
            
            # IP address assignment
            if uses_shared_ips:
                # High velocity users share IPs, especially high velocity IPs
                if random.random() < 0.6:
                    ip_address = random.choice(self.high_velocity_ips)
                else:
                    ip_address = random.choice(self.shared_ip_pool)
            else:
                # Normal users might occasionally share IPs but mostly unique
                if random.random() < 0.15:
                    ip_address = random.choice(self.shared_ip_pool)
                else:
                    ip_address = self.faker.ipv4()
            
            session = {
                'sessionId': str(uuid.uuid4()),
                'userId': user_id,
                'timestamp': session_time.isoformat(),
                'ipAddress': ip_address,
                'userAgent': random.choice(self.user_agents) if random.random() < 0.9 else self.faker.user_agent(),
                'location': {
                    'city': self.faker.city(),
                    'country': self.faker.country_code(),
                    'latitude': float(self.faker.latitude()),
                    'longitude': float(self.faker.longitude())
                },
                'deviceFingerprint': self.faker.sha256(),
                'sessionDuration': random.randint(60, 7200),  # 1 min to 2 hours
                'actionsPerformed': random.randint(1, 50),
                'isHighVelocityIP': ip_address in self.high_velocity_ips,
                'riskScore': round(random.uniform(0.0, 1.0), 3)
            }
            sessions.append(session)
        
        return sessions
    
    def generate_batch(self, count: int) -> Dict[str, List]:
        """Generate a batch of related IDV data."""
        user_profiles = []
        verifications = []
        attempts = []
        login_sessions = []
        
        for _ in range(count):
            # Generate user profile
            user_profile = self.generate_user_profile()
            user_profiles.append(user_profile)
            
            # Generate login sessions for this user (5-30 sessions)
            user_sessions = self.generate_login_sessions(user_profile['userId'])
            login_sessions.extend(user_sessions)
            
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
            'attempts': attempts,
            'login_sessions': login_sessions
        }


class DataIngestor:
    """Ingest generated data into MongoDB and OpenSearch."""
    
    def __init__(self, mongo_uri: str, opensearch_host: str, opensearch_port: int,
                 opensearch_user: str, opensearch_password: str):
        # MongoDB connection
        self.mongo_client = MongoClient(mongo_uri)
        self.db = self.mongo_client['idv_data']
        
        # OpenSearch connection with retry logic for authentication
        max_retries = 5
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                print(f"Connecting to OpenSearch at {opensearch_host}:{opensearch_port}... (attempt {attempt + 1}/{max_retries})")
                
                # Try without authentication first (security disabled)
                self.opensearch = OpenSearch(
                    hosts=[{'host': opensearch_host, 'port': opensearch_port}],
                    use_ssl=False,
                    verify_certs=False,
                    ssl_show_warn=False,
                    timeout=30,
                    max_retries=3,
                    retry_on_timeout=True
                )
                
                # Test connection
                info = self.opensearch.info()
                print(f"✓ Connected to OpenSearch version {info['version']['number']}")
                break
                
            except Exception as e:
                error_msg = str(e)
                if '401' in error_msg or 'Unauthorized' in error_msg:
                    print(f"Authentication failed (attempt {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        print(f"OpenSearch may still be initializing. Waiting {retry_delay} seconds...")
                        import time
                        time.sleep(retry_delay)
                    else:
                        print(f"\nError: Authentication failed after {max_retries} attempts")
                        print(f"Host: {opensearch_host}:{opensearch_port}")
                        print(f"User: {opensearch_user}")
                        print(f"\nPlease verify:")
                        print("  1. OpenSearch container is running: docker ps | grep opensearch")
                        print("  2. Check OpenSearch logs: docker logs lynx-opensearch")
                        print(f"  3. Try manually: curl -ku {opensearch_user}:{opensearch_password} https://localhost:{opensearch_port}")
                        raise
                else:
                    print(f"Connection error: {e}")
                    if attempt < max_retries - 1:
                        print(f"Retrying in {retry_delay} seconds...")
                        import time
                        time.sleep(retry_delay)
                    else:
                        raise
        
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
            # Need to remove MongoDB _id field for OpenSearch
            for verification in data['verifications']:
                # Create a copy to avoid modifying the original
                os_doc = verification.copy()
                # Remove _id field if present (it's metadata in OpenSearch)
                os_doc.pop('_id', None)
                
                self.opensearch.index(
                    index='idv_verifications',
                    id=verification['verificationId'],
                    body=os_doc
                )
            print(f"Indexed {len(data['verifications'])} verifications in OpenSearch")
        
        if data['attempts']:
            self.db.verification_attempts.insert_many(data['attempts'])
            print(f"Inserted {len(data['attempts'])} verification attempts into MongoDB")
        
        if data.get('login_sessions'):
            self.db.login_sessions.insert_many(data['login_sessions'])
            print(f"Inserted {len(data['login_sessions'])} login sessions into MongoDB")
    
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
