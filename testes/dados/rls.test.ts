/**
 * RLS de todas as tabelas (Marco 2, passo 2): o operador só lê e escreve os processos da própria OM; o
 * administrador da TI administra os usuários da OM e lê a auditoria, mas não abre processos (decisão 0012); a
 * auditoria só aceita inclusão; anon não vê nada. Roda no Supabase local (npm run test:banco).
 */
import { eq, getTableColumns, getTableName, is, sql } from "drizzle-orm";
import { PgTable } from "drizzle-orm/pg-core";
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { type Transacao, comoUsuario } from "../../src/dados/conexao.ts";
import * as esquema from "../../src/dados/esquema.ts";
import { abrirBancoDeTeste, criarOm, criarUsuario } from "./banco-de-teste.ts";

const { db, fechar } = abrirBancoDeTeste();
afterAll(fechar);

let omA: string;
let omB: string;
let operadorA: string;
let administradorA: string;
let operadorB: string;
let inativoA: string;
let processoA: string;

const como = <T>(usuario: string, fazer: (tx: Transacao) => Promise<T>) => comoUsuario(db, usuario, fazer);

/** Mensagem do erro do PostgreSQL (o Drizzle a guarda em cause); "" quando não houve erro. */
async function erroDoBanco(tentativa: Promise<unknown>): Promise<string> {
  try {
    await tentativa;
    return "";
  } catch (e) {
    return String((e as { cause?: { message?: string } }).cause?.message ?? (e as Error).message);
  }
}

/** Linhas fictícias de cada tabela filha do processo. */
const filhas = (processoId: string, usuarioId: string) =>
  [
    [esquema.respostaChecklist, { processoId, pergunta: "CK-C-1.1", valor: "Sim", origem: "OPERADOR" }],
    [esquema.revisaoConfirmada, { processoId, pergunta: "CK-C-1.1", motivo: "SEM_RESPOSTA", resposta: "Sim", confirmadoPor: usuarioId }],
    [esquema.complementoOperador, { processoId, pergunta: "CK-X-10", valor: [1] }],
    [esquema.item, { processoId, numero: 1, especificacao: "Item fictício", quantidade: "10" }],
    [esquema.respostaWizard, { processoId, pergunta: "WZ-01", valor: "LICITACAO", origem: "EQUIPE" }],
    [esquema.exportacao, { processoId, tipo: "COPIA_SECAO", secao: "Seção fictícia", feitoPor: usuarioId }],
  ] as const satisfies readonly (readonly [PgTable, Record<string, unknown>])[];

async function novoProcesso(tx: Transacao, omId: string, criadoPor: string) {
  const [linha] = await tx
    .insert(esquema.processo)
    .values({
      omId,
      numero: `00000.${Math.random().toString().slice(2, 8)}/2026-00`,
      objeto: "Objeto fictício",
      modalidade: "PREGAO",
      registroPrecos: false,
      checklists: ["CONSUMO"],
      pacote: "agu-tr-compras-2025-12",
      pacoteHash: "0".repeat(64),
      criadoPor,
    })
    .returning({ id: esquema.processo.id });
  return linha.id;
}

beforeAll(async () => {
  omA = await criarOm(db);
  omB = await criarOm(db);
  operadorA = await criarUsuario(db, omA, "OPERADOR");
  administradorA = await criarUsuario(db, omA, "ADMINISTRADOR");
  inativoA = await criarUsuario(db, omA, "OPERADOR", false);
  operadorB = await criarUsuario(db, omB, "OPERADOR");
  processoA = await como(operadorA, (tx) => novoProcesso(tx, omA, operadorA));
  await como(operadorA, async (tx) => {
    for (const [tabela, valores] of filhas(processoA, operadorA)) await tx.insert(tabela).values(valores as never);
  });
});

describe("estrutura", () => {
  it("toda tabela do esquema public tem RLS ligado", async () => {
    const semRls = await db.execute(sql`select relname from pg_class c join pg_namespace n on n.oid = c.relnamespace
      where n.nspname = 'public' and c.relkind = 'r' and not c.relrowsecurity`);
    expect(semRls.map((l) => l.relname)).toEqual([]);
  });

  it("o esquema em TypeScript tem as mesmas colunas da migração", async () => {
    const tabelas = (Object.values(esquema) as unknown[]).filter((x): x is PgTable => is(x, PgTable));
    const doBanco = await db.execute(sql`select table_name, column_name from information_schema.columns where table_schema = 'public'`);
    const noBanco = new Map<string, string[]>();
    for (const l of doBanco) noBanco.set(l.table_name as string, [...(noBanco.get(l.table_name as string) ?? []), l.column_name as string].sort());
    expect([...noBanco.keys()].sort()).toEqual(tabelas.map(getTableName).sort());
    for (const tabela of tabelas) {
      expect(Object.values(getTableColumns(tabela)).map((c) => c.name).sort(), getTableName(tabela)).toEqual(noBanco.get(getTableName(tabela)));
    }
  });
});

describe("operador", () => {
  it("lê o processo e os dados da própria OM", async () => {
    await como(operadorA, async (tx) => {
      expect(await tx.select().from(esquema.processo).where(eq(esquema.processo.id, processoA))).toHaveLength(1);
      for (const [tabela] of filhas(processoA, operadorA)) expect(await tx.select().from(tabela), getTableName(tabela)).not.toHaveLength(0);
    });
  });

  it("de outra OM não lê nem altera o processo, e não grava dados nele", async () => {
    await como(operadorB, async (tx) => {
      expect(await tx.select().from(esquema.processo).where(eq(esquema.processo.id, processoA))).toEqual([]);
      const alterados = await tx.update(esquema.processo).set({ objeto: "invadido" }).where(eq(esquema.processo.id, processoA)).returning();
      expect(alterados).toEqual([]);
      for (const [tabela] of filhas(processoA, operadorA)) {
        expect(await tx.select().from(tabela), getTableName(tabela)).toEqual([]);
      }
    });
    // Apagar: ou o RLS esconde as linhas (nada apagado), ou o papel nem tem permissão (exportacao).
    for (const [tabela] of filhas(processoA, operadorA)) {
      const erro = await erroDoBanco(como(operadorB, async (tx) => expect(await tx.delete(tabela).returning()).toEqual([])));
      expect(["", "permission denied for table exportacao"], getTableName(tabela)).toContain(erro);
    }
    await como(operadorA, async (tx) => {
      for (const [tabela] of filhas(processoA, operadorA)) expect(await tx.select().from(tabela), getTableName(tabela)).not.toHaveLength(0);
    });
    for (const [tabela, valores] of filhas(processoA, operadorB)) {
      await expect(como(operadorB, (tx) => tx.insert(tabela).values({ ...valores, pergunta: "CK-X-11", numero: 2 } as never)), getTableName(tabela)).rejects.toThrow();
    }
  });

  it("não cria processo em outra OM nem em nome de outro usuário", async () => {
    await expect(como(operadorB, (tx) => novoProcesso(tx, omA, operadorB))).rejects.toThrow();
    await expect(como(operadorA, (tx) => novoProcesso(tx, omA, administradorA))).rejects.toThrow();
  });

  it("não apaga processo", async () => {
    await expect(como(operadorA, (tx) => tx.delete(esquema.processo).where(eq(esquema.processo.id, processoA)))).rejects.toThrow();
  });

  it("vê só a própria linha de usuário e não muda o próprio perfil; tira a marca de senha provisória pela função", async () => {
    await como(operadorA, async (tx) => {
      expect((await tx.select().from(esquema.usuario)).map((u) => u.id)).toEqual([operadorA]);
      expect(await tx.update(esquema.usuario).set({ perfil: "ADMINISTRADOR" }).where(eq(esquema.usuario.id, operadorA)).returning()).toEqual([]);
      await tx.execute(sql`select public.concluir_troca_de_senha()`);
    });
    const [linha] = await db.select().from(esquema.usuario).where(eq(esquema.usuario.id, operadorA));
    expect(linha.perfil).toBe("OPERADOR");
    expect(linha.senhaProvisoria).toBe(false);
  });

  it("usuário desativado não vê nada", async () => {
    await como(inativoA, async (tx) => {
      expect(await tx.select().from(esquema.processo)).toEqual([]);
      expect(await tx.select().from(esquema.om)).toEqual([]);
    });
  });
});

describe("administrador da TI", () => {
  it("não abre processos (decisão 0012)", async () => {
    await como(administradorA, async (tx) => {
      expect(await tx.select().from(esquema.processo)).toEqual([]);
      for (const [tabela] of filhas(processoA, operadorA)) expect(await tx.select().from(tabela), getTableName(tabela)).toEqual([]);
    });
    await expect(como(administradorA, (tx) => novoProcesso(tx, omA, administradorA))).rejects.toThrow();
  });

  it("vê e administra só os usuários da própria OM", async () => {
    await como(administradorA, async (tx) => {
      const ids = (await tx.select().from(esquema.usuario)).map((u) => u.id);
      expect(ids.sort()).toEqual([operadorA, administradorA, inativoA].sort());
      expect(await tx.update(esquema.usuario).set({ ativo: false }).where(eq(esquema.usuario.id, operadorB)).returning()).toEqual([]);
      expect(await tx.update(esquema.usuario).set({ senhaProvisoria: true }).where(eq(esquema.usuario.id, inativoA)).returning()).toHaveLength(1);
    });
  });
});

describe("auditoria", () => {
  it("cada um inclui em nome próprio, na própria OM", async () => {
    await como(operadorA, (tx) => tx.insert(esquema.auditoria).values({ usuarioId: operadorA, omId: omA, processoId: processoA, acao: "TESTE" }));
    await expect(como(operadorA, (tx) => tx.insert(esquema.auditoria).values({ usuarioId: administradorA, omId: omA, acao: "TESTE" }))).rejects.toThrow();
    await expect(como(operadorB, (tx) => tx.insert(esquema.auditoria).values({ usuarioId: operadorB, omId: omA, acao: "TESTE" }))).rejects.toThrow();
  });

  it("o administrador lê a da OM; o operador, só as linhas de processo; outra OM, nada", async () => {
    await como(administradorA, (tx) => tx.insert(esquema.auditoria).values({ usuarioId: administradorA, omId: omA, acao: "TESTE_ADMIN" }));
    const acoes = async (u: string) => (await como(u, (tx) => tx.select().from(esquema.auditoria))).map((l) => l.acao);
    expect(await acoes(administradorA)).toEqual(expect.arrayContaining(["TESTE", "TESTE_ADMIN"]));
    expect(await acoes(operadorA)).toEqual(["TESTE"]);
    expect(await acoes(operadorB)).toEqual([]);
  });

  it("ninguém altera nem apaga, nem o dono do banco", async () => {
    await expect(como(administradorA, (tx) => tx.update(esquema.auditoria).set({ acao: "X" }))).rejects.toThrow();
    expect(await erroDoBanco(db.update(esquema.auditoria).set({ acao: "X" }))).toBe("a auditoria só aceita inclusão");
    expect(await erroDoBanco(db.delete(esquema.auditoria))).toBe("a auditoria só aceita inclusão");
    expect(await erroDoBanco(db.execute(sql`truncate public.auditoria cascade`))).toBe("a auditoria só aceita inclusão");
  });
});

describe("anon", () => {
  it("não lê nenhuma tabela", async () => {
    for (const nome of ["om", "usuario", "processo", "resposta_checklist", "revisao_confirmada", "complemento_operador", "item", "resposta_wizard", "exportacao", "auditoria"]) {
      const erro = await erroDoBanco(
        db.transaction(async (tx) => {
          await tx.execute(sql`set local role anon`);
          await tx.execute(sql.raw(`select * from public.${nome}`));
        }),
      );
      expect(erro, nome).toBe(`permission denied for table ${nome}`);
    }
  });
});
