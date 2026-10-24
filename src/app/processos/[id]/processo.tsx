/**
 * Topo das telas de um processo: número, objeto e situação; trilho das cinco etapas com a posição atual, as etapas
 * já percorridas e as pendências de cada uma (dados do motor).
 */
import Link from "next/link";
import type { UsuarioLogado } from "@/auth/sessao.ts";
import { type Pendencias, type ProcessoCompleto, dataDoExpurgo } from "@/dados/processos.ts";
import { Cabecalho } from "../../componentes/cabecalho.tsx";
import { Icone } from "../../componentes/icones.tsx";
import { ETAPAS, MODALIDADES, SITUACOES, dataBR } from "../../componentes/rotulos.ts";
import { Selo, type TipoDeEstado } from "../../componentes/ui.tsx";

type Caminho = (typeof ETAPAS)[number]["caminho"];

export function CabecalhoDoProcesso(props: { usuario: UsuarioLogado; p: ProcessoCompleto; pendencias: Pendencias; atual: Caminho }) {
  const { processo } = props.p;
  const expurgo = dataDoExpurgo(processo.concluidoEm);
  const { travas, perguntas, bloqueios, lacunas } = props.pendencias;
  const alcancada = ETAPAS.findIndex((e) => e.codigo === processo.etapa);
  const pendenciaDaEtapa: Partial<Record<Caminho, [number, string, TipoDeEstado]>> = {
    checklist: [travas, travas === 1 ? "trava" : "travas", "trava"],
    wizard: [perguntas, perguntas === 1 ? "pergunta" : "perguntas", "atencao"],
    revisao: [bloqueios, bloqueios === 1 ? "bloqueio" : "bloqueios", "trava"],
  };
  return (
    <>
      <Cabecalho usuario={props.usuario} />
      <div className="border-b border-linha bg-folha">
        <div className="mx-auto flex w-full max-w-[1400px] flex-col gap-4 px-4 pt-4 md:px-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="flex min-w-0 flex-col gap-1">
              <Link href="/processos" className="flex w-fit items-center gap-1.5 text-sm text-tinta-2 underline decoration-linha-forte hover:text-tinta">
                <Icone nome="voltar" tamanho={14} />
                Processos
              </Link>
              <p className="font-mono text-sm text-tinta-2">{processo.numero}</p>
              <h1 className="text-xl font-semibold leading-snug md:text-2xl">{processo.objeto}</h1>
              <p className="text-sm text-tinta-2">
                {MODALIDADES[processo.modalidade] ?? processo.modalidade} · {processo.registroPrecos ? "Registro de preços" : "Sem registro de preços"} · {SITUACOES[processo.situacao]}
                {expurgo && ` · será apagado em ${dataBR(expurgo)}`}
              </p>
            </div>
            <div className="flex flex-wrap gap-2" aria-label="Pendências">
              {travas > 0 && <Selo tipo="trava">{travas} {travas === 1 ? "trava" : "travas"}</Selo>}
              {bloqueios > 0 && <Selo tipo="trava">{bloqueios} {bloqueios === 1 ? "bloqueio" : "bloqueios"}</Selo>}
              {perguntas > 0 && <Selo tipo="atencao">{perguntas} {perguntas === 1 ? "pergunta" : "perguntas"} do wizard</Selo>}
              {lacunas > 0 && <Selo tipo="atencao">{lacunas} {lacunas === 1 ? "lacuna" : "lacunas"}</Selo>}
              {!travas && !bloqueios && !perguntas && !lacunas && <Selo tipo="ok">Sem pendências</Selo>}
            </div>
          </div>
          <nav aria-label="Etapas do processo">
            <ol className="flex overflow-x-auto">
              {ETAPAS.map((e, i) => {
                const atual = e.caminho === props.atual;
                const feita = i < alcancada && !atual;
                const pend = pendenciaDaEtapa[e.caminho];
                return (
                  <li key={e.codigo} className="flex-1">
                    <Link
                      href={`/processos/${processo.id}/${e.caminho}`}
                      aria-current={atual ? "step" : undefined}
                      className={`flex min-h-12 min-w-36 items-center gap-2.5 border-b-[3px] px-3 py-2 no-underline transition-colors ${atual ? "border-marca font-semibold text-tinta" : "border-transparent text-tinta-2 hover:border-linha-forte hover:text-tinta"}`}
                    >
                      <span className={`flex size-6 shrink-0 items-center justify-center border font-mono text-xs ${atual ? "border-tinta bg-tinta text-folha" : feita ? "border-tinta-2 text-tinta" : "border-linha-forte"}`}>
                        {feita ? <Icone nome="ok" tamanho={14} rotulo="percorrida" /> : i + 1}
                      </span>
                      <span>{e.rotulo}</span>
                      {pend && pend[0] > 0 && (
                        <span className={`ml-auto inline-flex items-center gap-1 font-mono text-xs ${pend[2] === "trava" ? "text-trava" : "text-atencao"}`} title={`${pend[0]} ${pend[1]}`}>
                          <Icone nome={pend[2] === "trava" ? "trava" : "atencao"} tamanho={13} />
                          {pend[0]}
                        </span>
                      )}
                    </Link>
                  </li>
                );
              })}
            </ol>
          </nav>
        </div>
      </div>
      {processo.situacao === "CONCLUIDO" && (
        <div className="border-b border-linha bg-papel-escuro">
          <p className="mx-auto flex w-full max-w-[1400px] items-center gap-2 px-4 py-2 text-sm md:px-6">
            <Icone nome="trava" tamanho={15} />
            Processo concluído: só leitura.
          </p>
        </div>
      )}
    </>
  );
}

/** Estado de revisão de uma resposta do checklist (passo 7): trava, destaque, ok ou sem resposta. */
export function Estado({ estado }: { estado: "trava" | "destaque" | "ok" | "vazio" }) {
  if (estado === "trava") return <Selo tipo="trava">Trava</Selo>;
  if (estado === "destaque") return <Selo tipo="atencao">Atenção</Selo>;
  if (estado === "ok") return <Selo tipo="ok">OK</Selo>;
  return <Selo tipo="vazio">Sem resposta</Selo>;
}
