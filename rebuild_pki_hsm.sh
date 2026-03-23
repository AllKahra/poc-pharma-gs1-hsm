#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "$0")"

log()  { printf '\n[INFO] %s\n' "$*"; }
ok()   { printf '[OK] %s\n' "$*"; }
warn() { printf '[WARN] %s\n' "$*"; }
err()  { printf '[ERRO] %s\n' "$*" >&2; }

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    err "Comando ausente: $1"
    exit 1
  }
}

log "Iniciando recriação de PKI + HSM e geração do DataMatrix"

require_cmd softhsm2-util
require_cmd pkcs11-tool
require_cmd openssl
require_cmd python3

if [[ -f ".venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
  ok "Virtualenv ativada"
else
  warn "Virtualenv não encontrada em .venv/bin/activate"
fi

if [[ -f "env.sh" ]]; then
  # shellcheck disable=SC1091
  source env.sh
  ok "env.sh carregado"
else
  err "env.sh não encontrado"
  exit 1
fi

: "${SOFTHSM2_CONF:?SOFTHSM2_CONF não definido}"
: "${HSM_MODULE:?HSM_MODULE não definido}"
: "${HSM_MFG_KEY:?HSM_MFG_KEY não definido}"

mkdir -p hsm/tokens pki data dm registry

log "Verificando arquivos de extensão"
[[ -f pki/ca.ext ]] || {
  err "Arquivo ausente: pki/ca.ext"
  exit 1
}
[[ -f pki/mfg.ext ]] || {
  err "Arquivo ausente: pki/mfg.ext"
  exit 1
}
ok "Arquivos de extensão presentes"

log "Limpando tokens antigos"
rm -rf hsm/tokens/*
mkdir -p hsm/tokens
ok "Diretório de tokens resetado"

log "Limpando artefatos antigos da PKI e da geração"
rm -f pki/ca.csr pki/ca.crt pki/ca.srl pki/mfg.csr pki/mfg.crt
rm -f data/new_token_test.txt data/new_token_test.sig
rm -f data/medicine.json data/gs1_base.txt data/gs1_hri.txt data/payload.txt data/payload_tampered.txt
rm -f dm/medicine.png dm/tampered.png
ok "Artefatos antigos removidos"

log "Conferindo configuração do SoftHSM"
echo "SOFTHSM2_CONF=$SOFTHSM2_CONF"
cat "$SOFTHSM2_CONF"

log "Slots antes da criação"
softhsm2-util --show-slots || true

log "Criando token da CA"
softhsm2-util --init-token --free --label "CA-TOKEN" --so-pin 5678 --pin 1234
ok "CA-TOKEN criado"

log "Criando token do fabricante"
softhsm2-util --init-token --free --label "MFG-TOKEN" --so-pin 5678 --pin 1234
ok "MFG-TOKEN criado"

log "Slots após criação"
softhsm2-util --show-slots

log "Gerando chave da CA no HSM"
pkcs11-tool --module "$HSM_MODULE" \
  --token-label "CA-TOKEN" \
  --login --pin 1234 \
  --keypairgen --key-type rsa:2048 \
  --label "CAkey" --id 01
ok "CAkey gerada"

log "Gerando chave do fabricante no HSM"
pkcs11-tool --module "$HSM_MODULE" \
  --token-label "MFG-TOKEN" \
  --login --pin 1234 \
  --keypairgen --key-type rsa:2048 \
  --label "MFGkey" --id 10
ok "MFGkey gerada"

log "Listando objetos da CA"
pkcs11-tool --module "$HSM_MODULE" \
  --token-label "CA-TOKEN" \
  --login --pin 1234 \
  --list-objects

log "Listando objetos do fabricante"
pkcs11-tool --module "$HSM_MODULE" \
  --token-label "MFG-TOKEN" \
  --login --pin 1234 \
  --list-objects

log "Testando engine PKCS#11 no OpenSSL"
openssl engine -t -c pkcs11
ok "Engine PKCS#11 testado"

log "Gerando CSR da CA"
openssl req -new \
  -engine pkcs11 -keyform engine \
  -key "pkcs11:token=CA-TOKEN;object=CAkey;type=private" \
  -subj "/C=BR/ST=SP/O=PoC Pharma/CN=PoC Pharma Root CA" \
  -out pki/ca.csr
ok "pki/ca.csr gerado"

log "Emitindo certificado da CA"
openssl x509 -req -days 3650 \
  -in pki/ca.csr \
  -engine pkcs11 -keyform engine \
  -signkey "pkcs11:token=CA-TOKEN;object=CAkey;type=private" \
  -extfile pki/ca.ext \
  -out pki/ca.crt
ok "pki/ca.crt gerado"

log "Conferindo certificado da CA"
openssl x509 -in pki/ca.crt -text -noout | grep "CA:TRUE"
ok "Certificado da CA válido"

log "Gerando CSR do fabricante"
openssl req -new \
  -engine pkcs11 -keyform engine \
  -key "pkcs11:token=MFG-TOKEN;object=MFGkey;type=private" \
  -subj "/C=BR/ST=SP/O=PoC Pharma/CN=PoC Pharma Manufacturer" \
  -out pki/mfg.csr
ok "pki/mfg.csr gerado"

log "Removendo serial antigo"
rm -f pki/ca.srl

log "Emitindo certificado do fabricante"
openssl x509 -req -days 825 \
  -in pki/mfg.csr \
  -CA pki/ca.crt -CAcreateserial \
  -engine pkcs11 -CAkeyform engine \
  -CAkey "pkcs11:token=CA-TOKEN;object=CAkey;type=private" \
  -extfile pki/mfg.ext \
  -out pki/mfg.crt
ok "pki/mfg.crt gerado"

log "Validando cadeia"
openssl verify -CAfile pki/ca.crt pki/mfg.crt
ok "Cadeia validada"

log "Testando assinatura manual"
echo -n "new-token-test" > data/new_token_test.txt

openssl dgst -sha256 \
  -engine pkcs11 -keyform engine \
  -sign "$HSM_MFG_KEY" \
  -out data/new_token_test.sig data/new_token_test.txt

openssl dgst -sha256 \
  -verify <(openssl x509 -in pki/mfg.crt -pubkey -noout) \
  -signature data/new_token_test.sig data/new_token_test.txt
ok "Teste manual de assinatura concluído"

log "Gerando dados do medicamento"
python scripts/01_generate_data.py \
  --gtin 05412345000013 \
  --lot L202401 \
  --exp 2027-05-31 \
  --serial ABC123456789
ok "Dados do medicamento gerados"

log "Assinando payload com PKCS#11"
python scripts/02_sign_pkcs11.py
ok "Payload assinado"

log "Gerando imagem do DataMatrix"
python scripts/03_generate_datamatrix.py
ok "DataMatrix gerado"

printf '\n'
ok "Processo concluído com sucesso até a geração do DataMatrix."
echo "Saídas principais:"
echo "  - Certificado da CA     : pki/ca.crt"
echo "  - Certificado do MFG    : pki/mfg.crt"
echo "  - Payload assinado      : data/payload.txt"
echo "  - Imagem DataMatrix     : dm/medicine.png"
echo
echo "Se quiser continuar depois, rode manualmente:"
echo "  python scripts/04_verify_datamatrix.py dm/medicine.png --check-chain"
