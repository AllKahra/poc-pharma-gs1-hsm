#!/bin/bash

echo "Starting project environment..."

cd ~/poc-pharma-gs1-hsm || exit 1

# Carregar variáveis do projeto
if [ -f env.sh ]; then
    source env.sh
else
    echo "Warning: env.sh not found"
fi

# Ativar ambiente Python
if [ -f .venv/bin/activate ]; then
    source .venv/bin/activate
else
    echo "Warning: virtual environment not found at .venv/bin/activate"
fi

echo ""
echo "Environment ready."
echo "Project directory: $(pwd)"
echo "Python: $(which python)"
echo "Virtualenv: $VIRTUAL_ENV"
echo "SoftHSM config: $SOFTHSM2_CONF"
echo "HSM module: $HSM_MODULE"

echo ""
echo "Checking HSM slots..."
softhsm2-util --show-slots

echo ""
echo "OpenSSL version: $(openssl version)"
echo "pkcs11-tool: $(which pkcs11-tool)"
