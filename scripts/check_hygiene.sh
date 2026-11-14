#!/usr/bin/env bash
set -euo pipefail

if git ls-files --error-unmatch .env >/dev/null 2>&1; then
  echo ".env must not be tracked" >&2
  exit 1
fi

forbidden='HIPAA'' compliant'
if git grep -n -i -F "$forbidden" -- . ':!node_modules' ':!.git' ':!specs/**' ':!.specify/**' >/dev/null; then
  echo 'A prohibited compliance claim must not appear in application files' >&2
  exit 1
fi
