/**
 * Expurgo (Marco 2, passo 12): 30 dias depois de "concluído", o processo e os dados dele somem; a auditoria fica e
 * ganha a linha do expurgo. A data é simulada pelo parâmetro `agora`. Roda no Supabase local (npm run test:banco).
 */
import { eq, inArray, sql } from "drizzle-orm";
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { comoUsuario } from "../../src/dados/conexao.ts";
import * as esquema from "../../src/dados/esquema.ts";
import { DIAS_ATE_O_EXPURGO } from "../../src/dados/processos.ts";
import { abrirBancoDeTeste, criarOm, criarUsuario } from "./banco-de-teste.ts";

const { db, fechar } = abrirBancoDeTeste();
afterAll(fechar);

/**
 * "Hoje" simulado, bem no futuro, para não depender da data em que o teste roda. Também apaga concluídos deixados por
 * execuções anteriores no banco local, o que não atrapalha: cada arquivo de teste cria os próprios dados.
 */
const HOJE = new Date("2099-06-30T12:00:00Z");
const diasAntes = (n: number) => new Date(HOJE.getTime() - n * 24 * 60 * 60 * 1000).toISOString();

let om: string;
let operador: string;
const ids: Record<"antigo" | "recente" | "rascunho", string> = { antigo: "", recente: "", rascunho: "" };

async function processo(situacao: "CONCLUIDO" | "RASCUNHO", concluidoEm: string | null): Promise<string> {
  const [linha] = await db
    .insert(esquema.processo)
    .values({
      omId: om,
      numero: `00000.${Math.random().toString().slice(2, 8)}/2099-00`,
      objeto: "Objeto fictício",
      modalidade: "PREGAO",
      registroPrecos: false,
      checklists: ["CONSUMO"],
      pacote: "agu-tr-compras-2025-12",
      pacoteHash: "0".repeat(64),
      criadoPor: operador,
      situacao,
      concluidoEm,
    })
    .returning({ id: esquema.processo.id });
  await db.insert(esquema.item).values({ processoId: linha.id, numero: 1, especificacao: "Item fictício", quantidade: "10" });
  await db.insert(esquema.respostaWizard).values({ processoId: linha.id, pergunta: "WZ-01", valor: "LICITACAO", origem: "EQUIPE" });
  await db.insert(esquema.auditoria).values({ usuarioId: operador, omId: om, processoId: linha.id, acao: "PROCESSO_CRIADO" });
  return linha.id;
}

const expurgar = async (agora: Date) => {
  const [linha] = await db.execute<{ apagados: number }>(sql`select privado.expurgar_processos(${agora.toISOString()}::timestamptz) as apagados`);
  return Number(linha.apagados);
};
const existe = async (id: string) => (await db.select({ id: esquema.processo.id }).from(esquema.processo).where(eq(esquema.processo.id, id))).length === 1;

beforeAll(async () => {
  om = await criarOm(db);
  operador = await criarUsuario(db, om, "OPERADOR");
  ids.antigo = await processo("CONCLUIDO", diasAntes(DIAS_ATE_O_EXPURGO + 1));
  ids.recente = await processo("CONCLUIDO", diasAntes(DIAS_ATE_O_EXPURGO - 1));
  ids.rascunho = await processo("RASCUNHO", null);
});

describe("expurgo", () => {
  it("apaga o concluído há mais de 30 dias, com itens e respostas, e mantém os demais", async () => {
    expect(await expurgar(HOJE)).toBeGreaterThanOrEqual(1);
    expect(await existe(ids.antigo)).toBe(false);
    expect(await db.select().from(esquema.item).where(eq(esquema.item.processoId, ids.antigo))).toEqual([]);
    expect(await db.select().from(esquema.respostaWizard).where(eq(esquema.respostaWizard.processoId, ids.antigo))).toEqual([]);
    expect(await existe(ids.recente)).toBe(true);
    expect(await existe(ids.rascunho)).toBe(true);
  });

  it("a auditoria do processo apagado fica, com a linha do expurgo", async () => {
    const linhas = await db.select().from(esquema.auditoria).where(eq(esquema.auditoria.processoId, ids.antigo));
    expect(linhas.map((l) => l.acao).sort()).toEqual(["PROCESSO_CRIADO", "PROCESSO_EXPURGADO"]);
    const expurgo = linhas.find((l) => l.acao === "PROCESSO_EXPURGADO");
    expect(expurgo?.usuarioId).toBeNull();
    expect(expurgo?.omId).toBe(om);
    expect(expurgo?.hashPacote).toBe("0".repeat(64));
  });

  it("com a data simulada 2 dias depois, o outro concluído também some; o rascunho nunca", async () => {
    await expurgar(new Date(HOJE.getTime() + 2 * 24 * 60 * 60 * 1000));
    expect(await existe(ids.recente)).toBe(false);
    expect(await existe(ids.rascunho)).toBe(true);
    const auditoria = await db.select().from(esquema.auditoria).where(inArray(esquema.auditoria.processoId, [ids.antigo, ids.recente]));
    expect(auditoria.filter((l) => l.acao === "PROCESSO_EXPURGADO")).toHaveLength(2);
  });

  it("o usuário do sistema não consegue chamar o expurgo", async () => {
    const tentativa = comoUsuario(db, operador, (tx) => tx.execute(sql`select privado.expurgar_processos()`));
    await expect(tentativa).rejects.toThrow();
  });

  it("a tarefa diária está agendada quando o banco tem pg_cron", async () => {
    const [cron] = await db.execute<{ existe: boolean }>(sql`select exists (select 1 from pg_extension where extname = 'pg_cron') as existe`);
    if (!cron.existe) return;
    const tarefas = await db.execute<{ schedule: string; command: string }>(sql`select schedule, command from cron.job where jobname = 'expurgo-diario'`);
    expect(tarefas).toHaveLength(1);
    expect(tarefas[0].command).toBe("select privado.expurgar_processos()");
  });
});
