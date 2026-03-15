# Parte 7 - decisões da PoC

## Conteúdo assinado
(01)GTIN(17)EXP(10)LOT<GS>(21)SERIAL

## Conteúdo total do payload
(01)GTIN(17)EXP(10)LOT<GS>(21)SERIAL<GS>(92)KID<GS>(91)SIGNATURE

## Regras de resultado
- assinatura inválida => adulteração / payload inconsistente
- assinatura válida + repetição de GTIN|SERIAL => suspeita de clonagem
- assinatura válida + primeira ocorrência => válido
