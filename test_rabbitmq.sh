#!/bin/bash
#
# Quick RabbitMQ Health Check Script
# Tests basic connectivity and service status
#

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

RABBITMQ_HOST=${RABBITMQ_HOST:-localhost}
RABBITMQ_USER=${RABBITMQ_USER:-admin}
RABBITMQ_PASS=${RABBITMQ_PASS:-rabbitmqpass123}
MANAGEMENT_URL="http://${RABBITMQ_HOST}:15672"

echo "========================================="
echo "RabbitMQ Quick Health Check"
echo "========================================="
echo ""

# Test 1: Check if container is running
echo "1. Checking Docker container status..."
if docker ps | grep -q lynx-rabbitmq; then
    STATUS=$(docker inspect --format='{{.State.Status}}' lynx-rabbitmq 2>/dev/null || echo "unknown")
    HEALTH=$(docker inspect --format='{{.State.Health.Status}}' lynx-rabbitmq 2>/dev/null || echo "no healthcheck")
    echo -e "${GREEN}✓${NC} Container is running"
    echo "  Status: $STATUS"
    echo "  Health: $HEALTH"
else
    echo -e "${RED}✗${NC} Container is not running"
    exit 1
fi

# Test 2: Check port bindings
echo ""
echo "2. Checking port bindings..."
AMQP_PORT=$(docker port lynx-rabbitmq 5672 2>/dev/null || echo "not bound")
MGMT_PORT=$(docker port lynx-rabbitmq 15672 2>/dev/null || echo "not bound")
echo "  AMQP Port (5672): $AMQP_PORT"
echo "  Management Port (15672): $MGMT_PORT"

if [[ "$AMQP_PORT" == *"0.0.0.0"* ]]; then
    echo -e "${GREEN}✓${NC} AMQP port accessible from network"
else
    echo -e "${YELLOW}⚠${NC} AMQP port may only be accessible locally"
fi

if [[ "$MGMT_PORT" == *"0.0.0.0"* ]]; then
    echo -e "${GREEN}✓${NC} Management port accessible from network"
else
    echo -e "${YELLOW}⚠${NC} Management port may only be accessible locally"
fi

# Test 3: Check logs for errors
echo ""
echo "3. Checking recent logs for errors..."
ERROR_COUNT=$(docker logs lynx-rabbitmq --tail 50 2>&1 | grep -i "error\|critical\|failed" | wc -l | tr -d ' ')
if [ "$ERROR_COUNT" -eq 0 ]; then
    echo -e "${GREEN}✓${NC} No recent errors in logs"
else
    echo -e "${YELLOW}⚠${NC} Found $ERROR_COUNT error message(s) in recent logs"
    echo "  Run 'docker logs lynx-rabbitmq' to investigate"
fi

# Test 4: Test Management API
echo ""
echo "4. Testing Management API..."
if curl -s -u "$RABBITMQ_USER:$RABBITMQ_PASS" "$MANAGEMENT_URL/api/overview" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Management API is accessible"
    
    # Get version info
    VERSION=$(curl -s -u "$RABBITMQ_USER:$RABBITMQ_PASS" "$MANAGEMENT_URL/api/overview" | python3 -c "import sys, json; print(json.load(sys.stdin).get('rabbitmq_version', 'unknown'))" 2>/dev/null || echo "unknown")
    echo "  RabbitMQ Version: $VERSION"
else
    echo -e "${RED}✗${NC} Management API is not accessible"
    echo "  URL: $MANAGEMENT_URL"
    echo "  Check credentials: $RABBITMQ_USER / $RABBITMQ_PASS"
fi

# Test 5: Check vhosts
echo ""
echo "5. Checking virtual hosts..."
VHOSTS=$(curl -s -u "$RABBITMQ_USER:$RABBITMQ_PASS" "$MANAGEMENT_URL/api/vhosts" 2>/dev/null)
if [ $? -eq 0 ]; then
    VHOST_COUNT=$(echo "$VHOSTS" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
    echo -e "${GREEN}✓${NC} Found $VHOST_COUNT virtual host(s)"
else
    echo -e "${YELLOW}⚠${NC} Could not retrieve vhost information"
fi

# Test 6: Check queues
echo ""
echo "6. Checking existing queues..."
QUEUES=$(curl -s -u "$RABBITMQ_USER:$RABBITMQ_PASS" "$MANAGEMENT_URL/api/queues" 2>/dev/null)
if [ $? -eq 0 ]; then
    QUEUE_COUNT=$(echo "$QUEUES" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
    echo "  Active queues: $QUEUE_COUNT"
    
    if [ "$QUEUE_COUNT" -gt 0 ]; then
        echo "  Queue details:"
        echo "$QUEUES" | python3 -c "
import sys, json
queues = json.load(sys.stdin)
for q in queues[:5]:  # Show first 5
    print(f\"    - {q['name']}: {q.get('messages', 0)} messages\")
" 2>/dev/null || echo "    (Could not parse queue details)"
    fi
else
    echo -e "${YELLOW}⚠${NC} Could not retrieve queue information"
fi

# Test 7: Test from inside Docker network (simulating Node-RED)
echo ""
echo "7. Testing from Docker network (simulating Node-RED)..."
if docker exec lynx-rabbitmq rabbitmq-diagnostics -q ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} RabbitMQ is responding to internal health checks"
else
    echo -e "${RED}✗${NC} RabbitMQ health check failed"
fi

# Test connection using hostname that Node-RED would use
if docker run --rm --network lynx_lynx-network alpine ping -c 1 rabbitmq > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} RabbitMQ hostname 'rabbitmq' is reachable from Docker network"
else
    echo -e "${YELLOW}⚠${NC} Could not ping 'rabbitmq' hostname from Docker network"
fi

# Test 8: Check Node-RED AMQP nodes
echo ""
echo "8. Checking Node-RED AMQP integration..."
if docker exec lynx-nodered ls /data/node_modules 2>/dev/null | grep -q amqp; then
    echo -e "${GREEN}✓${NC} AMQP nodes are installed in Node-RED"
    AMQP_MODULES=$(docker exec lynx-nodered ls /data/node_modules 2>/dev/null | grep amqp)
    echo "  Installed modules:"
    echo "$AMQP_MODULES" | sed 's/^/    - /'
else
    echo -e "${YELLOW}⚠${NC} AMQP nodes not found in Node-RED"
    echo "  Install with: docker exec lynx-nodered sh -c 'cd /data && npm install node-red-contrib-amqp'"
fi

# Summary
echo ""
echo "========================================="
echo "Summary"
echo "========================================="
echo ""
echo "Management UI: ${MANAGEMENT_URL}"
echo "Credentials: ${RABBITMQ_USER} / ${RABBITMQ_PASS}"
echo ""
echo "Node-RED Connection String:"
echo "  amqp://${RABBITMQ_USER}:${RABBITMQ_PASS}@rabbitmq:5672"
echo ""
echo "To run comprehensive tests:"
echo "  python3 test_rabbitmq.py"
echo ""
