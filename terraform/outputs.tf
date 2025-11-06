# Enterprise API Gateway Outputs
output "api_gateway_url" {
  value       = "https://${aws_api_gateway_rest_api.email_intelligence_api.id}.execute-api.${var.aws_region}.amazonaws.com/${local.environment}/email"
  description = "Enterprise Email Intelligence Platform API endpoint"
}

output "api_gateway_id" {
  value       = aws_api_gateway_rest_api.email_intelligence_api.id
  description = "API Gateway ID for enterprise integration"
}

# Lambda Function Outputs
output "lambda_function_name" {
  value       = aws_lambda_function.email_processor.function_name
  description = "Name of the enterprise email processing Lambda function"
}

output "lambda_function_arn" {
  value       = aws_lambda_function.email_processor.arn
  description = "ARN of the enterprise email processing Lambda function"
}

# DynamoDB Outputs
output "audit_table_name" {
  value       = aws_dynamodb_table.email_audit_log.name
  description = "Name of the enterprise audit log DynamoDB table"
}

output "classification_table_name" {
  value       = aws_dynamodb_table.email_classifications.name
  description = "Name of the email classifications DynamoDB table"
}

# Monitoring Outputs
output "cloudwatch_log_group" {
  value       = aws_cloudwatch_log_group.lambda_logs.name
  description = "CloudWatch log group for enterprise monitoring"
}

output "sns_alerts_topic" {
  value       = aws_sns_topic.alerts.arn
  description = "SNS topic for enterprise alerts and notifications"
}

# Environment Outputs
output "environment" {
  value       = local.environment
  description = "Environment name"
}

output "project_name" {
  value       = local.project_name
  description = "Enterprise project name"
}

# Security Outputs
output "lambda_execution_role_arn" {
  value       = aws_iam_role.lambda_role.arn
  description = "ARN of the Lambda execution role"
}

output "secrets_manager_arn" {
  value       = aws_secretsmanager_secret.email_credentials.arn
  description = "ARN of the enterprise secrets manager"
}

# API Key Output
output "api_key_id" {
  value       = aws_api_gateway_api_key.email_api_key.id
  description = "API Gateway API Key ID"
}

output "api_key_value" {
  value       = aws_api_gateway_api_key.email_api_key.value
  description = "API Gateway API Key Value (keep this secret!)"
  sensitive   = true
}
