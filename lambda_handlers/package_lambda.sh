#!/bin/bash

set -e

PROJECT_PATH="${PROJECT_PATH:-index_doc}"

SOURCE_CODE_SUBDIR="src"

OUTPUT_ZIP_FILE="lambda.zip"
# --------------------------


echo "Build..."

echo "Generate requirements.txt from '${PROJECT_PATH}/pyproject.toml'"
(cd "$PROJECT_PATH" && poetry export -f requirements.txt --output requirements.txt --without-hashes --without dev)

echo "Create package directory"
rm -rf package
mkdir -p package


echo "Install dependencies"
pip install -r "${PROJECT_PATH}/requirements.txt" -t ./package


echo "Copy '${PROJECT_PATH}'"

if [ ! -d "$PROJECT_PATH" ]; then
  echo "Project not found"
  exit 1
fi
cp -r ${PROJECT_PATH}/* ./package/


echo "Start zip"
(cd package && zip -qr "../${OUTPUT_ZIP_FILE}" .)


echo "Remove temporary directory and file"
rm -rf package
rm "${PROJECT_PATH}/requirements.txt"


echo ""
echo "Build completed successfully!"
