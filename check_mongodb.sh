#!/bin/bash
# Check for MongoDB process conflicts

echo "Checking for MongoDB processes on port 27017..."
echo ""

MONGO_PROCS=$(lsof -i :27017 2>/dev/null | grep LISTEN)

if [ -z "$MONGO_PROCS" ]; then
    echo "❌ No MongoDB processes found on port 27017"
    echo "   Make sure Docker containers are running: docker compose ps"
    exit 1
fi

# Count processes
NUM_PROCS=$(echo "$MONGO_PROCS" | wc -l | tr -d ' ')

if [ "$NUM_PROCS" -gt 1 ]; then
    echo "⚠️  WARNING: Multiple MongoDB processes detected!"
    echo ""
    echo "$MONGO_PROCS"
    echo ""
    echo "This will cause data to be split between databases."
    echo ""
    echo "To fix:"
    echo "  1. Find the local mongod process PID (not com.docker)"
    LOCAL_PID=$(echo "$MONGO_PROCS" | grep mongod | grep -v docker | awk '{print $2}' | head -1)
    if [ ! -z "$LOCAL_PID" ]; then
        echo "  2. Stop it: kill $LOCAL_PID"
    fi
    echo "  3. Or stop via Homebrew: brew services stop mongodb-community"
    echo ""
    exit 2
else
    echo "✓ Only Docker MongoDB is running (correct setup)"
    echo ""
    echo "$MONGO_PROCS"
    echo ""
fi
