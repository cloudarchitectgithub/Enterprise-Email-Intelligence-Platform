# PowerShell script to build and deploy Lambda function
# This script packages the Python code and deploys it to AWS

Write-Host "Building Crew AI Email Assistant Lambda function..." -ForegroundColor Green

# Check if we're in the right directory
if (-not (Test-Path "src\main.py")) {
    Write-Host "Error: src\main.py not found. Please run this script from the project root." -ForegroundColor Red
    exit 1
}

# Create build directory
$buildDir = "build"
if (Test-Path $buildDir) {
    Remove-Item -Recurse -Force $buildDir
}
New-Item -ItemType Directory -Path $buildDir | Out-Null

# Copy source files to build directory
Write-Host "Copying source files..." -ForegroundColor Yellow
Copy-Item -Path "src\*" -Destination $buildDir -Recurse

# Install dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
Set-Location $buildDir
pip install -r requirements.txt -t .

# Create deployment package
Write-Host "Creating deployment package..." -ForegroundColor Yellow
Compress-Archive -Path "*" -DestinationPath "..\lambda_function.zip" -Force

# Clean up build directory
Set-Location ..
Remove-Item -Recurse -Force $buildDir

$packageSize = (Get-Item "lambda_function.zip").Length / 1MB
Write-Host "Lambda package created: lambda_function.zip" -ForegroundColor Green
Write-Host "Size: $([math]::Round($packageSize, 2)) MB" -ForegroundColor Green

# Check if Terraform is available
if (Get-Command terraform -ErrorAction SilentlyContinue) {
    Write-Host "Terraform found. You can now run:" -ForegroundColor Cyan
    Write-Host "  cd terraform" -ForegroundColor White
    Write-Host "  terraform init" -ForegroundColor White
    Write-Host "  terraform plan" -ForegroundColor White
    Write-Host "  terraform apply" -ForegroundColor White
} else {
    Write-Host "Terraform not found. Please install Terraform to deploy infrastructure." -ForegroundColor Yellow
}

Write-Host "Build completed successfully!" -ForegroundColor Green
