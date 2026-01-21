# 🚀 Quick Start: Deploy to AWS

## What You Need To Do

### 1. Add OpenAI API Key to GitHub
```
1. Go to: https://github.com/adrgul/ai-agent-infra/settings/secrets/actions
2. Click "New repository secret"
3. Name: OPENAI_API_KEY
4. Value: sk-your-key-here
5. Click "Add secret"
```

### 2. Initialize Terraform State
```bash
cd terraform

# Create S3 bucket and DynamoDB table for state
terraform init
terraform apply

# Uncomment backend.tf (lines 12-30)
# Then migrate state:
terraform init -migrate-state
rm terraform.tfstate*
```

### 3. Commit and Push
```bash
git add -A
git commit -m "Add AWS ECS deployment infrastructure"
git push origin main
```

### 4. Watch Deployment
- Go to: https://github.com/adrgul/ai-agent-infra/actions
- Wait ~10 minutes
- Get your URLs from workflow output

## What Gets Deployed

✅ **VPC** with public/private subnets  
✅ **ECS Fargate** running your AI agent (0.5 vCPU, 1GB RAM)  
✅ **ECR** for Docker images  
✅ **Application Load Balancer** (public endpoint)  
✅ **Prometheus + Grafana** (monitoring built-in)  
✅ **CloudWatch** logs

## Access Your App

After deployment:
```bash
# API endpoint
http://YOUR-ALB-DNS/run

# Grafana dashboard
http://YOUR-ALB-DNS:3000
Login: admin/admin
```

## Test It

```bash
curl -X POST http://YOUR-ALB-DNS/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "What is Kubernetes?"}'
```

## Monthly Cost: ~$101

- ECS Fargate: $15
- ALB: $20
- NAT Gateway: $65
- CloudWatch: $1

**Reduce to ~$70:** Use 1 NAT Gateway instead of 2 (edit terraform/vpc.tf)

## Full Documentation

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete guide.

---

**Next:** Push to main branch to trigger automatic deployment! 🎉
