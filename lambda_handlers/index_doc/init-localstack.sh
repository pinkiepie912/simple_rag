#!/bin/bash
set -e # 오류 발생 시 스크립트 중단

echo "Starting AWS resource initialization..."

export AWS_DEFAULT_REGION=ap-northeast-2
alias awslocal="aws --endpoint-url=http://localhost:4566"

BUCKET_NAME="documents"
echo "Creating S3 bucket: ${BUCKET_NAME}"
awslocal s3 mb s3://${BUCKET_NAME}

ROLE_NAME="lambda-s3-role"
ROLE_ARN=$(awslocal iam create-role \
  --role-name ${ROLE_NAME} \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": { "Service": "lambda.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }]
  }' --query 'Role.Arn' --output text)

echo "Created IAM Role: ${ROLE_ARN}"

awslocal iam attach-role-policy --role-name ${ROLE_NAME} --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess
awslocal iam attach-role-policy --role-name ${ROLE_NAME} --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# 4. Lambda 함수 생성
FUNCTION_NAME="index-docs"
LAMBDA_ARN=$(awslocal lambda create-function \
  --function-name ${FUNCTION_NAME} \
  --runtime python3.12 \
  --role ${ROLE_ARN} \
  --handler index_docs.lambda_handler \
  --zip-file fileb:///tmp/lambda.zip \
  --timeout 300 \
  --memory-size 512 \
  --environment "Variables={ES_HOST=http://es_n1:9200,ES_INDEX=documents}" \
  --query 'FunctionArn' --output text)

echo "Created Lambda function: ${LAMBDA_ARN}"

echo "Waiting for Lambda function to become active..."
awslocal lambda wait function-active-v2 --function-name ${FUNCTION_NAME}
echo "Lambda function is active."

awslocal s3api put-bucket-notification-configuration \
  --bucket ${BUCKET_NAME} \
  --notification-configuration '{
    "LambdaFunctionConfigurations": [{
      "LambdaFunctionArn": "'${LAMBDA_ARN}'",
      "Events": ["s3:ObjectCreated:*"]
    }]
  }'

echo "Configured S3 bucket notification to trigger Lambda."
echo "Initialization complete!"
