-- Avisos do Supabase depois do esquema inicial:
-- - a função que tira a marca de senha provisória ficava no esquema public, exposta na API (/rest/v1/rpc): um
--   usuário logado poderia chamá-la sem trocar a senha. Vai para o esquema privado, que a API não expõe; só o
--   servidor a chama, depois de trocar a senha;
-- - a função da trava da auditoria ganha search_path fixo.

drop function public.concluir_troca_de_senha();

create function privado.concluir_troca_de_senha() returns void
language sql security definer set search_path = '' as $$
  update public.usuario set senha_provisoria = false where id = auth.uid() and ativo;
$$;

revoke all on function privado.concluir_troca_de_senha() from public, anon;
grant execute on function privado.concluir_troca_de_senha() to authenticated;

alter function privado.recusar_alteracao() set search_path = '';
