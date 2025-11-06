#!/bin/bash
echo "Building Lambda deployment package..."
cd src
pip3 install -r requirements.txt -t .
zip -r9 ../dist/lambda_function.zip . -x "*.git*" "*__pycache__*" "*.DS_Store*"
echo "Lambda package created: ../dist/lambda_function.zip"
