#!/bin/bash
# Generate .env file from template for ECS deployment
# Usage: ./generate_env.sh [production|development]

set -e

ENVIRONMENT=${1:-production}
TEMPLATE_FILE="backend/.env.template"
OUTPUT_FILE="backend/.env"

echo "🔧 Generating .env file for ${ENVIRONMENT} environment..."

if [ ! -f "$TEMPLATE_FILE" ]; then
    echo "❌ Template file not found: $TEMPLATE_FILE"
    exit 1
fi

# Check if required environment variables are set
REQUIRED_VARS=("POSTGRES_PASSWORD" "SECRET_KEY" "SMTP_SERVER" "SMTP_PORT" "SMTP_USER" "SMTP_PASSWORD" "SMTP_FROM_EMAIL")

missing_vars=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo "❌ Missing required environment variables:"
    for var in "${missing_vars[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "Please set these variables before running this script."
    echo "Example:"
    echo "  export POSTGRES_PASSWORD='your_password'"
    echo "  export SECRET_KEY='your_secret_key'"
    echo "  ..."
    exit 1
fi

# Set environment-specific variables
if [ "$ENVIRONMENT" = "production" ]; then
    export FRONTEND_URL="https://docs.mercator.cn"
    export API_URL="https://docsapi.mercator.cn"
    export DEBUG=False
else
    export FRONTEND_URL="http://localhost:3000"
    export API_URL="http://localhost:8000"
    export DEBUG=True
fi

# Generate .env file from template
cp "$TEMPLATE_FILE" "$OUTPUT_FILE"

# Replace placeholders with actual values
sed -i "s|\${POSTGRES_PASSWORD}|${POSTGRES_PASSWORD}|g" "$OUTPUT_FILE"
sed -i "s|\${SECRET_KEY}|${SECRET_KEY}|g" "$OUTPUT_FILE"
sed -i "s|\${SMTP_SERVER}|${SMTP_SERVER}|g" "$OUTPUT_FILE"
sed -i "s|\${SMTP_PORT}|${SMTP_PORT}|g" "$OUTPUT_FILE"
sed -i "s|\${SMTP_USER}|${SMTP_USER}|g" "$OUTPUT_FILE"
sed -i "s|\${SMTP_PASSWORD}|${SMTP_PASSWORD}|g" "$OUTPUT_FILE"
sed -i "s|\${SMTP_FROM_EMAIL}|${SMTP_FROM_EMAIL}|g" "$OUTPUT_FILE"
sed -i "s|\${SMTP_FROM_NAME}|${SMTP_FROM_NAME:-Mercator Doc Library}|g" "$OUTPUT_FILE"
sed -i "s|\${FRONTEND_URL}|${FRONTEND_URL}|g" "$OUTPUT_FILE"
sed -i "s|\${API_URL}|${API_URL}|g" "$OUTPUT_FILE"
sed -i "s|\${DEBUG}|${DEBUG}|g" "$OUTPUT_FILE"

echo "✅ .env file generated successfully: $OUTPUT_FILE"
echo ""
echo "Generated configuration:"
echo "  Environment: ${ENVIRONMENT}"
echo "  Frontend URL: ${FRONTEND_URL}"
echo "  API URL: ${API_URL}"
echo "  Debug: ${DEBUG}"
echo ""
echo "⚠️  Please verify the generated file and keep it secure!"
