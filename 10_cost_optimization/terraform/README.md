# Terraform AWS Infrastructure

This directory contains Terraform configuration for AWS infrastructure supporting the AI Agent Tutorial project.

## 📋 What This Creates

- **S3 Bucket**: Stores Terraform state files with versioning enabled
- **DynamoDB Table**: Provides state locking and consistency checking
- **Security**: Encryption at rest, public access blocked, versioning enabled

## 🔐 Authentication

This configuration uses **GitHub Actions OIDC** for AWS authentication - no hardcoded credentials required.

### Prerequisites

1. AWS Account with appropriate permissions
2. GitHub repository configured with OIDC provider
3. IAM role with trust relationship to GitHub Actions

## 🚀 First-Time Setup (Bootstrapping)

Since the backend references resources that don't exist yet, follow this bootstrap process:

### Step 1: Initialize with Local Backend

```bash
# Comment out backend.tf entirely
# Then initialize and create resources
terraform init
terraform plan
terraform apply
```

### Step 2: Migrate to Remote Backend

```bash
# Uncomment backend.tf
# Migrate local state to S3
terraform init -migrate-state

# Clean up local state files
rm terraform.tfstate terraform.tfstate.backup
```

### Step 3: Verify

```bash
# Verify state is in S3
aws s3 ls s3://terraform-state-ai-agent-tutorial/

# Verify DynamoDB table exists
aws dynamodb describe-table --table-name terraform-state-lock
```

## 📁 File Structure

```
terraform/
├── provider.tf      # AWS provider configuration
├── backend.tf       # S3 backend configuration
├── main.tf          # Main resources (S3 + DynamoDB)
├── variables.tf     # Input variables
├── outputs.tf       # Output values
└── README.md        # This file
```

## 🔧 Configuration

### Default Values

- **Region**: eu-central-1 (Frankfurt)
- **S3 Bucket**: terraform-state-ai-agent-tutorial
- **DynamoDB Table**: terraform-state-lock
- **Environment**: production

### Customize

Override defaults in `terraform.tfvars`:

```hcl
aws_region          = "eu-central-1"
environment         = "production"
project_name        = "ai-agent-tutorial"
state_bucket_name   = "your-custom-bucket-name"
dynamodb_table_name = "your-custom-table-name"
```

## 🔒 Security Features

- ✅ Server-side encryption (AES256)
- ✅ Versioning enabled on S3 bucket
- ✅ Public access blocked
- ✅ Point-in-time recovery for DynamoDB
- ✅ Lifecycle policies prevent accidental deletion
- ✅ Audit logging enabled

## 🎯 Usage with GitHub Actions

Example workflow snippet:

```yaml
- name: Configure AWS Credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::123456789012:role/github-actions-role
    aws-region: eu-central-1

- name: Terraform Init
  run: terraform init

- name: Terraform Plan
  run: terraform plan

- name: Terraform Apply
  run: terraform apply -auto-approve
```

## 📊 Outputs

After successful apply, you'll see:

```
state_bucket_arn        = "arn:aws:s3:::terraform-state-ai-agent-tutorial"
state_bucket_name       = "terraform-state-ai-agent-tutorial"
dynamodb_table_name     = "terraform-state-lock"
backend_config          = { ... }
```

## 🛠️ Common Commands

```bash
# Initialize Terraform
terraform init

# Validate configuration
terraform validate

# Format code
terraform fmt -recursive

# Plan changes
terraform plan

# Apply changes
terraform apply

# Show current state
terraform show

# List resources
terraform state list

# Destroy infrastructure (careful!)
terraform destroy
```

## ⚠️ Important Notes

1. **Prevent Destroy**: Both S3 bucket and DynamoDB table have `prevent_destroy = true` to avoid accidental deletion
2. **State Migration**: Follow the bootstrap process carefully when setting up for the first time
3. **No Credentials**: Never commit AWS credentials to version control
4. **Bucket Names**: S3 bucket names must be globally unique - adjust if needed

## 📚 Additional Resources

- [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Terraform S3 Backend](https://www.terraform.io/docs/language/settings/backends/s3.html)
- [AWS OIDC for GitHub Actions](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)

---

**Created**: January 21, 2026  
**Region**: eu-central-1  
**Authentication**: GitHub Actions OIDC
