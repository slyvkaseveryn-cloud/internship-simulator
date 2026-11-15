#!/usr/bin/env bash
# Build the frontend and upload it next to config.json and the case files (both owned by Terraform).
set -euo pipefail
cd "$(dirname "$0")/.."
BUCKET=$(terraform -chdir=infra output -raw site_bucket)
DIST_ID=$(terraform -chdir=infra output -raw distribution_id)

(cd frontend && npm ci --silent && npm run build)

# Hashed assets: cache for a year. index.html: always revalidate.
aws s3 sync frontend/dist "s3://$BUCKET" --delete \
  --exclude "config.json" --exclude "cases/*" --exclude "index.html" \
  --cache-control "public, max-age=31536000, immutable"
aws s3 cp frontend/dist/index.html "s3://$BUCKET/index.html" --cache-control "no-cache"
aws cloudfront create-invalidation --distribution-id "$DIST_ID" --paths "/index.html" >/dev/null
echo "Deployed: $(terraform -chdir=infra output -raw site_url)"
