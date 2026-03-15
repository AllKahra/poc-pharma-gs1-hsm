# Contrato do payload final da PoC

Formato final:
(01)GTIN(17)EXP(10)LOT<GS>(21)SERIAL<GS>(92)KID<GS>(91)SIGNATURE

Regras:
- O conteúdo assinado é somente o conteúdo lógico de data/gs1_base.txt
- O newline final do arquivo não entra na assinatura
- O caractere GS (ASCII 29 / \x1d) deve ser preservado
- O payload final adiciona:
  - AI 92 = KID
  - AI 91 = assinatura base64url
- O AI 91 fica no final
