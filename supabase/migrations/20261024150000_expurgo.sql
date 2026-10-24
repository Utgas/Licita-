-- Expurgo (Marco 2, passo 12; arquitetura, "Segurança e retenção"; decisão 0011): 30 dias depois de "concluído",
-- os dados do processo são apagados. As tabelas filhas vão junto (on delete cascade); a auditoria fica, porque
-- não tem chave estrangeira para o processo, e ganha uma linha do próprio expurgo.

-- agora e dias são parâmetros para o teste simular a data e para o prazo ser configurável; a tarefa diária usa
-- os padrões (agora = now(), 30 dias).
create function privado.expurgar_processos(agora timestamptz default now(), dias integer default 30)
returns integer
language plpgsql security definer set search_path = '' as $$
declare
  apagados integer;
begin
  with apagado as (
    delete from public.processo
    where situacao = 'CONCLUIDO' and concluido_em is not null and concluido_em <= agora - make_interval(days => dias)
    returning id, om_id, numero, pacote_hash, concluido_em
  )
  insert into public.auditoria (om_id, processo_id, acao, detalhes, hash_pacote)
  select om_id, id, 'PROCESSO_EXPURGADO', jsonb_build_object('concluido_em', concluido_em, 'dias', dias), pacote_hash
  from apagado;
  get diagnostics apagados = row_count;
  return apagados;
end;
$$;

-- Só o banco roda o expurgo: ninguém o chama pelo sistema.
revoke all on function privado.expurgar_processos(timestamptz, integer) from public, anon, authenticated;

-- Tarefa diária às 06:17 UTC (03:17 em Brasília). O pg_cron existe no Supabase (local e hospedado); num
-- PostgreSQL sem ele, a migração segue e o expurgo fica para ser agendado à mão.
do $$
begin
  if exists (select 1 from pg_available_extensions where name = 'pg_cron') then
    create extension if not exists pg_cron;
    perform cron.schedule('expurgo-diario', '17 6 * * *', 'select privado.expurgar_processos()');
  else
    raise notice 'pg_cron indisponível: agende privado.expurgar_processos() à mão';
  end if;
end;
$$;
