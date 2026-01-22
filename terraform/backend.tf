# Terraform Remote Backend Configuration
# Stores state in S3 with DynamoDB locking
# Backend configuration is provided via CLI -backend-config flags in GitHub Actions
# This prevents hardcoding credentials and allows flexibility across environments

terraform {
  backend "s3" {}
}
