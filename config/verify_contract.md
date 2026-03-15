# Contrato do verificador da PoC

## Formato do payload final

(01)GTIN(17)EXP(10)LOT<GS>(21)SERIAL<GS>(92)KID<GS>(91)SIGNATURE

## Regras de parsing

- AI 01 = fixo, 14 dígitos
- AI 17 = fixo, 6 dígitos
- AI 10 = variável até GS
- AI 21 = variável até GS
- AI 92 = variável até GS
- AI 91 = variável até o fim

## Regras de verificação

- O conteúdo assinado NÃO é o payload inteiro
- O conteúdo assinado é apenas a base GS1:

  (01)GTIN(17)EXP(10)LOT<GS>(21)SERIAL

- O KID (AI 92) é obrigatório
- O certificado deve ser localizado via config/cert_map.json
- A assinatura (AI 91) deve ser validada com a chave pública do certificado mapeado pelo KID

## Regras de clonagem

- A chave de detecção de clonagem será:
  GTIN|SERIAL

- O registro deve armazenar pelo menos:
  - gtin
  - serial
  - lot
  - first_seen
  - last_seen
  - seen_count
