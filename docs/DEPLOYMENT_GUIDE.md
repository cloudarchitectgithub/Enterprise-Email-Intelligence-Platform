# Email Assistant - EC2 Deployment Guide

## 🚀 Pre-Deployment Checklist

---

## 📋 Prerequisites

### Required Software on EC2:
1. **AWS CLI** (v2.0+)
2. **Terraform** (v1.0+)
3. **Python** (3.11+)
4. **PowerShell** (for Windows EC2) or **Bash** (for Linux EC2)

### AWS Account Requirements:
- AWS Account with appropriate permissions
- Bedrock access enabled (Claude 3 Sonnet model)
- IAM permissions for Lambda, DynamoDB, API Gateway, Secrets Manager, CloudWatch, SNS

---

## 🛠️ Step-by-Step Deployment

### Step 1: Upload Project to EC2
```bash
# Upload the entire project folder to your EC2 instance
scp -r email-assistant/ ec2-user@your-ec2-ip:/home/ec2-user/
```

### Step 2: Install Prerequisites
```bash
# Connect to your EC2 instance
ssh ec2-user@your-ec2-ip

# Install AWS CLI 
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Install Terraform
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# Install Python 3.11 
sudo yum update -y
sudo yum install -y python3.11 python3.11-pip
```

### Step 3: Configure AWS Credentials
```bash
# Configure AWS CLI with your credentials
aws configure
# Enter your:
# - AWS Access Key ID
# - AWS Secret Access Key  
# - Default region (e.g., us-east-1)
# - Default output format (json)
```

### Step 4: Run Setup Script
```bash
cd email-assistant
chmod +x setup.ps1
./setup.ps1
```

### Step 5: Deploy Infrastructure with Terraform
```bash
cd terraform

# Initialize Terraform
terraform init

# Review the plan
terraform plan

# Apply the infrastructure
terraform apply
# Type 'yes' when prompted
```

### Step 6: Build and Deploy Lambda Function
```bash
cd ../scripts
chmod +x build_lambda.ps1
./build_lambda.ps1

# The script will create lambda_function.zip
# Terraform will automatically deploy it
```

### Step 7: Configure Secrets Manager
```bash
# Update email credentials in Secrets Manager
aws secretsmanager update-secret \
    --secret-id email-assistant-dev-email-credentials \
    --secret-string '{
        "imap_server": "imap.gmail.com",
        "imap_port": 993,
        "smtp_server": "smtp.gmail.com", 
        "smtp_port": 587,
        "email_address": "your-email@example.com",
        "password": "your-app-password",
        "enterprise_mode": true,
        "compliance_level": "enterprise"
    }'
```

### Step 8: Test the Deployment
```bash
cd ../scripts
chmod +x test_invoke.ps1
./test_invoke.ps1
```

---

## 🔧 Configuration Details

### Environment Variables (Set by Terraform):
- `BEDROCK_MODEL_ID`: Claude 3 Sonnet model ID
- `LOG_LEVEL`: INFO
- `ENVIRONMENT`: dev
- `DYNAMODB_AUDIT_TABLE`: Email audit log table
- `DYNAMODB_CLASSIFICATION_TABLE`: Email classifications table
- `API_GATEWAY_URL`: API endpoint URL

### Terraform Variables (Customizable):
- `aws_region`: us-east-1 (default)
- `environment`: dev (default)
- `lambda_timeout`: 300 seconds
- `lambda_memory_size`: 512 MB
- `bedrock_model_id`: Claude 3 Sonnet model
- `log_retention_days`: 30 days

### Cost Tracking Tags (AWS Best Practices):
All resources are automatically tagged for cost tracking and resource management:
- `Project`: email-assistant
- `Environment`: dev/staging/prod (configurable)
- `ManagedBy`: terraform
- `CostCenter`: engineering (configurable via `cost_center` variable)
- `Owner`: ai-team (configurable via `owner` variable)
- `Application`: email-assistant
- `BusinessUnit`: email-assistant (configurable via `business_unit` variable)

**Customize tags during deployment:**
```bash
terraform apply \
  -var="cost_center=your-cost-center" \
  -var="owner=your-team" \
  -var="business_unit=your-business-unit"
```

These tags enable:
- **Cost allocation** in AWS Cost Explorer
- **Resource filtering** in AWS Console
- **Automated billing reports** by team/department
- **Resource governance** and compliance tracking

---

## 📊 AWS Resources Created

### Core Services:
1. **Lambda Function**: `email-assistant-dev-processor`
2. **API Gateway**: `email-assistant-dev-api`
3. **DynamoDB Tables**: 
   - `email-assistant-dev-audit-log`
   - `email-assistant-dev-classifications`
4. **Secrets Manager**: 
   - `email-assistant-dev-email-credentials`
   - `email-assistant-dev-api-keys`

### Monitoring & Security:
5. **CloudWatch Logs**: `/aws/lambda/email-assistant-dev-processor`
6. **CloudWatch Alarms**: Error and duration monitoring
7. **SNS Topic**: `email-assistant-dev-alerts`
8. **IAM Roles & Policies**: Lambda execution and API Gateway permissions

---

## 🧪 Testing the System

### Test API Endpoint:
```bash
# Get the API Gateway URL
cd terraform
API_URL=$(terraform output -raw api_gateway_url)
echo $API_URL

# Test with sample email
curl -X POST $API_URL \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Meeting Request",
    "sender": "test@example.com",
    "recipient": "ai@company.com",
    "body": "Hi, I would like to schedule a meeting to discuss the project.",
    "user_id": "test-user",
    "metadata": {
      "priority": "medium",
      "department": "engineering"
    }
  }'
```

### Expected Response:
```json
{
  "request_id": "uuid-here",
  "status": "success",
  "result": {
    "status": "success",
    "classification": {
      "email_type": "meeting_request",
      "priority": "medium",
      "category": "Project discussion meeting",
      "timestamp": "2024-01-01T12:00:00Z",
      "confidence": 0.95
    }
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

---

## 🔍 Troubleshooting

### Common Issues:

1. **Bedrock Access Denied**:
   ```bash
   # Enable Bedrock in your AWS region
   aws bedrock list-foundation-models --region us-east-1
   ```

2. **Lambda Deployment Failed**:
   ```bash
   # Check Lambda function logs
   aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/crew-ai"
   ```

3. **API Gateway 500 Error**:
   ```bash
   # Check CloudWatch logs for Lambda errors
   aws logs filter-log-events --log-group-name "/aws/lambda/email-assistant-dev-processor"
   ```

4. **DynamoDB Permission Issues**:
   ```bash
   # Verify IAM role permissions
   aws iam get-role-policy --role-name email-assistant-dev-lambda-role --policy-name email-assistant-dev-lambda-policy
   ```

---

## 📈 Monitoring & Maintenance

### CloudWatch Dashboards:
- Lambda function metrics (invocations, errors, duration)
- DynamoDB read/write capacity
- API Gateway request metrics

### Log Analysis:
```bash
# View recent Lambda logs
aws logs tail /aws/lambda/email-assistant-dev-processor --follow

# Check error patterns
aws logs filter-log-events \
  --log-group-name "/aws/lambda/email-assistant-dev-processor" \
  --filter-pattern "ERROR"
```

### Cost Optimization:
- Monitor Lambda execution time and memory usage
- Review DynamoDB read/write capacity
- Set up billing alerts for unexpected costs

---


## ✅ Deployment Complete!

Email Assistant is now deployed and ready to process emails intelligently using Claude 3 Sonnet via AWS Bedrock!

**Next Steps:**
1. Test the API endpoint with real email data
2. Configure your email client to send emails to the API
3. Monitor the CloudWatch dashboards
4. Set up alerting for production use


