import Link from "next/link";
import { Suspense } from "react";
import { abrirProcesso } from "@/dados/acesso-processo.ts";
import { carregarPacote } from "@/dados/pacote.ts";
import { minutaDoProcesso, pendenciasDaMinuta } from "@/dados/processos.ts";
import { variavelDoId } from "@/motor/pacote/nomes.ts";
import { Carregando } from "../../../componentes/cabecalho.tsx";
import { legivel } from "../../../componentes/rotulos.ts";
import { CabecalhoDoProcesso } from "../processo.tsx";
import { irParaMinuta, responderPergunta, salvarVariavel } from "./acoes.ts";
import { CampoExtra, PerguntaWizard } from "./formularios.tsx";
import { opcoesDaPergunta, pedeJustificativa } from "./regras.ts";

/** Tela do wizard (passo 9): perguntas com estado, uma por vez; sugestão do checklist; campos extras. */
export default function TelaDoWizard(props: PageProps<"/processos/[id]/wizard">) {
  return (
    <Suspense fallback={<Carregando />}>
      <Conteudo {...props} />
    </Suspense>
  );
}

type EstadoWz = "respondida" | "checklist" | "juridica" | "pendente";
const ROTULO: Record<EstadoWz, [string, string]> = {
  respondida: ["✓ Respondida", "border-green-800 bg-green-50 text-green-900"],
  checklist: ["☑ Veio do checklist", "border-blue-800 bg-blue-50 text-blue-900"],
  juridica: ["⚖ Decisão jurídica pendente", "border-red-800 bg-red-50 text-red-900"],
  pendente: ["⚠ Pendente", "border-amber-700 bg-amber-50 text-amber-950"],
};

async function Conteudo({ params, searchParams }: PageProps<"/processos/[id]/wizard">) {
  const { id } = await params;
  const { q } = await searchParams;
  const { usuario, p } = await abrirProcesso(id);
  const { pacote } = carregarPacote(p.processo.pacote);
  const minuta = minutaDoProcesso(p);
  const somenteLeitura = p.processo.situacao === "CONCLUIDO";
  const { wizard, origens, sugestoes, derivadas, dados } = minuta.processo;
  const m04 = new Map(pacote.matrizes.M04.map((l) => [l.id, l]));
  const m05 = new Map(pacote.matrizes.M05.map((l) => [l.id, l]));
  const pendentes = new Map(wizard.pendentes.map((x) => [x.id, x]));
  const respostas = new Map(p.respostasWizard.map((r) => [r.pergunta, r]));

  const estado = (wz: string): EstadoWz => {
    const pend = pendentes.get(wz);
    if (pend) return pend.decisaoJuridica ? "juridica" : "pendente";
    return origens[variavelDoId(wz)]?.origem === "CHECKLIST" && !respostas.has(wz) ? "checklist" : "respondida";
  };
  const lista = wizard.habilitadas;
  const atual = typeof q === "string" && lista.includes(q) ? q : (wizard.pendentes[0]?.id ?? lista[0]);
  const proxima = wizard.pendentes.map((x) => x.id).find((x) => x !== atual) ?? "";
  const linha = atual ? m04.get(atual) : undefined;
  const sugestao = atual ? sugestoes.filter((s) => s.destino === variavelDoId(atual) && s.item === undefined) : [];

  // Campos extras: o que a minuta acusa como faltando com fonte numa variável do M05 (decisão 0014).
  const faltando = new Map<string, string[]>();
  for (const l of minuta.lacunasNoTexto) {
    if (!l.fonte?.startsWith("VAR-")) continue;
    const v = m05.get(l.fonte);
    if (!v || v.nome.startsWith("tabela_itens") || v.calculo_expr !== null) continue;
    faltando.set(l.fonte, [...(faltando.get(l.fonte) ?? []), l.trecho]);
  }
  const informadas = p.respostasWizard.filter((r) => r.pergunta.startsWith("VAR-") && r.pergunta !== "VAR-057");
  const outrasLacunas = minuta.lacunasNoTexto.filter((l) => l.fonte?.startsWith("CK-X") || l.fonte?.startsWith("itens."));

  return (
    <>
      <CabecalhoDoProcesso usuario={usuario} p={p} pendencias={pendenciasDaMinuta(minuta)} atual="wizard" />
      <main className="grid gap-6 p-6 lg:grid-cols-[22rem_1fr]">
        <nav aria-label="Perguntas do wizard" className="flex flex-col gap-1">
          <h2 className="text-lg font-semibold">Perguntas ({lista.length})</h2>
          <p className="text-sm text-zinc-700">{wizard.pendentes.length} pendente(s)</p>
          <ul className="flex max-h-[70vh] flex-col gap-1 overflow-y-auto">
            {lista.map((wz) => {
              const [rotulo, cor] = ROTULO[estado(wz)];
              return (
                <li key={wz}>
                  <Link href={`?q=${wz}`} aria-current={wz === atual ? "true" : undefined} className={`flex min-h-11 flex-col rounded border px-2 py-1 text-sm ${wz === atual ? "border-blue-800 ring-2 ring-blue-800" : "border-zinc-300"}`}>
                    <span>
                      <strong>{wz}</strong> {m04.get(wz)?.pergunta.slice(0, 70)}
                      {(m04.get(wz)?.pergunta.length ?? 0) > 70 ? "…" : ""}
                    </span>
                    <span className={`mt-1 self-start rounded border px-1 text-xs ${cor}`}>{rotulo}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        <div className="flex flex-col gap-8">
          {linha && (
            <section className="flex flex-col gap-3">
              <p className="text-sm text-zinc-700">
                {linha.id} · {ROTULO[estado(linha.id)][0]}
              </p>
              <h2 className="text-xl font-semibold">{linha.pergunta}</h2>
              {linha.fundamento && <p className="text-sm text-zinc-700">Fundamento: {linha.fundamento}</p>}
              {origens[variavelDoId(linha.id)]?.origem === "CHECKLIST" && (
                <p className="rounded border border-blue-800 bg-blue-50 p-2 text-blue-900">
                  Preenchida pelo checklist ({(origens[variavelDoId(linha.id)] as { perguntas: string[] }).perguntas.join(", ")}): {JSON.stringify(dados[variavelDoId(linha.id)])}. Responder aqui substitui.
                </p>
              )}
              {!somenteLeitura && (
                <PerguntaWizard
                  key={linha.id}
                  acao={responderPergunta.bind(null, id)}
                  d={{
                    id: linha.id,
                    tipo: linha.tipo_resposta,
                    opcoes: opcoesDaPergunta(linha.tipo_resposta, linha.opcoes).map((o) => ({ valor: o, rotulo: o === "SIM" ? "Sim" : o === "NAO" ? "Não" : legivel(o) })),
                    valor: respostas.get(linha.id)?.valor ?? null,
                    justificativa: respostas.get(linha.id)?.justificativa ?? "",
                    regraJustificativa: pedeJustificativa(linha.exige_justificativa) ? linha.exige_justificativa : null,
                    sugestao: sugestao.length ? { valor: sugestao[0].valor, perguntas: sugestao.map((s) => s.pergunta).join(", ") } : null,
                    proxima,
                  }}
                />
              )}
            </section>
          )}

          {Object.keys(derivadas).length > 0 && (
            <section className="flex flex-col gap-2">
              <h2 className="text-lg font-semibold">Calculadas pelos itens</h2>
              <ul className="text-sm">
                {Object.entries(derivadas).map(([wz, v]) => (
                  <li key={wz}>
                    <strong>{wz}</strong> {m04.get(wz)?.pergunta}: <code>{v === null ? "sem valor (falta dado dos itens)" : JSON.stringify(v)}</code>
                  </li>
                ))}
              </ul>
            </section>
          )}

          <section className="flex flex-col gap-3">
            <h2 className="text-lg font-semibold">Campos que a minuta pede ({faltando.size})</h2>
            <p className="text-sm text-zinc-700">Dados que faltam no texto da minuta. Valor, quantidade, prazo e percentual nunca são inventados: sem eles, a minuta mostra a lacuna.</p>
            {!somenteLeitura &&
              [...faltando].map(([v, trechos]) => {
                const l = m05.get(v);
                return <CampoExtra key={v} acao={salvarVariavel.bind(null, id)} variavel={v} rotulo={l?.descricao ?? v} ajuda={`${l?.validacao ?? ""} · usado em ${[...new Set(trechos)].join(", ")}`} tipo={l?.tipo_dado ?? "TEXTO"} valor="" />;
              })}
            {informadas.length > 0 && (
              <details>
                <summary className="flex min-h-11 cursor-pointer items-center text-blue-800 underline">Campos já informados ({informadas.length})</summary>
                <div className="flex flex-col gap-3">
                  {informadas.map((r) => {
                    const l = m05.get(r.pergunta);
                    return <CampoExtra key={r.pergunta} acao={salvarVariavel.bind(null, id)} variavel={r.pergunta} rotulo={l?.descricao ?? r.pergunta} ajuda={l?.validacao ?? ""} tipo={l?.tipo_dado ?? "TEXTO"} valor={Array.isArray(r.valor) ? r.valor.join("\n") : String(r.valor ?? "")} />;
                  })}
                </div>
              </details>
            )}
            {outrasLacunas.length > 0 && (
              <p className="text-sm">
                Outras {outrasLacunas.length} lacuna(s) vêm de <Link href={`/processos/${id}/checklist`} className="text-blue-800 underline">complementos do checklist</Link> ou dos <Link href={`/processos/${id}/itens`} className="text-blue-800 underline">itens</Link>.
              </p>
            )}
          </section>

          {!somenteLeitura && (
            <form action={irParaMinuta.bind(null, id)}>
              <button type="submit" className="min-h-11 rounded bg-blue-800 px-4 font-medium text-white hover:bg-blue-900">
                Ver a minuta →
              </button>
            </form>
          )}
        </div>
      </main>
    </>
  );
}
