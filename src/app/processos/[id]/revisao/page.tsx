import Link from "next/link";
import { Suspense } from "react";
import { abrirProcesso } from "@/dados/acesso-processo.ts";
import { carregarPacote } from "@/dados/pacote.ts";
import { minutaDoProcesso, pendenciasDaMinuta } from "@/dados/processos.ts";
import { ehTabela, linhasDaTabela, partesDoTexto, secoesDaMinuta, tabelaNaoMontada } from "@/exportacao/secoes.ts";
import type { TrechoDaMinuta } from "@/motor/minuta.ts";
import { textoDoValor } from "@/motor/montagem/formatos.ts";
import type { Pacote } from "@/motor/pacote/esquema.ts";
import { Carregando } from "../../../componentes/cabecalho.tsx";
import { CabecalhoDoProcesso } from "../processo.tsx";
import { irParaExportar } from "./acoes.ts";

/**
 * Tela da minuta (passo 10): o texto vem do motor e não se edita aqui. Lacuna em amarelo, valor padrão em azul;
 * cada trecho abre a origem (bloco, motivo, respostas, notas e normas). Para mudar o texto, corrija respostas e dados.
 */
export default function TelaDaMinuta(props: PageProps<"/processos/[id]/revisao">) {
  return (
    <Suspense fallback={<Carregando />}>
      <Conteudo {...props} />
    </Suspense>
  );
}

async function Conteudo({ params }: PageProps<"/processos/[id]/revisao">) {
  const { id } = await params;
  const { usuario, p } = await abrirProcesso(id);
  const { pacote } = carregarPacote(p.processo.pacote);
  const minuta = minutaDoProcesso(p);
  const somenteLeitura = p.processo.situacao === "CONCLUIDO";
  const m10 = new Map(pacote.matrizes.M10.map((l) => [l.id, l]));
  const bloqueios = minuta.validacoes.disparadas.filter((v) => v.tipo === "BLOQUEIO");
  const alertas = minuta.validacoes.disparadas.filter((v) => v.tipo !== "BLOQUEIO");
  const { perguntasAoOperador } = minuta.revisao;
  const semResposta = minuta.perguntasSemResposta;
  const travada = minuta.bloqueada;

  return (
    <>
      <CabecalhoDoProcesso usuario={usuario} p={p} pendencias={pendenciasDaMinuta(minuta)} atual="revisao" />
      <main className="flex flex-col gap-6 p-6">
        <section aria-label="Bloqueios" className={`flex flex-col gap-2 rounded border p-4 ${travada ? "border-red-800 bg-red-50 text-red-950" : "border-green-800 bg-green-50 text-green-950"}`}>
          <h2 className="text-lg font-semibold">{travada ? "⛔ A minuta tem travas: a exportação fica bloqueada até resolvê-las" : "✓ Sem travas: a minuta pode ser exportada"}</h2>
          {bloqueios.length > 0 && (
            <ul className="list-disc pl-5">
              {bloqueios.map((v) => (
                <li key={v.id}>
                  <strong>{v.id}</strong>: {v.mensagem}
                </li>
              ))}
            </ul>
          )}
          {minuta.bloqueiosGrupoAlternativas.length > 0 && (
            <p>
              Grupos de alternativas do modelo sem uma opção escolhida: {minuta.bloqueiosGrupoAlternativas.join(", ")}. Responda as perguntas pendentes no{" "}
              <Link href={`/processos/${id}/wizard`} className="underline">
                wizard
              </Link>
              .
            </p>
          )}
          {perguntasAoOperador.length > 0 && (
            <p>
              {perguntasAoOperador.length} pergunta(s) da leitura do checklist esperam a sua resposta:{" "}
              <Link href={`/processos/${id}/checklist`} className="underline">
                resolver no checklist
              </Link>
              .
            </p>
          )}
          {semResposta.length > 0 && (
            <p>
              {semResposta.length} pergunta(s) do wizard sem resposta ({semResposta.filter((x) => x.decisaoJuridica).length} de decisão jurídica):{" "}
              <Link href={`/processos/${id}/wizard`} className="underline">
                responder no wizard
              </Link>
              .
            </p>
          )}
          <p className="text-sm">
            {minuta.lacunasNoTexto.length} lacuna(s) marcada(s) em amarelo e {minuta.valoresPadrao.length} valor(es) padrão em azul. Lacuna não trava a exportação, mas sai marcada no texto.
          </p>
        </section>

        {alertas.length > 0 && (
          <section aria-label="Alertas" className="flex flex-col gap-2 rounded border border-amber-700 bg-amber-50 p-4 text-amber-950">
            <h2 className="text-lg font-semibold">⚠ Alertas ({alertas.length})</h2>
            <ul className="list-disc pl-5">
              {alertas.map((v) => (
                <li key={v.id}>
                  <strong>{v.id}</strong>: {v.mensagem}
                </li>
              ))}
            </ul>
          </section>
        )}

        {minuta.validacoes.conferenciaManual.length > 0 && (
          <details className="rounded border border-zinc-500 bg-white p-4">
            <summary className="flex min-h-11 cursor-pointer items-center text-lg font-semibold">☐ Conferência manual ({minuta.validacoes.conferenciaManual.length} regras que o sistema não confere sozinho)</summary>
            <ul className="mt-2 flex flex-col gap-2">
              {minuta.validacoes.conferenciaManual.map((v) => (
                <li key={v.id}>
                  <strong>{v.id}</strong> ({m10.get(v.id)?.tipo ?? ""}): {v.regra}
                  <br />
                  <span className="text-sm text-zinc-700">{v.mensagem}</span>
                </li>
              ))}
            </ul>
          </details>
        )}

        <p className="text-sm text-zinc-700">
          Legenda: <span className="rounded bg-amber-200 px-1 text-amber-950">⚠ lacuna (falta dado)</span> <span className="rounded bg-blue-100 px-1 text-blue-950">valor padrão (ⓟ)</span>. Clique num trecho para ver de onde ele veio. O texto
          não se edita aqui: corrija as respostas e os dados, e a minuta é montada de novo.
        </p>

        <article className="flex flex-col gap-4 rounded border border-zinc-400 bg-white p-4 md:p-8">
          {secoesDaMinuta(minuta).map((s, k) => (
            <section key={`${s.titulo}-${k}`} className="flex flex-col gap-2">
              <h2 className="sr-only">{s.titulo}</h2>
              {s.trechos.map((t) => (
                <Trecho key={t.id} t={t} pacote={pacote} />
              ))}
            </section>
          ))}
        </article>

        {!somenteLeitura && (
          <form action={irParaExportar.bind(null, id)}>
            <button type="submit" className="min-h-11 rounded bg-blue-800 px-4 font-medium text-white hover:bg-blue-900">
              Seguir para exportar →
            </button>
          </form>
        )}
      </main>
    </>
  );
}

function Texto({ texto }: { texto: string }) {
  return (
    <>
      {partesDoTexto(texto).map((parte, k) =>
        parte.tipo === "texto" ? (
          <span key={k}>{parte.texto}</span>
        ) : parte.tipo === "lacuna" ? (
          <mark key={k} className="rounded bg-amber-200 px-1 text-amber-950">
            ⚠ {parte.texto}
          </mark>
        ) : (
          <mark key={k} className="rounded bg-blue-100 px-1 text-blue-950" title="Valor padrão do pacote: confira">
            {parte.texto} ⓟ
          </mark>
        ),
      )}
    </>
  );
}

function Trecho({ t, pacote }: { t: TrechoDaMinuta; pacote: Pacote }) {
  return (
    <details className="group rounded hover:bg-zinc-50">
      <summary className="cursor-pointer list-none rounded p-1 focus:outline-2 focus:outline-blue-700">
        {ehTabela(t) ? (
          <div className="overflow-x-auto">
            {tabelaNaoMontada(t.texto).naoMontada && (
              <p>
                <mark className="rounded bg-amber-200 px-1 text-amber-950">⚠ tabela não montada: faltam as linhas (veja a origem)</mark>
              </p>
            )}
            <table className="w-full border-collapse text-left text-sm">
              <tbody>
                {linhasDaTabela(t.texto).map((linha, k) => (
                  <tr key={k} className={k === 0 ? "border-b-2 border-zinc-500 font-semibold" : "border-b border-zinc-200"}>
                    {linha.map((c, j) => (
                      <td key={j} className="p-2 align-top whitespace-pre-line">
                        <Texto texto={c} />
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="whitespace-pre-line">
            {t.numero && <strong>{t.numero} </strong>}
            <Texto texto={t.texto} />
          </p>
        )}
      </summary>
      <Origem t={t} pacote={pacote} />
    </details>
  );
}

const valor = (v: unknown) => (v === null || v === undefined || v === "" ? "sem resposta" : textoDoValor(v as never));

function Origem({ t, pacote }: { t: TrechoDaMinuta; pacote: Pacote }) {
  const caixa = "mb-2 ml-1 flex flex-col gap-1 border-l-4 border-blue-800 bg-blue-50 p-3 text-sm text-zinc-900";
  if (t.tipo === "clausula_setorial") {
    const linha = pacote.matrizes.M08.find((l) => l.id === t.id);
    return (
      <div className={caixa}>
        <p>
          <strong>Cláusula setorial {t.id}</strong> ({t.tema}) · pacote {t.origem.pacote}
        </p>
        {linha?.condicao && <p>Entrou porque: {linha.condicao}</p>}
        <Respostas respostas={t.origem.respostas} />
        {linha?.base_no_modelo && <p>Base: {linha.base_no_modelo}</p>}
        {linha?.origem_checklist && <p>Checklist: {linha.origem_checklist}</p>}
      </div>
    );
  }
  const linha = pacote.matrizes.M02.find((l) => l.id === t.id);
  const notas = (linha?.notas ?? "")
    .split(/[,;]\s*/)
    .map((n) => n.trim())
    .filter(Boolean);
  const m03 = new Map(pacote.matrizes.M03.map((l) => [l.id, l]));
  return (
    <div className={caixa}>
      <p>
        <strong>Bloco {t.id}</strong> · item {linha?.item_modelo || "—"} do modelo · pacote {t.origem.pacote}
      </p>
      {linha?.condicao_inclusao && <p>Motivo: {linha.condicao_inclusao}</p>}
      {t.origem.ligadoPor.length > 0 && <p>Ligado pelas perguntas: {t.origem.ligadoPor.join(", ")}</p>}
      <Respostas respostas={t.origem.respostas} />
      {notas.length > 0 && (
        <div>
          Notas explicativas:
          <ul className="list-disc pl-5">
            {notas.map((n) => (
              <li key={n}>
                <strong>{n}</strong>
                {m03.get(n) ? `: ${m03.get(n)?.texto_integral}` : ""}
              </li>
            ))}
          </ul>
        </div>
      )}
      {linha?.normas && <p>Normas: {linha.normas}</p>}
    </div>
  );
}

function Respostas({ respostas }: { respostas: Record<string, unknown> }) {
  const lista = Object.entries(respostas);
  if (lista.length === 0) return null;
  return (
    <p>
      Respostas lidas:{" "}
      {lista.map(([k, v], i) => (
        <span key={k}>
          {i > 0 && "; "}
          <code>{k}</code> = {valor(v)}
        </span>
      ))}
    </p>
  );
}
