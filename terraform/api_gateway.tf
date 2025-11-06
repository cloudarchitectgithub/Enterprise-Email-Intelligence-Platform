# API Gateway for Enterprise Integration
resource "aws_api_gateway_rest_api" "email_intelligence_api" {
  name        = "${local.project_name}-${local.environment}-api"
  description = "Enterprise Email Intelligence Platform API"
  
  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = local.tags
}

resource "aws_api_gateway_resource" "email_resource" {
  rest_api_id = aws_api_gateway_rest_api.email_intelligence_api.id
  parent_id   = aws_api_gateway_rest_api.email_intelligence_api.root_resource_id
  path_part   = "email"
}

resource "aws_api_gateway_method" "email_post" {
  rest_api_id      = aws_api_gateway_rest_api.email_intelligence_api.id
  resource_id      = aws_api_gateway_resource.email_resource.id
  http_method      = "POST"
  authorization    = "NONE"
  api_key_required = true
}

resource "aws_api_gateway_integration" "email_integration" {
  rest_api_id = aws_api_gateway_rest_api.email_intelligence_api.id
  resource_id = aws_api_gateway_resource.email_resource.id
  http_method = aws_api_gateway_method.email_post.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.email_processor.invoke_arn
}

resource "aws_api_gateway_deployment" "email_deployment" {
  depends_on = [
    aws_api_gateway_integration.email_integration,
  ]

  rest_api_id = aws_api_gateway_rest_api.email_intelligence_api.id
  stage_name  = local.environment

  lifecycle {
    create_before_destroy = true
  }
}

# DynamoDB for Enterprise Data Storage and Audit Trail
resource "aws_dynamodb_table" "email_audit_log" {
  name           = "${local.project_name}-${local.environment}-audit-log"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "email_id"
  range_key      = "timestamp"

  attribute {
    name = "email_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  attribute {
    name = "user_id"
    type = "S"
  }

  global_secondary_index {
    name            = "user-timestamp-index"
    hash_key        = "user_id"
    range_key       = "timestamp"
    projection_type = "ALL"
  }

  server_side_encryption {
    enabled = true
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = local.tags
}

resource "aws_dynamodb_table" "email_classifications" {
  name           = "${local.project_name}-${local.environment}-classifications"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "classification_id"

  attribute {
    name = "classification_id"
    type = "S"
  }

  server_side_encryption {
    enabled = true
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = local.tags
}

# API Key for secure access
resource "aws_api_gateway_api_key" "email_api_key" {
  name        = "${local.project_name}-${local.environment}-api-key"
  description = "API Key for Email Intelligence Platform"
  enabled     = true
  
  tags = local.tags
}

# Usage Plan for API Key
resource "aws_api_gateway_usage_plan" "email_usage_plan" {
  name        = "${local.project_name}-${local.environment}-usage-plan"
  description = "Usage plan for Email Intelligence Platform"

  api_stages {
    api_id = aws_api_gateway_rest_api.email_intelligence_api.id
    stage  = aws_api_gateway_deployment.email_deployment.stage_name
  }

  quota_settings {
    limit  = 10000
    period = "MONTH"
  }

  throttle_settings {
    burst_limit = 100
    rate_limit  = 50
  }
  
  tags = local.tags
}

# Associate API Key with Usage Plan
resource "aws_api_gateway_usage_plan_key" "email_usage_plan_key" {
  key_id        = aws_api_gateway_api_key.email_api_key.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.email_usage_plan.id
}
