# Ubuntu Setup Guide

Complete guide for deploying the Lynx IDV Stack on Ubuntu 20.04+ or Debian 11+.

## Prerequisites

- Ubuntu 20.04 LTS or newer (or Debian 11+)
- Sudo privileges
- At least 4GB RAM recommended
- 10GB free disk space

## Quick Setup (Automated)

The easiest way to get started is using the automated setup script:

```bash
git clone https://github.com/smccamy1/linktool.git
cd linktool
chmod +x start-stack.sh
./start-stack.sh
```

The script will automatically:
1. Detect your OS and verify compatibility
2. Install Docker Engine and Docker Compose V2 if needed
3. Install Python 3, pip, and venv if needed
4. Start all containers (MongoDB, PostgreSQL, OpenSearch, Web UI, Node-RED)
5. Create a Python virtual environment
6. Generate fake data (50 users by default)
7. Set up OpenSearch dashboards
8. Display access URLs

**Total setup time: 5-10 minutes depending on internet speed**

## Manual Setup (Step-by-Step)

If you prefer manual installation or the automated script doesn't work:

### 1. Install Docker

```bash
# Update package index
sudo apt-get update

# Install prerequisites
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Add your user to docker group (to run without sudo)
sudo usermod -aG docker $USER
newgrp docker  # or log out and back in
```

### 2. Install Python and Dependencies

```bash
# Install Python 3, pip, and venv
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv python3-dev build-essential
```

### 3. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/smccamy1/linktool.git
cd linktool

# Start Docker containers
docker compose up -d

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Generate fake data (50 users, 134 policies, 88 claims)
python3 generate_all_data.py --num-users 50

# Optional: Set up OpenSearch dashboards
python3 setup_dashboards.py

deactivate
```

## Verification

After setup completes, verify all services are running:

```bash
docker ps
```

You should see 6 containers:
- lynx-web-ui
- lynx-mongodb
- lynx-postgres
- lynx-opensearch
- lynx-nodered
- opensearch-dashboards

Test the Web UI:
```bash
curl http://localhost:5050
```

## Access the Application

Open your browser and navigate to:
- **Graph Visualization**: http://localhost:5050

Other services:
- **OpenSearch Dashboards**: http://localhost:5601
- **Node-RED**: http://localhost:1880

## Troubleshooting

### Docker Permission Denied

If you see "permission denied" when running docker commands:

```bash
sudo usermod -aG docker $USER
newgrp docker
```

Or log out and back in for group changes to take effect.

### Port Already in Use

If you get port conflicts, check what's using the ports:

```bash
# Check port 5050 (Web UI)
sudo lsof -i :5050

# Check port 27017 (MongoDB)
sudo lsof -i :27017

# Check port 5432 (PostgreSQL)
sudo lsof -i :5432
```

Kill conflicting processes or modify `docker-compose.yml` to use different ports.

### MongoDB Connection Issues

If you see multiple MongoDB processes:

```bash
# Use the helper script
./check_mongodb.sh

# Or check manually
sudo lsof -i :27017

# Kill local MongoDB if needed
sudo systemctl stop mongod
```

### Container Health Checks Failing

View container logs:

```bash
# All containers
docker compose logs

# Specific container
docker compose logs web-ui
docker compose logs mongodb
docker compose logs postgres
```

### Python Virtual Environment Issues

If venv creation fails:

```bash
# Install venv package
sudo apt-get install -y python3-venv

# Try creating again
python3 -m venv venv
```

## Custom Configuration

### Change Number of Generated Users

```bash
# Generate 200 users instead of default 50
./start-stack.sh --num-users 200

# Or manually
python3 generate_all_data.py --num-users 200
```

### Skip Data Generation

```bash
./start-stack.sh --skip-data
```

### Change Database Credentials

Edit `docker-compose.yml` and update:
- MongoDB: `MONGO_INITDB_ROOT_PASSWORD`
- PostgreSQL: `POSTGRES_PASSWORD`

Also update connection strings in:
- `web-ui/app.py`
- `generate_all_data.py`
- `generate_insurance_data.py`

## Stopping the Stack

```bash
# Stop containers (keep data)
docker compose down

# Stop and remove all data
docker compose down -v
```

## System Requirements

### Minimum
- 2 CPU cores
- 4GB RAM
- 10GB disk space
- Ubuntu 20.04 LTS

### Recommended
- 4 CPU cores
- 8GB RAM
- 20GB disk space
- Ubuntu 22.04 LTS

## Security Notes

⚠️ **This is a development environment with security disabled:**
- OpenSearch has no authentication
- MongoDB and PostgreSQL use default credentials
- No SSL/TLS encryption
- All services exposed on localhost

**Do not expose to public networks without proper security configuration.**

## Next Steps

After successful setup:

1. Open the Graph UI at http://localhost:5050
2. Explore the graph visualization
3. Click user nodes to view IDV and insurance data
4. Right-click nodes to add them to investigations
5. Check out OpenSearch Dashboards for analytics

## Support

For issues, check:
1. Container logs: `docker compose logs`
2. Docker status: `docker ps`
3. Port conflicts: `sudo lsof -i :<port>`
4. MongoDB conflicts: `./check_mongodb.sh`

## Data Regeneration

To regenerate all data with a clean slate:

```bash
# Activate virtual environment
source venv/bin/activate

# Clear and regenerate
python3 generate_all_data.py --num-users 50 --clear

deactivate
```
