# poc-pharma-gs1-hsm

## 🇺🇸 English

Proof of Concept (PoC) demonstrating pharmaceutical data authentication using **PKI**, **HSM-backed signing**, and **GS1-style DataMatrix**.

The project simulates how medicine serialization data can be cryptographically protected to prevent tampering and counterfeit scenarios.

---

# Objective

Demonstrate a simplified architecture where:

- Serialized medicine data is generated
- Data is digitally signed using a private key protected by an **HSM**
- The signature is embedded into a **DataMatrix payload**
- The payload can later be verified for **authenticity and integrity**

---

# Security Goals

This PoC demonstrates how to:

- Protect signing keys inside an **HSM**
- Ensure **data integrity**
- Authenticate **manufacturer origin**
- Detect **tampering**
- Simulate **basic clone detection**

---

# Technologies Used

| Component | Purpose |
|----------|--------|
| SoftHSM2 | HSM simulation |
| PKCS#11 | Hardware security interface |
| OpenSSL | PKI operations |
| Python | Automation scripts |
| cryptography | Digital signatures |
| pylibdmtx | DataMatrix generation |
| Pillow | Image handling |

---

# Project Structure

```
poc-pharma-gs1-hsm
│
├── config/        # Configuration files
├── data/          # Generated payloads
├── dm/            # Generated DataMatrix images
├── docs/          # Technical documentation
│
├── hsm/
│   ├── softhsm2.conf
│   └── tokens/
│
├── pki/
│   ├── ca.ext
│   └── mfg.ext
│
├── registry/      # Simulated registry
├── scripts/       # Project scripts
│
├── env.sh
├── .gitignore
└── README.md
```

---

# Environment Setup

## Install dependencies

```bash
sudo apt update

sudo apt install -y \
softhsm2 \
opensc \
openssl \
libengine-pkcs11-openssl \
libdmtx0t64 \
libdmtx-dev \
python3 \
python3-venv \
python3-pip
```

---

## Create Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate

pip install -U pip setuptools wheel

pip install \
python-pkcs11 \
cryptography \
pillow \
pylibdmtx
```

---

# SoftHSM Configuration

File:

```
hsm/softhsm2.conf
```

Content:

```
directories.tokendir = ./hsm/tokens
objectstore.backend = file
log.level = INFO
```

Set environment variable:

```bash
export SOFTHSM2_CONF=$(pwd)/hsm/softhsm2.conf
```

---

# Initialize HSM Tokens

Create **CA token**:

```bash
softhsm2-util --init-token --free \
--label "CA-TOKEN" \
--so-pin 5678 \
--pin 1234
```

Create **manufacturer token**:

```bash
softhsm2-util --init-token --free \
--label "MFG-TOKEN" \
--so-pin 5678 \
--pin 1234
```

Verify tokens:

```bash
softhsm2-util --show-slots
```

---

# Current Project Status

✔ Environment prepared  
✔ SoftHSM configured  
✔ Tokens initialized  
✔ PKCS#11 module validated  
✔ Python environment validated  

Next steps:

- Generate keys inside the HSM
- Build local PKI
- Sign serialized medicine data
- Generate DataMatrix payload
- Implement verification workflow

---

# Security Considerations

Sensitive material is intentionally excluded from version control:

- HSM token storage
- private keys
- generated certificates
- serialized payload data

---

# Educational Purpose

This project is designed as a **learning and research PoC** demonstrating:

- PKI integration with HSM
- secure key management
- data authentication mechanisms
- anti-counterfeit concepts in pharmaceutical supply chains

---

---

## 🇧🇷 Português (Brasil)

Prova de conceito (PoC) demonstrando autenticação de dados farmacêuticos utilizando **PKI**, **assinatura com suporte de HSM** e **DataMatrix no estilo GS1**.

O projeto simula como dados de serialização de medicamentos podem ser protegidos criptograficamente para evitar adulteração e cenários de falsificação.

---

# Objetivo

Demonstrar uma arquitetura simplificada onde:

- Dados serializados de medicamentos são gerados
- Os dados são assinados digitalmente utilizando uma chave privada protegida por um **HSM**
- A assinatura é incorporada em um **DataMatrix**
- O conteúdo pode ser posteriormente verificado quanto à **autenticidade e integridade**

---

# Objetivos de Segurança

Esta PoC demonstra como:

- Proteger chaves de assinatura dentro de um **HSM**
- Garantir **integridade dos dados**
- Autenticar a **origem do fabricante**
- Detectar **adulterações**
- Simular **detecção básica de clonagem**

---

# Tecnologias Utilizadas

| Componente | Função |
|-----------|--------|
| SoftHSM2 | Simulação de HSM |
| PKCS#11 | Interface de segurança de hardware |
| OpenSSL | Operações de PKI |
| Python | Scripts de automação |
| cryptography | Assinaturas digitais |
| pylibdmtx | Geração de DataMatrix |
| Pillow | Manipulação de imagens |

---

# Estrutura do Projeto

```
poc-pharma-gs1-hsm
│
├── config/        # Arquivos de configuração
├── data/          # Dados gerados
├── dm/            # Imagens de DataMatrix
├── docs/          # Documentação técnica
│
├── hsm/
│   ├── softhsm2.conf
│   └── tokens/
│
├── pki/
│   ├── ca.ext
│   └── mfg.ext
│
├── registry/      # Registro simulado
├── scripts/       # Scripts do projeto
│
├── env.sh
├── .gitignore
└── README.md
```

---

# Configuração do Ambiente

## Instalar dependências

```bash
sudo apt update

sudo apt install -y \
softhsm2 \
opensc \
openssl \
libengine-pkcs11-openssl \
libdmtx0t64 \
libdmtx-dev \
python3 \
python3-venv \
python3-pip
```

---

## Criar ambiente Python

```bash
python3 -m venv .venv
source .venv/bin/activate

pip install -U pip setuptools wheel

pip install \
python-pkcs11 \
cryptography \
pillow \
pylibdmtx
```

---

# Configuração do SoftHSM

Arquivo:

```
hsm/softhsm2.conf
```

Conteúdo:

```
directories.tokendir = ./hsm/tokens
objectstore.backend = file
log.level = INFO
```

Definir variável de ambiente:

```bash
export SOFTHSM2_CONF=$(pwd)/hsm/softhsm2.conf
```

---

# Inicialização dos Tokens do HSM

Criar token da **CA**:

```bash
softhsm2-util --init-token --free \
--label "CA-TOKEN" \
--so-pin 5678 \
--pin 1234
```

Criar token do **fabricante**:

```bash
softhsm2-util --init-token --free \
--label "MFG-TOKEN" \
--so-pin 5678 \
--pin 1234
```

Verificar tokens:

```bash
softhsm2-util --show-slots
```

---

# Status Atual do Projeto

✔ Ambiente preparado  
✔ SoftHSM configurado  
✔ Tokens inicializados  
✔ Módulo PKCS#11 validado  
✔ Ambiente Python validado  

Próximos passos:

- Gerar chaves dentro do HSM
- Construir a PKI local
- Assinar dados serializados de medicamentos
- Gerar DataMatrix
- Implementar fluxo de verificação

---

# Considerações de Segurança

Materiais sensíveis são intencionalmente excluídos do controle de versão:

- armazenamento de tokens do HSM
- chaves privadas
- certificados gerados
- dados serializados gerados

---

# Finalidade Educacional

Este projeto foi criado como uma **prova de conceito educacional e de pesquisa**, demonstrando:

- integração de PKI com HSM
- gerenciamento seguro de chaves
- mecanismos de autenticação de dados
- conceitos de combate à falsificação na cadeia farmacêutica
