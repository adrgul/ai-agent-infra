#!/bin/bash
# AI Agent AWS Deployment Script
# Deploys complete infrastructure and application to AWS

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project variables
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="$PROJECT_ROOT/terraform"
AWS_REGION="us-east-1"

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   AI Agent AWS Infrastructure Deployment      ║${NC}"
echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

if ! command -v terraform &> /dev/null; then
    echo -e "${RED}❌ Terraform not found. Please install Terraform first.${NC}"
    exit 1
fi

if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found. Please install AWS CLI first.${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found. Please install Docker first.${NC}"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS credentials not configured. Please run 'aws configure' first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All prerequisites met!${NC}"
echo ""

# Check if .env exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from example...${NC}"
    if [ -f "$PROJECT_ROOT/.env.example" ]; then
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        echo -e "${YELLOW}⚠️  Please edit .env and add your OPENAI_API_KEY, then run this script again.${NC}"
        exit 1
    else
        echo -e "${YELLOW}⚠️  No OPENAI_API_KEY found. Will use Mock LLM client.${NC}"
    fi
fi

# Load .env
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
fi

# Step 1: Terraform Infrastructure
echo -e "${BLUE}════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 1: Deploying Terraform Infrastructure${NC}"
echo -e "${BLUE}════════════════════════════════════════════════${NC}"

cd "$TERRAFORM_DIR"

echo -e "${YELLOW}🔧 Initializing Terraform...${NC}"
terraform init

echo -e "${YELLOW}📝 Planning deployment...${NC}"
terraform plan -out=tfplan

echo -e "${YELLOW}🚀 Applying Terraform configuration...${NC}"
terraform apply tfplan

echo -e "${GREEN}✅ Infrastructure deployed!${NC}"
echo ""

# Get outputs
ECR_REPO=$(terraform output -raw ecr_repository_url)
ECS_CLUSTER=$(terraform output -raw ecs_cluster_name)
ECS_SERVICE=$(terraform output -raw ecs_service_name)
ALB_DNS=$(terraform output -raw alb_dns_name)
APP_URL=$(terraform output -raw app_url)
GRAFANA_URL=$(terraform output -raw grafana_url)

echo -e "${GREEN}📦 ECR Repository: ${ECR_REPO}${NC}"
echo -e "${GREEN}🖥️  ECS Cluster: ${ECS_CLUSTER}${NC}"
echo -e "${GREEN}⚙️  ECS Service: ${ECS_SERVICE}${NC}"
echo ""

# Step 2: Build and Push Docker Image
echo -e "${BLUE}════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 2: Building and Pushing Docker Image${NC}"
echo -e "${BLUE}════════════════════════════════════════════════${NC}"

cd "$PROJECT_ROOT"

echo -e "${YELLOW}🔐 Logging into ECR...${NC}"
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPO

echo -e "${YELLOW}🏗️  Building Docker image...${NC}"
docker build -t ai-agent-app -f docker/Dockerfile .

echo -e "${YELLOW}🏷️  Tagging image for ECR...${NC}"
docker tag ai-agent-app:latest $ECR_REPO:latest

echo -e "${YELLOW}⬆️  Pushing image to ECR...${NC}"
docker push $ECR_REPO:latest

echo -e "${GREEN}✅ Docker image pushed to ECR!${NC}"
echo ""

# Step 3: Deploy ECS Service
echo -e "${BLUE}════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 3: Deploying ECS Service${NC}"
echo -e "${BLUE}════════════════════════════════════════════════${NC}"

echo -e "${YELLOW}🔄 Forcing new ECS deployment...${NC}"
aws ecs update-service \
    --cluster $ECS_CLUSTER \
    --service $ECS_SERVICE \
    --force-new-deployment \
    --region $AWS_REGION \
    > /dev/null

echo -e "${GREEN}✅ ECS service deployment triggered!${NC}"
echo ""

# Step 4: Wait for deployment
echo -e "${BLUE}════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 4: Waiting for Deployment to Complete${NC}"
echo -e "${BLUE}════════════════════════════════════════════════${NC}"

echo -e "${YELLOW}⏳ Waiting for tasks to become healthy (this may take 2-3 minutes)...${NC}"

MAX_WAIT=180  # 3 minutes
WAIT_TIME=0
INTERVAL=10

while [ $WAIT_TIME -lt $MAX_WAIT ]; do
    RUNNING=$(aws ecs describe-services \
        --cluster $ECS_CLUSTER \
        --services $ECS_SERVICE \
        --region $AWS_REGION \
        --query 'services[0].runningCount' \
        --output text)
    
    DESIRED=$(aws ecs describe-services \
        --cluster $ECS_CLUSTER \
        --services $ECS_SERVICE \
        --region $AWS_REGION \
        --query 'services[0].desiredCount' \
        --output text)
    
    echo -e "${YELLOW}   Running: $RUNNING / $DESIRED tasks${NC}"
    
    if [ "$RUNNING" -ge "$DESIRED" ] && [ "$DESIRED" -gt "0" ]; then
        echo -e "${GREEN}✅ All tasks are running!${NC}"
        break
    fi
    
    sleep $INTERVAL
    WAIT_TIME=$((WAIT_TIME + INTERVAL))
done

if [ $WAIT_TIME -ge $MAX_WAIT ]; then
    echo -e "${RED}⚠️  Timeout waiting for tasks. Check ECS console for details.${NC}"
fi

echo ""

# Step 5: Check Health
echo -e "${BLUE}════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 5: Checking Application Health${NC}"
echo -e "${BLUE}════════════════════════════════════════════════${NC}"

echo -e "${YELLOW}🏥 Waiting for health check to pass...${NC}"
sleep 30  # Wait for ALB health check

HEALTH_CHECK_URL="http://${ALB_DNS}/health"
if curl -s -f $HEALTH_CHECK_URL > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Health check passed!${NC}"
else
    echo -e "${YELLOW}⚠️  Health check pending. Application may still be starting up.${NC}"
fi

echo ""

# Final Summary
echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          🎉 DEPLOYMENT SUCCESSFUL! 🎉          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📍 Access your application:${NC}"
echo ""
echo -e "${GREEN}🌐 FastAPI Application:${NC}"
echo -e "   ${APP_URL}"
echo ""
echo -e "${GREEN}📖 API Documentation (Swagger):${NC}"
echo -e "   ${APP_URL}/docs"
echo ""
echo -e "${GREEN}📊 Grafana Dashboard:${NC}"
echo -e "   ${GRAFANA_URL}"
echo -e "   Username: admin"
echo -e "   Password: admin"
echo ""
echo -e "${GREEN}📈 Prometheus:${NC}"
echo -e "   http://${ALB_DNS}:9090"
echo ""
echo -e "${GREEN}🔍 Metrics Endpoint:${NC}"
echo -e "   ${APP_URL}/metrics"
echo ""
echo -e "${YELLOW}⏳ Note: It may take 1-2 more minutes for all services to be fully ready.${NC}"
echo ""

# Save URLs to file
cat > "$PROJECT_ROOT/DEPLOYMENT_INFO.txt" << EOF
AI Agent Deployment Information
================================
Deployment Date: $(date)

Application URLs:
-----------------
FastAPI App:        ${APP_URL}
API Docs (Swagger): ${APP_URL}/docs
API Docs (ReDoc):   ${APP_URL}/redoc
Health Check:       ${APP_URL}/health
Metrics:            ${APP_URL}/metrics

Monitoring:
-----------
Grafana:            ${GRAFANA_URL}
  - Username: admin
  - Password: admin

Prometheus:         http://${ALB_DNS}:9090

AWS Resources:
--------------
ALB DNS:            ${ALB_DNS}
ECS Cluster:        ${ECS_CLUSTER}
ECS Service:        ${ECS_SERVICE}
ECR Repository:     ${ECR_REPO}

Test the API:
-------------
curl ${APP_URL}/health

curl -X POST ${APP_URL}/run \\
  -H "Content-Type: application/json" \\
  -d '{"user_input": "What is AI?", "scenario": "simple"}'

EOF

echo -e "${GREEN}✅ Deployment info saved to: DEPLOYMENT_INFO.txt${NC}"
echo ""
