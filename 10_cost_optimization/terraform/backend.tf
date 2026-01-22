# Terraform Remote Backend Configuration
# Backend config provided via CLI flags during terraform init
# This prevents hardcoded values and allows bootstrap without backend

terraform {
  backend "s3" {}
}
