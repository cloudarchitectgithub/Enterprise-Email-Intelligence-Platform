# Lambda function for Enterprise Email Intelligence Processing
resource "aws_lambda_function" "email_processor" {
  filename         = "lambda_function.zip"
  function_name    = "${local.project_name}-${local.environment}-processor"
  role            = aws_iam_role.lambda_role.arn
  handler         = "main.lambda_handler"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime         = "python3.11"
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory_size

  environment {
    variables = {
      BEDROCK_MODEL_ID           = var.bedrock_model_id
      LOG_LEVEL                  = "INFO"
      ENVIRONMENT                = local.environment
      DYNAMODB_AUDIT_TABLE       = aws_dynamodb_table.email_audit_log.name
      DYNAMODB_CLASSIFICATION_TABLE = aws_dynamodb_table.email_classifications.name
      API_GATEWAY_URL            = "https://${aws_api_gateway_rest_api.email_intelligence_api.id}.execute-api.${var.aws_region}.amazonaws.com/${local.environment}/email"
    }
  }

  tags = local.tags
}

# Create deployment package
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "../src"
  output_path = "lambda_function.zip"
}

# Lambda permission for API Gateway
resource "aws_lambda_permission" "allow_api_gateway" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.email_processor.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.email_intelligence_api.execution_arn}/*/*"
}

# CloudWatch Log Group with Enterprise Retention
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${aws_lambda_function.email_processor.function_name}"
  retention_in_days = 30  # Enterprise compliance requirement
  tags              = local.tags
}

# CloudWatch Alarms for Enterprise Monitoring
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${local.project_name}-${local.environment}-lambda-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "This metric monitors lambda errors"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = aws_lambda_function.email_processor.function_name
  }

  tags = local.tags
}

resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  alarm_name          = "${local.project_name}-${local.environment}-lambda-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Average"
  threshold           = "250000"  # 250 seconds
  alarm_description   = "This metric monitors lambda duration"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = aws_lambda_function.email_processor.function_name
  }

  tags = local.tags
}

# SNS Topic for Enterprise Alerts
resource "aws_sns_topic" "alerts" {
  name = "${local.project_name}-${local.environment}-alerts"
  tags = local.tags
}
