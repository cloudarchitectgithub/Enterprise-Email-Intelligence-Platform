# Enterprise Secrets Manager for credentials and configuration
resource "aws_secretsmanager_secret" "email_credentials" {
  name        = "${local.project_name}-${local.environment}-email-credentials"
  description = "Enterprise email processing credentials and configuration"

  tags = local.tags
}

resource "aws_secretsmanager_secret_version" "email_credentials_version" {
  secret_id = aws_secretsmanager_secret.email_credentials.id
  secret_string = jsonencode({
    imap_server = "imap.gmail.com"
    imap_port   = 993
    smtp_server = "smtp.gmail.com"
    smtp_port   = 587
    # Note: Add actual credentials via AWS Console or CLI
    # email_address = "your-email@example.com"
    # password      = "your-app-password"
    enterprise_mode = true
    compliance_level = "enterprise"
  })
}

# Enterprise API Keys Secret (if needed)
resource "aws_secretsmanager_secret" "api_keys" {
  name        = "${local.project_name}-${local.environment}-api-keys"
  description = "Enterprise API keys and external service credentials"

  tags = local.tags
}

resource "aws_secretsmanager_secret_version" "api_keys_version" {
  secret_id = aws_secretsmanager_secret.api_keys.id
  secret_string = jsonencode({
    # Add enterprise API keys as needed
    # external_service_key = "your-api-key"
    enterprise_environment = local.environment
  })
}

# Output secret ARNs for enterprise reference
output "email_credentials_secret_arn" {
  value       = aws_secretsmanager_secret.email_credentials.arn
  description = "ARN of the enterprise email credentials secret"
}

output "api_keys_secret_arn" {
  value       = aws_secretsmanager_secret.api_keys.arn
  description = "ARN of the enterprise API keys secret"
}
