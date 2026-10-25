/**
 * Limite de tentativas de login (decisão 0017): 5 falhas do mesmo e-mail ou 20 do mesmo IP em 15 minutos bloqueiam
 * novas tentativas até a janela passar. O banco guarda só marcadores (HMAC com a chave secreta do servidor), nunca o
 * e-mail ou o IP, e apaga cada linha depois de 24 horas.
 */
import { createHmac } from "node:crypto";
import { sql } from "drizzle-orm";
import { headers } from "next/headers";
import { bancoDaAplicacao, semSessao } from "../dados/conexao.ts";

export type Chaves = { email: string; ip: string };

/** Marcador do e-mail ou do IP: quem lê o banco não recupera o valor a partir dele. */
export function marcador(tipo: "EMAIL" | "IP", valor: string, chave = process.env.SUPABASE_SECRET_KEY): string {
  if (!chave) throw new Error("SUPABASE_SECRET_KEY não definida");
  return createHmac("sha256", chave).update(`${tipo}:${valor}`).digest("hex");
}

/** IP de quem pede: na Vercel, o primeiro de x-forwarded-for (a própria Vercel escreve o cabeçalho). */
async function ipDaRequisicao(): Promise<string> {
  const h = await headers();
  return h.get("x-forwarded-for")?.split(",")[0].trim() || h.get("x-real-ip") || "desconhecido";
}

export async function chavesDaTentativa(email: string): Promise<Chaves> {
  return { email: marcador("EMAIL", email), ip: marcador("IP", await ipDaRequisicao()) };
}

export async function loginBloqueado(c: Chaves): Promise<boolean> {
  const [linha] = await semSessao(bancoDaAplicacao(), (tx) => tx.execute<{ bloqueado: boolean }>(sql`select privado.login_bloqueado(${c.email}, ${c.ip}) as bloqueado`));
  return linha.bloqueado;
}

export async function registrarFalha(c: Chaves): Promise<void> {
  await semSessao(bancoDaAplicacao(), (tx) => tx.execute(sql`select privado.registrar_falha_login(${c.email}, ${c.ip})`));
}

/** Login certo zera a conta do e-mail; a do IP continua (protege contra quem testa vários e-mails). */
export async function limparFalhas(c: Chaves): Promise<void> {
  await semSessao(bancoDaAplicacao(), (tx) => tx.execute(sql`select privado.limpar_falhas_login(${c.email})`));
}
