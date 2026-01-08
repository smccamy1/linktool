#!/usr/bin/env python3
"""
Insurance Data Generator
Generates fake insurance customer data (customers, policies, claims) linked to IDV data via GUID.
Models products after Aflac supplemental insurance offerings.
"""

import random
import argparse
from datetime import datetime, timedelta
from decimal import Decimal

try:
    from faker import Faker
except ImportError:
    print("Error: 'faker' library is required. Install it with:")
    print("  pip install faker")
    exit(1)

try:
    from pymongo import MongoClient
except ImportError:
    print("Error: 'pymongo' library is required. Install it with:")
    print("  pip install pymongo")
    exit(1)

try:
    import psycopg2
    from psycopg2.extras import execute_values
except ImportError:
    print("Error: 'psycopg2' library is required. Install it with:")
    print("  pip install psycopg2-binary")
    exit(1)


class InsuranceDataGenerator:
    """Generate fake insurance company data."""
    
    def __init__(self, locale='en_US'):
        self.faker = Faker(locale)
        self.claim_types = ['accident', 'illness', 'hospitalization', 'disability', 'routine_care']
        self.claim_statuses = ['submitted', 'under_review', 'approved', 'denied', 'paid']
        self.payment_methods = ['credit_card', 'bank_draft', 'check', 'payroll_deduction']
        self.relationships = ['spouse', 'child', 'parent']
        
    def generate_customer_from_idv_user(self, idv_user):
        """Generate insurance customer data from IDV user profile."""
        customer_number = f"CUST{random.randint(100000, 999999)}"
        enrollment_date = datetime.fromisoformat(idv_user['createdAt']).date() + timedelta(days=random.randint(0, 30))
        
        # Extract address from IDV data
        address = idv_user.get('address', {})
        
        return {
            'user_id': idv_user['userId'],
            'customer_number': customer_number,
            'first_name': idv_user['firstName'],
            'last_name': idv_user['lastName'],
            'date_of_birth': idv_user['dateOfBirth'],
            'ssn_last_four': f"{random.randint(1000, 9999)}",
            'email': idv_user['email'],
            'phone': idv_user['phone'],
            'address_line1': address.get('street', self.faker.street_address()),
            'address_line2': self.faker.secondary_address() if random.random() > 0.7 else None,
            'city': address.get('city', self.faker.city()),
            'state': address.get('state', self.faker.state_abbr()),
            'zip_code': address.get('zipCode', self.faker.zipcode()),
            'enrollment_date': enrollment_date,
            'status': random.choices(['active', 'inactive', 'suspended'], weights=[85, 10, 5])[0]
        }
    
    def generate_policies(self, customer_id, product_ids, enrollment_date):
        """Generate 1-4 insurance policies for a customer."""
        num_policies = random.randint(1, 4)
        selected_products = random.sample(product_ids, min(num_policies, len(product_ids)))
        
        policies = []
        for i, product_id in enumerate(selected_products):
            policy_number = f"POL{random.randint(1000000, 9999999)}"
            effective_date = enrollment_date + timedelta(days=random.randint(0, 90))
            
            # Calculate premium (base + random variation)
            base_premiums = {
                1: 45.00, 2: 75.00, 3: 85.00, 4: 125.00, 5: 55.00, 6: 95.00,
                7: 125.00, 8: 185.00, 9: 65.00, 10: 115.00, 11: 45.00,
                12: 35.00, 13: 65.00, 14: 15.00, 15: 25.00, 16: 95.00, 17: 145.00
            }
            premium = base_premiums.get(product_id, 50.00) * random.uniform(0.9, 1.1)
            
            coverage_amounts = {
                1: 50000, 2: 100000, 3: 75000, 4: 150000, 5: 1500, 6: 3000,
                7: 60000, 8: 120000, 9: 50000, 10: 100000, 11: 250000,
                12: 1500, 13: 3000, 14: 500, 15: 750, 16: 25000, 17: 50000
            }
            
            policy = {
                'policy_number': policy_number,
                'customer_id': customer_id,
                'product_id': product_id,
                'effective_date': effective_date,
                'expiration_date': None if random.random() > 0.1 else effective_date + timedelta(days=365 * random.randint(1, 3)),
                'premium_amount': round(premium, 2),
                'payment_frequency': random.choice(['monthly', 'quarterly', 'annually']),
                'status': random.choices(['active', 'lapsed', 'cancelled', 'expired'], weights=[80, 10, 5, 5])[0],
                'coverage_amount': coverage_amounts.get(product_id, 50000),
                'beneficiary_name': self.faker.name() if random.random() > 0.3 else None,
                'beneficiary_relationship': random.choice(['spouse', 'child', 'parent', 'sibling']) if random.random() > 0.3 else None
            }
            policies.append(policy)
        
        return policies
    
    def generate_claims(self, customer_id, policies):
        """Generate 0-5 claims for a customer's policies."""
        if not policies or random.random() > 0.6:  # 60% of customers have claims
            return []
        
        num_claims = random.randint(1, 5)
        claims = []
        
        for _ in range(num_claims):
            policy = random.choice(policies)
            incident_date = policy['effective_date'] + timedelta(days=random.randint(30, 700))
            claim_date = incident_date + timedelta(days=random.randint(1, 14))
            submitted_date = claim_date
            
            claim_amount = round(random.uniform(500, 50000), 2)
            status = random.choice(self.claim_statuses)
            
            claim = {
                'claim_number': f"CLM{random.randint(1000000, 9999999)}",
                'policy_id': policy.get('policy_id'),  # Will be updated after policy insertion
                'customer_id': customer_id,
                'claim_date': claim_date,
                'incident_date': incident_date,
                'claim_type': random.choice(self.claim_types),
                'claim_amount': claim_amount,
                'approved_amount': round(claim_amount * random.uniform(0.7, 1.0), 2) if status in ['approved', 'paid'] else None,
                'status': status,
                'denial_reason': self.faker.sentence() if status == 'denied' else None,
                'diagnosis_code': f"{random.choice(['A', 'B', 'C', 'D', 'S', 'T'])}{random.randint(10, 99)}.{random.randint(0, 9)}",
                'diagnosis_description': self.faker.sentence(nb_words=6),
                'treatment_type': random.choice(['emergency_room', 'inpatient', 'outpatient', 'surgery', 'physical_therapy', 'diagnostic_test']),
                'provider_name': f"Dr. {self.faker.last_name()} {random.choice(['Medical Center', 'Hospital', 'Clinic', 'Associates'])}",
                'provider_npi': f"{random.randint(1000000000, 9999999999)}",
                'submitted_date': submitted_date,
                'processed_date': submitted_date + timedelta(days=random.randint(5, 45)) if status != 'submitted' else None,
                'paid_date': submitted_date + timedelta(days=random.randint(30, 90)) if status == 'paid' else None,
                'notes': self.faker.text(max_nb_chars=200) if random.random() > 0.5 else None
            }
            claims.append(claim)
        
        return claims
    
    def generate_payments(self, customer_id, policies):
        """Generate payment history for policies."""
        payments = []
        
        for policy in policies:
            if policy['status'] == 'active':
                # Generate 3-12 months of payments
                num_payments = random.randint(3, 12)
                
                for i in range(num_payments):
                    payment_date = policy['effective_date'] + timedelta(days=30 * i)
                    
                    if payment_date > datetime.now().date():
                        break
                    
                    payment = {
                        'policy_id': policy.get('policy_id'),  # Will be updated after policy insertion
                        'customer_id': customer_id,
                        'payment_date': payment_date,
                        'payment_amount': policy['premium_amount'],
                        'payment_method': random.choice(self.payment_methods),
                        'payment_status': random.choices(['completed', 'failed', 'pending'], weights=[95, 3, 2])[0],
                        'transaction_id': f"TXN{random.randint(10000000, 99999999)}",
                        'period_start_date': payment_date,
                        'period_end_date': payment_date + timedelta(days=30)
                    }
                    payments.append(payment)
        
        return payments
    
    def generate_dependents(self, customer_id, customer_dob):
        """Generate 0-3 dependents for a customer."""
        if random.random() > 0.5:  # 50% have dependents
            return []
        
        num_dependents = random.randint(1, 3)
        dependents = []
        customer_birth_date = datetime.fromisoformat(customer_dob).date()
        
        for _ in range(num_dependents):
            relationship = random.choice(self.relationships)
            
            if relationship == 'spouse':
                dob = customer_birth_date + timedelta(days=random.randint(-1825, 1825))  # +/- 5 years
            elif relationship == 'child':
                dob = customer_birth_date + timedelta(days=random.randint(6570, 10950))  # 18-30 years later
            else:  # parent
                dob = customer_birth_date - timedelta(days=random.randint(9125, 14600))  # 25-40 years earlier
            
            dependent = {
                'customer_id': customer_id,
                'first_name': self.faker.first_name(),
                'last_name': self.faker.last_name(),
                'date_of_birth': dob,
                'relationship': relationship,
                'ssn_last_four': f"{random.randint(1000, 9999)}",
                'is_covered': random.choice([True, False])
            }
            dependents.append(dependent)
        
        return dependents


class DataIngestor:
    """Ingest insurance data into PostgreSQL, linked to IDV data in MongoDB."""
    
    def __init__(self, mongo_uri: str, postgres_uri: str):
        # MongoDB connection
        self.mongo_client = MongoClient(mongo_uri)
        self.mongo_db = self.mongo_client['idv_data']
        
        # PostgreSQL connection
        self.pg_conn = psycopg2.connect(postgres_uri)
        self.pg_cursor = self.pg_conn.cursor()
        
    def get_idv_users(self):
        """Retrieve all IDV user profiles from MongoDB."""
        users = list(self.mongo_db.user_profiles.find({}))
        print(f"Found {len(users)} IDV users in MongoDB")
        return users
    
    def get_product_ids(self):
        """Get all insurance product IDs from PostgreSQL."""
        self.pg_cursor.execute("SELECT product_id FROM products WHERE is_active = true")
        product_ids = [row[0] for row in self.pg_cursor.fetchall()]
        return product_ids
    
    def insert_customer(self, customer_data):
        """Insert customer and return customer_id."""
        query = """
            INSERT INTO customers (
                user_id, customer_number, first_name, last_name, date_of_birth,
                ssn_last_four, email, phone, address_line1, address_line2,
                city, state, zip_code, enrollment_date, status
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING customer_id
        """
        self.pg_cursor.execute(query, (
            customer_data['user_id'], customer_data['customer_number'],
            customer_data['first_name'], customer_data['last_name'],
            customer_data['date_of_birth'], customer_data['ssn_last_four'],
            customer_data['email'], customer_data['phone'],
            customer_data['address_line1'], customer_data['address_line2'],
            customer_data['city'], customer_data['state'],
            customer_data['zip_code'], customer_data['enrollment_date'],
            customer_data['status']
        ))
        customer_id = self.pg_cursor.fetchone()[0]
        return customer_id
    
    def insert_policies(self, policies):
        """Insert policies and return policy_ids."""
        query = """
            INSERT INTO policies (
                policy_number, customer_id, product_id, effective_date,
                expiration_date, premium_amount, payment_frequency, status,
                coverage_amount, beneficiary_name, beneficiary_relationship
            ) VALUES %s RETURNING policy_id
        """
        values = [
            (p['policy_number'], p['customer_id'], p['product_id'],
             p['effective_date'], p['expiration_date'], p['premium_amount'],
             p['payment_frequency'], p['status'], p['coverage_amount'],
             p['beneficiary_name'], p['beneficiary_relationship'])
            for p in policies
        ]
        
        policy_ids = []
        for val in values:
            self.pg_cursor.execute(
                """INSERT INTO policies (
                    policy_number, customer_id, product_id, effective_date,
                    expiration_date, premium_amount, payment_frequency, status,
                    coverage_amount, beneficiary_name, beneficiary_relationship
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING policy_id""", val
            )
            policy_ids.append(self.pg_cursor.fetchone()[0])
        
        return policy_ids
    
    def insert_claims(self, claims):
        """Insert claims."""
        if not claims:
            return
        
        query = """
            INSERT INTO claims (
                claim_number, policy_id, customer_id, claim_date, incident_date,
                claim_type, claim_amount, approved_amount, status, denial_reason,
                diagnosis_code, diagnosis_description, treatment_type,
                provider_name, provider_npi, submitted_date, processed_date,
                paid_date, notes
            ) VALUES %s
        """
        values = [
            (c['claim_number'], c['policy_id'], c['customer_id'],
             c['claim_date'], c['incident_date'], c['claim_type'],
             c['claim_amount'], c['approved_amount'], c['status'],
             c['denial_reason'], c['diagnosis_code'], c['diagnosis_description'],
             c['treatment_type'], c['provider_name'], c['provider_npi'],
             c['submitted_date'], c['processed_date'], c['paid_date'], c['notes'])
            for c in claims
        ]
        execute_values(self.pg_cursor, query, values)
    
    def insert_payments(self, payments):
        """Insert payments."""
        if not payments:
            return
        
        query = """
            INSERT INTO payments (
                policy_id, customer_id, payment_date, payment_amount,
                payment_method, payment_status, transaction_id,
                period_start_date, period_end_date
            ) VALUES %s
        """
        values = [
            (p['policy_id'], p['customer_id'], p['payment_date'],
             p['payment_amount'], p['payment_method'], p['payment_status'],
             p['transaction_id'], p['period_start_date'], p['period_end_date'])
            for p in payments
        ]
        execute_values(self.pg_cursor, query, values)
    
    def insert_dependents(self, dependents):
        """Insert dependents."""
        if not dependents:
            return
        
        query = """
            INSERT INTO dependents (
                customer_id, first_name, last_name, date_of_birth,
                relationship, ssn_last_four, is_covered
            ) VALUES %s
        """
        values = [
            (d['customer_id'], d['first_name'], d['last_name'],
             d['date_of_birth'], d['relationship'], d['ssn_last_four'],
             d['is_covered'])
            for d in dependents
        ]
        execute_values(self.pg_cursor, query, values)
    
    def generate_and_insert_all(self, max_customers=None):
        """Generate and insert all insurance data for IDV users."""
        generator = InsuranceDataGenerator()
        idv_users = self.get_idv_users()
        
        if not idv_users:
            print("No IDV users found. Please run generate_idv_data.py first.")
            return
        
        if max_customers:
            idv_users = idv_users[:max_customers]
        
        product_ids = self.get_product_ids()
        
        if not product_ids:
            print("No insurance products found in database!")
            return
        
        total_customers = 0
        total_policies = 0
        total_claims = 0
        total_payments = 0
        total_dependents = 0
        
        for i, idv_user in enumerate(idv_users):
            try:
                # Generate customer from IDV user
                customer_data = generator.generate_customer_from_idv_user(idv_user)
                customer_id = self.insert_customer(customer_data)
                total_customers += 1
                
                # Generate and insert policies
                policies = generator.generate_policies(
                    customer_id, product_ids, customer_data['enrollment_date']
                )
                policy_ids = self.insert_policies(policies)
                total_policies += len(policies)
                
                # Update policies with their IDs
                for policy, policy_id in zip(policies, policy_ids):
                    policy['policy_id'] = policy_id
                
                # Generate and insert claims
                claims = generator.generate_claims(customer_id, policies)
                if claims:
                    self.insert_claims(claims)
                    total_claims += len(claims)
                
                # Generate and insert payments
                payments = generator.generate_payments(customer_id, policies)
                if payments:
                    self.insert_payments(payments)
                    total_payments += len(payments)
                
                # Generate and insert dependents
                dependents = generator.generate_dependents(customer_id, customer_data['date_of_birth'])
                if dependents:
                    self.insert_dependents(dependents)
                    total_dependents += len(dependents)
                
                if (i + 1) % 10 == 0:
                    print(f"Processed {i + 1}/{len(idv_users)} customers...")
                    self.pg_conn.commit()
                
            except Exception as e:
                print(f"Error processing user {idv_user.get('userId')}: {e}")
                self.pg_conn.rollback()
                continue
        
        # Final commit
        self.pg_conn.commit()
        
        print(f"\n=== Insurance Data Generation Complete ===")
        print(f"Customers created: {total_customers}")
        print(f"Policies created: {total_policies}")
        print(f"Claims created: {total_claims}")
        print(f"Payments created: {total_payments}")
        print(f"Dependents created: {total_dependents}")
    
    def close(self):
        """Close database connections."""
        self.pg_cursor.close()
        self.pg_conn.close()
        self.mongo_client.close()


def main():
    parser = argparse.ArgumentParser(
        description='Generate fake insurance company data linked to IDV users'
    )
    parser.add_argument(
        '--max-customers',
        type=int,
        help='Maximum number of customers to generate (default: all IDV users)'
    )
    parser.add_argument(
        '--mongo-uri',
        default='mongodb://admin:mongopass123@localhost:27017/',
        help='MongoDB connection URI'
    )
    parser.add_argument(
        '--postgres-uri',
        default='postgresql://admin:postgrespass123@localhost:5432/insurance_db',
        help='PostgreSQL connection URI'
    )
    
    args = parser.parse_args()
    
    print("Connecting to databases...")
    ingestor = DataIngestor(args.mongo_uri, args.postgres_uri)
    
    print("Generating insurance data...")
    ingestor.generate_and_insert_all(args.max_customers)
    
    ingestor.close()
    print("\nDone!")


if __name__ == '__main__':
    main()
