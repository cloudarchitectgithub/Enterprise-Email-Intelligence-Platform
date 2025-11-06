# PowerShell script to test Lambda function invocation
# This script tests the Lambda function with sample email data

Write-Host "Testing Crew AI Email Assistant Lambda function..." -ForegroundColor Green

# Check if test payload exists
if (-not (Test-Path "src\test_payload.json")) {
    Write-Host "Error: src\test_payload.json not found." -ForegroundColor Red
    exit 1
}

# Check if AWS CLI is available
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "Error: AWS CLI not found. Please install AWS CLI." -ForegroundColor Red
    exit 1
}

# Get Lambda function name from Terraform output
try {
    Push-Location terraform
    $lambdaFunctionName = terraform output -raw lambda_function_name 2>$null
    Pop-Location
    
    if (-not $lambdaFunctionName) {
        Write-Host "Error: Could not get Lambda function name from Terraform." -ForegroundColor Red
        Write-Host "Please ensure Terraform has been applied and the function exists." -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "Error accessing Terraform outputs: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "Testing function: $lambdaFunctionName" -ForegroundColor Cyan

# Invoke Lambda function
Write-Host "Invoking Lambda function..." -ForegroundColor Yellow
aws lambda invoke `
    --function-name $lambdaFunctionName `
    --payload file://src/test_payload.json `
    --cli-binary-format raw-in-base64-out `
    response.json

# Display response
Write-Host "Response:" -ForegroundColor Green
Get-Content response.json | ConvertFrom-Json | ConvertTo-Json -Depth 10

# Clean up
Remove-Item -Force response.json -ErrorAction SilentlyContinue

Write-Host "Test completed!" -ForegroundColor Green
