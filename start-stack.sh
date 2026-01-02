#!/bin/bash
#
# Lynx IDV Stack Startup Script
# This script sets up and starts the containerized stack on Ubuntu
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NUM_USERS=100
SKIP_DATA_GENERATION=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--num-users)
            NUM_USERS="$2"
            shift 2
            ;;
        --skip-data)
            SKIP_DATA_GENERATION=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -n, --num-users NUM    Number of fake users to generate (default: 100)"
            echo "  --skip-data           Skip data generation"
            echo "  -h, --help            Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Lynx IDV Stack Setup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if running on Ubuntu/Debian
if [ -f /etc/os-release ]; then
    . /etc/os-release
    if [[ "$ID" != "ubuntu" && "$ID_LIKE" != *"debian"* ]]; then
        echo -e "${YELLOW}Warning: This script is designed for Ubuntu. Your OS: $ID${NC}"
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    echo -e "${YELLOW}Warning: Cannot detect OS. Proceeding anyway...${NC}"
fi

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Docker
install_docker() {
    echo -e "${YELLOW}Installing Docker...${NC}"
    
    # Update apt package index
    sudo apt-get update
    
    # Install prerequisites
    sudo apt-get install -y \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    
    # Add Docker's official GPG key
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    # Set up the repository
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker Engine
    sudo apt-get update
    
    # Use DEBIAN_FRONTEND to avoid interactive prompts
    DEBIAN_FRONTEND=noninteractive sudo apt-get install -y \
        docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Start Docker service explicitly
    echo -e "${YELLOW}Starting Docker service...${NC}"
    sudo systemctl start docker || true
    sudo systemctl enable docker || true
    
    # Wait for Docker to be ready
    echo -e "${YELLOW}Waiting for Docker daemon to be ready...${NC}"
    MAX_WAIT=30
    ELAPSED=0
    while [ $ELAPSED -lt $MAX_WAIT ]; do
        if sudo docker info >/dev/null 2>&1; then
            break
        fi
        sleep 2
        ELAPSED=$((ELAPSED + 2))
    done
    
    # Add current user to docker group
    sudo usermod -aG docker $USER
    
    echo -e "${GREEN}Docker installed successfully!${NC}"
    echo -e "${YELLOW}Note: You may need to log out and back in for group changes to take effect.${NC}"
    echo -e "${YELLOW}Or run: newgrp docker${NC}"
}

# Function to install Python and pip
install_python() {
    echo -e "${YELLOW}Installing Python 3, pip, and venv...${NC}"
    sudo apt-get update
    DEBIAN_FRONTEND=noninteractive sudo apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        build-essential
    echo -e "${GREEN}Python installed successfully!${NC}"
    
    # Verify pip3 is working
    if ! command_exists pip3; then
        echo -e "${YELLOW}Ensuring pip3 is available...${NC}"
        python3 -m ensurepip --upgrade
    fi
    
    echo -e "${GREEN}✓ pip3 is ready${NC}"
}

# Check and install Docker
if ! command_exists docker; then
    echo -e "${YELLOW}Docker not found.${NC}"
    read -p "Would you like to install Docker? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_docker
    else
        echo -e "${RED}Docker is required to run this stack. Exiting.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ Docker is installed${NC}"
fi

# Check Docker Compose
if ! docker compose version >/dev/null 2>&1; then
    echo -e "${RED}Docker Compose is not available. Please install Docker Compose.${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Docker Compose is installed${NC}"
fi

# Check and install Python
if ! command_exists python3; then
    echo -e "${YELLOW}Python 3 not found.${NC}"
    read -p "Would you like to install Python 3? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_python
    else
        echo -e "${RED}Python 3 is required for data generation. Exiting.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ Python 3 is installed${NC}"
fi

# Ensure pip3 is installed
if ! command_exists pip3; then
    echo -e "${YELLOW}pip3 not found. Installing...${NC}"
    sudo apt-get update
    DEBIAN_FRONTEND=noninteractive sudo apt-get install -y python3-pip python3-venv
    echo -e "${GREEN}✓ pip3 is installed${NC}"
else
    echo -e "${GREEN}✓ pip3 is installed${NC}"
fi

# Navigate to script directory
cd "$SCRIPT_DIR"

# Stop and remove existing containers
echo ""
echo -e "${YELLOW}Stopping existing containers (if any)...${NC}"
docker compose down -v 2>/dev/null || true

# Pull latest images
echo ""
echo -e "${YELLOW}Pulling Docker images...${NC}"
docker compose pull

# Start the stack
echo ""
echo -e "${YELLOW}Starting the containerized stack...${NC}"
docker compose up -d

# Wait for services to be healthy
echo ""
echo -e "${YELLOW}Waiting for services to be ready...${NC}"
echo "This may take a few minutes..."

MAX_WAIT=300  # 5 minutes
ELAPSED=0
SLEEP_INTERVAL=10

while [ $ELAPSED -lt $MAX_WAIT ]; do
    MONGODB_HEALTHY=$(docker inspect --format='{{.State.Health.Status}}' lynx-mongodb 2>/dev/null || echo "starting")
    OPENSEARCH_HEALTHY=$(docker inspect --format='{{.State.Health.Status}}' lynx-opensearch 2>/dev/null || echo "starting")
    
    if [ "$MONGODB_HEALTHY" == "healthy" ] && [ "$OPENSEARCH_HEALTHY" == "healthy" ]; then
        echo -e "${GREEN}✓ All services are healthy!${NC}"
        break
    fi
    
    echo "  MongoDB: $MONGODB_HEALTHY | OpenSearch: $OPENSEARCH_HEALTHY"
    sleep $SLEEP_INTERVAL
    ELAPSED=$((ELAPSED + SLEEP_INTERVAL))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo -e "${RED}Services did not become healthy within $MAX_WAIT seconds.${NC}"
    echo "Check the logs with: docker compose logs"
    exit 1
fi

# Install Python dependencies and generate data
if [ "$SKIP_DATA_GENERATION" = false ]; then
    echo ""
    echo -e "${YELLOW}Setting up Python virtual environment...${NC}"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}Creating new virtual environment...${NC}"
        python3 -m venv venv
        echo -e "${GREEN}✓ Virtual environment created${NC}"
    else
        echo -e "${GREEN}✓ Virtual environment already exists${NC}"
    fi
    
    # Activate virtual environment and install dependencies
    echo -e "${YELLOW}Activating virtual environment and installing dependencies...${NC}"
    source venv/bin/activate
    
    # Upgrade pip in the venv
    python -m pip install --upgrade pip
    
    # Install requirements
    pip install -r requirements.txt
    
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
    
    echo ""
    echo -e "${YELLOW}Generating IDV data ($NUM_USERS users)...${NC}"
    python generate_idv_data.py --num-users $NUM_USERS
    
    deactivate
    
    echo -e "${GREEN}✓ Data generation completed!${NC}"
else
    echo ""
    echo -e "${YELLOW}Skipping data generation (--skip-data flag set)${NC}"
fi

# Display access information
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Stack is ready!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Services are accessible at:"
echo ""
echo -e "  ${GREEN}Node-RED:${NC}              http://localhost:1880"
echo -e "  ${GREEN}OpenSearch:${NC}            https://localhost:9200"
echo -e "  ${GREEN}OpenSearch Dashboards:${NC} http://localhost:5601"
echo -e "  ${GREEN}MongoDB:${NC}               mongodb://localhost:27017"
echo ""
echo "Credentials:"
echo -e "  ${YELLOW}OpenSearch:${NC}  admin / Admin123!"
echo -e "  ${YELLOW}MongoDB:${NC}     admin / mongopass123"
echo ""
echo "To view logs:"
echo "  docker compose logs -f"
echo ""
echo "To stop the stack:"
echo "  docker compose down"
echo ""
echo "To stop and remove all data:"
echo "  docker compose down -v"
echo ""
