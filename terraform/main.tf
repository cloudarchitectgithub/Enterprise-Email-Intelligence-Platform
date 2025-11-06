terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project      = "email-assistant"
      Environment  = var.environment
      ManagedBy    = "terraform"
      CostCenter   = var.cost_center
      Owner        = var.owner
      Application  = "email-assistant"
      BusinessUnit = var.business_unit
    }
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Local values
locals {
  project_name = "email-assistant"
  environment  = var.environment
  tags = {
    Project      = local.project_name
    Environment  = local.environment
    ManagedBy    = "terraform"
    CostCenter   = var.cost_center
    Owner        = var.owner
    Application  = local.project_name
    BusinessUnit = var.business_unit
  }
}
