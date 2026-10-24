/**
 * Antes de cada página: renova a sessão do Supabase (cookie httpOnly) e manda ao login quem não tem sessão. É só a
 * primeira barreira; cada página e cada ação confere a sessão de novo (src/auth/sessao.ts) e o banco confere pelo
 * RLS. A volta depois do login leva à página em que o usuário estava; o que ele salvou continua no banco.
 */
import { type NextRequest, NextResponse } from "next/server";
import { clienteDaSessao } from "./auth/supabase.ts";

const PUBLICAS = ["/login", "/esqueci-senha", "/sair"];

export async function proxy(request: NextRequest) {
  let resposta = NextResponse.next({ request });
  const supabase = clienteDaSessao({
    getAll: () => request.cookies.getAll(),
    setAll: (novos) => {
      for (const { name, value } of novos) request.cookies.set(name, value);
      resposta = NextResponse.next({ request });
      for (const { name, value, options } of novos) resposta.cookies.set(name, value, options);
    },
  });
  const { data } = await supabase.auth.getClaims();
  const caminho = request.nextUrl.pathname;
  if (!data?.claims?.sub && !PUBLICAS.includes(caminho)) {
    const login = new URL("/login", request.url);
    if (caminho !== "/") login.searchParams.set("volta", caminho + request.nextUrl.search);
    return NextResponse.redirect(login);
  }
  return resposta;
}

export const config = {
  // Tudo, menos os arquivos do próprio Next e o ícone.
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
