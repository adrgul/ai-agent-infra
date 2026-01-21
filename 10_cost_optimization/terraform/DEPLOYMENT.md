# AWS ECS Deployment Guide

This guide walks you through deploying the AI Agent application to AWS ECS using Terraform and GitHub Actions.

## 🎯 Architecture Overview

**Infrastructure:**
- **VPC**: Custom VPC with public/private subnets across 2 AZs
- **ECS Fargate**: Serverless container hosting (t3.small equivalent)
- **ECR**: Docker image registry
- **Application Load Balancer**: Public endpoint with health checks
- **CloudWatch**: Centralized logging and monitoring

**Containers (Single ECS Task):**
- FastAPI app (port 8000)
- Prometheus (port 9090)
- Grafana (port 3000)

## 📋 Prerequisites

1. ✅ AWS Account (Account ID: 021580456215)
2. ✅ GitHub repo: `adrgul/ai-agent-infra`
3. ✅ IAM Role for OIDC: `terraform-github-deployer` (already configured)
4. ✅ OpenAI API key

## 🚀 Deployment Steps

### Step 1: Add GitHub Secret

1. Go to your GitHub repo: https://github.com/adrgul/ai-agent-infra
2. Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Name: `OPENAI_API_KEY`
5. Value: Your OpenAI API key (sk-...)
6. Click "Add secret"

### Step 2: Bootstrap Terraform State (First Time Only)

The backend configuration is already commented out in `backend.tf` for bootstrapping.

**Run locally:**

```bash
cd terraform

# Initialize Terraform
terraform init

# Review what will be created
terraform plan

# Create S3 bucket and DynamoDB table for state
terraform apply

# Expected output:
# - S3 bucket: terraform-state-adriangulyas-ai-agent
# - DynamoDB table: terraform-state-lock
```

### Step 3: Enable Remote Backend

```bash
# Uncomment backend.tf
# Change lines 12-30 from commented to uncommented

# Migrate local state to S3
terraform init -migrate-state

# Confirm migration when prompted: yes

# Clean up local state files
rm terraform.tfstate terraform.tfstate.backup
```

### Step 4: Push to GitHub

```bash
git add -A
git commit -m "Add AWS ECS deployment with Terraform and GitHub Actions"
git push origin main
```

### Step 5: Trigger Deployment

The GitHub Actions workflow will automatically:
1. Build Docker image
2. Push to ECR
3. Deploy infrastructure via Terraform
4. Update ECS service with new task definition
5. Wait for deployment to stabilize

**Watch progress:**
- Go to: https://github.com/adrgul/ai-agent-infra/actions
- Click on the running workflow
- Monitor each step

### Step 6: Access Your Application

After deployment completes (~8-10 minutes), GitHub Actions will output:

```
🚀 Deployment successful!
📍 Application URL: http://ai-agent-tutorial-alb-XXXXXXXXX.eu-central-1.elb.amazonaws.com
📊 Grafana Dashboard: http://ai-agent-tutorial-alb-XXXXXXXXX.eu-central-1.elb.amazonaws.com:3000
🔑 Grafana credentials: admin/admin
```

**Test the API:**
```bash
curl -X POST http://YOUR_ALB_DNS/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "What is Kubernetes?"}'
```

## 🔧 Configuration

### Customize Infrastructure

Edit `terraform/terraform.tfvars`:

```hcl
# Change instance size
ecs_task_cpu    = "1024"  # 1 vCPU instead of 0.5
ecs_task_memory = "2048"  # 2 GB instead of 1 GB

# Scale up
ecs_desired_count = 2  # Run 2 tasks instead of 1

# Change networking
vpc_cidr = "10.1.0.0/16"  # Different VPC CIDR
```

### Environment Variables

The deployment automatically injects:
- `OPENAI_API_KEY` from GitHub Secrets
- `ENVIRONMENT=production`

Add more in `terraform/ecs.tf` under `container_definitions → environment`.

## 📊 Monitoring

### CloudWatch Logs

```bash
# View app logs
aws logs tail /ecs/ai-agent-tutorial/app --follow

# View Prometheus logs
aws logs tail /ecs/ai-agent-tutorial/prometheus --follow

# View Grafana logs
aws logs tail /ecs/ai-agent-tutorial/grafana --follow
```

### Grafana Dashboard

1. Open: http://YOUR_ALB_DNS:3000
2. Login: admin/admin
3. Dashboard already configured with metrics:
   - LLM inference counts by model
   - Cache hit rates
   - Cost tracking
   - Latency histograms

### ECS Metrics

```bash
# Check service status
aws ecs describe-services \
  --cluster ai-agent-tutorial-cluster \
  --services ai-agent-tutorial-service \
  --region eu-central-1

# List running tasks
aws ecs list-tasks \
  --cluster ai-agent-tutorial-cluster \
  --region eu-central-1
```

## 🔄 Updates and Redeployment

### Code Changes

Just push to main branch:

```bash
git add .
git commit -m "Update AI agent logic"
git push origin main
```

GitHub Actions will automatically:
1. Build new Docker image
2. Push to ECR
3. Update ECS service (zero-downtime deployment)

### Infrastructure Changes

Edit Terraform files and push:

```bash
# Modify terraform/*.tf files
git add terraform/
git commit -m "Update ECS task size"
git push origin main
```

## 🧹 Cost Optimization

**Current estimated costs** (eu-central-1):

| Resource | Monthly Cost |
|----------|-------------|
| ECS Fargate (0.5 vCPU, 1GB) | ~$15 |
| ALB | ~$20 |
| NAT Gateway (2x) | ~$65 |
| CloudWatch Logs (1GB) | ~$1 |
| **Total** | **~$101/month** |

**Reduce costs:**

1. **Use 1 NAT Gateway instead of 2:**
   - Edit `terraform/vpc.tf`
   - Remove `nat_2` resources
   - Update private route tables
   - **Savings: ~$32/month**

2. **Reduce task size:**
   ```hcl
   ecs_task_cpu    = "256"  # 0.25 vCPU
   ecs_task_memory = "512"  # 0.5 GB
   ```
   - **Savings: ~$7/month**

3. **Stop when not in use:**
   ```bash
   aws ecs update-service \
     --cluster ai-agent-tutorial-cluster \
     --service ai-agent-tutorial-service \
     --desired-count 0 \
     --region eu-central-1
   ```
   - **Savings: ~$15/month**

## 🗑️ Cleanup

### Stop Services (Keep Infrastructure)

```bash
# Scale down to 0 tasks
aws ecs update-service \
  --cluster ai-agent-tutorial-cluster \
  --service ai-agent-tutorial-service \
  --desired-count 0 \
  --region eu-central-1
```

### Destroy Everything

```bash
cd terraform

# Destroy all infrastructure
terraform destroy

# Confirm when prompted: yes
```

**Note:** S3 state bucket and DynamoDB table have `prevent_destroy = true`. To delete:

1. Edit `terraform/main.tf` and remove `prevent_destroy` lifecycle
2. Run `terraform destroy` again

## 🐛 Troubleshooting

### Task keeps restarting

```bash
# Check task logs
aws logs tail /ecs/ai-agent-tutorial/app --follow

# Common issues:
# - Missing OPENAI_API_KEY
# - Out of memory (increase ecs_task_memory)
# - Port conflicts
```

### Cannot access application

```bash
# Check ALB target health
aws elbv2 describe-target-health \
  --target-group-arn $(aws elbv2 describe-target-groups \
    --query 'TargetGroups[?contains(TargetGroupName, `ai-agent-tutorial-app`)].TargetGroupArn' \
    --output text \
    --region eu-central-1) \
  --region eu-central-1

# Check security groups allow traffic
# App SG should allow inbound from ALB SG on port 8000
```

### Terraform state locked

```bash
# Force unlock (use carefully)
terraform force-unlock LOCK_ID

# Or delete lock from DynamoDB table manually
```

### GitHub Actions fails

```bash
# Check IAM role permissions
# Verify OPENAI_API_KEY secret exists
# Check Terraform syntax: terraform validate
# Review workflow logs in GitHub Actions tab
```

## 📚 Resources

- **Terraform Docs**: https://registry.terraform.io/providers/hashicorp/aws/latest/docs
- **ECS Fargate Pricing**: https://aws.amazon.com/fargate/pricing/
- **GitHub Actions**: https://docs.github.com/en/actions
- **OIDC Setup**: https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services

## 🎓 Architecture Decisions

**Why Fargate over EC2?**
- No server management
- Pay only for what you use
- Automatic scaling
- Better for low-traffic apps

**Why ALB over API Gateway?**
- WebSocket support (future)
- Direct container integration
- Health checks included
- Better for long-running connections

**Why all-in-one task?**
- Simpler networking
- Lower cost (single task)
- Easier local development parity
- Prometheus/Grafana low resource usage

**Why NAT Gateway?**
- ECS tasks need internet for:
  - Pulling images from ECR
  - OpenAI API calls
  - Package downloads

---

**Created**: January 21, 2026  
**Region**: eu-central-1  
**Account**: 021580456215  
**GitHub Repo**: adrgul/ai-agent-infra
