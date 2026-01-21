# Deployment Issue Fix Guide

## Problem
Resources already exist in AWS but Terraform state is not synchronized, causing "already exists" errors during deployment in GitHub Actions.

## Root Cause
1. Resources were created in AWS (either manually or in a previous deployment)
2. Terraform state doesn't track these existing resources
3. When Terraform tries to create them again → "already exists" errors

## Solution: Automated Import in GitHub Actions

The fix is now automated in the GitHub Actions workflow. When you push changes:

1. **Workflow runs import script** - Attempts to import any existing AWS resources
2. **Import failures are ignored** - If resources don't exist, that's fine
3. **Terraform plan detects state** - Shows only what needs to be created
4. **Terraform apply succeeds** - No more "already exists" errors

### What Changed

**Updated Files:**
- [.github/workflows/deploy.yml](../.github/workflows/deploy.yml) - Added import step before terraform plan
- [terraform/import_resources.sh](import_resources.sh) - Script to import existing resources
- [terraform/backend.tf](backend.tf) - Fixed S3 bucket name to match terraform.tfvars

**Key Changes in Workflow:**
```yaml
- name: Import Existing Resources (if any)
  run: |
    chmod +x import_resources.sh
    ./import_resources.sh || echo "Some imports failed, continuing..."
  continue-on-error: true
```

This runs before `terraform plan` and imports any existing resources into state.

## Manual Import (if needed locally)

If you need to import resources locally:

```bash
cd terraform

# Ensure you have AWS credentials configured
export AWS_PROFILE=your-profile  # or use aws configure

# Run import script
chmod +x import_resources.sh
./import_resources.sh

# Verify state
terraform state list

# Check plan
terraform plan
```

## Alternative: Destroy and Recreate (Last Resort)

⚠️ **Warning**: This will cause downtime and delete all data.

```bash
cd terraform

# Option 1: Using Terraform
terraform destroy -auto-approve

# Option 2: Using AWS CLI (if state is broken)
aws elbv2 delete-load-balancer --load-balancer-arn <arn>
aws elbv2 delete-target-group --target-group-arn <arn>
aws ecr delete-repository --repository-name ai-agent-app --force
# ... etc for each resource

# Then fresh deployment
rm -rf .terraform terraform.tfstate*
terraform init
terraform apply -auto-approve
```

## Testing the Fix

1. Commit and push changes:
```bash
git add -A
git commit -m "Fix: Auto-import existing resources in GitHub Actions"
git push origin main
```

2. Watch GitHub Actions workflow - it should now succeed

3. Check the logs for "Import complete!" message

## Preventing This Issue

- ✅ **Use remote backend from day 1** - Already configured in backend.tf
- ✅ **Auto-import in CI/CD** - Now implemented in workflow
- ✅ **Consistent bucket names** - Fixed mismatch between backend.tf and terraform.tfvars
- ❌ **Never run `terraform apply` without migrating state** - If you do, run import script

## Troubleshooting

**Still getting "already exists" errors?**

Check if bucket name in backend.tf matches terraform.tfvars:
```bash
# Should both show: terraform-state-adriangulyas-ai-agent
grep bucket backend.tf
grep state_bucket_name terraform.tfvars
```

**Import script fails?**

Check AWS credentials in GitHub Actions:
```bash
# Verify OIDC role trust relationship allows GitHub Actions
aws iam get-role --role-name terraform-github-deployer
```

**State shows wrong resources?**

Refresh and reconcile:
```bash
terraform refresh
terraform plan
# If plan shows deletions of correct resources, check AWS region
```
