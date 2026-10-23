# Licita+

Gera minutas de Termo de Referência (e, depois, de ETP) no modelo AGU, para compras de saúde. A entrada é o checklist técnico da área requisitante e as decisões da equipe administrativa no wizard. A minuta é revisada por pessoas e colada no Compras.gov.br.

**Estado:** Marco 0 (esqueleto). Ainda não há código do sistema. As matrizes jurídicas estão prontas para revisão.

## Como começar

1. Clone o repositório (https://github.com/Utgas/licita-). Ele está público por enquanto; ver `docs/decisoes/0005-dados-reais-fora-do-repositorio.md`.
2. Abra o Claude Code nesta pasta e peça: "Leia o CLAUDE.md e execute a tarefa docs/tarefas/marco-0.md."
3. No fim do Marco 0, confira o critério de saída da tarefa e o relatório do compilador.

Vercel e Supabase só entram de verdade no Marco 2 (telas e banco). Até lá basta o GitHub.

## Estrutura

| Pasta | O que tem |
| --- | --- |
| `docs/` | escopo, arquitetura, decisões e tarefas por marco |
| `matrizes/v1/` | as matrizes M00 a M11 (CSV), a planilha de revisão e os registros do agente das matrizes |
| `referencias/` | modelo AGU de TR (DEZ/2025) e checklists técnicos em branco |
| `regras/` | pacote compilado (gerado no Marco 0) |
| `scripts/` | compilador e simulador |
| `src/` | motor, telas, banco, login, auditoria, exportação e IA |
| `supabase/` | configuração e migrações do banco |
| `testes/` | testes do motor, cenários de ouro e testes de tela |

## Plano

| Marco | Entrega | Depende de |
| --- | --- | --- |
| 0. Esqueleto | Repositório, testes e compilador lendo as matrizes | nada |
| 1. Motor do TR | Wizard, regras por item, montagem e validação, sem telas | regras CONDICAO validadas e checklist congelado |
| 2. Telas e banco | Login, checklist, wizard, itens, revisão, PDF, copiar por campo, auditoria | prazo de expurgo |
| 3. ETP | ETP montado a partir do checklist e derivação para o TR | Fases 4 a 9 das matrizes (feitas) |
| 4. Piloto | 3 processos reais em paralelo com o método atual | aprovação da hospedagem, conta e patrocinador |
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

## O que não entra aqui

ETPs, TRs e DFDs reais ficam fora do repositório: alguns têm nomes, assinaturas e CPFs. O `.gitignore` bloqueia PDFs e a pasta `Documentos/`. Antes do primeiro commit, confira que nenhum arquivo real entrou.
