# One-time bootstrap, applied from a laptop by the account owner:
#   1. a cost budget (the first resource: alerts on real money after credits),
#   2. the S3 bucket that holds Terraform state for ../ (the app stack),
#   3. the GitHub OIDC provider and the role that CI assumes (no long-lived keys).
# Its own state also lives in that bucket (see backend.tf).

terraform {
  required_version = ">= 1.10"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.region
  default_tags {
    tags = {
      project   = "internship-simulator"
      ManagedBy = "terraform"
    }
  }
}

variable "region" {
  type    = string
  default = "eu-central-1"
}

variable "alert_email" {
  description = "Where budget alerts go. Passed on the command line, never committed."
  type        = string
}

variable "budget_usd" {
  type    = string
  default = "1.0"
}

variable "github_repository" {
  description = "owner/name of the GitHub repository whose workflows may deploy"
  type        = string
  default     = "slyvkaseveryn-cloud/internship-simulator"
}

data "aws_caller_identity" "current" {}

# --- 1. Budget: actual and forecasted spend AFTER credits and refunds ---------
resource "aws_budgets_budget" "monthly" {
  name         = "internship-simulator-monthly"
  budget_type  = "COST"
  limit_amount = var.budget_usd
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  # Credits are excluded, so the amount is what would be charged to the card.
  cost_types {
    include_credit  = false
    include_refund  = false
    include_tax     = true
    include_support = true
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.alert_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.alert_email]
  }
}

# --- 2. Terraform state bucket ---------------------------------------------------
resource "aws_s3_bucket" "tfstate" {
  bucket = "internship-simulator-tfstate-${data.aws_caller_identity.current.account_id}"
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "tfstate" {
  bucket                  = aws_s3_bucket.tfstate.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  rule {
    id     = "expire-old-state-versions"
    status = "Enabled"
    filter {}
    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

output "state_bucket" {
  value = aws_s3_bucket.tfstate.bucket
}
