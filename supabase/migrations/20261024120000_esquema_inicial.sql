-- Esquema inicial do Licita+ (Marco 2, passo 2).
--
-- Regras (CLAUDE.md, regra 10; decisões 0010 e 0012):
-- - toda tabela nasce com RLS ligado;
-- - o navegador não consulta o banco: o servidor entra como o usuário logado (papel authenticated, com o sub do
--   JWT), e é o RLS que decide o que ele vê;
-- - cada usuário só vê os dados da própria OM; o operador abre os processos; o administrador da TI administra
--   usuários e lê a auditoria, mas não abre processos;
-- - a auditoria só aceita inclusão e guarda o ID do processo sem chave estrangeira, para continuar depois do
--   expurgo.

create schema if not exists privado;
revoke all on schema privado from public, anon;
grant usage on schema privado to authenticated;

-- ------------------------------------------------------------------ tabelas

create table public.om (
  id uuid primary key default gen_random_uuid(),
  uasg text not null unique,
  nome text not null,
  -- linhas do cabeçalho do TR, na ordem
  cabecalho text[] not null default '{}',
  -- endereços de entrega e foro, usados como padrão no wizard
  dados jsonb not null default '{}',
  criado_em timestamptz not null default now()
);

create table public.usuario (
  id uuid primary key references auth.users (id) on delete cascade,
  om_id uuid not null references public.om (id),
  nome text not null,
  email text not null unique,
  perfil text not null check (perfil in ('OPERADOR', 'ADMINISTRADOR')),
  ativo boolean not null default true,
  -- senha definida pela TI: o usuário cria a própria no primeiro acesso (decisão 0012)
  senha_provisoria boolean not null default true,
  criado_em timestamptz not null default now()
);

create table public.processo (
  id uuid primary key default gen_random_uuid(),
  om_id uuid not null references public.om (id),
  numero text not null,
  objeto text not null,
  modalidade text not null,
  registro_precos boolean not null,
  checklists text[] not null check (cardinality(checklists) between 1 and 2 and checklists <@ array['CONSUMO', 'PERMANENTES']),
  etapa text not null default 'CHECKLIST' check (etapa in ('CHECKLIST', 'ITENS', 'WIZARD', 'MINUTA', 'EXPORTACAO')),
  situacao text not null default 'RASCUNHO' check (situacao in ('RASCUNHO', 'EM_REVISAO', 'LIBERADO', 'CONCLUIDO')),
  concluido_em timestamptz,
  -- pacote de regras com que o processo nasceu (arquitetura, princípio 5)
  pacote text not null,
  pacote_hash text not null,
  -- metadados da leitura do Word (consumo, permanentes, marcas_multiplas...; src/motor/entrada.ts). O arquivo
  -- não fica: só o hash, na auditoria (decisão 0009).
  leitura_checklist jsonb not null default '{}',
  criado_por uuid not null references public.usuario (id),
  criado_em timestamptz not null default now(),
  atualizado_em timestamptz not null default now(),
  check ((situacao = 'CONCLUIDO') = (concluido_em is not null)),
  unique (om_id, numero)
);

create table public.resposta_checklist (
  processo_id uuid not null references public.processo (id) on delete cascade,
  -- CK-C-12.1, CK-P-13.1
  pergunta text not null check (pergunta ~ '^CK-[CP]-[0-9]+(\.[0-9]+)*$'),
  -- opção marcada (texto literal) ou lista, na MULTIPLA
  valor jsonb,
  -- texto da caixa "Resposta:" (CK_x_texto)
  texto text,
  -- número lido do "Outro" (CK_x_numero)
  numero numeric,
  -- pergunta por item: números dos itens a que a resposta se aplica
  itens integer[],
  origem text not null check (origem in ('LEITURA_WORD', 'OPERADOR')),
  atualizado_em timestamptz not null default now(),
  primary key (processo_id, pergunta)
);

create table public.revisao_confirmada (
  processo_id uuid not null references public.processo (id) on delete cascade,
  pergunta text not null check (pergunta ~ '^CK-[CPX]-[0-9]+(\.[0-9]+)*$'),
  motivo text not null,
  resposta text not null,
  confirmado_por uuid not null references public.usuario (id),
  confirmado_em timestamptz not null default now(),
  primary key (processo_id, pergunta, motivo)
);

create table public.complemento_operador (
  processo_id uuid not null references public.processo (id) on delete cascade,
  -- CK-X-01 a CK-X-19
  pergunta text not null check (pergunta ~ '^CK-X-[0-9]+$'),
  valor jsonb not null,
  atualizado_em timestamptz not null default now(),
  primary key (processo_id, pergunta)
);

-- Item: dados de entrada do M05 (tabela_itens.*). Os atributos calculados (tratamento ME/EPP, cota, totais) não
-- ficam aqui: o motor calcula.
create table public.item (
  processo_id uuid not null references public.processo (id) on delete cascade,
  numero integer not null check (numero > 0),
  especificacao text,
  catmat text,
  unidade_medida text,
  quantidade numeric check (quantidade > 0),
  valor_unitario numeric check (valor_unitario > 0),
  classe_pdm text,
  grupo text,
  categoria text check (categoria in ('CONSUMO', 'PERMANENTE')),
  exige_amostra text check (exige_amostra in ('S', 'N')),
  marca_indicada text,
  validade_minima text,
  compatibilidade text,
  faixa_temperatura text,
  controle_especial text check (controle_especial in ('S', 'N')),
  garantia_minima_meses integer check (garantia_minima_meses > 0),
  justificativa_excecao_me_epp text,
  atualizado_em timestamptz not null default now(),
  primary key (processo_id, numero)
);

-- Respostas do wizard (WZ-xx) e campos extras que ele pede (VAR-xxx).
create table public.resposta_wizard (
  processo_id uuid not null references public.processo (id) on delete cascade,
  pergunta text not null check (pergunta ~ '^(WZ-[0-9]+|VAR-[0-9]+)$'),
  valor jsonb,
  justificativa text,
  origem text not null check (origem in ('CHECKLIST', 'SUGESTAO_ACEITA', 'EQUIPE')),
  atualizado_em timestamptz not null default now(),
  primary key (processo_id, pergunta)
);

create table public.exportacao (
  id bigint generated always as identity primary key,
  processo_id uuid not null references public.processo (id) on delete cascade,
  tipo text not null check (tipo in ('COPIA_SECAO', 'PDF')),
  -- título da seção do modelo AGU copiada
  secao text,
  hash_pdf text,
  feito_por uuid not null references public.usuario (id),
  feito_em timestamptz not null default now(),
  check ((tipo = 'COPIA_SECAO') = (secao is not null) and (tipo = 'PDF') = (hash_pdf is not null))
);

create table public.auditoria (
  id bigint generated always as identity primary key,
  em timestamptz not null default now(),
  -- null só para ações do sistema (expurgo) e do script de criação do primeiro administrador
  usuario_id uuid references public.usuario (id),
  om_id uuid not null references public.om (id),
  -- sem chave estrangeira: a linha fica depois do expurgo do processo
  processo_id uuid,
  acao text not null,
  detalhes jsonb not null default '{}',
  hash_arquivo text,
  hash_pacote text,
  hash_pdf text
);

create index on public.processo (om_id, situacao);
create index on public.auditoria (om_id, em desc);
create index on public.auditoria (processo_id);

-- ------------------------------------------------------------------ auditoria só aceita inclusão

create function privado.recusar_alteracao() returns trigger
language plpgsql as $$
begin
  raise exception 'a auditoria só aceita inclusão';
end;
$$;

create trigger auditoria_so_inclusao
  before update or delete or truncate on public.auditoria
  for each statement execute function privado.recusar_alteracao();

-- ------------------------------------------------------------------ quem é o usuário

-- security definer: lê usuario sem passar pelo RLS dele (evita recursão nas políticas)
create function privado.om_do_usuario() returns uuid
language sql stable security definer set search_path = '' as $$
  select om_id from public.usuario where id = auth.uid() and ativo;
$$;

create function privado.perfil_do_usuario() returns text
language sql stable security definer set search_path = '' as $$
  select perfil from public.usuario where id = auth.uid() and ativo;
$$;

create function privado.eh_operador_do_processo(p uuid) returns boolean
language sql stable security definer set search_path = '' as $$
  select exists (
    select 1 from public.processo pr join public.usuario u on u.om_id = pr.om_id
    where pr.id = p and u.id = auth.uid() and u.ativo and u.perfil = 'OPERADOR'
  );
$$;

-- O usuário tira a marca de senha provisória da própria linha depois de trocar a senha; não pode mexer em
-- perfil, OM nem situação.
create function public.concluir_troca_de_senha() returns void
language sql security definer set search_path = '' as $$
  update public.usuario set senha_provisoria = false where id = auth.uid() and ativo;
$$;

revoke all on function privado.om_do_usuario(), privado.perfil_do_usuario(), privado.eh_operador_do_processo(uuid),
  public.concluir_troca_de_senha() from public, anon;
grant execute on function privado.om_do_usuario(), privado.perfil_do_usuario(), privado.eh_operador_do_processo(uuid),
  public.concluir_troca_de_senha() to authenticated;

-- ------------------------------------------------------------------ RLS

alter table public.om enable row level security;
alter table public.usuario enable row level security;
alter table public.processo enable row level security;
alter table public.resposta_checklist enable row level security;
alter table public.revisao_confirmada enable row level security;
alter table public.complemento_operador enable row level security;
alter table public.item enable row level security;
alter table public.resposta_wizard enable row level security;
alter table public.exportacao enable row level security;
alter table public.auditoria enable row level security;

-- anon nunca acessa nada; authenticated só pelo que as políticas deixam
revoke all on all tables in schema public from anon;
revoke all on all sequences in schema public from anon;
grant select, insert, update, delete on all tables in schema public to authenticated;
revoke update, delete on public.auditoria from authenticated;

-- OM: cada um vê a própria; ninguém altera pelo sistema (cadastro por script)
create policy om_ler on public.om for select to authenticated using (id = privado.om_do_usuario());

-- Usuário: cada um vê a própria linha; o administrador vê e administra os da própria OM
create policy usuario_ler on public.usuario for select to authenticated
  using (id = auth.uid() or (privado.perfil_do_usuario() = 'ADMINISTRADOR' and om_id = privado.om_do_usuario()));
create policy usuario_incluir on public.usuario for insert to authenticated
  with check (privado.perfil_do_usuario() = 'ADMINISTRADOR' and om_id = privado.om_do_usuario());
create policy usuario_alterar on public.usuario for update to authenticated
  using (privado.perfil_do_usuario() = 'ADMINISTRADOR' and om_id = privado.om_do_usuario())
  with check (privado.perfil_do_usuario() = 'ADMINISTRADOR' and om_id = privado.om_do_usuario());

-- Processo: só o operador da mesma OM; não se apaga pelo sistema (só o expurgo)
create policy processo_ler on public.processo for select to authenticated
  using (privado.perfil_do_usuario() = 'OPERADOR' and om_id = privado.om_do_usuario());
create policy processo_incluir on public.processo for insert to authenticated
  with check (privado.perfil_do_usuario() = 'OPERADOR' and om_id = privado.om_do_usuario() and criado_por = auth.uid());
create policy processo_alterar on public.processo for update to authenticated
  using (privado.perfil_do_usuario() = 'OPERADOR' and om_id = privado.om_do_usuario())
  with check (privado.perfil_do_usuario() = 'OPERADOR' and om_id = privado.om_do_usuario());
revoke delete on public.processo from authenticated;

-- Dados do processo: quem pode abrir o processo lê e escreve
create policy resposta_checklist_operador on public.resposta_checklist for all to authenticated
  using (privado.eh_operador_do_processo(processo_id)) with check (privado.eh_operador_do_processo(processo_id));
create policy revisao_confirmada_operador on public.revisao_confirmada for all to authenticated
  using (privado.eh_operador_do_processo(processo_id))
  with check (privado.eh_operador_do_processo(processo_id) and confirmado_por = auth.uid());
create policy complemento_operador_operador on public.complemento_operador for all to authenticated
  using (privado.eh_operador_do_processo(processo_id)) with check (privado.eh_operador_do_processo(processo_id));
create policy item_operador on public.item for all to authenticated
  using (privado.eh_operador_do_processo(processo_id)) with check (privado.eh_operador_do_processo(processo_id));
create policy resposta_wizard_operador on public.resposta_wizard for all to authenticated
  using (privado.eh_operador_do_processo(processo_id)) with check (privado.eh_operador_do_processo(processo_id));
create policy exportacao_ler on public.exportacao for select to authenticated
  using (privado.eh_operador_do_processo(processo_id));
create policy exportacao_incluir on public.exportacao for insert to authenticated
  with check (privado.eh_operador_do_processo(processo_id) and feito_por = auth.uid());
revoke update, delete on public.exportacao from authenticated;

-- Auditoria: cada um inclui linhas em nome próprio, na própria OM. O administrador lê tudo da OM (controle); o
-- operador, só as linhas de processo (histórico), sem as ações de administração de usuários
create policy auditoria_incluir on public.auditoria for insert to authenticated
  with check (usuario_id = auth.uid() and om_id = privado.om_do_usuario());
create policy auditoria_ler on public.auditoria for select to authenticated
  using (om_id = privado.om_do_usuario() and (privado.perfil_do_usuario() = 'ADMINISTRADOR' or processo_id is not null));
