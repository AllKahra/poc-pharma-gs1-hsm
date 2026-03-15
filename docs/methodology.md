# Methodology

1. Prepare environment and dependencies
2. Configure SoftHSM
3. Initialize CA and manufacturer tokens
4. Generate key pairs inside HSM
5. Build local PKI
6. Generate serialized medicine data
7. Sign payload using PKCS#11
8. Embed signature into GS1-style DataMatrix
9. Decode and verify payload
10. Test tampering and cloning scenarios
