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
# IMPORTANT: Use generate_all_data.py to ensure proper data linkage
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

### From Local Machine

Open your browser and navigate to:
- **Graph Visualization**: http://localhost:5050

Other services:
- **OpenSearch Dashboards**: http://localhost:5601
- **Node-RED**: http://localhost:1880

### From Remote Machine

The Web UI is exposed on all network interfaces and can be accessed from other machines:

```bash
# Find your server's IP address
ip addr show | grep inet
# or
hostname -I
```

Then access from any machine on the network:
- **Graph Visualization**: http://YOUR_SERVER_IP:5050
- **OpenSearch Dashboards**: http://YOUR_SERVER_IP:5601
- **Node-RED**: http://YOUR_SERVER_IP:1880

**Example**: If your Ubuntu server IP is `192.168.1.100`, access the UI at:
```
http://192.168.1.100:5050
```

## Firewall Configuration

If you need to access the UI from other machines, ensure your firewall allows the required ports:

### Using UFW (Ubuntu Firewall)

```bash
# Allow Web UI port
sudo ufw allow 5050/tcp

# Optional: Allow other services
sudo ufw allow 5601/tcp  # OpenSearch Dashboards
sudo ufw allow 1880/tcp  # Node-RED

# Check firewall status
sudo ufw status
```

### Using firewalld (RHEL/CentOS)

```bash
# Allow Web UI port
sudo firewall-cmd --permanent --add-port=5050/tcp
sudo firewall-cmd --reload

# Check status
sudo firewall-cmd --list-ports
```

### Cloud Provider Security Groups

If running on AWS, Azure, or GCP, you'll also need to:
1. Open port 5050 in your cloud security group/firewall rules
2. Ensure your VM's network interface is configured to allow inbound traffic

### Test Network Connectivity

```bash
# From remote machine, test if port is accessible
telnet YOUR_SERVER_IP 5050
# or
nc -zv YOUR_SERVER_IP 5050
# or
curl -v http://YOUR_SERVER_IP:5050
```

### Run Network Diagnostic Script

A comprehensive diagnostic script is included to check all network configurations:

```bash
./check_network_access.sh
```

This will check:
- Docker and container status
- Flask binding configuration
- Port binding on host (all interfaces vs localhost)
- Local and IP-based access
- Firewall rules (UFW, firewalld, iptables)
- Docker NAT rules
- Server IP addresses

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

### Can Access Locally but Not Remotely

This is a common issue. Check these in order:

**1. Verify port binding:**
```bash
# Check what's listening on port 5050
sudo ss -tlnp | grep 5050
# or
sudo netstat -tlnp | grep 5050
```

You should see `0.0.0.0:5050` or `*:5050`. If you see `127.0.0.1:5050`, Docker is not exposing correctly.

**2. Restart Docker networking:**
```bash
# Stop containers
docker compose down

# Verify port is released
sudo ss -tlnp | grep 5050  # Should return nothing

# Start containers
docker compose up -d

# Wait 30 seconds for services to start
sleep 30

# Check again
sudo ss -tlnp | grep 5050
```

**3. Check Docker iptables rules:**
```bash
# View Docker NAT rules
sudo iptables -t nat -L DOCKER -n | grep 5050
```

You should see a DNAT rule forwarding to the container.

**4. Test from server itself using server IP (not localhost):**
```bash
# Get your server IP
SERVER_IP=$(hostname -I | awk '{print $1}')

# Test access via IP
curl -v http://$SERVER_IP:5050

# If this fails but localhost works, it's a Docker or firewall issue
```

**5. Check if UFW is blocking Docker:**

UFW can sometimes block Docker ports even with rules. Try:

```bash
# Option A: Disable UFW temporarily to test
sudo ufw disable
curl http://YOUR_SERVER_IP:5050
sudo ufw enable

# Option B: Configure UFW to work with Docker
sudo ufw allow from any to any port 5050 proto tcp
```

**6. Cloud provider security groups:**

If on AWS, Azure, GCP, etc.:
- Open port 5050 in security group/firewall
- Verify VM has public IP
- Check network ACLs
- Try accessing via private IP first from another VM in same network

**7. Check for conflicting services:**
```bash
# See what else might be using port 5050
sudo lsof -i :5050
```

### Insurance Data Not Showing When Clicking Nodes

If you click user nodes and see "No insurance information found", the data wasn't generated with proper linkage.

**Cause:** Running `generate_idv_data.py` and `generate_insurance_data.py` separately instead of using `generate_all_data.py`.

**Solution:** Clear and regenerate all data:

```bash
source venv/bin/activate

# This will clear existing data and regenerate with proper linkage
python3 generate_all_data.py --num-users 50

deactivate
```

**Verify linkage:**
```bash
# Check MongoDB has users
docker exec lynx-mongodb mongosh idv_data --quiet --eval "db.user_profiles.countDocuments({})"

# Check PostgreSQL has matching customers
docker exec lynx-postgres psql -U admin -d insurance_db -c "SELECT COUNT(*) FROM customers;"

# The counts should match (both should be 50 if you generated 50 users)
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
