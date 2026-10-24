/**
 * Prepara o Supabase local para os testes de tela: duas OMs fictícias e, em cada uma, um operador; na primeira,
 * também um administrador. Senhas conhecidas e definitivas (sem senha provisória), só para o ambiente de teste.
 * Uso: node --env-file-if-exists=.env.local testes/telas/preparar.ts
 */
import { createClient } from "@supabase/supabase-js";
import { eq } from "drizzle-orm";
import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";
import * as esquema from "../../src/dados/esquema.ts";
import { USUARIOS } from "./usuarios.ts";

const url = process.env.DATABASE_URL_MIGRACAO ?? process.env.DATABASE_URL ?? "";
if (!/@(127\.0\.0\.1|localhost)[:/]/.test(url)) throw new Error("preparar.ts só roda no Supabase local");
const supabase = createClient(process.env.SUPABASE_URL as string, process.env.SUPABASE_SECRET_KEY as string, { auth: { persistSession: false } });
const cliente = postgres(url, { prepare: false, max: 1 });
const db = drizzle(cliente, { schema: esquema });

for (const [chave, u] of Object.entries(USUARIOS)) {
  let [om] = await db.select().from(esquema.om).where(eq(esquema.om.uasg, u.om));
  if (!om) [om] = await db.insert(esquema.om).values({ uasg: u.om, nome: `OM Fictícia ${u.om}` }).returning();
  // Usuário que já existe (de uma preparação anterior, talvez com processos) fica; só volta à senha de teste.
  const existente = (await supabase.auth.admin.listUsers()).data.users.find((x) => x.email === u.email);
  const { data, error } = existente
    ? await supabase.auth.admin.updateUserById(existente.id, { password: u.senha })
    : await supabase.auth.admin.createUser({ email: u.email, password: u.senha, email_confirm: true });
  if (error) throw error;
  const linha = { omId: om.id, nome: `Usuário ${chave}`, email: u.email, perfil: u.perfil, ativo: true, senhaProvisoria: false };
  await db.insert(esquema.usuario).values({ id: data.user.id, ...linha }).onConflictDoUpdate({ target: esquema.usuario.id, set: linha });
}
console.log("Usuários de teste prontos.");
await cliente.end();
