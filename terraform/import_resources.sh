#!/bin/bash
# Import existing AWS resources into Terraform state
# This script should be run in GitHub Actions or with proper AWS credentials

set -e

echo "🔄 Importing existing AWS resources into Terraform state..."

# Import resources one by one, ignoring errors if already imported
terraform import -input=false aws_s3_bucket.terraform_state terraform-state-adriangulyas-ai-agent 2>&1 | grep -v "already managed" || true
terraform import -input=false aws_s3_bucket_versioning.terraform_state terraform-state-adriangulyas-ai-agent 2>&1 | grep -v "already managed" || true
terraform import -input=false aws_s3_bucket_server_side_encryption_configuration.terraform_state terraform-state-adriangulyas-ai-agent 2>&1 | grep -v "already managed" || true
terraform import -input=false aws_s3_bucket_public_access_block.terraform_state terraform-state-adriangulyas-ai-agent 2>&1 | grep -v "already managed" || true
terraform import -input=false aws_s3_bucket_logging.terraform_state terraform-state-adriangulyas-ai-agent 2>&1 | grep -v "already managed" || true

terraform import -input=false aws_dynamodb_table.terraform_locks terraform-state-lock 2>&1 | grep -v "already managed" || true

terraform import -input=false aws_ecr_repository.app ai-agent-app 2>&1 | grep -v "already managed" || true

terraform import -input=false aws_cloudwatch_log_group.app /ecs/ai-agent-tutorial/app 2>&1 | grep -v "already managed" || true
terraform import -input=false aws_cloudwatch_log_group.prometheus /ecs/ai-agent-tutorial/prometheus 2>&1 | grep -v "already managed" || true
terraform import -input=false aws_cloudwatch_log_group.grafana /ecs/ai-agent-tutorial/grafana 2>&1 | grep -v "already managed" || true

terraform import -input=false aws_iam_role.ecs_task_execution ai-agent-tutorial-ecs-task-execution-role 2>&1 | grep -v "already managed" || true
terraform import -input=false aws_iam_role.ecs_task ai-agent-tutorial-ecs-task-role 2>&1 | grep -v "already managed" || true

# Get ARNs dynamically
ALB_ARN=$(aws elbv2 describe-load-balancers --query 'LoadBalancers[?LoadBalancerName==`ai-agent-tutorial-alb`].LoadBalancerArn' --output text --region eu-central-1)
if [ -n "$ALB_ARN" ] && [ "$ALB_ARN" != "None" ]; then
  terraform import -input=false aws_lb.main "$ALB_ARN" 2>&1 | grep -v "already managed" || true
fi

APP_TG_ARN=$(aws elbv2 describe-target-groups --query 'TargetGroups[?TargetGroupName==`ai-agent-tutorial-app-tg`].TargetGroupArn' --output text --region eu-central-1)
if [ -n "$APP_TG_ARN" ] && [ "$APP_TG_ARN" != "None" ]; then
  terraform import -input=false aws_lb_target_group.app "$APP_TG_ARN" 2>&1 | grep -v "already managed" || true
fi

GRAFANA_TG_ARN=$(aws elbv2 describe-target-groups --query 'TargetGroups[?TargetGroupName==`ai-agent-tutorial-grafana-tg`].TargetGroupArn' --output text --region eu-central-1)
if [ -n "$GRAFANA_TG_ARN" ] && [ "$GRAFANA_TG_ARN" != "None" ]; then
  terraform import -input=false aws_lb_target_group.grafana "$GRAFANA_TG_ARN" 2>&1 | grep -v "already managed" || true
fi

echo "✅ Import complete!"
