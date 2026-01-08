#!/bin/bash
#
# Data Verification Script
# Checks if IDV and insurance data are properly linked
#

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Data Linkage Verification${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check MongoDB
echo -e "${YELLOW}[1/6] Checking MongoDB data...${NC}"
MONGO_USERS=$(docker exec lynx-mongodb mongosh idv_data --quiet --eval "db.user_profiles.countDocuments({})" 2>/dev/null || echo "ERROR")

if [ "$MONGO_USERS" = "ERROR" ]; then
    echo -e "${RED}✗ Cannot connect to MongoDB${NC}"
    exit 1
else
    echo -e "${GREEN}✓ MongoDB users: $MONGO_USERS${NC}"
fi
echo ""

# Check PostgreSQL
echo -e "${YELLOW}[2/6] Checking PostgreSQL data...${NC}"
PG_CUSTOMERS=$(docker exec lynx-postgres psql -U admin -d insurance_db -t -c "SELECT COUNT(*) FROM customers;" 2>/dev/null | xargs || echo "ERROR")

if [ "$PG_CUSTOMERS" = "ERROR" ]; then
    echo -e "${RED}✗ Cannot connect to PostgreSQL${NC}"
    exit 1
else
    echo -e "${GREEN}✓ PostgreSQL customers: $PG_CUSTOMERS${NC}"
fi
echo ""

# Compare counts
echo -e "${YELLOW}[3/6] Checking data linkage...${NC}"
if [ "$MONGO_USERS" != "$PG_CUSTOMERS" ]; then
    echo -e "${RED}✗ MISMATCH: MongoDB has $MONGO_USERS users but PostgreSQL has $PG_CUSTOMERS customers${NC}"
    echo -e "${RED}  This means data was not generated with proper linkage!${NC}"
else
    echo -e "${GREEN}✓ Counts match ($MONGO_USERS users = $PG_CUSTOMERS customers)${NC}"
fi
echo ""

# Get sample user ID from MongoDB
echo -e "${YELLOW}[4/6] Getting sample user ID from MongoDB...${NC}"
SAMPLE_USER=$(docker exec lynx-mongodb mongosh idv_data --quiet --eval "db.user_profiles.findOne({}, {userId: 1}).userId" 2>/dev/null | grep -v "^$")

if [ -z "$SAMPLE_USER" ]; then
    echo -e "${RED}✗ No users found in MongoDB${NC}"
else
    echo -e "${GREEN}✓ Sample user ID: $SAMPLE_USER${NC}"
    
    # Check if this user exists in PostgreSQL
    echo ""
    echo -e "${YELLOW}[5/6] Checking if sample user exists in PostgreSQL...${NC}"
    PG_MATCH=$(docker exec lynx-postgres psql -U admin -d insurance_db -t -c "SELECT COUNT(*) FROM customers WHERE user_id = '$SAMPLE_USER';" 2>/dev/null | xargs)
    
    if [ "$PG_MATCH" = "1" ]; then
        echo -e "${GREEN}✓ User $SAMPLE_USER found in PostgreSQL customers table${NC}"
    else
        echo -e "${RED}✗ User $SAMPLE_USER NOT found in PostgreSQL${NC}"
        echo -e "${RED}  This confirms data linkage is broken!${NC}"
    fi
fi
echo ""

# Check for multiple MongoDB instances
echo -e "${YELLOW}[6/6] Checking for MongoDB conflicts...${NC}"
MONGO_PROCS=$(lsof -i :27017 2>/dev/null | grep LISTEN | wc -l || echo "0")

if [ "$MONGO_PROCS" -gt 1 ]; then
    echo -e "${RED}✗ WARNING: Multiple processes listening on port 27017${NC}"
    lsof -i :27017 2>/dev/null | grep LISTEN
    echo ""
    echo -e "${YELLOW}This causes data to go to different MongoDB instances!${NC}"
    echo "Run: ./check_mongodb.sh to see details and fix"
else
    echo -e "${GREEN}✓ Only one MongoDB process detected${NC}"
fi
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ "$MONGO_USERS" = "$PG_CUSTOMERS" ] && [ "$PG_MATCH" = "1" ]; then
    echo -e "${GREEN}✓ Data appears to be properly linked${NC}"
    echo ""
    echo "If UI still shows no insurance data:"
    echo "  1. Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)"
    echo "  2. Clear browser cache"
    echo "  3. Restart web-ui container: docker restart lynx-web-ui"
    echo "  4. Check browser console for errors (F12)"
else
    echo -e "${RED}✗ Data linkage is broken${NC}"
    echo ""
    echo "To fix, run:"
    echo "  source venv/bin/activate"
    echo "  python3 generate_all_data.py --num-users 50"
    echo "  deactivate"
fi
echo ""
