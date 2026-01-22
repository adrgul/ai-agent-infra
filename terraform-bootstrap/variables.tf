# Variables for Terraform remote state bootstrap infrastructure

variable "project_name" {
  description = "Project name for resource tagging"
  type        = string
  default     = "ai-agent-infra"
}

variable "state_bucket_name" {
  description = "Name of the S3 bucket for Terraform remote state storage"
  type        = string
  default     = "terraform-state-021580456215-ai-agent-infra"
}

variable "dynamodb_table_name" {
  description = "Name of the DynamoDB table for Terraform state locking"
  type        = string
  default     = "terraform-state-lock"
}

variable "aws_region" {
  description = "AWS region for backend infrastructure"
  type        = string
  default     = "eu-central-1"
}
