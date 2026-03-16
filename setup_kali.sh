#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="${PROJECT_DIR:-$HOME/poc-pharma-gs1-hsm}"
VENV_DIR="$PROJECT_DIR/.venv"

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

log "Preparando ambiente do projeto em: $PROJECT_DIR"

require_cmd sudo
require_cmd apt
require_cmd python3
require_cmd git

mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

log "Atualizando lista de pacotes"
sudo apt update

log "Instalando dependências do sistema"
sudo apt install -y \
  softhsm2 \
  opensc \
  libengine-pkcs11-openssl \
  libdmtx0b \
  libdmtx-dev \
  python3 \
  python3-venv \
  python3-pip \
  jq

ok "Dependências do sistema instaladas"

log "Criando estrutura mínima do projeto"
mkdir -p \
  hsm/tokens \
  pki \
  data \
  dm \
  scripts \
  config \
  registry \
  reference \
  docs

touch data/.gitkeep dm/.gitkeep registry/.gitkeep

ok "Estrutura mínima pronta"

if [[ ! -d "$VENV_DIR" ]]; then
  log "Criando ambiente virtual Python"
  python3 -m venv "$VENV_DIR"
  ok "Ambiente virtual criado"
else
  ok "Ambiente virtual já existe"
fi

log "Ativando ambiente virtual"
# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"

log "Atualizando pip, setuptools e wheel"
python -m pip install -U pip setuptools wheel

log "Instalando dependências Python"
pip install \
  python-pkcs11 \
  cryptography \
  pillow \
  pylibdmtx

ok "Dependências Python instaladas"

log "Verificando ferramentas principais"
softhsm2-util --version || true
pkcs11-tool --version || true
openssl version
python3 --version

log "Testando biblioteca DataMatrix em Python"
python - <<'PY'
from pylibdmtx.pylibdmtx import encode
r = encode(b"teste")
print("ok", r.width, r.height)
PY

ok "Teste básico de DataMatrix concluído"

if [[ ! -f "$PROJECT_DIR/hsm/softhsm2.conf" ]]; then
  log "Criando hsm/softhsm2.conf padrão"
  cat > "$PROJECT_DIR/hsm/softhsm2.conf" <<EOF
directories.tokendir = ${PROJECT_DIR}/hsm/tokens
objectstore.backend = file
log.level = INFO
EOF
  ok "hsm/softhsm2.conf criado"
else
  ok "hsm/softhsm2.conf já existe"
fi

if [[ ! -f "$PROJECT_DIR/env.sh" ]]; then
  log "Criando env.sh padrão"
  cat > "$PROJECT_DIR/env.sh" <<'EOF'
export SOFTHSM2_CONF="$HOME/poc-pharma-gs1-hsm/hsm/softhsm2.conf"
export HSM_MODULE="/usr/lib/x86_64-linux-gnu/softhsm/libsofthsm2.so"

export HSM_TOKEN_LABEL="MFG-TOKEN"
export HSM_PIN="1234"
export HSM_KEY_LABEL="MFGkey"

export HSM_CA_KEY="pkcs11:token=CA-TOKEN;object=CAkey;type=private"
export HSM_MFG_KEY="pkcs11:token=MFG-TOKEN;object=MFGkey;type=private"

export CA_CRT="pki/ca.crt"
export MFG_CRT="pki/mfg.crt"
EOF
  ok "env.sh criado"
else
  ok "env.sh já existe"
fi

if [[ ! -f "$PROJECT_DIR/start.sh" ]]; then
  log "Criando start.sh padrão"
  cat > "$PROJECT_DIR/start.sh" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "$0")"

if [[ -d ".venv" ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

if [[ -f "env.sh" ]]; then
  # shellcheck disable=SC1091
  source env.sh
fi

echo "Starting project environment..."
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
EOF
  chmod +x "$PROJECT_DIR/start.sh"
  ok "start.sh criado"
else
  ok "start.sh já existe"
fi

log "Validando caminhos padrão do projeto"
[[ -f "$PROJECT_DIR/hsm/softhsm2.conf" ]] && ok "softhsm2.conf presente" || warn "softhsm2.conf ausente"
[[ -f "$PROJECT_DIR/env.sh" ]] && ok "env.sh presente" || warn "env.sh ausente"
[[ -f "$PROJECT_DIR/start.sh" ]] && ok "start.sh presente" || warn "start.sh ausente"

log "Resumo do que este script fez"
ok "Atualizou apt"
ok "Instalou dependências do sistema"
ok "Criou/validou .venv"
ok "Instalou dependências Python"
ok "Criou estrutura mínima do projeto"
ok "Criou arquivos padrão ausentes (softhsm2.conf, env.sh, start.sh)"

printf '\n'
warn "Este script NÃO cria tokens, NÃO gera chaves e NÃO monta a PKI automaticamente."
warn "Para a PoC completa funcionar em outra máquina, você precisa:"
echo "  1. copiar hsm/tokens/ da máquina original OU recriar tokens/chaves"
echo "  2. garantir que pki/ca.crt e pki/mfg.crt existam"
echo "  3. depois abrir com: source ./start.sh"

printf '\n'
ok "Bootstrap concluído com sucesso."
