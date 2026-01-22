# Development Environment Configuration

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "readlock-terraform-state"
    key            = "dev/terraform.tfstate"
    region         = "ap-northeast-2"
    encrypt        = true
    dynamodb_table = "readlock-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "readlock"
      Environment = "dev"
      ManagedBy   = "terraform"
    }
  }
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-northeast-2"
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

# VPC Module
module "vpc" {
  source = "../../modules/vpc"

  project_name = "readlock"
  environment  = "dev"
  vpc_cidr     = "10.0.0.0/16"

  availability_zones = [
    "ap-northeast-2a",
    "ap-northeast-2c"
  ]
}

# RDS Module
module "rds" {
  source = "../../modules/rds"

  project_name      = "readlock"
  environment       = "dev"
  vpc_id            = module.vpc.vpc_id
  subnet_ids        = module.vpc.data_subnet_ids
  security_group_id = module.vpc.rds_security_group_id
  master_password   = var.db_password

  min_capacity = 0.5
  max_capacity = 2
}

# ECS Module
module "ecs" {
  source = "../../modules/ecs"

  project_name          = "readlock"
  environment           = "dev"
  vpc_id                = module.vpc.vpc_id
  private_subnet_ids    = module.vpc.private_subnet_ids
  public_subnet_ids     = module.vpc.public_subnet_ids
  ecs_security_group_id = module.vpc.ecs_security_group_id
  alb_security_group_id = module.vpc.alb_security_group_id
}

# Outputs
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "rds_endpoint" {
  description = "RDS endpoint"
  value       = module.rds.cluster_endpoint
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.ecs.cluster_name
}

output "alb_dns_name" {
  description = "ALB DNS name"
  value       = module.ecs.alb_dns_name
}
