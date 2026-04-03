#!/bin/bash
# Synapse Complete Startup Script
# Starts API server and Dashboard in the correct order

echo "🧠 SYNAPSE - AI Workspace Engine"
echo "=================================="
echo ""
echo "Starting all services..."
echo ""

# Function to check if port is in use
check_port() {
    netstat -an | grep -E "$$1" > /dev/null
    return $?
}

# Check for existing services
echo "Checking ports..."
if netstat -an | grep -q ":8000.*LISTEN"; then
    echo "⚠️  Port 8000 (API) already in use"
else
    echo "✓ Port 8000 available"
fi

if netstat -an | grep -q ":3000.*LISTEN"; then
    echo "⚠️  Port 3000 (Dashboard) already in use"
else
    echo "✓ Port 3000 available"
fi

echo ""
echo "Starting API Server on port 8000..."
cd "$(dirname "$0")"
python -m uvicorn api.server:app --reload --host 0.0.0.0 --port 8000 &
API_PID=$!
echo "API Server PID: $API_PID"

sleep 2

echo ""
echo "Starting Dashboard on port 3000..."
cd dashboard
npm run dev &
DASH_PID=$!
echo "Dashboard PID: $DASH_PID"

echo ""
echo "=================================="
echo "✓ Services Started"
echo "=================================="
echo "API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "Dashboard: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for both processes
wait $API_PID $DASH_PID
