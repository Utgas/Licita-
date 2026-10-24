/**
 * Sessão do usuário (camada de acesso: toda tela e toda ação passam por aqui).
 *
 * O id vem do JWT conferido pelo Supabase Auth (getClaims); o perfil, a OM e a marca de senha provisória vêm da
 * tabela usuario, lida com o RLS do próprio usuário. Usuário desativado não tem sessão.
 */
import { eq } from "drizzle-orm";
import { cookies } from "next/headers";
import { connection } from "next/server";
import { redirect } from "next/navigation";
import { bancoDaAplicacao, comoUsuario } from "../dados/conexao.ts";
import { usuario } from "../dados/esquema.ts";
import { clienteDaSessao } from "./supabase.ts";

export type UsuarioLogado = {
  id: string;
  nome: string;
  email: string;
  perfil: "OPERADOR" | "ADMINISTRADOR";
  omId: string;
  senhaProvisoria: boolean;
};

/** Cliente do Supabase com os cookies da requisição. Em componente de tela não grava cookie (o proxy renova). */
export async function clienteDaRequisicao() {
  const loja = await cookies();
  return clienteDaSessao({
    getAll: () => loja.getAll(),
    setAll: (novos) => {
      try {
        for (const { name, value, options } of novos) loja.set(name, value, options);
      } catch {
        // Componente de tela não pode gravar cookie; a renovação acontece no proxy e nas ações.
      }
    },
  });
}

/** Usuário da sessão, ou null sem sessão válida ou com usuário desativado. */
export async function usuarioAtual(): Promise<UsuarioLogado | null> {
  // Sessão é sempre da requisição: nada aqui entra no pré-render (o Supabase lê a hora para conferir o JWT).
  await connection();
  const supabase = await clienteDaRequisicao();
  const { data, error } = await supabase.auth.getClaims();
  const id = data?.claims?.sub;
  if (error || !id) return null;
  return carregarUsuario(id);
}

/** Linha do usuário pelo id já conferido pelo Supabase Auth; null quando não existe ou está desativado. */
export async function carregarUsuario(id: string): Promise<UsuarioLogado | null> {
  const [linha] = await comoUsuario(bancoDaAplicacao(), id, (tx) => tx.select().from(usuario).where(eq(usuario.id, id)));
  if (!linha || !linha.ativo) return null;
  return { id: linha.id, nome: linha.nome, email: linha.email, perfil: linha.perfil, omId: linha.omId, senhaProvisoria: linha.senhaProvisoria };
}

/** Página inicial de cada perfil. */
export function inicioDoPerfil(perfil: UsuarioLogado["perfil"]): string {
  return perfil === "ADMINISTRADOR" ? "/admin" : "/processos";
}

/**
 * Exige sessão (e o perfil, quando indicado). Sem sessão, vai ao login; com senha provisória, à troca de senha;
 * com outro perfil, à página inicial dele.
 */
export async function exigirUsuario(perfil?: UsuarioLogado["perfil"], opcoes: { permitirSenhaProvisoria?: boolean } = {}): Promise<UsuarioLogado> {
  const u = await usuarioAtual();
  if (!u) redirect("/login");
  if (u.senhaProvisoria && !opcoes.permitirSenhaProvisoria) redirect("/trocar-senha");
  if (perfil && u.perfil !== perfil) redirect(inicioDoPerfil(u.perfil));
  return u;
}
