/**
 * Clientes do Supabase Auth, só no servidor (decisões 0010 e 0012).
 *
 * O navegador não fala com o Supabase: a sessão fica num cookie httpOnly, que o servidor lê e renova. Nenhuma
 * variável tem o prefixo NEXT_PUBLIC_, então as chaves não vão para a página.
 */
import { type CookieMethodsServer, createServerClient } from "@supabase/ssr";
import { createClient } from "@supabase/supabase-js";

function variavel(nome: string): string {
  const valor = process.env[nome];
  if (!valor) throw new Error(`${nome} não definida`);
  return valor;
}

/**
 * Endereço do projeto Supabase só com a origem (https://<ref>.supabase.co). O painel do Supabase mostra também o
 * endereço da Data API, que termina em /rest/v1/; colado na variável, ele mandava o login para
 * /rest/v1/auth/v1/token (404) e todo login falhava. Aqui qualquer caminho é descartado.
 */
export function enderecoDoSupabase(valor = variavel("SUPABASE_URL")): string {
  try {
    return new URL(valor).origin;
  } catch {
    throw new Error("SUPABASE_URL não é um endereço válido (use https://<ref>.supabase.co)");
  }
}

export const OPCOES_DO_COOKIE = {
  httpOnly: true,
  secure: process.env.NODE_ENV === "production",
  sameSite: "lax" as const,
  path: "/",
};

/** Cliente com a sessão do usuário, lida e gravada pelos cookies que o chamador fornece. */
export function clienteDaSessao(cookies: CookieMethodsServer) {
  return createServerClient(enderecoDoSupabase(), variavel("SUPABASE_PUBLISHABLE_KEY"), {
    cookies,
    cookieOptions: OPCOES_DO_COOKIE,
  });
}

/**
 * Cliente com a chave secreta: cria usuários e troca senhas (administrador da TI e script criar-usuario). Ignora o
 * RLS; só é chamado depois de conferir que quem pede é administrador.
 */
export function clienteAdministrativo() {
  return createClient(enderecoDoSupabase(), variavel("SUPABASE_SECRET_KEY"), {
    auth: { persistSession: false, autoRefreshToken: false },
  });
}
