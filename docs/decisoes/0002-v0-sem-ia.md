# 0002. A primeira versão não usa IA

- Data: 21/10/2026
- Situação: aceita

## Contexto

Mandar dados de processo para um provedor de IA depende de autorização da chefia e da TI, que ainda não existe. A maior parte do TR é texto fixo da AGU mais escolhas do wizard.

## Decisão

A v0 monta o TR só por regras. A v1 monta o ETP a partir das respostas do checklist, também sem IA. A IA entra só na v2, para melhorar a redação do ETP, sempre citando a pergunta de origem, e depois que um provedor for aprovado.

## Consequências

- Até a v2, nenhum dado do processo sai do sistema.
- `src/ia/` fica vazio até lá.
