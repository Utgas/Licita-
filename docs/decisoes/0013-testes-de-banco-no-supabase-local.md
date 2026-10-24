# 0013. Testes de banco no Supabase local

- Data: 24/10/2026
- Situação: aceita. Autorizada pelo dono do projeto ("pode usar a ferramenta do Supabase").

## Contexto

O Marco 2 exige provar o RLS de todas as tabelas, a auditoria só de inclusão e o expurgo. Esses testes precisam de um PostgreSQL com o Supabase Auth de verdade (papéis `anon` e `authenticated`, `auth.uid()`), e não podem rodar no banco de desenvolvimento: sujariam os dados e precisariam das chaves no GitHub.

## Decisão

- **Ferramenta:** a CLI do Supabase (`supabase`, dependência de desenvolvimento, versão fixada) sobe o Supabase local em Docker (`npx supabase start`) e aplica as migrações de `supabase/migrations/`.
- **Pasta nova:** `testes/dados/`, com os testes de banco. Rodam com `npm run test:banco`, separados do `npm test`, que continua sem banco.
- **GitHub Actions:** um job próprio sobe o Supabase local e roda `npm run test:banco`. Nenhuma chave do Supabase vai para os segredos do GitHub.
- Os testes só aceitam endereço local (`127.0.0.1` ou `localhost`); com qualquer outro, param antes de conectar.

## Consequências

- Rodar os testes de banco na própria máquina exige Docker.
- As migrações são testadas a cada push antes de chegarem ao projeto de desenvolvimento.
