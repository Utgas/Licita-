/**
 * Esquema do banco em TypeScript (Drizzle), espelho de supabase/migrations/. A migração SQL é a fonte: ela tem as
 * restrições, o RLS e a trava da auditoria; aqui ficam só as colunas, para as consultas do servidor terem tipo.
 * O teste de banco (testes/dados/) confere que as duas não divergem.
 */
import { bigint, boolean, integer, jsonb, numeric, pgTable, primaryKey, text, timestamp, uuid } from "drizzle-orm/pg-core";

const momento = (nome: string) => timestamp(nome, { withTimezone: true, mode: "string" });

export const om = pgTable("om", {
  id: uuid("id").primaryKey().defaultRandom(),
  uasg: text("uasg").notNull().unique(),
  nome: text("nome").notNull(),
  cabecalho: text("cabecalho").array().notNull().default([]),
  dados: jsonb("dados").notNull().default({}),
  criadoEm: momento("criado_em").notNull().defaultNow(),
});

export const PERFIS = ["OPERADOR", "ADMINISTRADOR"] as const;

export const usuario = pgTable("usuario", {
  /** O mesmo id do usuário no Supabase Auth (auth.users). */
  id: uuid("id").primaryKey(),
  omId: uuid("om_id").notNull().references(() => om.id),
  nome: text("nome").notNull(),
  email: text("email").notNull().unique(),
  perfil: text("perfil", { enum: PERFIS }).notNull(),
  ativo: boolean("ativo").notNull().default(true),
  senhaProvisoria: boolean("senha_provisoria").notNull().default(true),
  criadoEm: momento("criado_em").notNull().defaultNow(),
});

export const ETAPAS = ["CHECKLIST", "ITENS", "WIZARD", "MINUTA", "EXPORTACAO"] as const;
export const SITUACOES = ["RASCUNHO", "EM_REVISAO", "LIBERADO", "CONCLUIDO"] as const;
export const CHECKLISTS = ["CONSUMO", "PERMANENTES"] as const;

export const processo = pgTable("processo", {
  id: uuid("id").primaryKey().defaultRandom(),
  omId: uuid("om_id").notNull().references(() => om.id),
  numero: text("numero").notNull(),
  objeto: text("objeto").notNull(),
  modalidade: text("modalidade").notNull(),
  registroPrecos: boolean("registro_precos").notNull(),
  checklists: text("checklists", { enum: CHECKLISTS }).array().notNull(),
  etapa: text("etapa", { enum: ETAPAS }).notNull().default("CHECKLIST"),
  situacao: text("situacao", { enum: SITUACOES }).notNull().default("RASCUNHO"),
  concluidoEm: momento("concluido_em"),
  pacote: text("pacote").notNull(),
  pacoteHash: text("pacote_hash").notNull(),
  leituraChecklist: jsonb("leitura_checklist").notNull().default({}),
  criadoPor: uuid("criado_por").notNull().references(() => usuario.id),
  criadoEm: momento("criado_em").notNull().defaultNow(),
  atualizadoEm: momento("atualizado_em").notNull().defaultNow(),
});

const doProcesso = () => uuid("processo_id").notNull().references(() => processo.id, { onDelete: "cascade" });

/** Uma linha por pergunta e conjunto de itens (itens vazio = vale para o processo inteiro). */
export const respostaChecklist = pgTable("resposta_checklist", {
  id: bigint("id", { mode: "number" }).primaryKey().generatedAlwaysAsIdentity(),
  processoId: doProcesso(),
  pergunta: text("pergunta").notNull(),
  valor: jsonb("valor"),
  texto: text("texto"),
  numero: numeric("numero"),
  itens: integer("itens").array().notNull().default([]),
  origem: text("origem", { enum: ["LEITURA_WORD", "OPERADOR"] }).notNull(),
  atualizadoEm: momento("atualizado_em").notNull().defaultNow(),
});

export const revisaoConfirmada = pgTable(
  "revisao_confirmada",
  {
    processoId: doProcesso(),
    pergunta: text("pergunta").notNull(),
    motivo: text("motivo").notNull(),
    resposta: text("resposta").notNull(),
    confirmadoPor: uuid("confirmado_por").notNull().references(() => usuario.id),
    confirmadoEm: momento("confirmado_em").notNull().defaultNow(),
  },
  (t) => [primaryKey({ columns: [t.processoId, t.pergunta, t.motivo] })],
);

export const complementoOperador = pgTable(
  "complemento_operador",
  {
    processoId: doProcesso(),
    pergunta: text("pergunta").notNull(),
    valor: jsonb("valor").notNull(),
    atualizadoEm: momento("atualizado_em").notNull().defaultNow(),
  },
  (t) => [primaryKey({ columns: [t.processoId, t.pergunta] })],
);

export const item = pgTable(
  "item",
  {
    processoId: doProcesso(),
    numero: integer("numero").notNull(),
    especificacao: text("especificacao"),
    catmat: text("catmat"),
    unidadeMedida: text("unidade_medida"),
    quantidade: numeric("quantidade"),
    valorUnitario: numeric("valor_unitario"),
    classePdm: text("classe_pdm"),
    grupo: text("grupo"),
    categoria: text("categoria", { enum: ["CONSUMO", "PERMANENTE"] }),
    exigeAmostra: text("exige_amostra", { enum: ["S", "N"] }),
    marcaIndicada: text("marca_indicada"),
    validadeMinima: text("validade_minima"),
    compatibilidade: text("compatibilidade"),
    faixaTemperatura: text("faixa_temperatura"),
    controleEspecial: text("controle_especial", { enum: ["S", "N"] }),
    garantiaMinimaMeses: integer("garantia_minima_meses"),
    justificativaExcecaoMeEpp: text("justificativa_excecao_me_epp"),
    atualizadoEm: momento("atualizado_em").notNull().defaultNow(),
  },
  (t) => [primaryKey({ columns: [t.processoId, t.numero] })],
);

export const respostaWizard = pgTable(
  "resposta_wizard",
  {
    processoId: doProcesso(),
    pergunta: text("pergunta").notNull(),
    valor: jsonb("valor"),
    justificativa: text("justificativa"),
    origem: text("origem", { enum: ["CHECKLIST", "SUGESTAO_ACEITA", "EQUIPE"] }).notNull(),
    atualizadoEm: momento("atualizado_em").notNull().defaultNow(),
  },
  (t) => [primaryKey({ columns: [t.processoId, t.pergunta] })],
);

export const exportacao = pgTable("exportacao", {
  id: bigint("id", { mode: "number" }).primaryKey().generatedAlwaysAsIdentity(),
  processoId: doProcesso(),
  tipo: text("tipo", { enum: ["COPIA_SECAO", "PDF"] }).notNull(),
  secao: text("secao"),
  hashPdf: text("hash_pdf"),
  feitoPor: uuid("feito_por").notNull().references(() => usuario.id),
  feitoEm: momento("feito_em").notNull().defaultNow(),
});

export const auditoria = pgTable("auditoria", {
  id: bigint("id", { mode: "number" }).primaryKey().generatedAlwaysAsIdentity(),
  em: momento("em").notNull().defaultNow(),
  usuarioId: uuid("usuario_id").references(() => usuario.id),
  omId: uuid("om_id").notNull().references(() => om.id),
  /** Sem chave estrangeira: a linha fica depois do expurgo do processo. */
  processoId: uuid("processo_id"),
  acao: text("acao").notNull(),
  detalhes: jsonb("detalhes").notNull().default({}),
  hashArquivo: text("hash_arquivo"),
  hashPacote: text("hash_pacote"),
  hashPdf: text("hash_pdf"),
});

export const TIPOS_DE_SOLICITACAO = [
  "CONFIRMACAO_ACESSO",
  "CORRECAO",
  "ANONIMIZACAO_BLOQUEIO_ELIMINACAO",
  "PORTABILIDADE",
  "INFORMACAO_COMPARTILHAMENTO",
  "OPOSICAO",
  "OUTRO",
] as const;

/** Pedido do titular (LGPD, art. 18): o usuário escreve o pedido; o administrador da TI da OM, a resposta. */
export const solicitacaoTitular = pgTable("solicitacao_titular", {
  id: bigint("id", { mode: "number" }).primaryKey().generatedAlwaysAsIdentity(),
  usuarioId: uuid("usuario_id").notNull().references(() => usuario.id),
  omId: uuid("om_id").notNull().references(() => om.id),
  tipo: text("tipo", { enum: TIPOS_DE_SOLICITACAO }).notNull(),
  descricao: text("descricao").notNull(),
  situacao: text("situacao", { enum: ["ABERTA", "RESPONDIDA"] }).notNull().default("ABERTA"),
  resposta: text("resposta"),
  criadaEm: momento("criada_em").notNull().defaultNow(),
  respondidaEm: momento("respondida_em"),
  respondidaPor: uuid("respondida_por").references(() => usuario.id),
});
