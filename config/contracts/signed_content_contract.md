# Conteúdo assinado da PoC

A assinatura digital cobre somente a base:

(01)GTIN(17)EXP(10)LOT<GS>(21)SERIAL

Ou seja, na implementação:
- part1 + GS + part2

Não entram na assinatura:
- AI 92 (KID)
- AI 91 (assinatura)
