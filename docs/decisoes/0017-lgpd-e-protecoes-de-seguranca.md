# 0017. LGPD, páginas legais e proteções de segurança

- Data: 25/10/2026
- Situação: aceita para desenvolvimento. O dono do projeto pediu política de privacidade, termos de uso, aviso de cookies, formulário da LGPD, coleta mínima, acessibilidade e uma revisão de segurança. Os textos legais são minuta e dependem de revisão da OM antes do piloto.

## Contexto

A revisão de 25/10/2026 encontrou uma base boa: RLS em todas as tabelas, o navegador nunca fala com o banco, cookie de sessão `httpOnly`, senha guardada só como hash pelo Supabase Auth, nenhum segredo no histórico do git, consultas sempre parametrizadas (Drizzle e `sql` com parâmetros, nenhum `sql.raw`), todas as rotas e ações conferindo a sessão de novo e campos de formulário lidos um a um (sem mass assignment). Faltavam:

1. limite de tentativas de login. O Supabase Auth limita por IP, mas o login passa pelo servidor, então o Supabase vê o IP da Vercel e não o do usuário;
2. cabeçalhos de segurança (CSP, proibição de abrir o sistema dentro de outro site e outros);
3. conexão cifrada garantida entre a Vercel e o banco;
4. registro técnico de erro sem conteúdo: o erro do Drizzle traz os valores da consulta;
5. política de privacidade, termos de uso, aviso de cookies e um canal para os direitos do titular (LGPD, art. 18);
6. atalho de teclado para pular o cabeçalho;
7. duas dependências com falha conhecida (`zod` 4.6.5 e `vitest` 4.1.11).

## Decisão

1. **Limite de tentativas** (`src/auth/tentativas.ts`, migração `20261025120000`): 5 falhas do mesmo e-mail ou 20 do mesmo IP em 15 minutos bloqueiam novas tentativas, no login e na conferência da senha atual. O banco guarda só um marcador HMAC-SHA256 (chave: `SUPABASE_SECRET_KEY`) do e-mail e do IP, nunca os valores, numa tabela do esquema `privado`, e apaga cada linha em 24 horas. A senha provisória da TI libera o e-mail bloqueado. O IP vem do `x-forwarded-for`, que a Vercel escreve.
2. **Robôs:** campo invisível no login (armadilha). Quem o preenche conta como falha e não chega ao Supabase. Captcha (hCaptcha ou Turnstile) seria serviço externo e fica para decisão própria, se o sistema sair da rede da OM.
3. **Cabeçalhos** em `next.config.ts`: `Content-Security-Policy` (só o próprio sistema; `'unsafe-inline'` em script porque o Next põe scripts na página), `X-Frame-Options: DENY`, `X-Content-Type-Options`, `Referrer-Policy: same-origin`, `Permissions-Policy`, `Cross-Origin-Opener-Policy` e, em produção, `Strict-Transport-Security`. Sem `X-Powered-By`.
4. **Saída (`/sair`)** recusa pedido vindo de outro site (Origin diferente). As ações do Next já fazem essa conferência sozinhas.
5. **Banco:** TLS obrigatório fora da máquina local (`ssl: "require"`), salvo quando a `DATABASE_URL` já define o `sslmode`.
6. **Registro técnico:** só tipo, primeira linha da mensagem e código do PostgreSQL; nunca a consulta com os valores.
7. **Senha:** a regra do Supabase passa a ser a mesma da tela (10 caracteres, letras e números). A senha provisória sempre tem letra e número.
8. **LGPD:**
   - páginas abertas `/privacidade` (com a seção de cookies) e `/termos`, e rodapé com os links em todas as telas;
   - aviso de cookies informativo: só há o cookie de sessão, que é necessário e não depende de consentimento (guia de cookies da ANPD). A marca de "já visto" fica no armazenamento local do navegador;
   - tela `/meus-dados` para todo usuário: o cadastro, as próprias ações na auditoria, a cópia em JSON (`/meus-dados/exportar`) e o pedido do titular;
   - tabela `solicitacao_titular` (migração `20261025130000`), com RLS: o usuário pede em nome próprio; o administrador da TI da mesma OM responde em `/admin/pedidos`. Uma trava no banco faz o pedido novo nascer sempre aberto e sem resposta, e só as colunas da resposta podem ser alteradas. Ninguém apaga pedido;
   - nova política da auditoria: cada usuário lê as linhas feitas por ele (acesso aos próprios dados, art. 18, II).
9. **Pastas novas** em `src/app/`: `privacidade/`, `termos/`, `meus-dados/` e `admin/pedidos/`.
10. **Textos legais** ficam nas páginas (`src/app/privacidade/page.tsx` e `src/app/termos/page.tsx`). Não são regra da minuta: descrevem o sistema. O que só a OM sabe aparece como lacuna marcada (`[A preencher pela OM: ...]`), nunca inventado.

## Pendências para o dono do projeto

- Preencher as lacunas das duas páginas: OM controladora, encarregado de dados e contato, prazos de guarda (auditoria, usuário desativado, pedidos) e o instrumento que autoriza Vercel e Supabase como operadoras (LGPD, art. 33).
- Levar os dois textos ao encarregado e à assessoria jurídica da OM antes do piloto.
- **Coleta mínima no checklist:** a pergunta CK-C-1.4 (e a CK-P equivalente) lê telefone e e-mail do responsável técnico, que "ficam só no processo" (M11) e não entram na minuta. Pela LGPD (art. 6º, III), o ideal é não guardar esses dois campos. Como isso muda a matriz, fica para a decisão do Gabriel.
- No projeto Supabase hospedado: conferir em Authentication > Providers > Email a senha mínima de 10 caracteres com letras e números; o `config.toml` só vale para o banco local.
- O segundo fator (decisão 0010) continua para antes do piloto.
- `exceljs` 4.4.0 depende de `uuid` com falha conhecida (GHSA-w5hq-g745-h8pq), mas a falha só atinge as funções v3, v5 e v6 com buffer, que o `exceljs` não usa. A correção do `npm audit` rebaixaria o `exceljs` para a 3.4.0; fica como está até sair versão nova.

## Consequências

- Uma senha vazada continua dando acesso, mas adivinhar a senha deixa de ser viável.
- Todo login faz duas consultas a mais ao banco (conferir e registrar).
- O aviso de cookies aparece uma vez por navegador.
- Os testes `testes/dados/protecoes.test.ts` (banco) e `testes/telas/protecoes.spec.ts` (navegador) cobrem o que entrou aqui.
