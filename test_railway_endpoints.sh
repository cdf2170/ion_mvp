#!/bin/bash

# Test script for Railway deployment endpoints
# Usage: ./test_railway_endpoints.sh [RAILWAY_URL]

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
RAILWAY_URL=${1:-"https://your-app.railway.app"}
API_TOKEN="demo-token-12345"

echo -e "${BLUE}Railway API Endpoint Test${NC}"
echo "=========================="
echo "Railway URL: $RAILWAY_URL"
echo "API Token: $API_TOKEN"
echo ""

# Function to test endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local description=$3
    local use_auth=${4:-true}
    
    echo -e "${YELLOW}Testing:${NC} $description"
    echo "Endpoint: $method $endpoint"
    
    if [ "$use_auth" = "true" ]; then
        response=$(curl -s -w "\n%{http_code}" \
            -X "$method" \
            -H "Authorization: Bearer $API_TOKEN" \
            -H "Content-Type: application/json" \
            "$RAILWAY_URL$endpoint" 2>/dev/null)
    else
        response=$(curl -s -w "\n%{http_code}" \
            -X "$method" \
            -H "Content-Type: application/json" \
            "$RAILWAY_URL$endpoint" 2>/dev/null)
    fi
    
    # Split response and status code
    body=$(echo "$response" | sed '$d')
    status_code=$(echo "$response" | tail -n1)
    
    case $status_code in
        200)
            echo -e "Status: ${GREEN}$status_code OK${NC}"
            # Show preview of response
            if echo "$body" | jq . >/dev/null 2>&1; then
                echo "Response preview:"
                echo "$body" | jq -r 'if type == "object" then 
                    if .total then "  Total items: \(.total)"
                    elif .message then "  Message: \(.message)"
                    elif .status then "  Status: \(.status)"
                    else "  Type: object with \(keys | length) keys"
                    end
                elif type == "array" then "  Array with \(length) items"
                else "  Value: \(.)"
                end'
            else
                echo "Response: ${body:0:100}..."
            fi
            ;;
        401)
            echo -e "Status: ${RED}$status_code UNAUTHORIZED${NC}"
            echo "❌ Authentication failed - check token"
            ;;
        404)
            echo -e "Status: ${RED}$status_code NOT FOUND${NC}"
            echo "❌ Endpoint not found - check deployment"
            ;;
        422)
            echo -e "Status: ${YELLOW}$status_code VALIDATION ERROR${NC}"
            echo "Response: $body"
            ;;
        000)
            echo -e "Status: ${RED}CONNECTION FAILED${NC}"
            echo "❌ Cannot connect to server"
            ;;
        *)
            echo -e "Status: ${YELLOW}$status_code${NC}"
            echo "Response: ${body:0:100}..."
            ;;
    esac
    echo ""
}

echo "1. HEALTH CHECK ENDPOINTS (No Auth)"
echo "-----------------------------------"
test_endpoint "GET" "/" "Root endpoint" false
test_endpoint "GET" "/health" "Health check" false
test_endpoint "GET" "/readiness" "Readiness check" false
test_endpoint "GET" "/liveness" "Liveness check" false

echo "2. MAIN API ENDPOINTS (With Auth)"
echo "--------------------------------"
test_endpoint "GET" "/api/v1/users" "Users list"
test_endpoint "GET" "/api/v1/devices" "Devices list"
test_endpoint "GET" "/api/v1/policies" "Policies list"
test_endpoint "GET" "/api/v1/apis" "API connections list"
test_endpoint "GET" "/api/v1/history/config" "Configuration history"

echo "3. SUMMARY ENDPOINTS"
echo "-------------------"
test_endpoint "GET" "/api/v1/devices/summary/counts" "Device counts"
test_endpoint "GET" "/api/v1/policies/summary/by-type" "Policy summary"
test_endpoint "GET" "/api/v1/apis/status/summary" "API status summary"

echo "4. AUTHENTICATION TEST (Should Fail)"
echo "------------------------------------"
test_endpoint "GET" "/api/v1/users" "Users without auth" false

echo "SUMMARY"
echo "======="
echo "✅ 200 = Success"
echo "❌ 401 = Authentication required"
echo "❌ 404 = Endpoint not found (deployment issue)"
echo "⚠️  422 = Validation error"
echo ""
echo "Common issues:"
echo "- 404 on /api/v1/* = Check Railway deployment logs"
echo "- 401 = Missing or wrong bearer token"
echo "- Connection failed = Wrong URL or server down"
