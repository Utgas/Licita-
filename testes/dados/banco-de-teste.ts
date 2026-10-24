/**
 * Banco de teste: o Supabase local (npx supabase start), nunca o de desenvolvimento. Os dados são criados com nomes
 * fictícios e aleatórios a cada execução; a auditoria não se apaga (só aceita inclusão), por isso nada depende de
 * o banco estar vazio.
 */
import { randomUUID } from "node:crypto";
import { sql } from "drizzle-orm";
import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";
import type { Banco } from "../../src/dados/conexao.ts";
import * as esquema from "../../src/dados/esquema.ts";

export const URL_DE_TESTE = process.env.DATABASE_URL_TESTE ?? "postgresql://postgres:postgres@127.0.0.1:54322/postgres";

export function abrirBancoDeTeste(): { db: Banco; fechar: () => Promise<void> } {
  if (!/@(127\.0\.0\.1|localhost)[:/]/.test(URL_DE_TESTE)) throw new Error("os testes de banco só rodam no Supabase local");
  const cliente = postgres(URL_DE_TESTE, { prepare: false, max: 3, onnotice: () => {} });
  return { db: drizzle(cliente, { schema: esquema }), fechar: () => cliente.end() };
}

export type Perfil = (typeof esquema.PERFIS)[number];

/** OM fictícia. */
export async function criarOm(db: Banco): Promise<string> {
  const [linha] = await db
    .insert(esquema.om)
    .values({ uasg: `9${randomUUID().slice(0, 5)}`, nome: `OM Fictícia ${randomUUID().slice(0, 4)}` })
    .returning({ id: esquema.om.id });
  return linha.id;
}

/** Usuário fictício no Auth e na tabela usuario. */
export async function criarUsuario(db: Banco, omId: string, perfil: Perfil, ativo = true): Promise<string> {
  const id = randomUUID();
  const email = `teste-${id.slice(0, 8)}@exemplo.invalid`;
  await db.execute(sql`insert into auth.users (id, email, aud, role) values (${id}, ${email}, 'authenticated', 'authenticated')`);
  await db.insert(esquema.usuario).values({ id, omId, nome: "Usuário Fictício", email, perfil, ativo });
  return id;
}
