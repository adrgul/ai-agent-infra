# Terraform Outputs
# Export important resource information for reference and integration

# S3 bucket ARN for state storage
output "state_bucket_arn" {
  description = "ARN of the S3 bucket storing Terraform state"
  value       = aws_s3_bucket.terraform_state.arn
}

# S3 bucket name
output "state_bucket_name" {
  description = "Name of the S3 bucket storing Terraform state"
  value       = aws_s3_bucket.terraform_state.id
}

# S3 bucket region
output "state_bucket_region" {
  description = "AWS region of the S3 state bucket"
  value       = aws_s3_bucket.terraform_state.region
}

# DynamoDB table ARN for state locking
output "dynamodb_table_arn" {
  description = "ARN of the DynamoDB table for state locking"
  value       = aws_dynamodb_table.terraform_locks.arn
}

# DynamoDB table name
output "dynamodb_table_name" {
  description = "Name of the DynamoDB table for state locking"
  value       = aws_dynamodb_table.terraform_locks.name
}

# Backend configuration reference (for documentation)
output "backend_config" {
  description = "Backend configuration for reference"
  value = {
    bucket         = aws_s3_bucket.terraform_state.id
    key            = "cost-optimization/terraform.tfstate"
    region         = var.aws_region
    dynamodb_table = aws_dynamodb_table.terraform_locks.name
    encrypt        = true
  }
}

# -----------------------------------------------------------------------------
# Application Outputs
# -----------------------------------------------------------------------------

# Application Load Balancer DNS
output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

# Application URL
output "app_url" {
  description = "URL to access the AI Agent API"
  value       = "http://${aws_lb.main.dns_name}"
}

# Grafana URL
output "grafana_url" {
  description = "URL to access Grafana dashboard"
  value       = "http://${aws_lb.main.dns_name}:3000"
}

# ECR Repository URL
output "ecr_repository_url" {
  description = "URL of the ECR repository"
  value       = aws_ecr_repository.app.repository_url
}

# ECS Cluster Name
output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

# ECS Service Name
output "ecs_service_name" {
  description = "Name of the ECS service"
  value       = aws_ecs_service.app.name
}
