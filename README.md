# Lynx IDV Stack

A containerized identity verification (IDV) data platform with OpenSearch, MongoDB, PostgreSQL, and Node-RED, featuring an interactive graph visualization UI with integrated insurance customer data and investigation tracking.

## 🏗️ Architecture

The stack consists of six main services:

- **OpenSearch** (with Dashboards): Search and analytics engine for IDV data
- **MongoDB**: Primary database for storing identity verification records and investigations
- **PostgreSQL**: Relational database for insurance customer data (Aflac-modeled products)
- **Node-RED**: Low-code platform for building data workflows and integrations
- **Web UI**: Interactive graph visualization with integrated IDV and insurance data
- **Data Generators**: Automated fake data generation for testing

## ✨ Key Features

- 🔍 **Interactive Graph Visualization**: Explore IDV data as nodes and edges with drag-and-drop
- 🏥 **Insurance Integration**: Aflac-modeled supplemental insurance products (17 product types)
- 🔗 **Linked Data**: Insurance customers linked to IDV users via GUID with 100% data integrity
- 🔎 **Investigation Tracking**: Right-click nodes to add them to investigations with connected entities
- 📊 **Real-time Analytics**: Click nodes to view detailed IDV and insurance information
- 🎨 **Beautiful UI**: Modern, responsive interface with status-based color coding
- 🚀 **One-Command Setup**: Automated installation and data generation

## 📋 Prerequisites

### Ubuntu 20.04+ / Debian 11+

The setup script will automatically install the following if not present:
- Docker Engine (latest)
- Docker Compose V2 (plugin)
- Python 3.8+
- pip and Python virtual environment tools

### macOS

Please install manually:
- [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/) (Intel or Apple Silicon)
- Python 3.8+ (included with macOS or via Homebrew: `brew install python3`)

### Windows

Please install manually:
- [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/) (with WSL2)
- [Python 3.8+](https://www.python.org/downloads/)

## 🚀 Quick Start

### Ubuntu / Debian

1. Clone the repository:
```bash
git clone https://github.com/smccamy1/linktool.git
cd linktool
```

2. Make setup script executable and run:
```bash
chmod +x start-stack.sh
./start-stack.sh
```

The script will:
- Check for and install required dependencies (Docker, Python)
- Start all containerized services (MongoDB, OpenSearch, PostgreSQL, Web UI, Node-RED)
- Wait for services to be healthy
- Generate fake IDV data (50 users by default)
- Generate fake insurance data linked to IDV users
- Set up OpenSearch dashboards

📖 **For detailed Ubuntu setup instructions and troubleshooting, see [UBUNTU_SETUP.md](UBUNTU_SETUP.md)**
- Display access information

**Once complete, open http://localhost:5050 to see the graph visualization!**

### macOS / Windows

1. Ensure Docker Desktop is running
2. Install Python dependencies:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Start the stack:
```bash
docker compose up -d
```

4. Generate data:
```bash
# IMPORTANT: Always use generate_all_data.py for proper data linkage
python3 generate_all_data.py --num-users 50
```

**⚠️ Note:** Do not run `generate_idv_data.py` and `generate_insurance_data.py` separately, as this will cause insurance data to not link properly to IDV users.

**Access the UI at http://localhost:5050**

### Custom Options

```bash
# Generate more fake users
./start-stack.sh --num-users 500

# Skip OpenSearch and data generation
./start-stack.sh --skip-data

# Help
./start-stack.sh --help
```

## 🔧 Manual Setup

If you prefer to set up manually or are not using Ubuntu:

### 1. Start the Stack

```bash
docker compose up -d
```

### 2. Install Python Dependencies

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Generate Fake Data

```bash
python3 generate_all_data.py --num-users 50
```

This generates both IDV data (users, verifications, attempts) and linked insurance data (customers, policies, claims) in one command.

### 4. Setup OpenSearch Dashboards (Optional)

```bash
python3 setup_dashboards.py
```

This will create:
- Index pattern for IDV data
- 5 visualizations (status distribution, risk levels, timeline, document types, confidence scores)
- A complete IDV Analytics Dashboard

## 🌐 Service Access

Once the stack is running, services are available at:

| Service | URL | Credentials |
|---------|-----|-------------|
| **Graph Visualization UI** | http://localhost:5050 | None |
| Node-RED | http://localhost:1880 | None (default) |
| OpenSearch | http://localhost:9200 | No authentication (dev mode) |
| OpenSearch Dashboards | http://localhost:5601 | No authentication (dev mode) |
| MongoDB | mongodb://localhost:27017 | admin / mongopass123 |
| PostgreSQL | postgresql://localhost:5432/insurance_db | admin / postgrespass123 |

## 🎯 Graph Visualization Quick Guide

1. **Open the UI**: Navigate to http://localhost:5050
2. **Explore the Graph**: 
   - Blue circles = IDV Users
   - Colored diamonds = Verifications (green=approved, red=rejected, yellow=pending, orange=review)
   - Gray squares = Verification attempts
3. **View Details**: Left-click any user node to see:
   - IDV profile information
   - Insurance policies and coverage
   - Claims history
   - Payment records
   - Dependents
4. **Add to Investigation**: Right-click any node to:
   - Add node to investigation
   - Select connected nodes to include
   - Create investigation with name and description
   - All investigation data saved to MongoDB
5. **Navigate**: Drag to pan, scroll to zoom, click "Fit to Screen" to reset

## 🌐 Network Access

The Web UI is accessible from any network interface:

- **Local access**: http://localhost:5050
- **Network access**: http://YOUR_SERVER_IP:5050

To access from other machines:
1. Find your server's IP: `hostname -I` or `ip addr`
2. Open firewall port if needed: `sudo ufw allow 5050/tcp`
3. Access from any browser: `http://YOUR_SERVER_IP:5050`

For detailed firewall configuration and cloud deployment, see [UBUNTU_SETUP.md](UBUNTU_SETUP.md#firewall-configuration).

## 📊 Generated Data Structure

The data generator creates three types of documents:

### User Profiles
Stored in MongoDB collection: `user_profiles`

```json
{
  "userId": "uuid",
  "email": "user@example.com",
  "firstName": "John",
  "lastName": "Doe",
  "dateOfBirth": "1990-01-01",
  "phone": "+1234567890",
  "address": { "street": "...", "city": "...", "state": "...", "zipCode": "...", "country": "US" },
  "createdAt": "2023-01-01T00:00:00",
  "lastUpdated": "2025-12-30T00:00:00"
}
```

### Identity Verifications
Stored in MongoDB collection: `identity_verifications` and OpenSearch index: `idv_verifications`

```json
{
  "verificationId": "uuid",
  "userId": "uuid",
  "status": "approved|rejected|pending|under_review|...",
  "riskLevel": "low|medium|high|critical",
  "verificationMethod": "manual_review|automated|hybrid|video_call",
  "documentType": "passport|drivers_license|national_id|...",
  "documentNumber": "XX12345678",
  "confidence_score": 0.95,
  "biometric_match_score": 0.87,
  "liveness_check_passed": true,
  "sanctions_check_passed": true,
  "pep_check_passed": true,
  "aml_check_passed": true,
  "submittedAt": "2025-12-01T10:00:00",
  "reviewedAt": "2025-12-01T10:15:00",
  "processingTime": 900,
  "flags": ["age_mismatch", "low_quality_image"],
  "metadata": { ... }
}
```

### Verification Attempts
Stored in MongoDB collection: `verification_attempts`

```json
{
  "attemptId": "uuid",
  "verificationId": "uuid",
  "attemptNumber": 1,
  "timestamp": "2025-12-01T10:00:00",
  "ipAddress": "192.168.1.1",
  "userAgent": "Mozilla/5.0...",
  "location": { "latitude": 40.7128, "longitude": -74.0060, "city": "New York", "country": "US" },
  "deviceFingerprint": "sha256hash",
  "duration": 120
}
```

## � Data Generation

### Generate Complete Dataset (Recommended)

The easiest way to generate a complete, linked dataset with both IDV and insurance data:

```bash
# Generate 50 users with full IDV and insurance data
python3 generate_all_data.py --num-users 50 --skip-opensearch

# With OpenSearch ingestion
python3 generate_all_data.py --num-users 50
```

This single command will:
1. Generate IDV user profiles with verifications and attempts
2. Insert data into MongoDB
3. Automatically create linked insurance records for every user
4. Generate policies, claims, payments, and dependents
5. Insert all insurance data into PostgreSQL

**Every IDV user will have corresponding insurance data!**

### Generate IDV Data Only

```bash
# Generate 100 users with verifications and attempts
python3 generate_idv_data.py --num-users 100

# With custom MongoDB URI
python3 generate_idv_data.py --num-users 50 --mongo-uri "mongodb://localhost:27017/"
```

### Generate Insurance Data Only

```bash
# Generate insurance data for existing IDV users
python3 generate_insurance_data.py

# Limit to first 50 users
python3 generate_insurance_data.py --max-customers 50
```

### Clear All Data

```bash
# Clear MongoDB
docker exec lynx-mongodb mongosh idv_data --eval "db.user_profiles.deleteMany({}); db.identity_verifications.deleteMany({}); db.verification_attempts.deleteMany({});"

# Clear PostgreSQL
docker exec lynx-postgres psql -U admin -d insurance_db -c "TRUNCATE TABLE payments, claims, dependents, policies, customers RESTART IDENTITY CASCADE;"
```

## �🔍 Using the Data

### Query MongoDB

```bash
# Connect to MongoDB
docker exec -it lynx-mongodb mongosh -u admin -p mongopass123

# Use the IDV database
use idv_data

# Query verifications
db.identity_verifications.find({status: "approved"}).limit(5)

# Count by status
db.identity_verifications.aggregate([
  { $group: { _id: "$status", count: { $sum: 1 } } }
])
```

### Query OpenSearch

```bash
# Search verifications with high risk
curl -k -u admin:Admin123! -X GET "https://localhost:9200/idv_verifications/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "term": { "riskLevel": "high" }
  }
}'

# Aggregate by status
curl -k -u admin:Admin123! -X GET "https://localhost:9200/idv_verifications/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "aggs": {
    "status_counts": {
      "terms": { "field": "status" }
    }
  }
}'
```

### Use Node-RED

1. Open http://localhost:1880
2. Install MongoDB and OpenSearch nodes from the palette manager
3. Create flows to process and route IDV data

Example Node-RED flows:
- Monitor new verifications
- Alert on high-risk verifications
- Generate daily statistics
- Export data for reporting

## 🛠️ Data Generation Script Options

```bash
python3 generate_idv_data.py --help

Options:
  -n, --num-users NUM           Number of users to generate (default: 100)
  --mongo-uri URI               MongoDB connection URI
  --opensearch-host HOST        OpenSearch host (default: localhost)
  --opensearch-port PORT        OpenSearch port (default: 9200)
  --opensearch-user USER        OpenSearch username (default: admin)
  --opensearch-password PASS    OpenSearch password (default: Admin123!)
  --json-output FILE            Output to JSON file instead of databases
```

### Generate Data to JSON File

```bash
python3 generate_idv_data.py --num-users 50 --json-output idv_data.json
```

## 📝 Docker Compose Commands

```bash
# Start the stack
docker compose up -d

# View logs
docker compose logs -f

# View logs for specific service
docker compose logs -f opensearch

# Stop the stack (preserves data)
docker compose down

# Stop and remove all data
docker compose down -v

# Restart a service
docker compose restart mongodb

# Check service status
docker compose ps
```

## 🔒 Security Notes

**⚠️ This setup is for development/testing only!**

For production use:
- Change all default passwords
- Enable SSL/TLS for all services
- Configure proper authentication
- Set up network security groups
- Enable audit logging
- Use secrets management
- Implement backup strategies

## 🐛 Troubleshooting

### Services not starting

Check Docker logs:
```bash
docker compose logs
```

### OpenSearch memory errors

Increase Docker memory allocation or reduce OpenSearch heap size in docker-compose.yml:
```yaml
OPENSEARCH_JAVA_OPTS: "-Xms256m -Xmx256m"
```

### Python dependencies fail to install

Ensure you have Python development headers:
```bash
sudo apt-get install python3-dev
```

### Data generation fails

Check connectivity:
```bash
# Test MongoDB
docker exec -it lynx-mongodb mongosh -u admin -p mongopass123 --eval "db.adminCommand('ping')"

# Test OpenSearch
curl -k -u admin:Admin123! https://localhost:9200
```

### Insurance data not showing when clicking nodes

This means the data wasn't generated with proper linkage. Fix it:

```bash
# Clear and regenerate all data with proper linkage
source venv/bin/activate  # On Windows: venv\Scripts\activate
python3 generate_all_data.py --num-users 50
deactivate
```

Verify the fix by checking if user counts match:
```bash
# MongoDB user count
docker exec lynx-mongodb mongosh idv_data --quiet --eval "db.user_profiles.countDocuments({})"

# PostgreSQL customer count (should match MongoDB)
docker exec lynx-postgres psql -U admin -d insurance_db -c "SELECT COUNT(*) FROM customers;"
```

## 📦 Volumes

Data is persisted in Docker volumes:
- `opensearch-data`: OpenSearch indices
- `mongodb-data`: MongoDB databases
- `nodered-data`: Node-RED flows and settings

## 🤝 Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## 📄 License

This project is provided as-is for development and testing purposes.
