/** Cabeçalho das telas de um processo: número, objeto, situação, abas das etapas e pendências do motor. */
import Link from "next/link";
import type { UsuarioLogado } from "@/auth/sessao.ts";
import { type Pendencias, type ProcessoCompleto, dataDoExpurgo } from "@/dados/processos.ts";
import { Cabecalho } from "../../componentes/cabecalho.tsx";
import { ETAPAS, MODALIDADES, SITUACOES, dataBR } from "../../componentes/rotulos.ts";

export function CabecalhoDoProcesso(props: { usuario: UsuarioLogado; p: ProcessoCompleto; pendencias: Pendencias; atual: (typeof ETAPAS)[number]["caminho"] }) {
  const { processo } = props.p;
  const expurgo = dataDoExpurgo(processo.concluidoEm);
  const { travas, perguntas, bloqueios, lacunas } = props.pendencias;
  return (
    <>
      <Cabecalho usuario={props.usuario} />
      <div className="flex flex-col gap-3 border-b border-zinc-300 bg-zinc-50 px-4 py-3">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <div>
            <Link href="/processos" className="text-sm text-blue-800 underline">
              ← Processos
            </Link>
            <h1 className="text-xl font-semibold">
              {processo.numero} · {processo.objeto}
            </h1>
            <p className="text-sm text-zinc-700">
              {MODALIDADES[processo.modalidade] ?? processo.modalidade} · {processo.registroPrecos ? "Registro de preços" : "Sem registro de preços"} · {SITUACOES[processo.situacao]}
              {expurgo && ` · Será apagado em ${dataBR(expurgo)}`}
            </p>
          </div>
          <p className="text-sm" aria-label="Pendências">
            <Contagem n={travas} rotulo="trava(s)" cor="vermelho" /> <Contagem n={perguntas} rotulo="pergunta(s) do wizard" cor="amarelo" />{" "}
            <Contagem n={bloqueios} rotulo="bloqueio(s)" cor="vermelho" /> <Contagem n={lacunas} rotulo="lacuna(s)" cor="amarelo" />
          </p>
        </div>
        <nav aria-label="Etapas do processo" className="flex flex-wrap gap-2">
          {ETAPAS.map((e, i) => (
            <Link
              key={e.codigo}
              href={`/processos/${processo.id}/${e.caminho}`}
              aria-current={e.caminho === props.atual ? "page" : undefined}
              className={`flex min-h-11 items-center rounded border px-3 ${e.caminho === props.atual ? "border-blue-800 bg-blue-800 text-white" : "border-zinc-500 bg-white hover:bg-zinc-100"}`}
            >
              {i + 1}. {e.rotulo}
            </Link>
          ))}
        </nav>
        {processo.situacao === "CONCLUIDO" && <p className="rounded border border-zinc-600 bg-white p-2">Processo concluído: só leitura.</p>}
      </div>
    </>
  );
}

const CORES = { vermelho: "border-red-800 bg-red-50 text-red-900", amarelo: "border-amber-700 bg-amber-50 text-amber-950" };

function Contagem({ n, rotulo, cor }: { n: number; rotulo: string; cor: keyof typeof CORES }) {
  if (n === 0) return null;
  return <span className={`mr-1 inline-block rounded border px-2 py-1 ${CORES[cor]}`}>{n} {rotulo}</span>;
}

/** Estado de revisão com cor e texto (passo 7): trava, destaque ou ok. */
export function Estado({ estado }: { estado: "trava" | "destaque" | "ok" | "vazio" }) {
  const e = {
    trava: ["border-red-800 bg-red-50 text-red-900", "⛔ Trava"],
    destaque: ["border-amber-700 bg-amber-50 text-amber-950", "⚠ Atenção"],
    ok: ["border-green-800 bg-green-50 text-green-900", "✓ OK"],
    vazio: ["border-zinc-500 bg-white text-zinc-800", "Sem resposta"],
  }[estado];
  return <span className={`inline-block shrink-0 rounded border px-2 py-0.5 text-sm font-medium ${e[0]}`}>{e[1]}</span>;
}
