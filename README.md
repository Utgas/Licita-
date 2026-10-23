# Licita+

Gera minutas de Termo de Referência (e, depois, de ETP) no modelo AGU, para compras de saúde. A entrada é o checklist técnico da área requisitante e as decisões da equipe administrativa no wizard. A minuta é revisada por pessoas e colada no Compras.gov.br.

**Estado:** Marco 0 concluído; Marco 1 (motor do TR) em andamento no ramo `marco-1`. As matrizes da Fase 10 já estão lá, mas o compilador só as aceita depois do passo 1 do Marco 1. Ainda não há telas, banco, login nem IA.

## Como começar

1. Clone o repositório (https://github.com/Utgas/licita-). Ele está público por enquanto; ver `docs/decisoes/0005-dados-reais-fora-do-repositorio.md`.
2. Abra o Claude Code nesta pasta e peça: "Leia o CLAUDE.md e execute a tarefa docs/tarefas/marco-0.md."
3. No fim do Marco 0, confira o critério de saída da tarefa e o relatório do compilador.

Vercel e Supabase só entram de verdade no Marco 2 (telas e banco). Até lá basta o GitHub.

## Como rodar

Precisa do Node 22.18 ou mais novo.

```
npm ci                    # instala as dependências nas versões fixadas
npm run compilar          # confere as matrizes e gera o pacote de regras
npm test                  # testes automáticos
npm run lint              # padrões de código e isolamento do motor
npm run typecheck         # tipos do TypeScript
npm run dev               # página inicial em http://localhost:3000
```

O `npm run compilar` imprime um relatório: linhas por matriz, contagem de status (EXTRAIDO, INFERIDO, A_VERIFICAR), situação da validação no M03 e no M04 e a lista de erros. Sem erro, ele grava `regras/agu-tr-compras-2025-12/pacote.json` e o hash em `pacote.sha256`; compilar de novo dá o mesmo hash. `npm run compilar:piloto` falha enquanto houver regra CONDICAO do M03 ou pergunta do M04 sem `validacao = OK`.

O GitHub Actions roda lint, typecheck, testes e compilação em todo push e pull request, e falha se o pacote em `regras/` não corresponder às matrizes.

## Estrutura

| Pasta | O que tem |
| --- | --- |
| `docs/` | escopo, arquitetura, decisões e tarefas por marco |
| `matrizes/v1/` | as matrizes M00 a M12 (CSV), os cenários de ouro, a planilha de revisão e os registros do agente das matrizes |
| `referencias/` | modelo AGU de TR (DEZ/2025) e checklists técnicos em branco |
| `regras/` | pacote compilado (`npm run compilar`; nunca editar à mão) |
| `scripts/` | compilador e simulador |
| `src/` | motor, telas, banco, login, auditoria, exportação e IA |
| `supabase/` | configuração e migrações do banco |
| `testes/` | testes do motor, cenários de ouro e testes de tela |

## Plano

| Marco | Entrega | Depende de |
| --- | --- | --- |
| 0. Esqueleto | Repositório, testes e compilador lendo as matrizes | nada |
| 1. Motor do TR | Wizard, regras por item, montagem e validação, sem telas | matrizes da Fase 10 (feitas) |
| 2. Telas e banco | Login, checklist, wizard, itens, revisão, PDF, copiar por campo, auditoria | nada (checklist, formato e expurgo decididos) |
| 3. ETP | ETP montado a partir do checklist e derivação para o TR | Fases 4 a 9 das matrizes (feitas) |
| 4. Piloto | 3 processos reais em paralelo com o método atual | regras do M03 e do M04 validadas, aprovação da hospedagem, conta e patrocinador |
| 5. IA | Melhora a redação do ETP, citando a pergunta de origem | provedor de IA aprovado |

Detalhes em `docs/arquitetura.md`.

## Como validar as matrizes

1. Abra `matrizes/v1/matrizes_v1.xlsx`.
2. Nas abas M03 e M04, preencha as colunas amarelas `validacao` (OK, CORRIGIR ou DUVIDA) e `comentario_validacao`. Comece pelas regras do M03 com natureza CONDICAO: são elas que decidem o que entra no TR.
3. Leve a planilha de volta para os CSV com o comando abaixo (precisa de Python 3 com `openpyxl`; o Claude Code pode rodar para você):

   ```
   python3 -I matrizes/v1/scripts/importar_validacao.py matrizes/v1/matrizes_v1.xlsx matrizes/v1 matrizes/v1/logs/validacao.txt
   ```

   O registro lista as linhas marcadas CORRIGIR e DUVIDA, que voltam para o agente das matrizes.

4. Rode `npm run compilar` e confira, no relatório, a tabela "Validação do Gabriel (M03 e M04)". Quando tudo estiver OK, `npm run compilar:piloto` passa.

## O que não entra aqui

ETPs, TRs e DFDs reais ficam fora do repositório: alguns têm nomes, assinaturas e CPFs. O `.gitignore` bloqueia PDFs e a pasta `Documentos/`. Antes do primeiro commit, confira que nenhum arquivo real entrou.
