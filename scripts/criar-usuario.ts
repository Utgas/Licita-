/**
 * Cria um usuário com senha provisória (decisão 0012). Serve para o primeiro administrador da TI; os demais nascem
 * pela tela do administrador. Cria a OM pela UASG, se ainda não existir.
 *
 * Uso:
 *   npm run criar-usuario -- --uasg 999999 --om "OM Fictícia" --nome "Nome" --email pessoa@exemplo.invalid --perfil ADMINISTRADOR
 *
 * Lê do ambiente (ou do .env.local): SUPABASE_URL, SUPABASE_SECRET_KEY e DATABASE_URL_MIGRACAO (ou DATABASE_URL).
 * Imprime a senha provisória uma vez; ela não fica gravada em lugar nenhum além do Supabase Auth (com hash).
 */
import { parseArgs } from "node:util";
import { createClient } from "@supabase/supabase-js";
import { eq } from "drizzle-orm";
import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";
import { gerarSenhaProvisoria } from "../src/auth/senha.ts";
import * as esquema from "../src/dados/esquema.ts";

function exigir(nome: string, valor: string | undefined): string {
  if (!valor) {
    console.error(`Falta ${nome}. Veja o uso no início de scripts/criar-usuario.ts.`);
    process.exit(1);
  }
  return valor;
}

const { values: a } = parseArgs({
  options: { uasg: { type: "string" }, om: { type: "string" }, nome: { type: "string" }, email: { type: "string" }, perfil: { type: "string" } },
});
const uasg = exigir("--uasg", a.uasg);
const nome = exigir("--nome", a.nome);
const email = exigir("--email", a.email).trim().toLowerCase();
const perfil = exigir("--perfil", a.perfil) as (typeof esquema.PERFIS)[number];
if (!esquema.PERFIS.includes(perfil)) exigir("--perfil OPERADOR ou ADMINISTRADOR", undefined);

const supabase = createClient(exigir("SUPABASE_URL", process.env.SUPABASE_URL), exigir("SUPABASE_SECRET_KEY", process.env.SUPABASE_SECRET_KEY), {
  auth: { persistSession: false, autoRefreshToken: false },
});
const cliente = postgres(exigir("DATABASE_URL_MIGRACAO", process.env.DATABASE_URL_MIGRACAO ?? process.env.DATABASE_URL), { prepare: false, max: 1 });
const db = drizzle(cliente, { schema: esquema });

try {
  let [om] = await db.select().from(esquema.om).where(eq(esquema.om.uasg, uasg));
  if (!om) {
    [om] = await db.insert(esquema.om).values({ uasg, nome: exigir("--om (OM nova)", a.om) }).returning();
    console.log(`OM criada: ${om.nome} (UASG ${uasg}).`);
  }
  const senha = gerarSenhaProvisoria();
  const { data, error } = await supabase.auth.admin.createUser({ email, password: senha, email_confirm: true });
  if (error || !data.user) throw new Error(`Supabase Auth: ${error?.message}`);
  try {
    await db.transaction(async (tx) => {
      await tx.insert(esquema.usuario).values({ id: data.user.id, omId: om.id, nome, email, perfil, senhaProvisoria: true });
      await tx.insert(esquema.auditoria).values({ omId: om.id, acao: "USUARIO_CRIADO", detalhes: { usuario: data.user.id, perfil, origem: "script criar-usuario" } });
    });
  } catch (e) {
    await supabase.auth.admin.deleteUser(data.user.id);
    throw e;
  }
  console.log(`Usuário criado: ${nome} <${email}>, ${perfil}.`);
  console.log(`Senha provisória (aparece só agora; vale para o primeiro acesso): ${senha}`);
} catch (e) {
  console.error(`Não foi possível criar o usuário: ${(e as Error).message}`);
  process.exitCode = 1;
} finally {
  await cliente.end();
}
