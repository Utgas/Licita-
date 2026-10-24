import Link from "next/link";
import { Suspense } from "react";
import { abrirProcesso } from "@/dados/acesso-processo.ts";
import { carregarPacote } from "@/dados/pacote.ts";
import { minutaDoProcesso, pendenciasDaMinuta } from "@/dados/processos.ts";
import type { LinhaM11 } from "@/motor/pacote/esquema.ts";
import { Carregando } from "../../../componentes/cabecalho.tsx";
import { CabecalhoDoProcesso, Estado } from "../processo.tsx";
import { apagarResposta, confirmarRevisao, enviarWord, irParaItens, salvarComplemento, salvarResposta } from "./acoes.ts";
import { Complemento, type DadosDaPergunta, EnviarWord, FormularioResposta, Trava } from "./formularios.tsx";

/** Tela do checklist (passo 7): leitura do Word, revisão (trava, destaque, ok), correção e complementos. */
export default function TelaDoChecklist(props: PageProps<"/processos/[id]/checklist">) {
  return (
    <Suspense fallback={<Carregando />}>
      <Conteudo {...props} />
    </Suspense>
  );
}

const opcoes = (l: LinhaM11) =>
  l.opcoes
    .split(/;\s*/)
    .map((o) => o.trim())
    .filter((o) => o && !o.startsWith("campos:") && o !== "números dos itens da tabela");

function dadosDaPergunta(l: LinhaM11): DadosDaPergunta {
  return {
    pergunta: l.id,
    tipo: l.tipo_resposta,
    opcoes: opcoes(l),
    campos: /campos:\s*(.+)$/.exec(l.opcoes)?.[1].split(/;\s*/) ?? [],
    porItem: l.por_item === "S",
    temNumero: /número seguido de '/.test(l.leitura),
  };
}

function mostrar(valor: unknown): string {
  if (valor === null || valor === undefined) return "";
  if (Array.isArray(valor)) return valor.map((v) => (typeof v === "object" ? Object.entries(v as object).map(([k, x]) => `${k}: ${x}`).join(", ") : String(v))).join("; ");
  return String(valor);
}

async function Conteudo({ params, searchParams }: PageProps<"/processos/[id]/checklist">) {
  const { id } = await params;
  const { ver } = await searchParams;
  const todas = ver === "todas";
  const { usuario, p } = await abrirProcesso(id);
  const { pacote } = carregarPacote(p.processo.pacote);
  const minuta = minutaDoProcesso(p);
  const somenteLeitura = p.processo.situacao === "CONCLUIDO";

  const destaques = new Map(minuta.revisao.destaques.map((d) => [d.pergunta, d.motivos]));
  const travas = minuta.revisao.perguntasAoOperador;
  const comTrava = new Set(travas.map((t) => t.pergunta));
  const porPergunta = Map.groupBy(p.respostasChecklist, (r) => r.pergunta);
  const usados = new Set(p.processo.checklists);
  const linhas = pacote.matrizes.M11.filter((l) => usados.has(l.checklist as "CONSUMO" | "PERMANENTES"));
  const visiveis = todas ? linhas : linhas.filter((l) => destaques.has(l.id));
  const secoes = Map.groupBy(visiveis, (l) => `${l.checklist === "CONSUMO" ? "Consumo" : "Permanentes"} · ${l.secao}`);
  const m11 = new Map(pacote.matrizes.M11.map((l) => [l.id, l]));
  const complementos = minuta.complementosDoOperador.map((cid) => m11.get(cid) as LinhaM11);
  const valorDoComplemento = new Map(p.complementos.map((c) => [c.pergunta, c.valor]));

  const acaoResposta = salvarResposta.bind(null, id);
  const acaoApagar = apagarResposta.bind(null, id);

  return (
    <>
      <CabecalhoDoProcesso usuario={usuario} p={p} pendencias={pendenciasDaMinuta(minuta)} atual="checklist" />
      <main className="flex flex-col gap-8 p-6">
        {!somenteLeitura && (
          <section className="flex max-w-2xl flex-col gap-3">
            <h2 className="text-xl font-semibold">Enviar o checklist preenchido</h2>
            <p>
              Checklists deste processo: {p.processo.checklists.map((c) => (c === "CONSUMO" ? "consumo" : "permanentes")).join(" e ")}. Também é possível digitar ou corrigir as respostas abaixo, sem o Word.
            </p>
            <EnviarWord acao={enviarWord.bind(null, id)} />
          </section>
        )}

        <section className="flex flex-col gap-3">
          <h2 className="text-xl font-semibold">Travas ({travas.length})</h2>
          {travas.length === 0 ? (
            <p className="text-green-800">✓ Nenhuma trava: nenhuma dúvida da leitura muda a minuta.</p>
          ) : (
            <ul className="flex flex-col gap-3">
              {travas.map((t) => {
                const l = m11.get(t.pergunta) as LinhaM11;
                return (
                  <li key={`${t.pergunta}-${t.motivo}`} className="flex flex-col gap-2 rounded border-2 border-red-800 bg-red-50 p-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <Estado estado="trava" />
                      <strong>{t.pergunta}</strong> <span>{l.pergunta}</span>
                    </div>
                    <p>{t.texto}</p>
                    {!somenteLeitura && (
                      <Trava acaoResposta={acaoResposta} acaoConfirmar={confirmarRevisao.bind(null, id)} pergunta={t.pergunta} motivo={t.motivo} opcoes={l.tipo_resposta === "SIM_NAO" || l.tipo_resposta === "UNICA" ? opcoes(l) : []}
                        outro={t.motivo === "OUTRO_ILEGIVEL" ? opcoes(l).find((o) => o.toLowerCase().startsWith("outro")) : undefined}
                      />
                    )}
                  </li>
                );
              })}
            </ul>
          )}
        </section>

        <section className="flex flex-col gap-3">
          <h2 className="text-xl font-semibold">Complementos do operador ({complementos.length})</h2>
          <p className="text-zinc-700">Dados que o checklist distribuído não pede e que a minuta usa (decisão 0009).</p>
          {complementos.length === 0 && <p>Nenhum complemento se aplica a este processo agora.</p>}
          {complementos.map((l) => (
            <div key={l.id} className="flex flex-col gap-2 rounded border border-zinc-400 p-3">
              <div className="flex flex-wrap items-center gap-2">
                <Estado estado={valorDoComplemento.has(l.id) ? "ok" : "destaque"} />
                <strong>{l.id}</strong> <span>{l.pergunta}</span>
              </div>
              {!somenteLeitura && (
                <Complemento acao={salvarComplemento.bind(null, id)} pergunta={l.id} tipo={l.tipo_resposta} opcoes={opcoes(l)} itens={l.por_item === "S" ? p.itens.map((i) => i.numero) : null} valor={valorDoComplemento.get(l.id) ?? null} />
              )}
            </div>
          ))}
        </section>

        <section className="flex flex-col gap-3">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-xl font-semibold">{todas ? "Todas as perguntas" : "Perguntas que pedem atenção"}</h2>
            <Link href={todas ? "?" : "?ver=todas"} className="flex min-h-11 items-center text-blue-800 underline">
              {todas ? "Mostrar só as que pedem atenção" : "Mostrar todas as perguntas (para digitar ou corrigir)"}
            </Link>
          </div>
          {visiveis.length === 0 && <p className="text-green-800">✓ Nenhuma pergunta pede atenção.</p>}
          {[...secoes].map(([secao, ls]) => (
            <div key={secao} className="flex flex-col gap-2">
              <h3 className="font-semibold">{secao}</h3>
              <ul className="flex flex-col gap-2">
                {ls.map((l) => {
                  const respostas = porPergunta.get(l.id) ?? [];
                  const motivos = destaques.get(l.id) ?? [];
                  const estado = comTrava.has(l.id) ? "trava" : motivos.length ? "destaque" : respostas.length ? "ok" : "vazio";
                  return (
                    <li key={l.id} className="flex flex-col gap-2 border-b border-zinc-200 pb-2">
                      <div className="flex flex-wrap items-start gap-2">
                        <Estado estado={estado} />
                        <span>
                          <strong>{l.numero}.</strong> {l.pergunta}
                        </span>
                      </div>
                      {respostas.map((r) => (
                        <p key={r.id} className="pl-2 text-sm">
                          {r.itens.length ? `Itens ${r.itens.join(", ")}: ` : ""}
                          <strong>{mostrar(r.valor) || "—"}</strong>
                          {r.texto && <span> · {r.texto}</span>}
                          {r.numero !== null && <span> · número: {r.numero}</span>}
                          <span className="text-zinc-700"> ({r.origem === "LEITURA_WORD" ? "lida do Word" : "digitada"})</span>
                        </p>
                      ))}
                      {motivos.map((m) => (
                        <p key={m.motivo} className="pl-2 text-sm text-amber-950">
                          ⚠ {m.texto}
                        </p>
                      ))}
                      {!somenteLeitura && (
                        <details className="pl-2">
                          <summary className="flex min-h-11 cursor-pointer items-center text-blue-800 underline">{respostas.length ? "Corrigir" : "Responder"}</summary>
                          <div className="flex flex-col gap-2">
                            {respostas.map((r) => (
                              <FormularioResposta key={r.id} acao={acaoResposta} apagar={acaoApagar} p={dadosDaPergunta(l)} linha={{ id: r.id, valor: r.valor, texto: r.texto, numero: r.numero, itens: r.itens }} />
                            ))}
                            {(respostas.length === 0 || l.por_item === "S") && <FormularioResposta acao={acaoResposta} p={dadosDaPergunta(l)} />}
                          </div>
                        </details>
                      )}
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </section>

        {!somenteLeitura && (
          <form action={irParaItens.bind(null, id)}>
            <button type="submit" className="min-h-11 rounded bg-blue-800 px-4 font-medium text-white hover:bg-blue-900">
              Seguir para os itens →
            </button>
          </form>
        )}
      </main>
    </>
  );
}
