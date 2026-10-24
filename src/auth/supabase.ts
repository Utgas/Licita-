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

export const OPCOES_DO_COOKIE = {
  httpOnly: true,
  secure: process.env.NODE_ENV === "production",
  sameSite: "lax" as const,
  path: "/",
};

/** Cliente com a sessão do usuário, lida e gravada pelos cookies que o chamador fornece. */
export function clienteDaSessao(cookies: CookieMethodsServer) {
  return createServerClient(variavel("SUPABASE_URL"), variavel("SUPABASE_PUBLISHABLE_KEY"), {
    cookies,
    cookieOptions: OPCOES_DO_COOKIE,
  });
}

/**
 * Cliente com a chave secreta: cria usuários e troca senhas (administrador da TI e script criar-usuario). Ignora o
 * RLS; só é chamado depois de conferir que quem pede é administrador.
 */
export function clienteAdministrativo() {
  return createClient(variavel("SUPABASE_URL"), variavel("SUPABASE_SECRET_KEY"), {
    auth: { persistSession: false, autoRefreshToken: false },
  });
}
