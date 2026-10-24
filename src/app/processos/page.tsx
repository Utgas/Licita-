import { and, desc, eq, ilike, or } from "drizzle-orm";
import Link from "next/link";
import { Suspense } from "react";
import { exigirUsuario } from "@/auth/sessao.ts";
import { bancoDaAplicacao, comoUsuario } from "@/dados/conexao.ts";
import { SITUACOES as CODIGOS_DE_SITUACAO, processo } from "@/dados/esquema.ts";
import { carregarProcesso, dataDoExpurgo, minutaDoProcesso, pendenciasDaMinuta } from "@/dados/processos.ts";
import { Cabecalho, Carregando } from "../componentes/cabecalho.tsx";
import { Icone } from "../componentes/icones.tsx";
import { ETAPAS, SITUACOES, dataBR } from "../componentes/rotulos.ts";
import { CLASSE_DA_CAIXA, Selo, classesDoBotao } from "../componentes/ui.tsx";

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
      <main className="mx-auto flex w-full max-w-[1400px] flex-col gap-6 px-4 py-6 md:px-6">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Processos</h1>
            <p className="text-sm text-tinta-2">
              {linhas.length} {linhas.length === 1 ? "processo" : "processos"} da OM{busca || situacao ? " com esses filtros" : ""}
            </p>
          </div>
          <Link href="/processos/novo" className={classesDoBotao("principal")}>
            <Icone nome="mais" tamanho={16} />
            Novo processo
          </Link>
        </div>
        <form className="flex flex-wrap items-end gap-3 border border-linha bg-folha p-3" role="search">
          <label className="flex flex-col gap-1.5 text-sm font-medium">
            Buscar por número ou objeto
            <input name="q" defaultValue={busca} className={`${CLASSE_DA_CAIXA} md:w-80`} />
          </label>
          <label className="flex flex-col gap-1.5 text-sm font-medium">
            Situação
            <select name="situacao" defaultValue={situacao} className={`${CLASSE_DA_CAIXA} w-auto`}>
              <option value="">Todas</option>
              {Object.entries(SITUACOES).map(([codigo, rotulo]) => (
                <option key={codigo} value={codigo}>
                  {rotulo}
                </option>
              ))}
            </select>
          </label>
          <button type="submit" className={classesDoBotao("secundario")}>
            <Icone nome="busca" tamanho={16} />
            Filtrar
          </button>
        </form>
        {linhas.length === 0 ? (
          <p className="border border-dashed border-linha-forte bg-folha p-6 text-tinta-2">Nenhum processo{busca || situacao ? " com esses filtros" : ""}. Para começar, use “Novo processo”.</p>
        ) : (
          <div className="overflow-x-auto border border-linha bg-folha">
            <table className="w-full border-collapse text-left text-sm">
              <thead>
                <tr className="border-b border-linha-forte bg-papel text-xs uppercase tracking-wide text-tinta-2">
                  <th className="px-3 py-2.5 font-medium">Número</th>
                  <th className="px-3 py-2.5 font-medium">Objeto</th>
                  <th className="px-3 py-2.5 font-medium">Etapa</th>
                  <th className="px-3 py-2.5 font-medium">Situação</th>
                  <th className="px-3 py-2.5 font-medium">Pendências</th>
                </tr>
              </thead>
              <tbody>
                {linhas.map(({ p, pendencias }) => {
                  const indice = Math.max(0, ETAPAS.findIndex((e) => e.codigo === p.etapa));
                  const etapa = ETAPAS[indice];
                  const expurgo = dataDoExpurgo(p.concluidoEm);
                  return (
                    <tr key={p.id} className="border-b border-linha align-top last:border-b-0 hover:bg-papel">
                      <td className="px-3 py-3 whitespace-nowrap">
                        <Link href={`/processos/${p.id}/${etapa.caminho}`} className="font-mono underline decoration-linha-forte hover:decoration-tinta">
                          {p.numero}
                        </Link>
                      </td>
                      <td className="px-3 py-3">{p.objeto}</td>
                      <td className="px-3 py-3 whitespace-nowrap">
                        <span className="font-mono text-tinta-2">{indice + 1}/{ETAPAS.length}</span> {etapa.rotulo}
                      </td>
                      <td className="px-3 py-3">
                        {SITUACOES[p.situacao]}
                        {expurgo && <span className="block text-tinta-2">Será apagado em {dataBR(expurgo)}</span>}
                      </td>
                      <td className="px-3 py-3">{pendencias ? <ResumoDePendencias {...pendencias} /> : <span className="text-tinta-2">—</span>}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </>
  );
}

function ResumoDePendencias(p: { travas: number; perguntas: number; bloqueios: number; lacunas: number; bloqueada: boolean }) {
  if (!p.travas && !p.perguntas && !p.bloqueios && !p.lacunas) return <Selo tipo="ok">Sem pendências</Selo>;
  return (
    <span className="flex flex-wrap gap-1.5">
      {p.travas > 0 && <Selo tipo="trava">{p.travas} {p.travas === 1 ? "trava" : "travas"} do checklist</Selo>}
      {p.bloqueios > 0 && <Selo tipo="trava">{p.bloqueios} {p.bloqueios === 1 ? "bloqueio" : "bloqueios"}</Selo>}
      {p.perguntas > 0 && <Selo tipo="atencao">{p.perguntas} {p.perguntas === 1 ? "pergunta" : "perguntas"} do wizard</Selo>}
      {p.lacunas > 0 && <Selo tipo="atencao">{p.lacunas} {p.lacunas === 1 ? "lacuna" : "lacunas"}</Selo>}
    </span>
  );
}
