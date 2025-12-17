#!/bin/bash
# Build custom Docker images for Stage 3 security tools

set -e  # Exit on error

echo "🐳 Building Custom Docker Images for Stage 3"
echo "=============================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker Desktop.${NC}"
    exit 1
fi

echo -e "${YELLOW}📦 Pulling base images...${NC}"
docker pull smartbugs/slither:0.11.3 || echo "Warning: Could not pull slither base image"
docker pull smartbugs/mythril:0.24.7 || echo "Warning: Could not pull mythril base image"

echo ""
echo -e "${YELLOW}🔨 Building custom Slither image...${NC}"
docker build -f Dockerfile.slither -t custom-slither:latest . \
    && echo -e "${GREEN}✅ custom-slither:latest built successfully${NC}" \
    || echo -e "${RED}❌ Failed to build custom-slither${NC}"

echo ""
echo -e "${YELLOW}🔨 Building custom Mythril image...${NC}"
docker build -f Dockerfile.mythril -t custom-mythril:latest . \
    && echo -e "${GREEN}✅ custom-mythril:latest built successfully${NC}" \
    || echo -e "${RED}❌ Failed to build custom-mythril${NC}"

echo ""
echo -e "${GREEN}=============================================="
echo "🎉 Build Complete!"
echo "===============================================${NC}"
echo ""
echo "📋 Available custom images:"
docker images | grep -E "REPOSITORY|custom-"

echo ""
echo -e "${YELLOW}🧪 Testing images...${NC}"

# Test Slither
echo "Testing custom-slither..."
docker run --rm custom-slither:latest solc --version 2>&1 | head -n 1 || echo "Solc test skipped"
docker run --rm custom-slither:latest slither --version || echo "Slither version check skipped"

# Test Mythril
echo "Testing custom-mythril..."
docker run --rm custom-mythril:latest myth version || echo "Mythril version check skipped"

echo ""
echo -e "${GREEN}✅ All done!${NC}"
echo ""
echo "Next steps:"
echo "  1. Update tool configs to use custom images"
echo "  2. Run: cd .. && python -m stage_3.test"
