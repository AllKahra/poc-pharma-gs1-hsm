# Architecture

## Components

- Root CA key stored in HSM token
- Manufacturer key stored in HSM token
- Local PKI for certificate issuance
- Python scripts for signing and verification
- GS1-style DataMatrix payload with signature and key identifier

## Trust Model

The verifier trusts the manufacturer certificate because it is issued by the local root CA.
The manufacturer private key is protected inside the HSM token.

## Security Goals

- authenticate serialized medicine data
- detect field tampering
- demonstrate protected key usage
- simulate clone detection through serial reuse
