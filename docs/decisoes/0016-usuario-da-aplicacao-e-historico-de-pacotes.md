# 0016. Usuário próprio da aplicação no banco e histórico de pacotes

- Data: 25/10/2026
- Situação: aceita. O dono do projeto pediu para conferir e corrigir toda a ligação entre a Vercel e o Supabase.

## Contexto

O login no sistema publicado falhava, por dois motivos em sequência:

1. A variável `SUPABASE_URL` trazia o endereço da Data API (corrigido em 24/10/2026, PR #3).
2. Com o endereço certo, o Supabase aceitava a senha, mas a aplicação caía (erro 500) ao ler o perfil do usuário no banco. A `DATABASE_URL` da Vercel tinha a senha errada do usuário `postgres` ("password authentication failed for user postgres").

Na mesma revisão apareceu um terceiro problema, ainda sem efeito: a correção nas matrizes de 25/10/2026 mudou o hash do pacote de regras. Com isso, um processo já aberto deixaria de abrir, porque o sistema recusava pacote com hash diferente do gravado no processo.

## Decisão

1. **A aplicação entra no banco com um usuário só dela, `licita_app`, e não mais com `postgres`.**
   - Ele só pode assumir o papel `authenticated` (com o RLS ligado), que é o que `comoUsuario` já faz em toda consulta.
   - Ele não ignora o RLS e não cria tabela nem usuário.
   - Se a senha vazar, o estrago fica limitado ao que o RLS deixa.

   A senha fica só na `DATABASE_URL` da Vercel (Transaction pooler, porta 6543, usuário `licita_app.<ref>`).
2. **O compilador guarda cada pacote em `regras/<nome>/historico/<hash>.json`, e esses arquivos nunca são apagados.**
   - O processo carrega o pacote exato com que nasceu (`carregarPacote(nome, hash)`), como manda o princípio 5 da arquitetura.
   - O GitHub Actions falha se o pacote atual não estiver no histórico.

## Como recriar o usuário (outro projeto Supabase)

No SQL Editor do Supabase, trocando a senha:

```sql
create role licita_app login noinherit nobypassrls password '<senha forte>';
grant authenticated to licita_app;
```

Depois, na Vercel: `DATABASE_URL = postgresql://licita_app.<ref>:<senha>@aws-1-sa-east-1.pooler.supabase.com:6543/postgres`. Para valer, é preciso um novo deploy.

## Consequências

- Os testes locais e o CI continuam entrando como `postgres` no banco local: o comportamento é o mesmo, porque toda consulta passa por `comoUsuario`.
- Script ou tarefa que precise ignorar o RLS (`criar-usuario`, migrações) usa a `DATABASE_URL_MIGRACAO`, só na máquina de quem administra, nunca na Vercel.
