# AWS Provider Configuration
# Authentication is handled via GitHub Actions OIDC (no hardcoded credentials)
# The provider assumes an IAM role configured in the GitHub Actions workflow

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# AWS Provider for eu-central-1 (Frankfurt)
provider "aws" {
  region = var.aws_region

  # Default tags applied to all resources
  default_tags {
    tags = {
      Environment = var.environment
      ManagedBy   = "Terraform"
      Project     = var.project_name
    }
  }
}
