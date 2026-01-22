# Terraform Bootstrap Infrastructure

This directory contains the bootstrap infrastructure for Terraform remote state management.

## Purpose

Creates the foundational AWS resources required for Terraform remote state:
- **S3 Bucket**: `terraform-state-021580456215-ai-agent-infra` (stores Terraform state files)
- **DynamoDB Table**: `terraform-state-lock` (provides state locking mechanism)

## Features

### S3 Bucket Configuration
- ✅ Versioning enabled (state file history)
- ✅ Server-side encryption (AES256)
- ✅ Public access blocked
- ✅ Lifecycle protection (prevent accidental deletion)

### DynamoDB Table Configuration
- ✅ Pay-per-request billing
- ✅ Primary key: `LockID` (String)
- ✅ Lifecycle protection

## Usage

### First-Time Setup (After AWS Account Wipe)

1. **Run the bootstrap job** (via GitHub Actions):
   ```bash
   # Go to GitHub Actions → Deploy AI Agent to AWS ECS → Run workflow
   # This will execute the bootstrap-state job
   ```

2. **Or run locally** (if needed):
   ```bash
   cd terraform-bootstrap
   terraform init
   terraform plan
   terraform apply
   ```

3. **Verify resources**:
   ```bash
   aws s3 ls s3://terraform-state-021580456215-ai-agent-infra
   aws dynamodb describe-table --table-name terraform-state-lock --region eu-central-1
   ```

### Important Notes

- ⚠️ This infrastructure uses **LOCAL state** (not remote)
- ⚠️ The local state file (`terraform.tfstate`) is **critical** - do not delete it
- ⚠️ Run bootstrap **BEFORE** deploying main infrastructure
- ⚠️ Both resources have `prevent_destroy = true` for safety

## Integration with Main Infrastructure

After bootstrap completes, the main infrastructure (`terraform/`) will use the remote backend:

```hcl
terraform {
  backend "s3" {
    bucket         = "terraform-state-021580456215-ai-agent-infra"
    key            = "cost-optimization/terraform.tfstate"
    region         = "eu-central-1"
    dynamodb_table = "terraform-state-lock"
    encrypt        = true
  }
}
```

## Workflow Automation

The GitHub Actions workflow handles the bootstrap automatically:

1. **Manual trigger** (`workflow_dispatch`): Runs bootstrap job first
2. **Push to main**: Assumes bootstrap already exists (includes safety check)

If the S3 bucket doesn't exist during main deployment, the workflow will fail with clear instructions.
