/**
 * Cabeçalho das telas logadas: barra escura e fina, espaço do brasão (marcador neutro: o brasão só entra depois de
 * autorizado), nome do sistema, navegação do perfil, usuário, troca de senha e saída.
 */
import Link from "next/link";
import type { UsuarioLogado } from "@/auth/sessao.ts";
import { Icone } from "./icones.tsx";

const NAVEGACAO = {
  OPERADOR: [{ href: "/processos", rotulo: "Processos" }],
  ADMINISTRADOR: [
    { href: "/admin", rotulo: "Usuários" },
    { href: "/admin/auditoria", rotulo: "Auditoria" },
  ],
} as const;

export function Cabecalho({ usuario }: { usuario: UsuarioLogado }) {
  return (
    <header className="bg-tinta text-folha">
      <div className="mx-auto flex w-full max-w-[1400px] flex-wrap items-center justify-between gap-x-6 gap-y-1 px-4 md:px-6">
        <div className="flex items-center gap-5">
          <Link href="/" className="flex min-h-12 items-center gap-3 no-underline">
            <span aria-hidden title="Espaço do brasão" className="size-7 border border-dashed border-folha/50" />
            <span className="text-[1.05rem] font-semibold tracking-tight">Licita+</span>
          </Link>
          <nav aria-label="Principal" className="flex items-center">
            {NAVEGACAO[usuario.perfil].map((n) => (
              <Link key={n.href} href={n.href} className="flex min-h-12 items-center border-b-2 border-transparent px-3 text-sm text-folha/85 no-underline transition-colors hover:border-folha/60 hover:text-folha">
                {n.rotulo}
              </Link>
            ))}
          </nav>
        </div>
        <div className="flex flex-wrap items-center gap-1 text-sm">
          <span className="hidden pr-2 text-folha/80 sm:inline">
            {usuario.nome} · {usuario.perfil === "ADMINISTRADOR" ? "Administrador da TI" : "Operador"}
          </span>
          <Link href="/trocar-senha" className="flex min-h-11 items-center px-2 text-folha underline decoration-folha/40 hover:decoration-folha">
            Alterar minha senha
          </Link>
          <form action="/sair" method="post">
            <button type="submit" className="flex min-h-11 items-center gap-2 px-2 text-folha transition-colors hover:bg-folha/10">
              <Icone nome="sair" tamanho={16} />
              Sair
            </button>
          </form>
        </div>
      </div>
    </header>
  );
}

export function Carregando() {
  return <p className="p-6 text-tinta-2">Carregando…</p>;
}

/** Área de conteúdo com largura máxima e margens iguais em todas as telas. */
export function Conteudo({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <main className={`mx-auto flex w-full max-w-[1400px] flex-col gap-8 px-4 py-6 md:px-6 ${className}`}>{children}</main>;
}
