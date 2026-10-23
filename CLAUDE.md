# CLAUDE.md

Instruções para qualquer agente de código que trabalhe neste repositório.

## O projeto

O Licita+ gera minutas de Termo de Referência (e, depois, de ETP) no modelo AGU, para compras de saúde de organizações militares. A área requisitante responde ao checklist técnico, a equipe administrativa responde ao wizard jurídico, e o sistema monta a minuta. A minuta é revisada por pessoas e colada no Compras.gov.br.

O dono do projeto, Gabriel, é pregoeiro e não escreve código. Explique cada decisão técnica em português simples, em poucas linhas, e diga sempre como ele pode testar o que você fez.

## Leia antes de qualquer tarefa

1. `docs/arquitetura.md`: como o sistema é montado e por quê.
2. A tarefa do marco atual, em `docs/tarefas/`.
3. `matrizes/v1/README.md`: o que cada matriz contém e as convenções de IDs e de JSON Logic.

## Estado atual

**Marco 0 (esqueleto).** Tarefa: `docs/tarefas/marco-0.md`. Trabalhe só no marco atual. Não adiante telas, banco, login, motor ou IA.

## Onde está cada coisa

| Caminho | Conteúdo |
| --- | --- |
| `docs/` | escopo, arquitetura, decisões (`decisoes/`) e tarefas por marco (`tarefas/`) |
| `matrizes/v1/` | as matrizes em CSV: fonte da verdade jurídica |
| `referencias/` | modelo AGU de TR (DEZ/2025) e os dois checklists técnicos em branco |
| `regras/` | pacote compilado das matrizes; gerado pelo compilador, nunca editado à mão |
| `scripts/` | compilador e simulador (TypeScript) |
| `supabase/` | configuração e migrações do banco |
| `src/motor/` | núcleo puro: wizard, itens, montagem, validação, derivação |
| `src/app/` | telas e rotas (Next.js) |
| `src/dados/`, `src/auth/`, `src/auditoria/`, `src/exportacao/`, `src/ia/` | banco, login, auditoria, PDF e IA (v2) |
| `testes/` | testes do motor, cenários de ouro e testes de tela |

## Regras invioláveis

1. Nunca escreva texto jurídico no código. Cláusula, pergunta e condição vêm do pacote de regras.
2. Para mudar uma regra, altere o CSV em `matrizes/`, rode o compilador e rode os cenários. Nunca edite `regras/` à mão.
3. `src/motor` é puro: sem banco, sem rede, sem data atual e sem aleatoriedade. A mesma entrada sempre gera a mesma saída.
4. Todo trecho da minuta precisa ser rastreável até o ID do bloco e o pacote de onde veio.
5. Valor, quantidade, prazo e percentual nunca são inventados pelo código. Se faltar um dado, a minuta mostra a lacuna marcada.
6. Nada de chamada a serviço externo, nem fonte ou script de terceiros, sem uma decisão registrada em `docs/decisoes/`.
7. Nenhum dado real de processo em teste, exemplo, commit ou log. Use dados fictícios.
8. Toda mudança roda lint, os testes do motor, os cenários de ouro e a reprodução dos TRs reais (a partir do Marco 1). Se algum cenário mudar, a mudança explica por quê.
9. Siga a árvore de `docs/arquitetura.md`. Pasta nova ou mudança de estrutura vira decisão em `docs/decisoes/`.
10. Toda tabela nova nasce com RLS ligado no Supabase, e nenhuma consulta ao banco sai do navegador. Nada de recurso exclusivo da Vercel ou do Supabase dentro de `src/motor`.

## Matrizes

- São a fonte da verdade jurídica. As colunas atuais são o padrão: não renomeie colunas nem arquivos.
- Não corrija regra jurídica por conta própria. Se uma matriz parecer errada, descreva o problema e espere a decisão do Gabriel.
- Status: `EXTRAIDO` (copiado da fonte), `INFERIDO` (leitura do agente das matrizes) ou `A_VERIFICAR` (depende de conferência). `INFERIDO` e `A_VERIFICAR` geram aviso, não erro, em desenvolvimento.
- No M03 e no M04, a coluna `validacao` (OK, CORRIGIR ou DUVIDA) é preenchida pelo Gabriel. No modo piloto, o compilador exige `OK` em todas as regras CONDICAO do M03 e em todas as perguntas do M04.
- Variáveis em JSON Logic: `WZ_23` é a resposta da `WZ-23`; `CK_C_14_2` é a resposta da `CK-C-14.2`; `VAR_001` é a variável `VAR-001`; `itens` é a lista de itens com os atributos do M05. A lista completa está em `matrizes/v1/README.md`.
- Os scripts Python em `matrizes/v1/scripts/` geraram as matrizes a partir dos documentos reais, que ficam fora deste repositório. São registro de origem: não rode nem altere.

## Dados pessoais

- ETPs, TRs e DFDs reais não entram no repositório. O `.gitignore` bloqueia PDFs e a pasta `Documentos/`.
- Nenhum nome, CPF, telefone, e-mail ou número de processo real em código, teste, exemplo, commit ou log.

## Como trabalhar

- Passos pequenos, um commit por passo, mensagem em português.
- Fixe as versões das dependências (sem `^` nem `~`).
- Ao terminar uma tarefa, diga: o que mudou, o comando para testar e o que ficou pendente.
- Pare e pergunte antes de seguir quando:
  - uma regra jurídica estiver ambígua;
  - uma matriz conflitar com o modelo AGU;
  - for preciso dependência nova fora da stack de `docs/arquitetura.md`, serviço externo ou mudança na árvore;
  - aparecer qualquer dado que pareça real.

## Comandos

Definidos no Marco 0. Atualize esta seção quando eles existirem.

- `npm run compilar`: gera `regras/agu-tr-compras-2025-12/` a partir das matrizes
- `npm run compilar:piloto`: igual, mas falha se houver regra sem validação
- `npm test`, `npm run lint`, `npm run typecheck`
