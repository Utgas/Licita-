-- Direitos do titular (LGPD, art. 18; decisão 0017). O usuário vê os próprios dados na tela "Meus dados" e faz
-- pedidos (correção, eliminação, informação...); o administrador da TI da mesma OM responde. Ninguém mais lê os
-- pedidos, e o pedido não pode ser apagado pelo sistema (fica como prova do atendimento).

create table public.solicitacao_titular (
  id bigint generated always as identity primary key,
  usuario_id uuid not null references public.usuario (id),
  om_id uuid not null references public.om (id),
  tipo text not null check (tipo in ('CONFIRMACAO_ACESSO', 'CORRECAO', 'ANONIMIZACAO_BLOQUEIO_ELIMINACAO',
    'PORTABILIDADE', 'INFORMACAO_COMPARTILHAMENTO', 'OPOSICAO', 'OUTRO')),
  descricao text not null check (char_length(descricao) between 1 and 2000),
  situacao text not null default 'ABERTA' check (situacao in ('ABERTA', 'RESPONDIDA')),
  resposta text check (char_length(resposta) <= 2000),
  criada_em timestamptz not null default now(),
  respondida_em timestamptz,
  respondida_por uuid references public.usuario (id),
  check ((situacao = 'RESPONDIDA') = (resposta is not null and respondida_em is not null and respondida_por is not null))
);
create index on public.solicitacao_titular (om_id, situacao, criada_em desc);

alter table public.solicitacao_titular enable row level security;

-- Contra mass assignment: o pedido novo sempre nasce aberto, sem resposta e com a hora do banco, seja o que for que
-- venha na inclusão; na alteração, só as colunas da resposta podem mudar.
create function privado.solicitacao_nova() returns trigger
language plpgsql set search_path = '' as $$
begin
  new.situacao := 'ABERTA';
  new.resposta := null;
  new.respondida_em := null;
  new.respondida_por := null;
  new.criada_em := now();
  return new;
end;
$$;
create trigger solicitacao_nova before insert on public.solicitacao_titular
  for each row execute function privado.solicitacao_nova();

revoke all on public.solicitacao_titular from public, anon, authenticated;
grant select, insert on public.solicitacao_titular to authenticated;
grant update (situacao, resposta, respondida_em, respondida_por) on public.solicitacao_titular to authenticated;

create policy solicitacao_ler on public.solicitacao_titular for select to authenticated
  using (usuario_id = auth.uid() or (privado.perfil_do_usuario() = 'ADMINISTRADOR' and om_id = privado.om_do_usuario()));
create policy solicitacao_incluir on public.solicitacao_titular for insert to authenticated
  with check (usuario_id = auth.uid() and om_id = privado.om_do_usuario());
create policy solicitacao_responder on public.solicitacao_titular for update to authenticated
  using (privado.perfil_do_usuario() = 'ADMINISTRADOR' and om_id = privado.om_do_usuario() and situacao = 'ABERTA')
  with check (privado.perfil_do_usuario() = 'ADMINISTRADOR' and om_id = privado.om_do_usuario()
    and situacao = 'RESPONDIDA' and respondida_por = auth.uid());

-- Acesso aos próprios dados (art. 18, II): cada usuário lê também as linhas da auditoria feitas por ele (login,
-- saída, troca de senha), que antes só o administrador via.
create policy auditoria_ler_proprias on public.auditoria for select to authenticated using (usuario_id = auth.uid());
