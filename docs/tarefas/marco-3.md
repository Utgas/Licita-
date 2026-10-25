# Marco 3: ETP e derivação

**Objetivo:** o operador vê o ETP do processo montado campo a campo, na ordem das telas do ETP Digital, a partir das mesmas respostas que montam o TR. Ele completa o que falta, copia cada campo para o ETP Digital e baixa o PDF. Cada bloco do TR que repete uma decisão do ETP mostra de qual campo ela veio (M06). Sem IA (decisão 0002): o que o M01 marca como "IA" fica como lacuna para a equipe escrever.

**Critério de saída (arquitetura, com a decisão 0008):**

- A derivação ETP para TR é testada no par 117/2025.
- Os blocos que o M06 marca como consistentes saem iguais no ETP e no TR a partir das mesmas respostas.
- As divergências do par ficam classificadas, como foi feito no R1 e no R2.

O DFD do processo não está na base (P10), por isso o teste é só da derivação.

**Antes de começar:** leia `CLAUDE.md`, `docs/arquitetura.md`, as decisões 0002, 0008, 0010 e 0015, e o `matrizes/v1/README.md` (M01, M05, M06 e M11).

## Análise de prontidão (24/10/2026)

O Marco 2 está no `main` e no ar. Falta só o teste com alguém de fora do desenvolvimento, que não depende de código. As matrizes de que o ETP precisa já estão no pacote:

| O que o ETP precisa | Onde já está | Lido por máquina? |
| --- | --- | --- |
| Campos, ordem, seção, obrigatoriedade e inciso | M01 (24 campos) | sim |
| Dado de cada campo | `M05.usada_em` (VAR para campo do ETP) | sim, lista de IDs |
| Pergunta do checklist que justifica o campo | `M11.destinos` (CK para campo do ETP) | sim, lista de IDs |
| Justificativa do wizard que vai para o ETP | `M04.exige_justificativa` (cita o campo) | sim, ID no texto |
| Bloco do TR que repete o campo | `M06.campos_etp`, `variaveis` e `perguntas_wz`; `M01.destino_tr` | sim, listas de IDs |
| Teste do par 117/2025 | `M06.teste_par_117` e `evidencia_par_117` (14 blocos testados) | sim, domínio fechado |
| Texto padrão quando não se aplica (ETP-05.01, 10.01, 13.01, 14.01) | `M01.quando_nao_se_aplica` e `M04.liga_blocos` (WZ-46 a WZ-48) | **não**: só em texto livre |
| Caso de reprodução com as respostas do par 117/2025 | não existe (`cenarios/` só tem R1 e R2) | **não** |

**Conclusão:** dá para fazer o Marco 3. Duas coisas ficam fora do alcance do código, porque dependem das matrizes:

- **Texto padrão.** O texto padrão do ETP só existe como frase dentro de texto livre. Transformar isso em regra seria escrever regra jurídica no código (regra 1). Nesses campos, a tela mostra a orientação do M01 com o texto proposto, e a equipe escreve ou cola o texto. O pedido da coluna de máquina está no fim desta tarefa.
- **Reprodução completa do par 117/2025.** As respostas do processo real ficam fora do repositório e só o agente das matrizes chega a elas. O código testa a derivação pelas evidências do M06 e deixa pronto o teste do caso R3 para quando ele chegar.

**Banco:** o ETP não precisa de tabela nem de coluna nova:

- os dados do ETP são variáveis (VAR), que já são gravadas em `resposta_wizard` (`pergunta = VAR-xxx`);
- a marca de "copiado" usa `exportacao` com `secao = ETP-xx.yy`;
- o PDF do ETP fica só na auditoria, com o hash.

Nenhuma migração neste marco (detalhes na decisão 0015).

## Regras deste marco

- Nenhum texto jurídico no código. O conteúdo de cada campo vem só das respostas (VAR, checklist e justificativas); rótulos e orientações vêm do pacote.
- O motor continua puro. O ETP e a derivação entram em `src/motor/montagem/etp.ts` e `src/motor/derivacao/`, pastas que já estão na árvore.
- A minuta do TR não muda: os cenários de ouro e a reprodução R1 e R2 continuam passando sem alteração do esperado.
- Valor que falta vira lacuna marcada (`[[LACUNA VAR-xxx]]`). O ETP nunca recebe "Sim" ou "Não" solto de resposta do checklist: resposta de opção entra com a pergunta ao lado.

## Passos

1. **Compilador: referências do ETP.** Conferir que todo ID de campo do ETP citado no M04 (`exige_justificativa`), no M05 (`usada_em`), no M06 (`campos_etp`) e no M11 (`destinos`) existe no M01. Conferir também que todo bloco do `M01.destino_tr` e do `M06.bloco_tr` existe no M02. Referência quebrada é erro. Um teste de erro para cada coluna.

2. **Entrada do motor.** `EntradaProcesso` ganha `justificativas` (WZ para o texto escrito pela equipe), opcional. A aplicação já grava esse texto em `resposta_wizard.justificativa`.

3. **ETP montado** (`src/motor/montagem/etp.ts`, `gerarEtp`). Para cada campo do M01, na ordem:
   - **partes de dado:** as VAR cujo `usada_em` cita o campo, com o valor formatado pelo `tipo_dado`, a descrição do M05 como rótulo e a origem (pergunta do checklist que preencheu, equipe ou cálculo). Atributo de item sai por item ("item 1: …; item 3: …"), com o código traduzido pelo `textos` da tabela do M02 quando houver;
   - **partes do checklist:** as perguntas do M11 que citam o campo em `destinos` e não preenchem nenhuma das VAR do campo (JUSTIFICA, SUGERE, ALERTA), respondidas e com a condicional verdadeira. Entra o texto da caixa de resposta; resposta de opção entra com a pergunta;
   - **justificativas do wizard:** as WZ cujo `exige_justificativa` cita o campo, quando a equipe escreveu a justificativa;
   - **tabela:** campo do tipo TB monta a tabela do bloco do `destino_tr` que tem `tabela_colunas` (a mesma tabela de itens do TR);
   - **texto do ETP Digital:** campo do tipo TF, sem dado ligado, é texto que o próprio ETP Digital imprime; não é copiado;
   - **lacunas:** VAR obrigatória (S) sem valor vira lacuna marcada. VAR CONDICIONAL sem valor só aparece como "não informado". Campo obrigatório (art. 18, § 2º) sem nenhuma parte fica pendente;
   - **orientação:** `regra_preenchimento`, `regra_anti_alucinacao` e `quando_nao_se_aplica` do M01;
   - **validações:** as do M10 que citam o campo ou uma VAR dele em `afeta`, já avaliadas pela minuta do TR.

4. **Derivação** (`src/motor/derivacao/derivacao.ts`, `derivarEtpParaTr`). Para cada bloco do TR na minuta que o M06 liga a campos do ETP:
   - quais campos, VAR e WZ ele repete e a `regra_derivacao`;
   - **situação:** "derivado" (o campo do ETP tem conteúdo) ou "campo vazio" (o TR repete um campo que está vazio no ETP: o ETP precisa ser revisto antes, como diz o M06).

   Para cada campo do ETP, os blocos do TR que o repetem, com o número na minuta.

5. **Testes do motor e cenários.**
   - ETP de C1 a C8, R1 e R2:
     - os 24 campos na ordem do M01;
     - todo valor do ETP igual ao dado do processo (nada inventado);
     - toda lacuna com o ID da regra;
     - nenhum "Sim" ou "Não" solto;
     - a minuta do TR igual à de antes.
   - **Derivação do par 117/2025** pelas evidências do M06 (`testes/cenarios/derivacao-117.test.ts`), com a classificação em `derivacao-117-classificacao.ts`:
     - bloco CONSISTENTE: tem de sair derivado do mesmo campo, com as mesmas VAR;
     - bloco DIVERGENTE ou PARCIAL: classificado como diferença do documento real (o sistema monta os dois do mesmo dado e não reproduz a divergência), com a remissão ao M09 ou à nota do M03 quando houver.
   - **Teste do R3** (`testes/cenarios/reproducao-etp.test.ts`): roda quando `matrizes/v1/cenarios/R3.json` existir e confere os campos e os blocos esperados; até lá, diz que o caso ainda não chegou.

6. **Simulação legível.** `npm run simular -- C1 --etp` imprime o ETP em texto corrido, campo a campo, com as lacunas e a derivação.

7. **Exportação** (`src/exportacao/etp.ts` e `pdf.tsx`):
   - texto de cada campo para colar no ETP Digital, na ordem do M01;
   - hash do ETP;
   - PDF do ETP gerado no servidor, nunca gravado; o hash vai para a auditoria.

8. **Tela do ETP** (`src/app/processos/[id]/etp/`):
   - o ETP como folha de documento, com a seção, o campo, as partes e a origem de cada uma;
   - lacunas em amarelo e o selo de obrigatório;
   - a orientação do M01 e os blocos do TR que repetem o campo;
   - formulário das VAR do ETP que a equipe informa (mesma forma de entrada do wizard) e remissão ao checklist para as de origem CHECKLIST;
   - botão "Copiar" por campo, com a marca de copiado, e o PDF do ETP;
   - na tela da minuta do TR, cada trecho derivado mostra o campo do ETP de origem.

9. **Testes de tela** (Playwright). O fluxo do Marco 2 passa a abrir o ETP, informar um campo, copiar um campo e baixar o PDF do ETP.

10. **Documentos.** Decisão 0015, arquitetura (árvore e estado), `CLAUDE.md` (estado atual) e o relatório final ao Gabriel.

## Critério de saída

- `npm test`, `npm run lint`, `npm run typecheck`, `npm run test:banco`, `npm run test:telas` e o GitHub Actions passam.
- Cenários de ouro e R1 e R2 sem mudança no TR.
- Derivação do par 117/2025: nenhum bloco CONSISTENTE fora do derivado e todas as divergências classificadas.
- O teste do R3 roda sozinho quando o caso chegar.

## Não faça

- IA, DFD, texto jurídico no código, mudança nas matrizes ou nos scripts das matrizes.
- Migração ou mudança direta no banco publicado sem autorização.

## Pedido ao agente das matrizes (Fase 16)

Para o ETP sair completo sem a equipe colar texto padrão, e para a reprodução do par 117/2025 rodar com as respostas do processo:

1. **M01:** duas colunas novas.
   - `texto_padrao`: o texto padrão proposto, literal. Hoje ele está dentro de `quando_nao_se_aplica` nos campos ETP-05.01, 10.01, 13.01 e 14.01.
   - `texto_padrao_expr`: JSON Logic, só com os operadores gerais. Verdadeira quando o texto padrão entra; por exemplo, `{"==": [{"var": "WZ_46"}, "NAO"]}` no ETP-10.01, como diz o `liga_blocos` da WZ-46.

   O texto padrão entra marcado como valor padrão (P37).
2. **M01, WZ-11 participante:** coluna `participante` (S ou N) com os campos que o ETP do participante traz. Hoje isso está só no texto do `liga_blocos` da WZ-11.
3. **Cenário R3** (par 117/2025):
   - formato: o mesmo do R1 e do R2;
   - `entrada`: anonimizada, com as respostas tiradas do ETP e do TR reais;
   - `esperado.campos_etp`: os campos com conteúdo no ETP real;
   - `esperado.blocos`: os blocos do TR real;
   - `divergencias_conhecidas`: ligadas ao M09.

   O teste `testes/cenarios/reproducao-etp.test.ts` já espera esse formato.
4. **Feito em 25/10/2026, a pedido do dono do projeto.** **M06:** o `campos_etp` estava vazio no TR-4.H04, no TR-5.4 e no TR-5.5. A evidência do par 117/2025 desses blocos compara com o ETP: amostra no ETP-04.01, endereços (VAR-064) no ETP-04.01 e garantia do bem no ETP-06.01. O teste da derivação lista os três em `derivacao-117-classificacao.ts` (campo `matriz`).
5. **Feito em 25/10/2026** (formato `ANO` no mapa; o motor aceita o próprio ano). **M02, TR-2.2 e TR-2.3:** o marcador `[ANO]` lê a VAR-038, que é NUMERO, sem formato, e sai "2.026" na minuta. O simulador das matrizes faz o mesmo, então o motor está certo e a correção é na matriz. Duas saídas possíveis: um formato próprio para ano (por exemplo `ANO_NUMERO`) ou a VAR-038 como TEXTO. O ETP já mostra "2026", porque lê o "AAAA" da validação do M05.

## Estado (24/10/2026)

Passos 1 a 10 feitos, no ramo `claude/quirky-bohr-ez4er7`. O que ficou com o critério de saída:

- **Feito:** derivação do par 117/2025 testada pelas evidências do M06.
  - Os 5 blocos consistentes saem derivados do mesmo campo e das mesmas respostas.
  - Os 9 divergentes estão classificados, com a fonte comum conferida nos dois lados.
  - O TR dos cenários de ouro e da reprodução R1 e R2 não mudou.
- **Pendente, fora do código:**
  - o caso R3 e as colunas da Fase 16, com o agente das matrizes;
  - a revisão do Gabriel na tela do ETP publicada.

  O teste do R3 já roda sozinho quando o arquivo chegar.

As correções 4 e 5 foram feitas direto nos CSV, a pedido do dono do projeto. A coluna `fonte` de cada linha registra a mudança. O agente das matrizes precisa levar as duas para os geradores, senão a próxima regeneração as desfaz.
