/**
 * Saída por POST comum (não por ação do React): a resposta é um redirecionamento que recarrega a página inteira. Assim
 * o navegador descarta as telas guardadas da sessão (o Next mantém a tela anterior escondida para navegar rápido), e
 * quem usar o mesmo computador depois não as encontra.
 */
import { type NextRequest, NextResponse } from "next/server";
import { registrar } from "@/auditoria/registrar.ts";
import { clienteDaSessao } from "@/auth/supabase.ts";
import { carregarUsuario } from "@/auth/sessao.ts";
import { bancoDaAplicacao, comoUsuario } from "@/dados/conexao.ts";

export async function POST(request: NextRequest) {
  const resposta = NextResponse.redirect(new URL("/login", request.url), 303);
  const supabase = clienteDaSessao({
    getAll: () => request.cookies.getAll(),
    setAll: (novos) => {
      for (const { name, value, options } of novos) resposta.cookies.set(name, value, options);
    },
  });
  const { data } = await supabase.auth.getClaims();
  const u = data?.claims?.sub ? await carregarUsuario(data.claims.sub) : null;
  if (u) await comoUsuario(bancoDaAplicacao(), u.id, (tx) => registrar(tx, { usuarioId: u.id, omId: u.omId, acao: "SAIDA" }));
  await supabase.auth.signOut();
  return resposta;
}
