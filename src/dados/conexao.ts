/**
 * Conexão do servidor com o banco (Drizzle, pelo pooler do Supabase).
 *
 * Toda consulta passa por `comoUsuario`: numa transação, assume o papel `authenticated` com o id do usuário logado,
 * e o RLS decide o que ele vê. O id vem da sessão já verificada pelo Supabase Auth (src/auth/), nunca do navegador.
 * Em produção a aplicação entra como `licita_app`, que só pode assumir `authenticated` (decisão 0016); nos testes
 * locais, como `postgres`.
 */
import { sql } from "drizzle-orm";
import { type PostgresJsDatabase, drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";
import * as esquema from "./esquema.ts";

export type Banco = PostgresJsDatabase<typeof esquema>;
export type Transacao = Parameters<Parameters<Banco["transaction"]>[0]>[0];

let banco: Banco | undefined;

/** Banco da aplicação (DATABASE_URL, Transaction pooler). Só no servidor. */
export function bancoDaAplicacao(url = process.env.DATABASE_URL): Banco {
  if (banco) return banco;
  if (!url) throw new Error("DATABASE_URL não definida");
  // prepare: false porque o pooler em modo transação não guarda comandos preparados entre conexões.
  banco = drizzle(postgres(url, { prepare: false, max: 5 }), { schema: esquema });
  return banco;
}

/** Roda `fazer` com o papel authenticated e o id do usuário: o RLS vale para tudo que estiver dentro. */
export async function comoUsuario<T>(db: Banco, usuarioId: string, fazer: (tx: Transacao) => Promise<T>): Promise<T> {
  return db.transaction(async (tx) => {
    const claims = JSON.stringify({ sub: usuarioId, role: "authenticated" });
    await tx.execute(sql`select set_config('request.jwt.claims', ${claims}, true), set_config('role', 'authenticated', true)`);
    return fazer(tx);
  });
}
