# Terraform Variables
# Define input variables for the infrastructure configuration

# AWS region where resources will be created
variable "aws_region" {
  description = "AWS region for infrastructure deployment"
  type        = string
  default     = "eu-central-1"
}

# Environment name (e.g., dev, staging, production)
variable "environment" {
  description = "Environment name for resource tagging"
  type        = string
  default     = "production"
}

# Project name for resource tagging and naming
variable "project_name" {
  description = "Project name for resource identification"
  type        = string
  default     = "ai-agent-tutorial"
}

# S3 bucket name for Terraform state storage
variable "state_bucket_name" {
  description = "Name of the S3 bucket for Terraform state storage"
  type        = string
  default     = "terraform-state-021580456215-ai-agent-infra"

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]*[a-z0-9]$", var.state_bucket_name))
    error_message = "Bucket name must contain only lowercase letters, numbers, and hyphens"
  }
}

# DynamoDB table name for state locking
variable "dynamodb_table_name" {
  description = "Name of the DynamoDB table for Terraform state locking"
  type        = string
  default     = "terraform-state-lock"

  validation {
    condition     = length(var.dynamodb_table_name) >= 3 && length(var.dynamodb_table_name) <= 255
    error_message = "DynamoDB table name must be between 3 and 255 characters"
  }
}

# -----------------------------------------------------------------------------
# Networking Variables
# -----------------------------------------------------------------------------

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_1_cidr" {
  description = "CIDR block for public subnet 1"
  type        = string
  default     = "10.0.1.0/24"
}

variable "public_subnet_2_cidr" {
  description = "CIDR block for public subnet 2"
  type        = string
  default     = "10.0.2.0/24"
}

variable "private_subnet_1_cidr" {
  description = "CIDR block for private subnet 1"
  type        = string
  default     = "10.0.11.0/24"
}

variable "private_subnet_2_cidr" {
  description = "CIDR block for private subnet 2"
  type        = string
  default     = "10.0.12.0/24"
}

# -----------------------------------------------------------------------------
# ECR Variables
# -----------------------------------------------------------------------------

variable "ecr_repository_name" {
  description = "Name of the ECR repository"
  type        = string
  default     = "ai-agent-app"
}

# -----------------------------------------------------------------------------
# ECS Variables
# -----------------------------------------------------------------------------

variable "ecs_task_cpu" {
  description = "CPU units for ECS task (1024 = 1 vCPU)"
  type        = string
  default     = "512" # 0.5 vCPU
}

variable "ecs_task_memory" {
  description = "Memory for ECS task in MB"
  type        = string
  default     = "1024" # 1 GB
}

variable "ecs_desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 1
}

# OpenAI API Key - passed via environment variable TF_VAR_openai_api_key
variable "openai_api_key" {
  description = "OpenAI API key for the application"
  type        = string
  sensitive   = true
  default     = ""
}
