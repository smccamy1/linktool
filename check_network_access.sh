#!/bin/bash
#
# Network Access Diagnostic Script
# Checks if the Web UI is properly configured for network access
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Lynx Web UI Network Diagnostic${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if Docker is running
echo -e "${YELLOW}[1/8] Checking if Docker is running...${NC}"
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"
echo ""

# Check if container is running
echo -e "${YELLOW}[2/8] Checking if web-ui container is running...${NC}"
if ! docker ps | grep -q lynx-web-ui; then
    echo -e "${RED}✗ lynx-web-ui container is not running${NC}"
    echo "Run: docker compose up -d"
    exit 1
fi
echo -e "${GREEN}✓ Container is running${NC}"
echo ""

# Check container logs for binding information
echo -e "${YELLOW}[3/8] Checking Flask binding configuration...${NC}"
LOGS=$(docker logs lynx-web-ui 2>&1 | tail -20)
if echo "$LOGS" | grep -q "Running on all addresses"; then
    echo -e "${GREEN}✓ Flask is bound to 0.0.0.0 (all interfaces)${NC}"
elif echo "$LOGS" | grep -q "127.0.0.1"; then
    echo -e "${RED}✗ Flask is bound to localhost only${NC}"
    echo "This is a configuration error. Flask should bind to 0.0.0.0"
else
    echo -e "${YELLOW}⚠ Cannot determine Flask binding from logs${NC}"
fi
echo ""

# Check port binding with netstat/ss
echo -e "${YELLOW}[4/8] Checking port 5050 binding on host...${NC}"
if command -v ss >/dev/null 2>&1; then
    PORT_INFO=$(ss -tlnp 2>/dev/null | grep ":5050" || true)
elif command -v netstat >/dev/null 2>&1; then
    PORT_INFO=$(netstat -tlnp 2>/dev/null | grep ":5050" || true)
else
    PORT_INFO=""
fi

if [ -n "$PORT_INFO" ]; then
    echo "$PORT_INFO"
    if echo "$PORT_INFO" | grep -q "0.0.0.0:5050\|:::5050\|\*:5050"; then
        echo -e "${GREEN}✓ Port 5050 is bound to all interfaces${NC}"
    else
        echo -e "${RED}✗ Port 5050 is NOT bound to all interfaces${NC}"
        echo "This means Docker is not exposing the port correctly"
    fi
else
    echo -e "${RED}✗ Port 5050 is not listening${NC}"
    echo "Docker may not be exposing the port correctly"
fi
echo ""

# Check local access
echo -e "${YELLOW}[5/8] Testing local access (localhost:5050)...${NC}"
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5050 | grep -q "200"; then
    echo -e "${GREEN}✓ Local access works${NC}"
else
    echo -e "${RED}✗ Local access failed${NC}"
    echo "The web server is not responding on localhost"
fi
echo ""

# Get all IP addresses
echo -e "${YELLOW}[6/8] Detecting server IP addresses...${NC}"
if command -v ip >/dev/null 2>&1; then
    IPS=$(ip addr show | grep "inet " | grep -v "127.0.0.1" | awk '{print $2}' | cut -d/ -f1)
elif command -v ifconfig >/dev/null 2>&1; then
    IPS=$(ifconfig | grep "inet " | grep -v "127.0.0.1" | awk '{print $2}')
else
    IPS=$(hostname -I 2>/dev/null | tr ' ' '\n' | grep -v "^$")
fi

if [ -z "$IPS" ]; then
    echo -e "${RED}✗ Could not detect IP addresses${NC}"
else
    echo -e "${GREEN}Server IP addresses:${NC}"
    for IP in $IPS; do
        echo "  $IP"
    done
fi
echo ""

# Test access via server IP
echo -e "${YELLOW}[7/8] Testing access via server IP...${NC}"
FIRST_IP=$(echo "$IPS" | head -n1)
if [ -n "$FIRST_IP" ]; then
    echo "Testing http://$FIRST_IP:5050"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://$FIRST_IP:5050 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✓ Access via IP works${NC}"
    else
        echo -e "${RED}✗ Access via IP failed (HTTP $HTTP_CODE)${NC}"
        echo "This suggests a firewall or routing issue"
    fi
else
    echo -e "${YELLOW}⚠ Skipping - no IP address found${NC}"
fi
echo ""

# Check firewall status
echo -e "${YELLOW}[8/8] Checking firewall configuration...${NC}"
if command -v ufw >/dev/null 2>&1; then
    UFW_STATUS=$(sudo ufw status 2>/dev/null | grep "5050" || echo "not found")
    if echo "$UFW_STATUS" | grep -q "5050.*ALLOW"; then
        echo -e "${GREEN}✓ UFW: Port 5050 is allowed${NC}"
        echo "$UFW_STATUS"
    else
        echo -e "${RED}✗ UFW: Port 5050 is NOT in allowed rules${NC}"
        echo "Run: sudo ufw allow 5050/tcp"
    fi
elif command -v firewall-cmd >/dev/null 2>&1; then
    if sudo firewall-cmd --list-ports 2>/dev/null | grep -q "5050"; then
        echo -e "${GREEN}✓ firewalld: Port 5050 is open${NC}"
    else
        echo -e "${RED}✗ firewalld: Port 5050 is NOT open${NC}"
        echo "Run: sudo firewall-cmd --permanent --add-port=5050/tcp && sudo firewall-cmd --reload"
    fi
elif command -v iptables >/dev/null 2>&1; then
    if sudo iptables -L -n | grep -q "5050"; then
        echo -e "${GREEN}✓ iptables has rules for port 5050${NC}"
    else
        echo -e "${YELLOW}⚠ No iptables rules found for port 5050${NC}"
        echo "You may need to add an iptables rule"
    fi
else
    echo -e "${YELLOW}⚠ No firewall detected (ufw, firewalld, or iptables)${NC}"
fi
echo ""

# Check Docker iptables rules
echo -e "${YELLOW}Checking Docker iptables rules...${NC}"
if command -v iptables >/dev/null 2>&1; then
    DOCKER_RULES=$(sudo iptables -t nat -L DOCKER -n 2>/dev/null | grep "5050" || echo "")
    if [ -n "$DOCKER_RULES" ]; then
        echo -e "${GREEN}✓ Docker NAT rules found for port 5050:${NC}"
        echo "$DOCKER_RULES"
    else
        echo -e "${RED}✗ No Docker NAT rules found for port 5050${NC}"
        echo "This might indicate a Docker networking issue"
        echo "Try: docker compose down && docker compose up -d"
    fi
else
    echo -e "${YELLOW}⚠ Cannot check iptables${NC}"
fi
echo ""

# Summary and recommendations
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Summary & Recommendations${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ -n "$FIRST_IP" ]; then
    echo -e "${GREEN}Your Web UI should be accessible at:${NC}"
    for IP in $IPS; do
        echo "  http://$IP:5050"
    done
    echo ""
fi

echo -e "${YELLOW}If you still cannot access from remote machines:${NC}"
echo ""
echo "1. Verify firewall is open:"
echo "   sudo ufw allow 5050/tcp"
echo "   sudo ufw status"
echo ""
echo "2. Check if you're on a cloud provider (AWS, Azure, GCP):"
echo "   - Open port 5050 in Security Group / Network ACL"
echo "   - Ensure VM has public IP assigned"
echo ""
echo "3. Restart Docker networking:"
echo "   docker compose down"
echo "   docker compose up -d"
echo ""
echo "4. Test from remote machine:"
echo "   curl -v http://$FIRST_IP:5050"
echo "   telnet $FIRST_IP 5050"
echo ""
echo "5. Check container logs:"
echo "   docker logs lynx-web-ui"
echo ""
