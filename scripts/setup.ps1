# Enterprise Deployment Setup Script
Write-Host "Enterprise Email Intelligence Platform - Setup Script" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green

# Check if AWS CLI is installed
Write-Host "`nChecking AWS CLI installation..." -ForegroundColor Yellow
try {
    $awsVersion = aws --version
    Write-Host "✓ AWS CLI is installed: $awsVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ AWS CLI not found. Please install from: https://aws.amazon.com/cli/" -ForegroundColor Red
}

# Check if Terraform is installed
Write-Host "`nChecking Terraform installation..." -ForegroundColor Yellow
try {
    $terraformVersion = terraform version
    Write-Host "✓ Terraform is installed" -ForegroundColor Green
} catch {
    Write-Host "✗ Terraform not found. Please install from: https://developer.hashicorp.com/terraform/downloads" -ForegroundColor Red
}

# Check if Python is installed
Write-Host "`nChecking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version
    Write-Host "✓ Python is installed: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.11+ from: https://python.org" -ForegroundColor Red
}

Write-Host "`nNext Steps:" -ForegroundColor Cyan
Write-Host "1. Install any missing prerequisites above" -ForegroundColor White
Write-Host "2. Configure AWS credentials: aws configure" -ForegroundColor White
Write-Host "3. Deploy infrastructure: cd terraform && terraform init && terraform apply" -ForegroundColor White
Write-Host "4. Build Lambda package: cd scripts && .\build_lambda.ps1" -ForegroundColor White
Write-Host "5. Test the system: .\test_invoke.ps1" -ForegroundColor White

Write-Host "
Enterprise deployment ready! 🚀" -ForegroundColor Green

