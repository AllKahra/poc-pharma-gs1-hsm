# Contrato de assinatura da PoC

O conteúdo assinado na Parte 6 será exatamente:

- o conteúdo lógico de data/gs1_base.txt
- removendo apenas o newline final do arquivo
- preservando o caractere GS (ASCII 29 / \x1d)
- codificado em UTF-8

Exemplo lógico:
01054123450000131727053110L202401<GS>21ABC123456789

Exemplo em bytes:
b"01054123450000131727053110L202401\x1d21ABC123456789"
