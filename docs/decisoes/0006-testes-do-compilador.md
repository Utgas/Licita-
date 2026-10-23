# 0006. Testes do compilador em `testes/compilador/`

- Data: 23/10/2026
- Situação: aceita no Marco 0, pendente de confirmação do Gabriel

## Contexto

A árvore de `docs/arquitetura.md` tem `testes/motor/`, `testes/cenarios/` e `testes/telas/`. O compilador (`scripts/compilar-regras.ts`) não é parte do motor, mas o Marco 0 pede testes para ele, com matrizes pequenas de exemplo (fixtures).

## Decisão

- Os testes do compilador ficam em `testes/compilador/`, e as fixtures em `testes/compilador/fixtures/`:
  - `validas/`: as 12 matrizes com uma ou duas linhas fictícias cada, coerentes entre si;
  - `quebradas/<caso>/`: só o arquivo que muda em cada caso de falha (ID duplicado, referência quebrada, JSON inválido, operador fora da lista, variável desconhecida).
- O teste da regra de lint que isola o motor fica em `testes/motor/`, porque protege o motor.

## Consequências

- A árvore ganha uma pasta em `testes/`. Nenhuma outra pasta muda.
- Toda fixture usa dados fictícios (regra 7 do `CLAUDE.md`).
