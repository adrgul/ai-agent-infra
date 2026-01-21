#!/bin/bash
# Terraform State Migration Script
# This script migrates existing AWS resources into Terraform state
# Run this once to fix the "resources already exist" errors

set -e

echo "🔧 Starting Terraform state migration..."

# Navigate to terraform directory
cd "$(dirname "$0")"

# Initialize Terraform with local backend (backend.tf should be commented out)
echo "📦 Initializing Terraform with local backend..."
terraform init -reconfigure

# Import existing resources into state
echo "📥 Importing existing AWS resources..."

# S3 and DynamoDB (backend resources)
echo "  → Importing S3 bucket..."
terraform import aws_s3_bucket.terraform_state terraform-state-021580456215-ai-agent-infra 2>/dev/null || echo "    Already imported or doesn't exist"

echo "  → Importing DynamoDB table..."
terraform import aws_dynamodb_table.terraform_locks terraform-state-lock 2>/dev/null || echo "    Already imported or doesn't exist"

# ECR Repository
echo "  → Importing ECR repository..."
terraform import aws_ecr_repository.app ai-agent-app 2>/dev/null || echo "    Already imported or doesn't exist"

# CloudWatch Log Groups
echo "  → Importing CloudWatch log groups..."
terraform import aws_cloudwatch_log_group.app /ecs/ai-agent-tutorial/app 2>/dev/null || echo "    Already imported or doesn't exist"
terraform import aws_cloudwatch_log_group.prometheus /ecs/ai-agent-tutorial/prometheus 2>/dev/null || echo "    Already imported or doesn't exist"
terraform import aws_cloudwatch_log_group.grafana /ecs/ai-agent-tutorial/grafana 2>/dev/null || echo "    Already imported or doesn't exist"

# IAM Roles
echo "  → Importing IAM roles..."
terraform import aws_iam_role.ecs_task_execution ai-agent-tutorial-ecs-task-execution-role 2>/dev/null || echo "    Already imported or doesn't exist"
terraform import aws_iam_role.ecs_task ai-agent-tutorial-ecs-task-role 2>/dev/null || echo "    Already imported or doesn't exist"

# Load Balancer and Target Groups
echo "  → Importing Load Balancer resources..."
ALB_ARN=$(aws elbv2 describe-load-balancers --query 'LoadBalancers[?LoadBalancerName==`ai-agent-tutorial-alb`].LoadBalancerArn' --output text 2>/dev/null)
if [ -n "$ALB_ARN" ]; then
    terraform import aws_lb.main "$ALB_ARN" 2>/dev/null || echo "    Already imported"
fi

APP_TG_ARN=$(aws elbv2 describe-target-groups --query 'TargetGroups[?TargetGroupName==`ai-agent-tutorial-app-tg`].TargetGroupArn' --output text 2>/dev/null)
if [ -n "$APP_TG_ARN" ]; then
    terraform import aws_lb_target_group.app "$APP_TG_ARN" 2>/dev/null || echo "    Already imported"
fi

GRAFANA_TG_ARN=$(aws elbv2 describe-target-groups --query 'TargetGroups[?TargetGroupName==`ai-agent-tutorial-grafana-tg`].TargetGroupArn' --output text 2>/dev/null)
if [ -n "$GRAFANA_TG_ARN" ]; then
    terraform import aws_lb_target_group.grafana "$GRAFANA_TG_ARN" 2>/dev/null || echo "    Already imported"
fi

echo "✅ Import complete!"
echo ""
echo "📊 Current state:"
terraform state list

echo ""
echo "🎯 Next steps:"
echo "1. Uncomment the backend configuration in backend.tf"
echo "2. Run: terraform init -migrate-state"
echo "3. Answer 'yes' when prompted to migrate state to S3"
echo "4. Commit and push changes - GitHub Actions will now work!"
