#!/bin/bash

echo "Starting project environment..."

cd ~/poc-pharma-gs1-hsm || exit 1

source .venv/bin/activate
source env.sh

echo "Environment ready."
echo "Project directory: $(pwd)"
echo "Python: $(which python)"
echo "VIRTUAL_ENV: $VIRTUAL_ENV"
echo "SoftHSM config: $SOFTHSM2_CONF"
