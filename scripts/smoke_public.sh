#!/bin/sh
set -eu

BASE_URL="${BASE_URL:?Set BASE_URL to the deployed application URL}"
curl --fail --silent --show-error "$BASE_URL/health"
printf '\n'
echo "Public health check passed."
