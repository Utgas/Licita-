import { and, desc, eq, ilike, or } from "drizzle-orm";
import Link from "next/link";
import { Suspense } from "react";
import { exigirUsuario } from "@/auth/sessao.ts";
import { bancoDaAplicacao, comoUsuario } from "@/dados/conexao.ts";
import { SITUACOES as CODIGOS_DE_SITUACAO, processo } from "@/dados/esquema.ts";
import { carregarProcesso, dataDoExpurgo, minutaDoProcesso, pendenciasDaMinuta } from "@/dados/processos.ts";
import { Cabecalho, Carregando } from "../componentes/cabecalho.tsx";
import { ETAPAS, SITUACOES, dataBR } from "../componentes/rotulos.ts";

/** Painel do operador (passo 5): processos da OM com etapa, pendências, busca e filtros. */
export default function Processos({ searchParams }: PageProps<"/processos">) {
  return (
    <Suspense fallback={<Carregando />}>
      <Conteudo searchParams={searchParams} />
    </Suspense>
  );
}

async function Conteudo({ searchParams }: Pick<PageProps<"/processos">, "searchParams">) {
  const usuario = await exigirUsuario("OPERADOR");
  const filtros = await searchParams;
  const busca = typeof filtros.q === "string" ? filtros.q.trim() : "";
  const situacao = typeof filtros.situacao === "string" && (CODIGOS_DE_SITUACAO as readonly string[]).includes(filtros.situacao) ? (filtros.situacao as (typeof CODIGOS_DE_SITUACAO)[number]) : "";
  const linhas = await comoUsuario(bancoDaAplicacao(), usuario.id, async (tx) => {
    const condicoes = [
      busca ? or(ilike(processo.numero, `%${busca}%`), ilike(processo.objeto, `%${busca}%`)) : undefined,
      situacao ? eq(processo.situacao, situacao) : undefined,
    ].filter(Boolean);
    const lista = await tx.select().from(processo).where(and(...condicoes)).orderBy(desc(processo.atualizadoEm));
    return Promise.all(
      lista.map(async (p) => {
        if (p.situacao === "CONCLUIDO") return { p, pendencias: null };
        const completo = await carregarProcesso(tx, p.id);
        return { p, pendencias: completo ? pendenciasDaMinuta(minutaDoProcesso(completo)) : null };
      }),
    );
  });
  return (
    <>
      <Cabecalho usuario={usuario} />
      <main className="flex flex-col gap-6 p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-2xl font-semibold">Processos</h1>
          <Link href="/processos/novo" className="flex min-h-11 items-center rounded bg-blue-800 px-4 font-medium text-white hover:bg-blue-900">
            Novo processo
          </Link>
        </div>
        <form className="flex flex-wrap items-end gap-3" role="search">
          <label className="flex flex-col gap-1 text-sm font-medium">
            Buscar por número ou objeto
            <input name="q" defaultValue={busca} className="min-h-11 w-72 rounded border border-zinc-500 px-3 font-normal" />
          </label>
          <label className="flex flex-col gap-1 text-sm font-medium">
            Situação
            <select name="situacao" defaultValue={situacao} className="min-h-11 rounded border border-zinc-500 px-3 font-normal">
              <option value="">Todas</option>
              {Object.entries(SITUACOES).map(([codigo, rotulo]) => (
                <option key={codigo} value={codigo}>
                  {rotulo}
                </option>
              ))}
            </select>
          </label>
          <button type="submit" className="min-h-11 rounded border border-zinc-600 px-4 hover:bg-zinc-100">
            Filtrar
          </button>
        </form>
        {linhas.length === 0 ? (
          <p className="text-zinc-700">Nenhum processo{busca || situacao ? " com esses filtros" : ""}.</p>
        ) : (
          <table className="w-full border-collapse text-left text-sm">
            <thead>
              <tr className="border-b border-zinc-400">
                <th className="p-2">Número</th>
                <th className="p-2">Objeto</th>
                <th className="p-2">Etapa</th>
                <th className="p-2">Situação</th>
                <th className="p-2">Pendências</th>
              </tr>
            </thead>
            <tbody>
              {linhas.map(({ p, pendencias }) => {
                const etapa = ETAPAS.find((e) => e.codigo === p.etapa) ?? ETAPAS[0];
                const expurgo = dataDoExpurgo(p.concluidoEm);
                return (
                  <tr key={p.id} className="border-b border-zinc-200 align-top">
                    <td className="p-2">
                      <Link href={`/processos/${p.id}/${etapa.caminho}`} className="text-blue-800 underline">
                        {p.numero}
                      </Link>
                    </td>
                    <td className="p-2">{p.objeto}</td>
                    <td className="p-2">{etapa.rotulo}</td>
                    <td className="p-2">
                      {SITUACOES[p.situacao]}
                      {expurgo && <span className="block text-zinc-700">Será apagado em {dataBR(expurgo)}</span>}
                    </td>
                    <td className="p-2">{pendencias ? <ResumoDePendencias {...pendencias} /> : "—"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </main>
    </>
  );
}

function ResumoDePendencias(p: { travas: number; perguntas: number; bloqueios: number; lacunas: number; bloqueada: boolean }) {
  const partes = [
    p.travas && `${p.travas} trava(s) do checklist`,
    p.perguntas && `${p.perguntas} pergunta(s) do wizard`,
    p.bloqueios && `${p.bloqueios} bloqueio(s)`,
    p.lacunas && `${p.lacunas} lacuna(s)`,
  ].filter(Boolean);
  return partes.length ? <span>{partes.join(" · ")}</span> : <span className="text-green-800">✓ Sem pendências</span>;
}
