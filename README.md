# poc-pharma-gs1-hsm

Proof of concept for pharmaceutical data authentication using PKI, HSM-backed signing and GS1-style DataMatrix.

## Objective

Demonstrate how serialized medicine data can be digitally signed with a private key protected by an HSM and later verified for:

- authenticity
- integrity
- tampering detection
- basic cloning detection

## Technologies

- SoftHSM2
- PKCS#11
- OpenSSL
- Python
- pylibdmtx
- cryptography

## Project Structure

- `hsm/` SoftHSM configuration
- `pki/` certificate templates and PKI-related files
- `scripts/` generation, signing and verification scripts
- `config/` auxiliary mappings and configuration
- `docs/` technical documentation

## Status

Current stage:
- environment prepared
- SoftHSM configured
- tokens initialized
- PKCS#11 module validated
- Python environment validated

## Security Notes

Sensitive material is intentionally excluded from version control:
- HSM token storage
- generated certificates
- private keys
- generated barcode data

