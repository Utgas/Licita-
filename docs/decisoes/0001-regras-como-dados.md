# 0001. Regras jurídicas são dados, não código

- Data: 21/10/2026
- Situação: aceita

## Contexto

O TR segue o modelo AGU, que tem 556 parágrafos, 102 notas explicativas e muda de versão algumas vezes por ano. Se as cláusulas e condições ficarem escritas no código, cada versão nova do modelo vira uma reescrita, e o pregoeiro não consegue conferir as regras.

## Decisão

Texto do modelo, condições e perguntas do wizard ficam nas matrizes (`matrizes/`). Um compilador transforma as matrizes num pacote versionado (`regras/`), e o motor só executa esse pacote. Cada processo grava o pacote com que foi criado.

## Consequências

- Mudar uma regra é mudar uma linha de CSV e compilar, sem tocar no motor.
- Modelo novo da AGU vira pacote novo; processos antigos continuam reproduzíveis.
- O compilador precisa conferir tudo (IDs, referências, condições), porque erro na matriz vira erro na minuta.
