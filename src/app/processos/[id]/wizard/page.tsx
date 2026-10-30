import Link from "next/link";
import { Icone, type NomeDoIcone } from "../../../componentes/icones.tsx";
import { Aviso, Codigo, Selo, TituloDeSecao, type TipoDeEstado, classesDoBotao } from "../../../componentes/ui.tsx";
import { Suspense } from "react";
import { abrirProcesso } from "@/dados/acesso-processo.ts";
import { carregarPacote } from "@/dados/pacote.ts";
import { minutaDoProcesso, pendenciasDaMinuta } from "@/dados/processos.ts";
import { type EstadoDaPergunta, type PerguntaDoWizard, camposDaMinuta, perguntasDoWizard, proximaPendente, textoDoCampo } from "@/dados/wizard.ts";
import type { Valor } from "@/motor/pacote/avaliador.ts";
import { textoDoValor } from "@/motor/montagem/formatos.ts";
import { Carregando } from "../../../componentes/cabecalho.tsx";
import { legivel, nomeDaPergunta } from "../../../componentes/rotulos.ts";
import { CabecalhoDoProcesso } from "../processo.tsx";
import { irParaMinuta, limparPergunta, responderPergunta, salvarCampo } from "./acoes.ts";
import { AceitarSugestao, FormularioCampo, FormularioPergunta } from "./formularios.tsx";

/** Tela do wizard (passo 9): uma pergunta por vez, com o estado de cada uma, e os dados que a minuta ainda pede. */
export default function TelaDoWizard(props: PageProps<"/processos/[id]/wizard">) {
  return (
    <Suspense fallback={<Carregando />}>
      <Conteudo {...props} />
    </Suspense>
  );
}

const ESTADOS: Record<EstadoDaPergunta, [TipoDeEstado, string]> = {
  respondida: ["ok", "Respondida"],
  checklist: ["ok", "Veio do checklist"],
  calculada: ["calculada", "Calculada pelos itens"],
  decisao_pendente: ["juridica", "Decisão jurídica pendente"],
  pendente: ["pendente", "Sem resposta"],
};

const ICONE_DO_ESTADO: Record<TipoDeEstado, NomeDoIcone> = {
  ok: "ok",
  calculada: "calculada",
  juridica: "juridica",
  pendente: "pendente",
  trava: "trava",
  atencao: "atencao",
  padrao: "padrao",
  neutro: "documento",
  vazio: "vazio",
};

function EstadoDaPerguntaRotulo({ estado }: { estado: EstadoDaPergunta }) {
  const [tipo, texto] = ESTADOS[estado];
  return <Selo tipo={tipo}>{texto}</Selo>;
}

const lista = (v: Valor): string[] => (v === null || v === undefined ? [] : Array.isArray(v) ? v.map((x) => String(x)) : [String(v)]);
const mostrar = (v: Valor) => lista(v).map(legivelSeCodigo).join(", ");
function legivelSeCodigo(s: string) {
  return /^[A-Z][A-Z0-9_]+$/.test(s) ? legivel(s) : s;
}

async function Conteudo({ params, searchParams }: PageProps<"/processos/[id]/wizard">) {
  const { id } = await params;
  const { p: escolhida } = await searchParams;
  const { usuario, p } = await abrirProcesso(id);
  const { pacote } = carregarPacote(p.processo.pacote, p.processo.pacoteHash);
  const minuta = minutaDoProcesso(p);
  const somenteLeitura = p.processo.situacao === "CONCLUIDO";
  const perguntas = perguntasDoWizard(pacote, minuta, p);
  const pendentes = perguntas.filter((x) => x.estado === "pendente" || x.estado === "decisao_pendente").length;
  const atualId = typeof escolhida === "string" && escolhida !== "fim" ? escolhida : escolhida === "fim" ? null : (proximaPendente(perguntas) ?? perguntas[0]?.id ?? null);
  const atual = perguntas.find((x) => x.id === atualId) ?? null;
  const { campos, doChecklist, daEquipe } = camposDaMinuta(pacote, minuta, p);
  const faltando = campos.filter((c) => c.trechos.length > 0);
  const informados = campos.filter((c) => c.trechos.length === 0);

  return (
    <>
      <CabecalhoDoProcesso usuario={usuario} p={p} pendencias={pendenciasDaMinuta(minuta)} atual="wizard" />
      <main className="mx-auto flex w-full max-w-[1400px] flex-col gap-8 px-4 py-6 md:px-6">
        <div className="grid gap-6 lg:grid-cols-[minmax(0,22rem)_minmax(0,1fr)]">
          <nav aria-label="Perguntas do wizard" className="flex flex-col border border-linha bg-folha lg:sticky lg:top-4 lg:self-start">
            <h2 className="flex items-baseline justify-between gap-2 border-b border-linha px-4 py-3 font-semibold">
              Perguntas <span className="text-sm font-normal text-tinta-2">{pendentes} sem resposta</span>
            </h2>
            <ol className="flex max-h-[70vh] flex-col overflow-y-auto">
              {perguntas.map((x) => {
                const [tipo, texto] = ESTADOS[x.estado];
                const ativa = x.id === atual?.id;
                return (
                  <li key={x.id}>
                    <Link
                      href={`/processos/${id}/wizard?p=${x.id}`}
                      aria-current={ativa ? "true" : undefined}
                      className={`flex min-h-11 gap-3 border-b border-l-[3px] border-b-linha px-3 py-2.5 no-underline transition-colors ${ativa ? "border-l-marca bg-selecao" : "border-l-transparent hover:bg-papel"}`}
                    >
                      <span className={`mt-0.5 ${tipo === "ok" ? "text-ok" : tipo === "juridica" ? "text-trava" : tipo === "pendente" ? "text-atencao" : "text-tinta-2"}`}>
                        <Icone nome={ICONE_DO_ESTADO[tipo]} tamanho={16} rotulo={texto} />
                      </span>
                      <span className="flex min-w-0 flex-col">
                        <span className="font-mono text-xs text-tinta-2">{x.id}</span>
                        <span className="line-clamp-2 text-sm">{x.pergunta}</span>
                      </span>
                    </Link>
                  </li>
                );
              })}
            </ol>
          </nav>

          <section className="flex flex-col gap-4 border border-linha bg-folha p-4 md:p-6" aria-live="polite">
            {atual ? <Pergunta id={id} x={atual} somenteLeitura={somenteLeitura} daEquipe={p.respostasWizard.some((r) => r.pergunta === atual.id)} /> : <Fim pendentes={pendentes} />}
          </section>
        </div>

        <section className="flex flex-col gap-4 border border-linha bg-folha p-4 md:p-5">
          <TituloDeSecao>Dados que a minuta pede ({faltando.length} faltando)</TituloDeSecao>
          <p className="text-sm text-tinta-2">Cada dado preenche uma lacuna da minuta. O que não for informado continua marcado como lacuna; o sistema não inventa valor, prazo nem percentual.</p>
          {faltando.length === 0 && <Aviso tipo="ok" titulo="Nenhum dado faltando nesta tela." />}
          <ul className="grid gap-4 md:grid-cols-2">
            {[...faltando, ...informados].map((c) => (
              <li key={c.id} className={`flex flex-col gap-2 border border-l-4 p-3 ${c.trechos.length ? "border-linha border-l-atencao bg-folha" : "border-linha border-l-ok bg-folha"}`}>
                <p>
                  <Codigo>{c.id}</Codigo> · {c.descricao}
                </p>
                <p className="text-sm">{c.trechos.length ? <Selo tipo="atencao">Falta em {c.trechos.join(", ")}</Selo> : <Selo tipo="ok">Informado: {textoDoValor(c.valor)}</Selo>}</p>
                {!somenteLeitura && (
                  <FormularioCampo acao={salvarCampo.bind(null, id)} c={{ id: c.id, descricao: c.descricao, validacao: c.validacao, codigos: c.codigos, forma: c.forma, valores: c.id === "VAR-001" && c.valor === null ? { valor: p.processo.numero } : textoDoCampo(c), falta: c.trechos.length > 0 }} />
                )}
              </li>
            ))}
          </ul>
          {doChecklist.length > 0 && (
            <Aviso tipo="atencao" titulo="Faltam dados que vêm do checklist">
              <ul className="list-disc pl-5 text-sm">
                {doChecklist.map((c) => (
                  <li key={c.id}>
                    <strong>{c.id}</strong> · {c.descricao} (em {c.trechos.join(", ")})
                  </li>
                ))}
              </ul>
              <Link href={`/processos/${id}/checklist`} className="flex min-h-11 w-fit items-center text-link underline">
                Corrigir ou completar na tela do checklist
              </Link>
            </Aviso>
          )}
          {daEquipe.length > 0 && (
            <p className="text-sm text-tinta-2">
              Trechos que a equipe completa no Compras.gov.br, sem dado ligado no sistema: {daEquipe.map((x) => `${x.trecho} (${x.marcador})`).join("; ")}.
            </p>
          )}
        </section>

        {!somenteLeitura && (
          <form action={irParaMinuta.bind(null, id)}>
            <button type="submit" className={classesDoBotao("principal")}>
              Seguir para a minuta <Icone nome="avancar" tamanho={16} />
            </button>
          </form>
        )}
      </main>
    </>
  );
}

function Pergunta({ id, x, somenteLeitura, daEquipe }: { id: string; x: PerguntaDoWizard; somenteLeitura: boolean; daEquipe: boolean }) {
  const respondida = x.valor !== null && x.valor !== undefined && x.valor !== "";
  return (
    <>
      <div className="flex flex-wrap items-center gap-3">
        <Codigo>{x.id}</Codigo>
        <EstadoDaPerguntaRotulo estado={x.estado} />
      </div>
      <h2 className="text-xl font-semibold leading-snug">{x.pergunta}</h2>
      {respondida && (
        <p className="border border-linha bg-papel p-3">
          Resposta atual: <strong>{mostrar(x.valor)}</strong>
          {x.doChecklist.length > 0 && <> (preenchida pelo checklist: {x.doChecklist.map(nomeDaPergunta).join(", ")}; a resposta da equipe vale sobre ela)</>}
        </p>
      )}
      {x.estado === "decisao_pendente" && <Aviso tipo="trava" titulo="Decisão jurídica: a equipe responde. O checklist, no máximo, sugere." />}
      {x.sugestoes.map((s) => (
        <div key={`${s.pergunta}-${String(s.valor)}`} className="flex flex-col gap-2 border border-l-4 border-linha border-l-padrao bg-padrao-fundo p-3 text-padrao">
          <p className="flex items-start gap-2">
            <Icone nome="sugestao" className="mt-0.5" />
            <span>
              Sugestão do checklist (<span title={s.pergunta}>{nomeDaPergunta(s.pergunta)}</span>): <strong>{mostrar(s.valor)}</strong>. É só sugestão; quem decide é a equipe.
            </span>
          </p>
          {!somenteLeitura && x.estado !== "calculada" && <AceitarSugestao acao={responderPergunta.bind(null, id)} pergunta={x.id} valor={lista(s.valor)} rotulo={mostrar(s.valor)} />}
        </div>
      ))}
      {x.estado === "calculada" ? (
        <p className="text-tinta-2">Calculada pelo motor a partir da tabela de itens. Para mudar, corrija os itens.</p>
      ) : (
        !somenteLeitura && (
          <FormularioPergunta
            key={x.id}
            acao={responderPergunta.bind(null, id)}
            limpar={limparPergunta.bind(null, id)}
            d={{
              id: x.id,
              tipo: x.tipo,
              opcoes: x.opcoes.map((o) => ({ codigo: o, rotulo: legivel(o) })),
              orientacao: x.orientacao,
              valor: lista(x.valor),
              daEquipe,
              justificativa: x.justificativa,
              justificativaAtual: x.justificativaAtual,
            }}
          />
        )
      )}
      {x.fundamento && <p className="text-sm text-tinta-2">Fundamento: {x.fundamento}</p>}
    </>
  );
}

function Fim({ pendentes }: { pendentes: number }) {
  return pendentes === 0 ? (
    <Aviso tipo="ok" titulo="Todas as perguntas que se aplicam a este processo estão respondidas.">Confira os dados abaixo e siga para a minuta.</Aviso>
  ) : (
    <Aviso tipo="atencao" titulo={`Ainda há ${pendentes} pergunta(s) sem resposta.`}>Escolha uma na lista.</Aviso>
  );
}
