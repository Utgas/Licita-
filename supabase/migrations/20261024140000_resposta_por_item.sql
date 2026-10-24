-- Pergunta por item pode ter respostas diferentes para itens diferentes (ex.: validade de 12 meses no item 1 e
-- 75% do prazo total no item 2). A chave deixa de ser (processo, pergunta): cada linha é uma resposta para um
-- conjunto de itens; sem itens, vale para o processo inteiro.

alter table public.resposta_checklist drop constraint resposta_checklist_pkey;
alter table public.resposta_checklist add column id bigint generated always as identity primary key;
alter table public.resposta_checklist alter column itens set default '{}';
update public.resposta_checklist set itens = '{}' where itens is null;
alter table public.resposta_checklist alter column itens set not null;
create unique index resposta_checklist_pergunta_itens on public.resposta_checklist (processo_id, pergunta, itens);

-- O checklist tem perguntas de cabeçalho (CK-C-CAB.01 a CK-P-CAB.05).
alter table public.resposta_checklist drop constraint resposta_checklist_pergunta_check;
alter table public.resposta_checklist add constraint resposta_checklist_pergunta_check
  check (pergunta ~ '^CK-[CP]-(CAB\.[0-9]+|[0-9]+(\.[0-9]+)*)$');
alter table public.revisao_confirmada drop constraint revisao_confirmada_pergunta_check;
alter table public.revisao_confirmada add constraint revisao_confirmada_pergunta_check
  check (pergunta ~ '^CK-[CPX]-(CAB\.[0-9]+|[0-9]+(\.[0-9]+)*)$');
