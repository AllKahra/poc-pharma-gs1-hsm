# Formato oficial da base GS1 do projeto

Formato GS1 base oficial:
(01)GTIN(17)EXP(10)LOT<GS>(21)SERIAL

Onde:
- GTIN = 14 dígitos
- EXP = YYMMDD
- LOT = variável
- SERIAL = variável
- <GS> = ASCII 29

Regras congeladas do projeto:
- Ordem fixa dos AIs: 01, 17, 10, GS, 21
- O arquivo data/gs1_base.txt contém o caractere GS real (ASCII 29)
- O conteúdo assinado será o conteúdo de data/gs1_base.txt sem o newline final
- O caractere GS deve ser preservado
- O conteúdo será tratado em UTF-8
- Não alterar essa convenção nas próximas etapas
