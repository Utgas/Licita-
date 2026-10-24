/** Cabeçalho das telas logadas: espaço do brasão (marcador neutro), nome do usuário, troca de senha e saída. */
import Link from "next/link";
import type { UsuarioLogado } from "@/auth/sessao.ts";

export function Cabecalho({ usuario }: { usuario: UsuarioLogado }) {
  return (
    <header className="flex flex-wrap items-center justify-between gap-3 border-b border-zinc-300 px-4 py-2">
      <div className="flex items-center gap-3">
        <div aria-hidden className="size-10 rounded border border-dashed border-zinc-500" title="Espaço do brasão" />
        <span className="text-lg font-semibold">Licita+</span>
      </div>
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <span>
          {usuario.nome} ({usuario.perfil === "ADMINISTRADOR" ? "Administrador da TI" : "Operador"})
        </span>
        <Link href="/trocar-senha" className="flex min-h-11 items-center px-2 text-blue-800 underline">
          Alterar minha senha
        </Link>
        <form action="/sair" method="post">
          <button type="submit" className="min-h-11 rounded border border-zinc-600 px-3 hover:bg-zinc-100">
            Sair
          </button>
        </form>
      </div>
    </header>
  );
}

export function Carregando() {
  return <p className="p-6 text-zinc-700">Carregando…</p>;
}
