#!/usr/bin/env bash

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export PROJECT_DIR
export SOFTHSM2_CONF="$PROJECT_DIR/hsm/softhsm2.conf"
export HSM_MODULE="/usr/lib/x86_64-linux-gnu/softhsm/libsofthsm2.so"

export HSM_TOKEN_LABEL="MFG-TOKEN"
export HSM_PIN="1234"
export HSM_KEY_LABEL="MFGkey"

export HSM_CA_KEY="pkcs11:token=CA-TOKEN;object=CAkey;type=private"
export HSM_MFG_KEY="pkcs11:token=MFG-TOKEN;object=MFGkey;type=private"

export CA_CRT="$PROJECT_DIR/pki/ca.crt"
export MFG_CRT="$PROJECT_DIR/pki/mfg.crt"
