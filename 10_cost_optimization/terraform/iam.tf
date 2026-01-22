# IAM Configuration for GitHub Actions OIDC Authentication
# This enables GitHub Actions to assume an AWS IAM role without long-lived credentials

# -----------------------------------------------------------------------------
# GitHub Actions OIDC Provider
# -----------------------------------------------------------------------------

# OIDC provider for GitHub Actions
resource "aws_iam_openid_connect_provider" "github_actions" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = [
    "sts.amazonaws.com",
  ]

  # GitHub's OIDC thumbprint (stable, rarely changes)
  thumbprint_list = [
    "6938fd4d98bab03faadb97b34396831e3780aea1",
    "1c58a3a8518e8759bf075b76b750d4f2df264fcd"
  ]

  tags = {
    Name        = "GitHub Actions OIDC Provider"
    Description = "Allows GitHub Actions to authenticate with AWS"
  }
}

# -----------------------------------------------------------------------------
# IAM Role for GitHub Actions
# -----------------------------------------------------------------------------

# IAM role that GitHub Actions can assume
resource "aws_iam_role" "terraform_github_deployer" {
  name        = "terraform-github-deployer"
  description = "Role for GitHub Actions to deploy infrastructure via Terraform"

  # Trust policy allowing GitHub Actions from your repository to assume this role
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github_actions.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            # Replace with your GitHub org/repo (e.g., "repo:adrgul/ai-agent-infra:*")
            "token.actions.githubusercontent.com:sub" = "repo:adrgul/*:*"
          }
        }
      }
    ]
  })

  tags = {
    Name        = "Terraform GitHub Deployer"
    Description = "Allows GitHub Actions to manage AWS infrastructure"
  }
}

# -----------------------------------------------------------------------------
# IAM Policies for Terraform State Management
# -----------------------------------------------------------------------------

# Policy for S3 state bucket access
resource "aws_iam_policy" "terraform_state_access" {
  name        = "TerraformStateAccess"
  description = "Allows access to Terraform S3 state bucket and DynamoDB lock table"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetBucketVersioning",
          "s3:GetBucketLocation"
        ]
        Resource = "arn:aws:s3:::${var.state_bucket_name}"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "arn:aws:s3:::${var.state_bucket_name}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:DescribeTable",
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:DeleteItem"
        ]
        Resource = "arn:aws:dynamodb:${var.aws_region}:${data.aws_caller_identity.current.account_id}:table/${var.dynamodb_table_name}"
      }
    ]
  })
}

# Policy for managing AWS infrastructure (ECS, ECR, VPC, etc.)
resource "aws_iam_policy" "terraform_infrastructure" {
  name        = "TerraformInfrastructureManagement"
  description = "Allows Terraform to manage AWS infrastructure resources"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          # ECS permissions
          "ecs:*",
          "ecr:*",
          
          # VPC and networking
          "ec2:*",
          
          # Load balancing
          "elasticloadbalancing:*",
          
          # Logs
          "logs:*",
          
          # IAM (for ECS task roles)
          "iam:GetRole",
          "iam:CreateRole",
          "iam:DeleteRole",
          "iam:AttachRolePolicy",
          "iam:DetachRolePolicy",
          "iam:PutRolePolicy",
          "iam:DeleteRolePolicy",
          "iam:GetRolePolicy",
          "iam:PassRole",
          "iam:ListRolePolicies",
          "iam:ListAttachedRolePolicies",
          "iam:CreatePolicy",
          "iam:DeletePolicy",
          "iam:GetPolicy",
          "iam:GetPolicyVersion",
          "iam:ListPolicyVersions",
          
          # Secrets Manager (if using)
          "secretsmanager:*",
          
          # CloudWatch
          "cloudwatch:*",
          
          # Application Auto Scaling
          "application-autoscaling:*"
        ]
        Resource = "*"
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# Attach Policies to Role
# -----------------------------------------------------------------------------

resource "aws_iam_role_policy_attachment" "terraform_state_access" {
  role       = aws_iam_role.terraform_github_deployer.name
  policy_arn = aws_iam_policy.terraform_state_access.arn
}

resource "aws_iam_role_policy_attachment" "terraform_infrastructure" {
  role       = aws_iam_role.terraform_github_deployer.name
  policy_arn = aws_iam_policy.terraform_infrastructure.arn
}

# -----------------------------------------------------------------------------
# Data Sources
# -----------------------------------------------------------------------------

data "aws_caller_identity" "current" {}

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------

output "github_actions_role_arn" {
  description = "ARN of the IAM role for GitHub Actions"
  value       = aws_iam_role.terraform_github_deployer.arn
}

output "oidc_provider_arn" {
  description = "ARN of the GitHub Actions OIDC provider"
  value       = aws_iam_openid_connect_provider.github_actions.arn
}
