export SOFTHSM2_CONF="$HOME/poc-pharma-gs1-hsm/hsm/softhsm2.conf"

export HSM_MODULE="/usr/lib/x86_64-linux-gnu/softhsm/libsofthsm2.so"

export HSM_TOKEN_LABEL="MFG-TOKEN"
export HSM_PIN="1234"
export HSM_KEY_LABEL="MFGkey"

export CA_CRT="pki/ca.crt"
export MFG_CRT="pki/mfg.crt"
