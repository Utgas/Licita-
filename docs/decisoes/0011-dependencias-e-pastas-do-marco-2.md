# 0011. Dependências e pastas do Marco 2

- Data: 24/10/2026
- Situação: aceita.

## Contexto

O Marco 2 precisa ler o checklist em Word, guardar o desenho das telas e rodar uma tarefa diária de expurgo. Nada disso estava na stack nem na árvore.

## Decisão

- **Leitura do Word:** `jszip`, para abrir o `.docx`, e `fast-xml-parser`, para ler o XML. Escolhidas porque leem o documento como ele é (parágrafos, tabelas e caracteres de marcação ☐ e ☒), sem converter para HTML nem perder a estrutura. Versões fixadas, sem `^` nem `~`.
- **Pastas novas:**
  - `src/dados/leitura-checklist/`: a leitura do Word. Fica em `dados` porque transforma arquivo em dado, e não em `motor`, que não lê arquivo;
  - `docs/design/`: o desenho das telas usado como referência (imagens e guia de estilo). Só material sem dado real nem símbolo oficial.
- **Expurgo:** `pg_cron` no próprio banco do Supabase. Fica fora de `src/motor`, como manda a regra 10.

## Consequências

- Outras bibliotecas de Word (por exemplo, as que convertem para HTML) não entram sem nova decisão.
- Se um dia o banco sair do Supabase, o expurgo vira tarefa agendada da própria aplicação; a regra (30 dias após "concluído") não muda.
