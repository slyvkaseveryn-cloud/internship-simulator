terraform {
  required_version = ">= 1.10"

  backend "s3" {
    bucket       = "internship-simulator-tfstate-637965527585"
    key          = "app/terraform.tfstate"
    region       = "eu-central-1"
    use_lockfile = true
    encrypt      = true
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.7"
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

data "aws_caller_identity" "current" {}

locals {
  name      = "internship-simulator"
  repo_root = "${path.module}/.."
}
