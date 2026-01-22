# Terraform Variables Configuration

# -----------------------------------------------------------------------------
# AWS Configuration
# -----------------------------------------------------------------------------

variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "eu-central-1"
}

# -----------------------------------------------------------------------------
# Terraform State Configuration
# -----------------------------------------------------------------------------

variable "state_bucket_name" {
  description = "Name of the S3 bucket for Terraform state storage"
  type        = string
  default     = "terraform-state-adriangulyas-ai-agent"
}

variable "dynamodb_table_name" {
  description = "Name of the DynamoDB table for Terraform state locking"
  type        = string
  default     = "terraform-state-lock"
}

# -----------------------------------------------------------------------------
# Application Configuration
# -----------------------------------------------------------------------------

variable "openai_api_key" {
  description = "OpenAI API key for the AI agent (passed from GitHub Secrets)"
  type        = string
  sensitive   = true
}

variable "app_environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "app_version" {
  description = "Application version tag"
  type        = string
  default     = "latest"
}

# -----------------------------------------------------------------------------
# ECS Configuration
# -----------------------------------------------------------------------------

variable "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  type        = string
  default     = "ai-agent-tutorial-cluster"
}

variable "ecs_service_name" {
  description = "Name of the ECS service"
  type        = string
  default     = "ai-agent-tutorial-service"
}

variable "app_container_port" {
  description = "Port the application container listens on"
  type        = number
  default     = 8000
}

variable "desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 1
}

# -----------------------------------------------------------------------------
# ECR Configuration
# -----------------------------------------------------------------------------

variable "ecr_repository_name" {
  description = "Name of the ECR repository"
  type        = string
  default     = "ai-agent-app"
}

# -----------------------------------------------------------------------------
# Networking Configuration
# -----------------------------------------------------------------------------

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["eu-central-1a", "eu-central-1b"]
}

# -----------------------------------------------------------------------------
# Monitoring Configuration
# -----------------------------------------------------------------------------

variable "grafana_admin_password" {
  description = "Admin password for Grafana dashboard"
  type        = string
  default     = "admin"
  sensitive   = true
}
