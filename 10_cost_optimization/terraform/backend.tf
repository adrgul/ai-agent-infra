# Terraform Remote Backend Configuration
# Stores state in S3 with DynamoDB locking
# Note: This backend configuration references resources created by main.tf
# 
# Terraform Remote Backend Configuration
# Stores state in S3 with DynamoDB locking
# Note: This backend configuration references resources created by main.tf

terraform {
  backend "s3" {
    # S3 bucket for storing Terraform state
    bucket = "terraform-state-adriangulyas-ai-agent"
    
    # State file path within the bucket
    key = "cost-optimization/terraform.tfstate"
    
    # AWS region where the S3 bucket is located
    region = "eu-central-1"
    
    # DynamoDB table for state locking and consistency
    dynamodb_table = "terraform-state-lock"
    
    # Encrypt state file at rest using AWS KMS
    encrypt = true
    
    # Note: No credentials specified - authentication via GitHub Actions OIDC
  }
}
