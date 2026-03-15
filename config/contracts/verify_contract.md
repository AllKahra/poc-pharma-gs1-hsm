# Contrato do verificador da PoC

Formato do payload final:
(01)GTIN(17)EXP(10)LOT<GS>(21)SERIAL<GS>(92)KID<GS>(91)SIGNATURE

Regras de parsing:
- AI 01 = fixo, 14 dígitos
- AI 17 = fixo, 6 dígitos
- AI 10 = variável até GS
- AI 21 = variável até GS
- AI 92 = variável até GS
- AI 91 = variável até o fim

Conteúdo assinado:
(01)GTIN(17)EXP(10)LOT<GS>(21)SERIAL

Observações:
- O verificador não deve usar strip() no payload inteiro
- Remover no máximo o newline final do arquivo
- O caractere GS (ASCII 29 / \x1d) deve ser preservado
