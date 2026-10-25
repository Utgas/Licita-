/**
 * Moldura das páginas de leitura abertas a todos (política de privacidade e termos de uso; decisão 0017): barra com
 * o nome do sistema, título, versão e o texto em coluna de leitura.
 */
import Link from "next/link";
import type { ReactNode } from "react";
import { Marca } from "./marca.tsx";

export function PaginaDeDocumento({ titulo, versao, children }: { titulo: string; versao: string; children: ReactNode }) {
  return (
    <>
      <header className="bg-tinta text-folha">
        <div className="mx-auto flex w-full max-w-[1400px] items-center px-4 md:px-6">
          <Link href="/" className="flex min-h-12 items-center gap-3 no-underline">
            <Marca tamanho={28} />
            <span className="text-[1.05rem] font-semibold tracking-tight">Licita+</span>
          </Link>
        </div>
      </header>
      <main id="conteudo" className="mx-auto flex w-full max-w-3xl flex-col gap-6 px-4 py-8 leading-relaxed md:px-6">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-semibold tracking-tight">{titulo}</h1>
          <p className="text-sm text-tinta-2">{versao}</p>
        </div>
        {children}
      </main>
    </>
  );
}

export function Secao({ id, titulo, children }: { id?: string; titulo: string; children: ReactNode }) {
  return (
    <section id={id} aria-labelledby={id ? `${id}-titulo` : undefined} className="flex scroll-mt-4 flex-col gap-3">
      <h2 id={id ? `${id}-titulo` : undefined} className="border-b border-linha pb-2 text-lg font-semibold">
        {titulo}
      </h2>
      {children}
    </section>
  );
}

/** Dado que só a OM pode informar: aparece marcado, nunca inventado (CLAUDE.md, regra 5). */
export function Lacuna({ children }: { children: ReactNode }) {
  return <mark className="rounded-sm bg-atencao-marca px-1 text-tinta">[A preencher pela OM: {children}]</mark>;
}

export function Tabela({ titulo, colunas, linhas }: { titulo: string; colunas: string[]; linhas: ReactNode[][] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse border border-linha bg-folha text-left text-sm">
        <caption className="sr-only">{titulo}</caption>
        <thead>
          <tr className="border-b border-linha-forte bg-papel text-xs uppercase tracking-wide text-tinta-2">
            {colunas.map((c) => (
              <th key={c} scope="col" className="px-3 py-2.5 font-medium">
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {linhas.map((l, i) => (
            <tr key={i} className="border-b border-linha align-top">
              {l.map((c, j) => (
                <td key={j} className="px-3 py-2">
                  {c}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
