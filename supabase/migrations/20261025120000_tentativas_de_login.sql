-- Limite de tentativas de login (decisão 0017). O Supabase Auth limita por endereço IP, mas aqui o login passa pelo
-- servidor: o Supabase vê o IP da Vercel, não o do usuário. A conta das falhas fica no banco, por e-mail e por IP.
--
-- Coleta mínima: a tabela guarda só um marcador (HMAC-SHA256 com chave do servidor) do e-mail e do IP, nunca os
-- valores, e cada linha vive 24 horas. Fica no esquema privado, que a API não expõe, e só as funções abaixo a usam.

create table privado.tentativa_login (
  id bigint generated always as identity primary key,
  chave text not null check (chave ~ '^[0-9a-f]{64}$'),
  tipo text not null check (tipo in ('EMAIL', 'IP')),
  em timestamptz not null default now()
);
alter table privado.tentativa_login enable row level security;
revoke all on privado.tentativa_login from public, anon, authenticated;
create index on privado.tentativa_login (chave, em desc);

-- Bloqueado: 5 falhas do mesmo e-mail ou 20 do mesmo IP nos últimos 15 minutos.
create function privado.login_bloqueado(email text, ip text) returns boolean
language sql stable security definer set search_path = '' as $$
  select (select count(*) from privado.tentativa_login where chave = email and tipo = 'EMAIL' and em > now() - interval '15 minutes') >= 5
      or (select count(*) from privado.tentativa_login where chave = ip and tipo = 'IP' and em > now() - interval '15 minutes') >= 20;
$$;

create function privado.registrar_falha_login(email text, ip text) returns void
language sql security definer set search_path = '' as $$
  delete from privado.tentativa_login where em < now() - interval '24 hours';
  insert into privado.tentativa_login (chave, tipo) values (email, 'EMAIL'), (ip, 'IP');
$$;

-- Login certo zera a conta do e-mail (a do IP continua: protege contra quem testa vários e-mails).
create function privado.limpar_falhas_login(email text) returns void
language sql security definer set search_path = '' as $$
  delete from privado.tentativa_login where chave = email and tipo = 'EMAIL';
$$;

revoke all on function privado.login_bloqueado(text, text), privado.registrar_falha_login(text, text),
  privado.limpar_falhas_login(text) from public, anon;
grant execute on function privado.login_bloqueado(text, text), privado.registrar_falha_login(text, text),
  privado.limpar_falhas_login(text) to authenticated;
