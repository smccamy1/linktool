-- Insurance Database Schema
-- Modeled after Aflac Insurance products

-- Create tables for insurance company data

-- Customers table - linked to IDV data via user_id GUID
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE,  -- Links to IDV user_profiles.userId
    customer_number VARCHAR(50) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    ssn_last_four VARCHAR(4),
    email VARCHAR(255),
    phone VARCHAR(50),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(10),
    enrollment_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insurance products table (Aflac-style supplemental insurance)
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    product_code VARCHAR(20) UNIQUE NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    product_category VARCHAR(50) NOT NULL,  -- accident, cancer, hospital, disability, life, dental, vision
    description TEXT,
    base_premium DECIMAL(10, 2) NOT NULL,
    coverage_amount DECIMAL(12, 2),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Policies table
CREATE TABLE policies (
    policy_id SERIAL PRIMARY KEY,
    policy_number VARCHAR(30) UNIQUE NOT NULL,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    effective_date DATE NOT NULL,
    expiration_date DATE,
    premium_amount DECIMAL(10, 2) NOT NULL,
    payment_frequency VARCHAR(20),  -- monthly, quarterly, annually
    status VARCHAR(20) DEFAULT 'active',  -- active, lapsed, cancelled, expired
    coverage_amount DECIMAL(12, 2),
    beneficiary_name VARCHAR(255),
    beneficiary_relationship VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Claims table
CREATE TABLE claims (
    claim_id SERIAL PRIMARY KEY,
    claim_number VARCHAR(30) UNIQUE NOT NULL,
    policy_id INTEGER NOT NULL REFERENCES policies(policy_id),
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    claim_date DATE NOT NULL,
    incident_date DATE NOT NULL,
    claim_type VARCHAR(50) NOT NULL,  -- accident, illness, hospitalization, disability, death
    claim_amount DECIMAL(12, 2) NOT NULL,
    approved_amount DECIMAL(12, 2),
    status VARCHAR(30) DEFAULT 'submitted',  -- submitted, under_review, approved, denied, paid
    denial_reason TEXT,
    diagnosis_code VARCHAR(20),
    diagnosis_description TEXT,
    treatment_type VARCHAR(100),
    provider_name VARCHAR(255),
    provider_npi VARCHAR(20),
    submitted_date DATE NOT NULL,
    processed_date DATE,
    paid_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Payments table
CREATE TABLE payments (
    payment_id SERIAL PRIMARY KEY,
    policy_id INTEGER NOT NULL REFERENCES policies(policy_id),
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    payment_date DATE NOT NULL,
    payment_amount DECIMAL(10, 2) NOT NULL,
    payment_method VARCHAR(30),  -- credit_card, bank_draft, check, payroll_deduction
    payment_status VARCHAR(20) DEFAULT 'completed',  -- pending, completed, failed, reversed
    transaction_id VARCHAR(100),
    period_start_date DATE,
    period_end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dependents table
CREATE TABLE dependents (
    dependent_id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    relationship VARCHAR(50) NOT NULL,  -- spouse, child, parent
    ssn_last_four VARCHAR(4),
    is_covered BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX idx_customers_user_id ON customers(user_id);
CREATE INDEX idx_customers_customer_number ON customers(customer_number);
CREATE INDEX idx_policies_customer_id ON policies(customer_id);
CREATE INDEX idx_policies_status ON policies(status);
CREATE INDEX idx_claims_customer_id ON claims(customer_id);
CREATE INDEX idx_claims_policy_id ON claims(policy_id);
CREATE INDEX idx_claims_status ON claims(status);
CREATE INDEX idx_payments_customer_id ON payments(customer_id);
CREATE INDEX idx_payments_policy_id ON payments(policy_id);
CREATE INDEX idx_dependents_customer_id ON dependents(customer_id);

-- Insert sample Aflac-style insurance products
INSERT INTO products (product_code, product_name, product_category, description, base_premium, coverage_amount, is_active) VALUES
-- Accident Insurance
('ACC-1000', 'Accident Advantage', 'accident', 'Coverage for accidental injuries including emergency treatment, hospital stays, and disability benefits', 45.00, 50000.00, true),
('ACC-2000', 'Accident Plus', 'accident', 'Enhanced accident coverage with higher benefit amounts and additional riders', 75.00, 100000.00, true),

-- Cancer Insurance
('CAN-1000', 'Cancer Care', 'cancer', 'Coverage for cancer diagnosis, treatment, and related expenses', 85.00, 75000.00, true),
('CAN-2000', 'Cancer Protection Plus', 'cancer', 'Comprehensive cancer coverage including experimental treatments and wellness benefits', 125.00, 150000.00, true),

-- Hospital Indemnity
('HOS-1000', 'Hospital Indemnity', 'hospital', 'Daily benefit for hospital confinement and ICU stays', 55.00, 1500.00, true),
('HOS-2000', 'Hospital Advantage', 'hospital', 'Enhanced hospital coverage with higher daily benefits and surgical benefits', 95.00, 3000.00, true),

-- Short-Term Disability
('DIS-1000', 'Short-Term Disability', 'disability', 'Income replacement for temporary disability due to illness or injury', 125.00, 60000.00, true),
('DIS-2000', 'Long-Term Disability', 'disability', 'Extended income protection for long-term disabilities', 185.00, 120000.00, true),

-- Life Insurance
('LIF-1000', 'Whole Life 50K', 'life', 'Permanent life insurance with cash value accumulation', 65.00, 50000.00, true),
('LIF-2000', 'Whole Life 100K', 'life', 'Higher coverage whole life insurance policy', 115.00, 100000.00, true),
('LIF-3000', 'Term Life 250K', 'life', '20-year term life insurance', 45.00, 250000.00, true),

-- Dental Insurance
('DEN-1000', 'Dental Care Basic', 'dental', 'Basic dental coverage for preventive and basic procedures', 35.00, 1500.00, true),
('DEN-2000', 'Dental Care Premier', 'dental', 'Comprehensive dental coverage including major procedures and orthodontia', 65.00, 3000.00, true),

-- Vision Insurance
('VIS-1000', 'Vision Essential', 'vision', 'Basic vision coverage for exams and eyewear', 15.00, 500.00, true),
('VIS-2000', 'Vision Plus', 'vision', 'Enhanced vision benefits with designer frame allowance', 25.00, 750.00, true),

-- Critical Illness
('CRI-1000', 'Critical Illness', 'critical_illness', 'Lump sum benefit for heart attack, stroke, or other critical conditions', 95.00, 25000.00, true),
('CRI-2000', 'Critical Illness Plus', 'critical_illness', 'Higher benefit critical illness coverage with health screening benefits', 145.00, 50000.00, true);

-- Create a view for easy policy and claim reporting
CREATE VIEW policy_summary AS
SELECT 
    c.customer_id,
    c.user_id,
    c.customer_number,
    c.first_name,
    c.last_name,
    c.email,
    c.status as customer_status,
    COUNT(DISTINCT p.policy_id) as total_policies,
    COUNT(DISTINCT CASE WHEN p.status = 'active' THEN p.policy_id END) as active_policies,
    SUM(p.premium_amount) as total_monthly_premium,
    COUNT(cl.claim_id) as total_claims,
    COUNT(CASE WHEN cl.status = 'approved' THEN cl.claim_id END) as approved_claims,
    COALESCE(SUM(CASE WHEN cl.status = 'approved' THEN cl.approved_amount END), 0) as total_claims_paid
FROM customers c
LEFT JOIN policies p ON c.customer_id = p.customer_id
LEFT JOIN claims cl ON c.customer_id = cl.customer_id
GROUP BY c.customer_id, c.user_id, c.customer_number, c.first_name, c.last_name, c.email, c.status;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO admin;
GRANT SELECT ON policy_summary TO admin;

-- Create update timestamp function and trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_policies_updated_at BEFORE UPDATE ON policies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_claims_updated_at BEFORE UPDATE ON claims
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_dependents_updated_at BEFORE UPDATE ON dependents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
