# Terraform version and provider configuration for bootstrap infrastructure

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "eu-central-1"

  default_tags {
    tags = {
      ManagedBy = "Terraform"
      Component = "RemoteStateBackend"
    }
  }
}
