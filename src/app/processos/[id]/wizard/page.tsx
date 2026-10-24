import Link from "next/link";
import { Suspense } from "react";
import { abrirProcesso } from "@/dados/acesso-processo.ts";
import { carregarPacote } from "@/dados/pacote.ts";
import { minutaDoProcesso, pendenciasDaMinuta } from "@/dados/processos.ts";
import { type EstadoDaPergunta, type PerguntaDoWizard, camposDaMinuta, perguntasDoWizard, proximaPendente, textoDoCampo } from "@/dados/wizard.ts";
import type { Valor } from "@/motor/pacote/avaliador.ts";
import { textoDoValor } from "@/motor/montagem/formatos.ts";
import { Carregando } from "../../../componentes/cabecalho.tsx";
import { legivel } from "../../../componentes/rotulos.ts";
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

const ESTADOS: Record<EstadoDaPergunta, [string, string]> = {
  respondida: ["border-green-800 bg-green-50 text-green-900", "✓ Respondida"],
  checklist: ["border-green-800 bg-green-50 text-green-900", "✓ Veio do checklist"],
  calculada: ["border-zinc-600 bg-zinc-50 text-zinc-900", "= Calculada pelos itens"],
  decisao_pendente: ["border-red-800 bg-red-50 text-red-900", "⛔ Decisão jurídica pendente"],
  pendente: ["border-amber-700 bg-amber-50 text-amber-950", "⚠ Sem resposta"],
};

function EstadoDaPerguntaRotulo({ estado }: { estado: EstadoDaPergunta }) {
  const [cor, texto] = ESTADOS[estado];
  return <span className={`inline-block shrink-0 rounded border px-2 py-0.5 text-sm font-medium ${cor}`}>{texto}</span>;
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
  const { pacote } = carregarPacote(p.processo.pacote);
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
      <main className="flex flex-col gap-8 p-6">
        <div className="grid gap-6 lg:grid-cols-[minmax(0,22rem)_minmax(0,1fr)]">
          <nav aria-label="Perguntas do wizard" className="flex flex-col gap-2">
            <h2 className="text-xl font-semibold">Perguntas ({pendentes} sem resposta)</h2>
            <ol className="flex max-h-[70vh] flex-col gap-1 overflow-y-auto pr-1">
              {perguntas.map((x) => (
                <li key={x.id}>
                  <Link
                    href={`/processos/${id}/wizard?p=${x.id}`}
                    aria-current={x.id === atual?.id ? "true" : undefined}
                    className={`flex min-h-11 flex-col gap-1 rounded border px-3 py-2 ${x.id === atual?.id ? "border-blue-800 bg-blue-50" : "border-zinc-300 bg-white hover:bg-zinc-50"}`}
                  >
                    <span className="flex flex-wrap items-center gap-2">
                      <strong>{x.id}</strong> <EstadoDaPerguntaRotulo estado={x.estado} />
                    </span>
                    <span className="text-sm text-zinc-800">{x.pergunta}</span>
                  </Link>
                </li>
              ))}
            </ol>
          </nav>

          <section className="flex flex-col gap-4" aria-live="polite">
            {atual ? <Pergunta id={id} x={atual} somenteLeitura={somenteLeitura} daEquipe={p.respostasWizard.some((r) => r.pergunta === atual.id)} /> : <Fim pendentes={pendentes} />}
          </section>
        </div>

        <section className="flex flex-col gap-4">
          <h2 className="text-xl font-semibold">Dados que a minuta pede ({faltando.length} faltando)</h2>
          <p className="text-sm text-zinc-700">Cada dado preenche uma lacuna da minuta. O que não for informado continua marcado como lacuna; o sistema não inventa valor, prazo nem percentual.</p>
          {faltando.length === 0 && <p className="rounded border border-green-800 bg-green-50 p-3 text-green-900">✓ Nenhum dado faltando nesta tela.</p>}
          <ul className="grid gap-4 md:grid-cols-2">
            {[...faltando, ...informados].map((c) => (
              <li key={c.id} className={`flex flex-col gap-2 rounded border p-3 ${c.trechos.length ? "border-amber-700 bg-amber-50" : "border-zinc-300"}`}>
                <p>
                  <strong>{c.id}</strong> · {c.descricao}
                </p>
                <p className="text-sm">{c.trechos.length ? `⚠ Falta em: ${c.trechos.join(", ")}` : `✓ Informado: ${textoDoValor(c.valor)}`}</p>
                {!somenteLeitura && (
                  <FormularioCampo acao={salvarCampo.bind(null, id)} c={{ id: c.id, descricao: c.descricao, validacao: c.validacao, codigos: c.codigos, forma: c.forma, valores: c.id === "VAR-001" && c.valor === null ? { valor: p.processo.numero } : textoDoCampo(c), falta: c.trechos.length > 0 }} />
                )}
              </li>
            ))}
          </ul>
          {doChecklist.length > 0 && (
            <div className="flex flex-col gap-2 rounded border border-amber-700 bg-amber-50 p-3">
              <h3 className="font-semibold">⚠ Faltam dados que vêm do checklist</h3>
              <ul className="list-disc pl-5 text-sm">
                {doChecklist.map((c) => (
                  <li key={c.id}>
                    <strong>{c.id}</strong> · {c.descricao} (em {c.trechos.join(", ")})
                  </li>
                ))}
              </ul>
              <Link href={`/processos/${id}/checklist`} className="flex min-h-11 items-center text-blue-800 underline">
                Corrigir ou completar na tela do checklist
              </Link>
            </div>
          )}
          {daEquipe.length > 0 && (
            <p className="text-sm text-zinc-800">
              Trechos que a equipe completa no Compras.gov.br, sem dado ligado no sistema: {daEquipe.map((x) => `${x.trecho} (${x.marcador})`).join("; ")}.
            </p>
          )}
        </section>

        {!somenteLeitura && (
          <form action={irParaMinuta.bind(null, id)}>
            <button type="submit" className="min-h-11 rounded bg-blue-800 px-4 font-medium text-white hover:bg-blue-900">
              Seguir para a minuta →
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
      <div className="flex flex-wrap items-center gap-2">
        <h2 className="text-xl font-semibold">{x.id}</h2>
        <EstadoDaPerguntaRotulo estado={x.estado} />
      </div>
      <p className="text-lg">{x.pergunta}</p>
      {respondida && (
        <p className="rounded border border-zinc-400 bg-white p-3">
          Resposta atual: <strong>{mostrar(x.valor)}</strong>
          {x.doChecklist.length > 0 && <> (preenchida pelo checklist: {x.doChecklist.join(", ")}; a resposta da equipe vale sobre ela)</>}
        </p>
      )}
      {x.estado === "decisao_pendente" && <p className="rounded border border-red-800 bg-red-50 p-3 text-red-900">⛔ Decisão jurídica: a equipe responde. O checklist, no máximo, sugere.</p>}
      {x.sugestoes.map((s) => (
        <div key={`${s.pergunta}-${String(s.valor)}`} className="flex flex-col gap-2 rounded border border-blue-800 bg-blue-50 p-3 text-blue-950">
          <p>
            💡 Sugestão do checklist ({s.pergunta}): <strong>{mostrar(s.valor)}</strong>. É só sugestão; quem decide é a equipe.
          </p>
          {!somenteLeitura && x.estado !== "calculada" && <AceitarSugestao acao={responderPergunta.bind(null, id)} pergunta={x.id} valor={lista(s.valor)} rotulo={mostrar(s.valor)} />}
        </div>
      ))}
      {x.estado === "calculada" ? (
        <p className="text-zinc-800">Calculada pelo motor a partir da tabela de itens. Para mudar, corrija os itens.</p>
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
      {x.fundamento && <p className="text-sm text-zinc-700">Fundamento: {x.fundamento}</p>}
    </>
  );
}

function Fim({ pendentes }: { pendentes: number }) {
  return pendentes === 0 ? (
    <p className="rounded border border-green-800 bg-green-50 p-3 text-green-900">✓ Todas as perguntas que se aplicam a este processo estão respondidas. Confira os dados abaixo e siga para a minuta.</p>
  ) : (
    <p className="rounded border border-amber-700 bg-amber-50 p-3 text-amber-950">⚠ Ainda há {pendentes} pergunta(s) sem resposta. Escolha uma na lista.</p>
  );
}
