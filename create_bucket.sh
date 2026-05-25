#!/bin/bash
# ==============================================================================
# Shell script to create GCS bucket for OnBrand Asset Creator
# ==============================================================================

BUCKET_NAME="image-bucket-sandbox-dce"
REGION="us-central1"

echo "====================================================="
echo "🌐 OnBrand Asset Creator - GCS Bucket Setup"
echo "====================================================="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI is not installed. Please install it and try again."
    exit 1
fi

# Check if user is authenticated
echo "Checking active Google Cloud account..."
ACTIVE_ACCOUNT=$(gcloud config get-value account 2>/dev/null)
if [ -z "$ACTIVE_ACCOUNT" ]; then
    echo "❌ Error: No active Google Cloud account found."
    echo "Please authenticate first by running: gcloud auth login"
    exit 1
fi
echo "✅ Active account: $ACTIVE_ACCOUNT"

# Check if project is set
ACTIVE_PROJECT=$(gcloud config get-value project 2>/dev/null)
if [ -z "$ACTIVE_PROJECT" ]; then
    echo "❌ Error: No active Google Cloud project set."
    echo "Please set your project by running: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi
echo "✅ Active project: $ACTIVE_PROJECT"

# Check if bucket already exists
echo "Checking if bucket gs://${BUCKET_NAME} already exists..."
if gcloud storage buckets describe gs://${BUCKET_NAME} &>/dev/null; then
    echo "✨ Bucket gs://${BUCKET_NAME} already exists in your project!"
    exit 0
fi

# Create GCS Bucket
echo "Creating Google Cloud Storage bucket gs://${BUCKET_NAME} in region ${REGION}..."
gcloud storage buckets create gs://${BUCKET_NAME} \
    --location=${REGION} \
    --uniform-bucket-level-access

if [ $? -eq 0 ]; then
    echo "====================================================="
    echo "✅ Success: Bucket gs://${BUCKET_NAME} successfully created!"
    echo "The application is now ready to save assets to GCS."
    echo "====================================================="
else
    echo "❌ Error: Failed to create the GCS bucket."
    exit 1
fi
