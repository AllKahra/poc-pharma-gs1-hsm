#!/bin/bash

echo "Starting project environment..."

# entrar na pasta do projeto
cd ~/poc-pharma-gs1-hsm

# ativar ambiente python
source .venv/bin/activate

# carregar variáveis do projeto
source env.sh

echo "Environment ready."
echo "Project directory: $(pwd)"
echo "Python: $(which python)"
echo "SoftHSM config: $SOFTHSM2_CONF"
