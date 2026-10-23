# Marco 0: esqueleto

**Objetivo:** o repositório roda, tem testes automáticos e o compilador lê as matrizes. Nada de tela, banco, login, motor ou IA.

**Antes de começar:** leia `CLAUDE.md`, `docs/arquitetura.md` e `matrizes/v1/README.md`.

## Passos

1. **Projeto Next.js** com TypeScript, App Router, pasta `src/`, ESLint e Tailwind.
   - Não rode `create-next-app` na raiz: ele recusa pasta que já tem arquivos. Gere numa pasta temporária e traga para a raiz só o que falta, sem apagar nem sobrescrever nada que já existe.
   - Fixe as versões no `package.json`, sem `^` nem `~`.

2. **Isolamento do motor.** Crie uma regra de lint: arquivos em `src/motor/` não podem importar de:
   - `src/app`, `src/dados`, `src/auth`, `src/ia`, `src/auditoria` ou `src/exportacao`;
   - `next`, `react` ou `@supabase/*`;
   - módulos de sistema de arquivos ou rede (`fs`, `net`, `http` e equivalentes com prefixo `node:`).

   Prove com um teste que a regra quebra o lint num arquivo proibido.

3. **Compilador** em `scripts/compilar-regras.ts`.
   - Lê `matrizes/v1/M00` a `M11` (UTF-8 com BOM, vírgula, campos entre aspas), com `csv-parse`.
   - Valida cada matriz com Zod, usando as colunas exatamente como estão hoje no cabeçalho de cada CSV. Não renomeie colunas.
   - Confere IDs únicos em cada matriz.
   - Confere referências: toda coluna que cita IDs (padrões `ETP-`, `TR-`, `NE-`, `WZ-`, `VAR-`, `NRM-`, `SET-`, `DV-`, `VAL-`, `CK-`) só pode citar ID que existe na matriz de origem.
   - Confere o JSON Logic de todas as colunas terminadas em `_expr`:
     - o JSON é válido;
     - só usa os operadores `var`, `==`, `!=`, `!`, `!!`, `and`, `or`, `if`, `in`, `merge`, `some`, `none`, `<=`, `>`;
     - só usa variáveis conhecidas: `WZ_xx` (perguntas do M04), `CK_C_...` e `CK_P_...` (perguntas do M11, inclusive os sufixos `_texto` e o cabeçalho `CAB`), `VAR_xxx` (M05), `itens` e os atributos de item do M05, além de `textos_livres`, `importacao.*`, `checklist.*` e `parametros.*`;
     - `WZ_23` corresponde à `WZ-23`, `CK_C_14_2` à `CK-C-14.2` e `VAR_001` à `VAR-001`.
   - Gera `regras/agu-tr-compras-2025-12/pacote.json` com chaves ordenadas, ordem estável e sem data ou hora dentro, e `pacote.sha256` com o hash. Compilar duas vezes gera o mesmo hash.
   - Imprime um relatório com:
     - número de linhas por matriz;
     - contagem por `status` (EXTRAIDO, INFERIDO, A_VERIFICAR);
     - no M03 e no M04, contagem de `validacao` vazia, OK, CORRIGIR e DUVIDA.
   - Com `--piloto`, falha se alguma regra de natureza CONDICAO do M03, ou alguma pergunta do M04, não estiver com `validacao = OK`.

4. **Testes com Vitest.**
   - As matrizes atuais compilam sem erro.
   - O hash é determinístico.
   - Fixtures pequenas provam que o compilador falha nestes casos: ID duplicado, referência quebrada, JSON inválido, operador fora da lista e variável desconhecida.

5. **Scripts npm:** `compilar`, `compilar:piloto`, `test`, `lint` e `typecheck`.

6. **GitHub Actions:** roda lint, typecheck, test e compilar em todo push e pull request.

7. **Vercel e Supabase, só os arquivos.**
   - `vercel.json` com `"regions": ["gru1"]`.
   - `npx supabase init`: só gera `supabase/config.toml`. Não sobe banco local e não cria tabelas.

8. **Documentação.** Atualize a seção "Comandos" do `CLAUDE.md` e o `README.md`.

## Critério de saída

- `npm run compilar` gera o pacote sem erro a partir dos CSV atuais.
- `npm test`, `npm run lint` e `npm run typecheck` passam.
- O GitHub Actions passa.

## Não faça

- Telas além da página inicial padrão.
- Banco, login, motor ou IA.
- Qualquer mudança nas matrizes. Se o compilador encontrar erro numa matriz, não corrija: liste os erros e pare para o Gabriel decidir. Avisos (status INFERIDO, validação vazia) não param o trabalho.

## Ao terminar

Mostre o relatório do compilador e liste os problemas que ele encontrou nas matrizes, sem corrigi-los. Diga em português simples o que foi feito e como o Gabriel pode conferir.
