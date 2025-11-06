variable "aws_region" {
  description = "AWS region for enterprise resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Enterprise environment name"
  type        = string
  default     = "dev"
}

variable "lambda_timeout" {
  description = "Enterprise Lambda function timeout in seconds"
  type        = number
  default     = 300
}

variable "lambda_memory_size" {
  description = "Enterprise Lambda function memory size in MB"
  type        = number
  default     = 512
}

variable "bedrock_model_id" {
  description = "Bedrock model ID for enterprise AI processing"
  type        = string
  default     = "anthropic.claude-3-sonnet-20240229-v1:0"
}

variable "log_retention_days" {
  description = "Enterprise log retention period in days"
  type        = number
  default     = 30
}

variable "enable_monitoring" {
  description = "Enable enterprise monitoring and alerting"
  type        = bool
  default     = true
}

# Cost tracking and resource management variables
variable "cost_center" {
  description = "Cost center for resource tracking and billing"
  type        = string
  default     = "engineering"
}

variable "owner" {
  description = "Owner or team responsible for the resources"
  type        = string
  default     = "ai-team"
}

variable "business_unit" {
  description = "Business unit or department"
  type        = string
  default     = "email-assistant"
}
