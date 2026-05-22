#!/bin/bash
# 完整质量检查运行脚本
# 运行所有质检工具并生成报告

set -e

echo "=========================================="
echo "  Mercator Doc Library - 质量检查"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

run_test() {
    local test_name=$1
    local test_command=$2
    
    echo -e "${BLUE}Running: ${test_name}${NC}"
    echo "----------------------------------------"
    
    if eval "$test_command"; then
        echo -e "${GREEN}✓ ${test_name} PASSED${NC}\n"
        ((PASSED_TESTS++))
    else
        echo -e "${RED}✗ ${test_name} FAILED${NC}\n"
        ((FAILED_TESTS++))
    fi
    
    ((TOTAL_TESTS++))
    echo ""
}

# Change to project root
cd "$(dirname "$0")/.."

echo -e "${YELLOW}Starting quality checks...${NC}\n"

# Test 1: Frontend route completeness
run_test "Frontend Route Completeness" \
    "python3 tests/check_frontend_routes.py"

# Test 2: API-Frontend coverage
run_test "API-Frontend Coverage" \
    "python3 tests/check_api_frontend_coverage.py"

# Test 3: Broken links check
run_test "Broken Links Check" \
    "python3 tests/check_broken_links.py"

# Test 4: P0 security fixes verification
run_test "P0 Security Fixes" \
    "python3 tests/check_p0_fixes.py"

# Test 5: Complete user flow (only if services are running)
echo -e "${BLUE}Checking if services are running...${NC}"
if curl -s http://localhost:8000/health > /dev/null 2>&1 && \
   curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}Services are running, executing E2E tests...${NC}\n"
    run_test "Complete User Flow E2E" \
        "python3 tests/test_complete_user_flow.py"
else
    echo -e "${YELLOW}Services not running, skipping E2E tests${NC}\n"
    echo -e "${YELLOW}To run E2E tests, start the services first:${NC}"
    echo -e "  - Backend: uvicorn app.main:app --reload --port 8000"
    echo -e "  - Frontend: npm run dev\n"
fi

# Print summary
echo "=========================================="
echo -e "${BLUE}  Quality Check Summary${NC}"
echo "=========================================="
echo ""
echo -e "Total Tests:  ${TOTAL_TESTS}"
echo -e "${GREEN}Passed:       ${PASSED_TESTS}${NC}"
echo -e "${RED}Failed:       ${FAILED_TESTS}${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✅ All quality checks PASSED!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some quality checks FAILED${NC}"
    echo ""
    echo -e "${YELLOW}Please fix the issues above before proceeding.${NC}"
    exit 1
fi
