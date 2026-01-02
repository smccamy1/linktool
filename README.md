# Lynx IDV Stack

A containerized identity verification (IDV) data platform with OpenSearch, MongoDB, and Node-RED, including automated fake data generation for testing and development.

## 🏗️ Architecture

The stack consists of three main services:

- **OpenSearch** (with Dashboards): Search and analytics engine for IDV data
- **MongoDB**: Primary database for storing identity verification records
- **Node-RED**: Low-code platform for building data workflows and integrations

## 📋 Prerequisites

### For Ubuntu/Debian

The setup script will automatically install the following if not present:
- Docker Engine
- Docker Compose (plugin)
- Python 3
- pip

### For Other Operating Systems

Please install manually:
- [Docker Desktop](https://www.docker.com/products/docker-desktop)
- [Python 3.8+](https://www.python.org/downloads/)

## 🚀 Quick Start

### On Ubuntu

1. Clone or download this repository
2. Run the setup script:

```bash
./start-stack.sh
```

The script will:
- Check for and install required dependencies (Docker, Python)
- Start all containerized services
- Wait for services to be healthy
- Generate fake IDV data (100 users by default)
- Display access information

### Custom Options

```bash
# Generate more fake users
./start-stack.sh --num-users 500

# Skip data generation
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
python3 generate_idv_data.py --num-users 100
```

### 4. Setup OpenSearch Dashboards

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
| Node-RED | http://localhost:1880 | None (default) |
| OpenSearch | http://localhost:9200 | No authentication (dev mode) |
| OpenSearch Dashboards | http://localhost:5601 | No authentication (dev mode) |
| MongoDB | mongodb://localhost:27017 | admin / mongopass123 |

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

## 🔍 Using the Data

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

## 📦 Volumes

Data is persisted in Docker volumes:
- `opensearch-data`: OpenSearch indices
- `mongodb-data`: MongoDB databases
- `nodered-data`: Node-RED flows and settings

## 🤝 Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## 📄 License

This project is provided as-is for development and testing purposes.
