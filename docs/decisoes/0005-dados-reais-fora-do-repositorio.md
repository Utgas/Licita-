# 0005. Documentos reais ficam fora do repositório

- Data: 22/10/2026
- Situação: aceita

## Contexto

As matrizes foram feitas a partir de ETPs, TRs e DFDs reais. Alguns têm nomes, assinaturas e, em pelo menos um DFD, CPFs.

## Decisão

- O repositório guarda só as matrizes, que foram conferidas sem nomes de pessoas, e os modelos em branco (modelo AGU e checklists).
- Os documentos reais ficam numa pasta local fora do Git. O `.gitignore` bloqueia PDFs e a pasta `Documentos/`.
- O repositório no GitHub deve ser privado. Exceção temporária: desde 23/10/2026 ele está público, por decisão do Gabriel. Ele vira privado antes do piloto (Marco 4), ou antes, se entrar no repositório qualquer dado sensível.
- Testes e exemplos usam só dados fictícios.

## Consequências

- Os scripts em `matrizes/v1/scripts/` não rodam a partir do repositório, porque precisam dos documentos reais. Ficam como registro de origem das matrizes.
