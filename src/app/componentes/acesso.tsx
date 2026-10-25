/**
 * Moldura das telas sem sessão (login e "esqueci minha senha"): à esquerda, o que o sistema faz, como o sumário de
 * um documento; à direita, o formulário. Em tela estreita, só o formulário com o nome do sistema.
 */
import type { ReactNode } from "react";
import { Marca } from "./marca.tsx";
import { ETAPAS } from "./rotulos.ts";

export function PaginaDeAcesso({ titulo, children }: { titulo: string; children: ReactNode }) {
  return (
    <div className="grid flex-1 md:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
      <aside className="hidden flex-col justify-between bg-tinta p-10 text-folha md:flex">
        <div className="flex items-center gap-3">
          <Marca tamanho={36} />
          <span className="text-xl font-semibold tracking-tight">Licita+</span>
        </div>
        <div className="flex max-w-sm flex-col gap-6">
          <p className="text-lg leading-relaxed text-folha/90">Minuta de Termo de Referência no modelo da AGU, montada a partir do checklist técnico e das decisões da equipe.</p>
          <ol className="flex flex-col border-t border-folha/20">
            {ETAPAS.map((e, i) => (
              <li key={e.codigo} className="flex items-baseline gap-4 border-b border-folha/20 py-2.5 text-sm">
                <span className="font-mono text-folha/60">{String(i + 1).padStart(2, "0")}</span>
                <span className="text-folha/90">{e.rotulo}</span>
              </li>
            ))}
          </ol>
        </div>
        <p className="text-xs text-folha/60">Acesso restrito à equipe de licitação. Toda ação fica registrada na auditoria.</p>
      </aside>
      <main id="conteudo" className="flex flex-col justify-center px-6 py-10 md:px-16">
        <div className="mx-auto flex w-full max-w-sm flex-col gap-6">
          <p className="flex items-center gap-3 text-lg font-semibold md:hidden">
            <Marca tamanho={28} />
            Licita+
          </p>
          <h1 className="text-2xl font-semibold tracking-tight">{titulo}</h1>
          {children}
        </div>
      </main>
    </div>
  );
}
