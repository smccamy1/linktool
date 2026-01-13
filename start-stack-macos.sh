#!/bin/bash
#
# Lynx IDV Stack Startup Script for macOS
# This script sets up and starts the containerized stack on macOS
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
echo -e "${GREEN}  Lynx IDV Stack Setup (macOS)${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}This script is designed for macOS. Current OS: $OSTYPE${NC}"
    echo -e "${YELLOW}For Linux, use start-stack.sh instead.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Running on macOS${NC}"

# Check Docker
if ! command_exists docker; then
    echo -e "${RED}Docker not found.${NC}"
    echo -e "${YELLOW}Please install Docker Desktop for Mac from:${NC}"
    echo -e "${YELLOW}https://www.docker.com/products/docker-desktop/${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Docker is installed${NC}"
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}Docker is not running.${NC}"
        echo -e "${YELLOW}Please start Docker Desktop and try again.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Docker is running${NC}"
fi

# Check Docker Compose
if ! docker compose version >/dev/null 2>&1; then
    echo -e "${RED}Docker Compose is not available.${NC}"
    echo -e "${YELLOW}Docker Compose should be included with Docker Desktop.${NC}"
    echo -e "${YELLOW}Please reinstall Docker Desktop.${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Docker Compose is installed${NC}"
fi

# Check Python 3
if ! command_exists python3; then
    echo -e "${RED}Python 3 not found.${NC}"
    echo -e "${YELLOW}Please install Python 3 using Homebrew:${NC}"
    echo -e "${YELLOW}  brew install python3${NC}"
    echo -e "${YELLOW}Or download from: https://www.python.org/downloads/${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Python 3 is installed${NC}"
fi

# Check pip3
if ! command_exists pip3; then
    echo -e "${YELLOW}pip3 not found. Installing...${NC}"
    python3 -m ensurepip --upgrade
    if ! command_exists pip3; then
        echo -e "${RED}Failed to install pip3. Please install manually.${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}✓ pip3 is installed${NC}"

# Navigate to script directory
cd "$SCRIPT_DIR"

# Stop and remove existing containers
echo ""
echo -e "${YELLOW}Stopping existing containers (if any)...${NC}"
docker compose down -v 2>/dev/null || true

echo ""
echo -e "${YELLOW}Note: Removing volumes to ensure clean initialization...${NC}"
docker volume rm lynx_opensearch-data 2>/dev/null || true
docker volume rm lynx_mongodb-data 2>/dev/null || true
docker volume rm lynx_nodered-data 2>/dev/null || true
docker volume rm lynx_postgres-data 2>/dev/null || true
docker volume rm lynx_rabbitmq-data 2>/dev/null || true

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
    POSTGRES_HEALTHY=$(docker inspect --format='{{.State.Health.Status}}' lynx-postgres 2>/dev/null || echo "starting")
    RABBITMQ_HEALTHY=$(docker inspect --format='{{.State.Health.Status}}' lynx-rabbitmq 2>/dev/null || echo "starting")
    
    if [ "$MONGODB_HEALTHY" == "healthy" ] && [ "$OPENSEARCH_HEALTHY" == "healthy" ] && [ "$POSTGRES_HEALTHY" == "healthy" ] && [ "$RABBITMQ_HEALTHY" == "healthy" ]; then
        echo -e "${GREEN}✓ All services are healthy!${NC}"
        break
    fi
    
    echo "  MongoDB: $MONGODB_HEALTHY | OpenSearch: $OPENSEARCH_HEALTHY | PostgreSQL: $POSTGRES_HEALTHY | RabbitMQ: $RABBITMQ_HEALTHY"
    sleep $SLEEP_INTERVAL
    ELAPSED=$((ELAPSED + SLEEP_INTERVAL))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo -e "${RED}Services did not become healthy within $MAX_WAIT seconds.${NC}"
    echo "Check the logs with: docker compose logs"
    exit 1
fi

# Additional wait for OpenSearch security to fully initialize
echo ""
echo -e "${YELLOW}Waiting for OpenSearch to be fully ready...${NC}"
echo "Testing OpenSearch connection..."

OPENSEARCH_READY=false
for i in {1..10}; do
    if curl -s http://localhost:9200/_cluster/health >/dev/null 2>&1; then
        echo -e "${GREEN}✓ OpenSearch is accessible!${NC}"
        OPENSEARCH_READY=true
        break
    fi
    echo "  Attempt $i/10 - OpenSearch not ready yet, waiting..."
    sleep 5
done

if [ "$OPENSEARCH_READY" = false ]; then
    echo -e "${RED}OpenSearch still not responding after waiting.${NC}"
    echo "Checking OpenSearch logs:"
    docker logs lynx-opensearch --tail 50
    echo ""
    echo -e "${YELLOW}You can try running the data generation manually later with:${NC}"
    echo "  source venv/bin/activate"
    echo "  python generate_idv_data.py --num-users $NUM_USERS"
fi

# Install amqplib for RabbitMQ integration in Node-RED
echo ""
echo -e "${YELLOW}Installing amqplib for RabbitMQ in Node-RED...${NC}"
if docker exec lynx-nodered npm install amqplib >/dev/null 2>&1; then
    echo -e "${GREEN}✓ amqplib installed in Node-RED${NC}"
    echo -e "${YELLOW}Restarting Node-RED to load library...${NC}"
    docker restart lynx-nodered >/dev/null 2>&1
    sleep 5
    echo -e "${GREEN}✓ Node-RED restarted${NC}"
    
    # Import the RabbitMQ work queue example flows
    echo -e "${YELLOW}Importing RabbitMQ work queue example flows...${NC}"
    sleep 2  # Wait for Node-RED to fully start
    
    # Import basic work queue flow
    if [ -f "${SCRIPT_DIR}/rabbitmq_queue_flow.json" ]; then
        if curl -s -X POST http://localhost:1880/flows \
            -H "Content-Type: application/json" \
            -H "Node-RED-Deployment-Type: flows" \
            -d @"${SCRIPT_DIR}/rabbitmq_queue_flow.json" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ RabbitMQ basic work queue flow imported${NC}"
        else
            echo -e "${YELLOW}⚠ Could not import basic flow automatically${NC}"
            echo "  You can import rabbitmq_queue_flow.json manually in Node-RED"
        fi
    else
        echo -e "${YELLOW}⚠ rabbitmq_queue_flow.json not found, skipping import${NC}"
    fi
    
    # Import advanced patterns flow (prefetch, priority, DLQ)
    if [ -f "${SCRIPT_DIR}/rabbitmq_advanced_flows.json" ]; then
        sleep 1
        if curl -s -X POST http://localhost:1880/flows \
            -H "Content-Type: application/json" \
            -H "Node-RED-Deployment-Type: flows" \
            -d @"${SCRIPT_DIR}/rabbitmq_advanced_flows.json" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ RabbitMQ advanced patterns flow imported (Prefetch, Priority, DLQ)${NC}"
        else
            echo -e "${YELLOW}⚠ Could not import advanced flow automatically${NC}"
            echo "  You can import rabbitmq_advanced_flows.json manually in Node-RED"
        fi
    else
        echo -e "${YELLOW}⚠ rabbitmq_advanced_flows.json not found, skipping import${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Could not install amqplib automatically${NC}"
    echo "  You can install it manually: docker exec lynx-nodered npm install amqplib"
fi

# Install Python dependencies and generate data
if [ "$SKIP_DATA_GENERATION" = false ] && [ "$OPENSEARCH_READY" = true ]; then
    echo ""
    echo -e "${YELLOW}Setting up Python virtual environment...${NC}"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}Creating new virtual environment...${NC}"
        python3 -m venv venv
        
        if [ ! -f "venv/bin/activate" ]; then
            echo -e "${RED}Virtual environment creation failed.${NC}"
            exit 1
        fi
        
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
    echo -e "${YELLOW}Generating complete dataset with IDV and insurance data ($NUM_USERS users)...${NC}"
    python generate_all_data.py --num-users $NUM_USERS --skip-opensearch
    
    echo ""
    echo -e "${YELLOW}Setting up OpenSearch dashboards...${NC}"
    python setup_dashboards.py
    
    deactivate
    
    echo -e "${GREEN}✓ Data generation completed!${NC}"
else
    if [ "$SKIP_DATA_GENERATION" = true ]; then
        echo ""
        echo -e "${YELLOW}Skipping data generation (--skip-data flag set)${NC}"
    fi
fi

# Display access information
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Stack is ready!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Services are accessible at:"
echo ""
echo -e "  ${GREEN}Web UI (Graph Viz):${NC}    http://localhost:5050"
echo -e "  ${GREEN}Node-RED:${NC}              http://localhost:1880"
echo -e "  ${GREEN}RabbitMQ Management:${NC}   http://localhost:15672"
echo -e "  ${GREEN}OpenSearch:${NC}            http://localhost:9200"
echo -e "  ${GREEN}OpenSearch Dashboards:${NC} http://localhost:5601"
echo -e "  ${GREEN}MongoDB:${NC}               mongodb://localhost:27017"
echo -e "  ${GREEN}PostgreSQL:${NC}            postgresql://localhost:5432/insurance_db"
echo ""
echo "Credentials:"
echo -e "  ${YELLOW}OpenSearch:${NC}  No authentication (security disabled for development)"
echo -e "  ${YELLOW}MongoDB:${NC}     admin / mongopass123"
echo -e "  ${YELLOW}PostgreSQL:${NC}  admin / postgrespass123"
echo -e "  ${YELLOW}RabbitMQ:${NC}    admin / rabbitmqpass123"
echo ""
echo -e "${GREEN}Quick Start:${NC}"
echo "  1. Open the Graph Visualization UI: ${GREEN}http://localhost:5050${NC}"
echo "  2. Left-click any user node to view IDV and insurance data"
echo "  3. Right-click any node to add it to an investigation"
echo "  4. Explore the graph to see relationships between users, verifications, and attempts"
echo ""
echo -e "${GREEN}Network Access:${NC}"
echo "  The Web UI is accessible from other machines on your network."
echo "  Find your IP: ${YELLOW}ipconfig getifaddr en0${NC} (or en1 for WiFi)"
echo "  Access from network: ${GREEN}http://YOUR_IP:5050${NC}"
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
