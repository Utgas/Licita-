# supabase/

Configuração e migrações do banco. No Marco 0, `npx supabase init` gera só o `config.toml`; as tabelas entram no Marco 2.

- Região do projeto: São Paulo (`sa-east-1`).
- Toda tabela nasce com RLS ligado.
- Dois projetos: desenvolvimento (dados fictícios) e produção.
- Expurgo: `privado.expurgar_processos()` apaga, 30 dias depois de "concluído", os dados do processo; a auditoria fica. Roda todo dia às 06:17 UTC pelo `pg_cron` (tarefa `expurgo-diario`).
