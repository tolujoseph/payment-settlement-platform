variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "eu-west-2"
}

variable "environment" {
  description = "Deployment environment name"
  type        = string
  default     = "dev"
}

variable "db_password" {
  description = "Password for the Intake RDS instance"
  type        = string
  sensitive   = true
}