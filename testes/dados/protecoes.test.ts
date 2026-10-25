/**
 * Proteções da decisão 0017, no Supabase local (npm run test:banco): limite de tentativas de login e pedidos do
 * titular (LGPD, art. 18), com o RLS e as permissões por coluna.
 */
import { eq, sql } from "drizzle-orm";
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { marcador } from "../../src/auth/tentativas.ts";
import { type Transacao, comoUsuario, exigeTls, semSessao } from "../../src/dados/conexao.ts";
import * as esquema from "../../src/dados/esquema.ts";
import { abrirBancoDeTeste, criarOm, criarUsuario } from "./banco-de-teste.ts";

const { db, fechar } = abrirBancoDeTeste();
afterAll(fechar);

const como = <T>(usuario: string, fazer: (tx: Transacao) => Promise<T>) => comoUsuario(db, usuario, fazer);
const CHAVE = "chave-ficticia-de-teste";
const chaves = (sufixo: string) => ({ email: marcador("EMAIL", `teste-${sufixo}@exemplo.invalid`, CHAVE), ip: marcador("IP", `198.51.100.${sufixo.length}`, CHAVE) });
const bloqueado = async (c: { email: string; ip: string }) =>
  (await semSessao(db, (tx) => tx.execute<{ b: boolean }>(sql`select privado.login_bloqueado(${c.email}, ${c.ip}) as b`)))[0].b;
const falha = (c: { email: string; ip: string }) => semSessao(db, (tx) => tx.execute(sql`select privado.registrar_falha_login(${c.email}, ${c.ip})`));

describe("tentativas de login", () => {
  it("o marcador é fixo para o mesmo valor, muda com a chave e não contém o e-mail", () => {
    const m = marcador("EMAIL", "teste@exemplo.invalid", CHAVE);
    expect(m).toMatch(/^[0-9a-f]{64}$/);
    expect(marcador("EMAIL", "teste@exemplo.invalid", CHAVE)).toBe(m);
    expect(marcador("EMAIL", "teste@exemplo.invalid", "outra")).not.toBe(m);
    expect(marcador("IP", "teste@exemplo.invalid", CHAVE)).not.toBe(m);
  });

  it("bloqueia o e-mail na 5ª falha e libera depois do login certo", async () => {
    const c = chaves(crypto.randomUUID().slice(0, 8));
    for (let i = 0; i < 4; i++) await falha(c);
    expect(await bloqueado(c)).toBe(false);
    await falha(c);
    expect(await bloqueado(c)).toBe(true);
    await semSessao(db, (tx) => tx.execute(sql`select privado.limpar_falhas_login(${c.email})`));
    expect(await bloqueado(c)).toBe(false);
  });

  it("bloqueia o IP que erra 20 vezes, mesmo trocando de e-mail", async () => {
    const ip = marcador("IP", crypto.randomUUID(), CHAVE);
    for (let i = 0; i < 20; i++) await falha({ email: marcador("EMAIL", crypto.randomUUID(), CHAVE), ip });
    expect(await bloqueado({ email: marcador("EMAIL", crypto.randomUUID(), CHAVE), ip })).toBe(true);
  });

  it("a tabela não é lida nem gravada direto, nem por usuário logado", async () => {
    await expect(semSessao(db, (tx) => tx.execute(sql`select * from privado.tentativa_login`))).rejects.toThrow();
    await expect(semSessao(db, (tx) => tx.execute(sql`delete from privado.tentativa_login`))).rejects.toThrow();
  });

  it("sem sessão, nenhuma tabela do sistema aparece", async () => {
    await semSessao(db, async (tx) => {
      expect(await tx.select().from(esquema.usuario)).toEqual([]);
      expect(await tx.select().from(esquema.processo)).toEqual([]);
      expect(await tx.select().from(esquema.auditoria)).toEqual([]);
    });
  });
});

describe("conexão", () => {
  it("exige TLS fora da máquina local, salvo quando a URL já define o sslmode", () => {
    expect(exigeTls("postgresql://u:s@aws-1-sa-east-1.pooler.supabase.com:6543/postgres")).toBe(true);
    expect(exigeTls("postgresql://u:s@aws-1-sa-east-1.pooler.supabase.com:6543/postgres?sslmode=verify-full")).toBe(false);
    expect(exigeTls("postgresql://postgres:postgres@127.0.0.1:54322/postgres")).toBe(false);
  });
});

describe("pedidos do titular", () => {
  let omA: string;
  let omB: string;
  let operadorA: string;
  let administradorA: string;
  let administradorB: string;
  let pedido: number;

  beforeAll(async () => {
    omA = await criarOm(db);
    omB = await criarOm(db);
    operadorA = await criarUsuario(db, omA, "OPERADOR");
    administradorA = await criarUsuario(db, omA, "ADMINISTRADOR");
    administradorB = await criarUsuario(db, omB, "ADMINISTRADOR");
    [{ id: pedido }] = await como(operadorA, (tx) =>
      tx.insert(esquema.solicitacaoTitular).values({ usuarioId: operadorA, omId: omA, tipo: "CORRECAO", descricao: "Pedido fictício." }).returning({ id: esquema.solicitacaoTitular.id }),
    );
  });

  it("o usuário só pede em nome próprio e não escreve a resposta", async () => {
    await expect(como(operadorA, (tx) => tx.insert(esquema.solicitacaoTitular).values({ usuarioId: administradorA, omId: omA, tipo: "OUTRO", descricao: "x" }))).rejects.toThrow();
    const [forjado] = await como(operadorA, (tx) =>
      tx.insert(esquema.solicitacaoTitular).values({ usuarioId: operadorA, omId: omA, tipo: "OUTRO", descricao: "x", situacao: "RESPONDIDA", resposta: "feito", respondidaPor: operadorA, criadaEm: "2000-01-01T00:00:00Z" }).returning(),
    );
    expect([forjado.situacao, forjado.resposta, forjado.respondidaPor, forjado.criadaEm.startsWith("2000")]).toEqual(["ABERTA", null, null, false]);
    await expect(como(operadorA, (tx) => tx.update(esquema.solicitacaoTitular).set({ descricao: "mudado" }).where(eq(esquema.solicitacaoTitular.id, pedido)))).rejects.toThrow();
  });

  it("o administrador da mesma OM responde; o de outra OM nem vê", async () => {
    expect(await como(administradorB, (tx) => tx.select().from(esquema.solicitacaoTitular).where(eq(esquema.solicitacaoTitular.id, pedido)))).toEqual([]);
    const resposta = { situacao: "RESPONDIDA" as const, resposta: "Corrigido.", respondidaEm: sql`now()`, respondidaPor: administradorB };
    expect(await como(administradorB, (tx) => tx.update(esquema.solicitacaoTitular).set(resposta).where(eq(esquema.solicitacaoTitular.id, pedido)).returning())).toEqual([]);
    const feitas = await como(administradorA, (tx) =>
      tx.update(esquema.solicitacaoTitular).set({ ...resposta, respondidaPor: administradorA }).where(eq(esquema.solicitacaoTitular.id, pedido)).returning(),
    );
    expect(feitas).toHaveLength(1);
    const [lido] = await como(operadorA, (tx) => tx.select().from(esquema.solicitacaoTitular).where(eq(esquema.solicitacaoTitular.id, pedido)));
    expect(lido.resposta).toBe("Corrigido.");
  });

  it("ninguém apaga pedido", async () => {
    await expect(como(administradorA, (tx) => tx.delete(esquema.solicitacaoTitular))).rejects.toThrow();
  });

  it("o operador lê as próprias linhas de login na auditoria, mas não as dos outros", async () => {
    await como(operadorA, (tx) => tx.insert(esquema.auditoria).values({ usuarioId: operadorA, omId: omA, acao: "LOGIN" }));
    await como(administradorA, (tx) => tx.insert(esquema.auditoria).values({ usuarioId: administradorA, omId: omA, acao: "LOGIN" }));
    const linhas = await como(operadorA, (tx) => tx.select().from(esquema.auditoria).where(eq(esquema.auditoria.omId, omA)));
    expect(linhas.map((l) => l.usuarioId)).toEqual([operadorA]);
  });
});
