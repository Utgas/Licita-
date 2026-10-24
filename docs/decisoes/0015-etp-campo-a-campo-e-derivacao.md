# 0015. ETP montado campo a campo, derivação pelo M06 e nenhuma migração

- Data: 24/10/2026
- Situação: aceita. O dono do projeto autorizou o Marco 3 e pediu que nada fosse aplicado direto no banco.

## Contexto

O TR tem um modelo de texto (M02), e o motor preenche as lacunas dele. Já o ETP Digital é um formulário: cada campo (M01) recebe o conteúdo que a equipe escreve. As matrizes não trazem texto de modelo para o ETP. Elas trazem as ligações:

- `M05.usada_em`: qual variável alimenta cada campo;
- `M11.destinos`: qual pergunta do checklist justifica o campo;
- `M04.exige_justificativa`: qual justificativa do wizard vai para ele;
- `M06`: quais blocos do TR repetem o campo.

O M01 marca vários campos como "IA". A IA só entra no Marco 5 (decisão 0002).

## Decisão

1. **O ETP é montado das respostas, campo a campo, na ordem do M01.** Cada campo recebe:
   - o valor das variáveis ligadas a ele;
   - as respostas do checklist que o justificam;
   - as justificativas do wizard que o citam.

   Cada parte mostra de onde veio, e o rótulo vem do pacote (descrição do M05, pergunta do M11 ou do M04). O código não escreve frase nenhuma: o que não tem resposta vira lacuna marcada, e o campo "IA" fica para a equipe escrever.
2. **Texto padrão do ETP não é automático por enquanto.** Nos campos ETP-05.01, 10.01, 13.01 e 14.01, o texto padrão e a condição dele estão só em texto livre (`M01.quando_nao_se_aplica` e `M04.liga_blocos`). A tela mostra a orientação e a equipe escreve o texto. A coluna de máquina (`texto_padrao` e `texto_padrao_expr`) foi pedida ao agente das matrizes (tarefa do Marco 3, Fase 16).
3. **Derivação é rastreabilidade, não cópia.** O ETP e o TR saem das mesmas respostas, então o TR não tem como contradizer o ETP. O M06 serve para mostrar, em cada bloco do TR, o campo do ETP de origem e para avisar quando o TR repete um campo que está vazio no ETP. Nesse caso, o ETP é completado antes.
4. **Campos de texto do ETP Digital** (tipo TF sem dado ligado, como a declaração de viabilidade) não são copiados: o próprio ETP Digital os imprime.
5. **Pastas:**
   - o ETP fica em `src/motor/montagem/etp.ts` e a derivação em `src/motor/derivacao/`, ambas já na árvore;
   - a exportação fica em `src/exportacao/etp.ts`;
   - a tela é a única pasta nova: `src/app/processos/[id]/etp/`.
6. **Nenhuma migração.**
   - Os dados do ETP são variáveis e já vão para `resposta_wizard` (`VAR-xxx`).
   - A marca de copiado usa `exportacao` com `secao = ETP-xx.yy`. O ID do campo não colide com as seções do TR, que usam o título do modelo.
   - O PDF do ETP é registrado só na auditoria, com o hash, para não ser contado como PDF do TR.

   Se um dia for preciso separar TR e ETP na tabela `exportacao`, entra uma coluna `documento` com nova migração e nova decisão.

## Consequências

- O ETP sai como rascunho estruturado (rótulo e resposta). Ele melhora sem mudar o código quando as matrizes ganharem texto padrão e, no Marco 5, com a IA.
- A reprodução completa do par 117/2025 depende do caso R3, a ser feito pelo agente das matrizes. Até ele chegar, a derivação é testada pelas evidências do M06.
- Nada muda no banco publicado: o Marco 3 sobe para produção sem migração.
