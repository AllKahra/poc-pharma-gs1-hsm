#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "$0")"

echo "Starting project environment..."

if [[ -f env.sh ]]; then
  # shellcheck disable=SC1091
  source env.sh
else
  echo "Warning: env.sh not found"
fi

if [[ -f .venv/bin/activate ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
else
  echo "Warning: virtual environment not found at .venv/bin/activate"
fi

echo
echo "Environment ready."
echo "Project directory: $(pwd)"
echo "Python: $(command -v python || true)"
echo "Virtualenv: ${VIRTUAL_ENV:-<none>}"
echo "SoftHSM config: ${SOFTHSM2_CONF:-<unset>}"
echo "HSM module: ${HSM_MODULE:-<unset>}"

echo
echo "Checking HSM slots..."
softhsm2-util --show-slots || true

echo
echo "OpenSSL version: $(openssl version)"
echo "pkcs11-tool: $(command -v pkcs11-tool || true)"
