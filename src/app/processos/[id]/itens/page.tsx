import { Suspense } from "react";
import { abrirProcesso } from "@/dados/acesso-processo.ts";
import { carregarPacote } from "@/dados/pacote.ts";
import { COLUNAS } from "@/dados/planilha-itens.ts";
import { minutaDoProcesso, pendenciasDaMinuta } from "@/dados/processos.ts";
import { textoDoValor } from "@/motor/montagem/formatos.ts";
import { Carregando } from "../../../componentes/cabecalho.tsx";
import { CabecalhoDoProcesso } from "../processo.tsx";
import { apagarItem, importarPlanilha, irParaWizard, responderAqui, salvarItem } from "./acoes.ts";
import { FormularioItem, Importar, RespostaAqui } from "./formularios.tsx";

/** Tela dos itens (passo 8): planilha ou digitação; classificação ME/EPP e cotas calculadas pelo motor. */
export default function TelaDosItens(props: PageProps<"/processos/[id]/itens">) {
  return (
    <Suspense fallback={<Carregando />}>
      <Conteudo {...props} />
    </Suspense>
  );
}

const TRATAMENTOS: Record<string, string> = {
  EXCLUSIVO: "Exclusivo para ME/EPP",
  AMPLA: "Ampla participação",
  COTA: "Cota reservada (com cota principal)",
  EXCECAO_JUSTIFICADA: "Ampla, com exceção justificada",
};

async function Conteudo({ params }: PageProps<"/processos/[id]/itens">) {
  const { id } = await params;
  const { usuario, p } = await abrirProcesso(id);
  const { pacote } = carregarPacote(p.processo.pacote);
  const minuta = minutaDoProcesso(p);
  const somenteLeitura = p.processo.situacao === "CONCLUIDO";
  const m05 = new Map(pacote.matrizes.M05.map((l) => [l.id, l]));
  const colunas = COLUNAS.map(({ titulo, coluna, tipo, obrigatoria }) => ({ titulo, coluna, tipo, obrigatoria }));
  const calculados = Map.groupBy(
    minuta.processo.calculados.filter((c) => c.item !== undefined),
    (c) => c.item as number,
  );
  const itensDoMotor = new Map(minuta.processo.itens.map((i) => [i.numero, i]));
  const tabela = minuta.trechos.find((t) => t.id === "TR-1.1.TAB1");
  const respostaWz = (pergunta: string) => p.respostasWizard.find((r) => r.pergunta === pergunta)?.valor;
  const origensDeItem = minuta.processo.origensDeItem;

  return (
    <>
      <CabecalhoDoProcesso usuario={usuario} p={p} pendencias={pendenciasDaMinuta(minuta)} atual="itens" />
      <main className="flex flex-col gap-8 p-6">
        {!somenteLeitura && (
          <section className="grid gap-6 md:grid-cols-2">
            <div className="flex flex-col gap-3">
              <h2 className="text-xl font-semibold">Importar planilha</h2>
              <p>
                Use as colunas fixas do{" "}
                <a href={`/processos/${id}/itens/modelo`} className="text-blue-800 underline">
                  modelo de planilha (baixar)
                </a>
                . Valores e quantidades vêm da pesquisa de preços e do DFD; o sistema não os calcula.
              </p>
              <Importar acao={importarPlanilha.bind(null, id)} />
            </div>
            <div className="flex flex-col gap-4">
              <h2 className="text-xl font-semibold">Orçamento e cota</h2>
              <RespostaAqui acao={responderAqui.bind(null, id)} pergunta="WZ-40" rotulo="Orçamento sigiloso?" tipo="simnao" valor={String(respostaWz("WZ-40") ?? "")} ajuda="Com orçamento sigiloso, os valores saem da tabela da minuta (WZ-40)." />
              <RespostaAqui acao={responderAqui.bind(null, id)} pergunta="VAR-057" rotulo={`Percentual da cota reservada (%) — ${m05.get("VAR-057")?.descricao ?? ""}`} tipo="numero" valor={String(respostaWz("VAR-057") ?? "")} ajuda={m05.get("VAR-057")?.validacao} />
            </div>
          </section>
        )}

        <section className="flex flex-col gap-3">
          <h2 className="text-xl font-semibold">Itens ({p.itens.length})</h2>
          {p.itens.length === 0 && <p>Nenhum item ainda. Importe a planilha ou inclua item a item.</p>}
          <ul className="flex flex-col gap-3">
            {p.itens.map((i) => {
              const doMotor = itensDoMotor.get(i.numero);
              const tratamento = doMotor?.tratamento_me_epp as string | null | undefined;
              const valores = Object.fromEntries(COLUNAS.map((c) => [c.coluna, i[c.coluna as keyof typeof i] === null ? "" : String(i[c.coluna as keyof typeof i])]));
              return (
                <li key={i.numero} className="flex flex-col gap-2 rounded border border-zinc-400 p-3">
                  <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1">
                    <strong>Item {i.numero}</strong>
                    <span>{i.especificacao ?? "—"}</span>
                    <span>
                      {i.quantidade ?? "—"} {i.unidadeMedida ?? ""}
                    </span>
                    <span>{i.valorUnitario ? `R$ ${textoDoValor(Number(i.valorUnitario))} /un.` : "sem valor unitário"}</span>
                    <span className="rounded border border-zinc-600 px-2">ME/EPP: {tratamento ? (TRATAMENTOS[tratamento] ?? tratamento) : "não calculado (falta dado)"}</span>
                  </div>
                  <details>
                    <summary className="flex min-h-11 cursor-pointer items-center text-blue-800 underline">Como o item foi classificado</summary>
                    <ul className="flex flex-col gap-1 pl-4 text-sm">
                      {(calculados.get(i.numero) ?? []).map((c) => (
                        <li key={`${c.regra}-${c.destino}`}>
                          <strong>{c.regra}</strong> {m05.get(c.regra)?.descricao ?? c.destino}: <code>{c.valor === null ? "sem valor (falta dado)" : JSON.stringify(c.valor)}</code>
                        </li>
                      ))}
                      {Object.entries(origensDeItem)
                        .filter(([k]) => k.startsWith(`${i.numero}.`))
                        .map(([k, pergunta]) => (
                          <li key={k}>
                            <strong>{k.split(".")[1]}</strong> veio do checklist ({pergunta}): <code>{JSON.stringify(doMotor?.[k.split(".")[1]])}</code>
                          </li>
                        ))}
                    </ul>
                  </details>
                  {!somenteLeitura && (
                    <details>
                      <summary className="flex min-h-11 cursor-pointer items-center text-blue-800 underline">Editar</summary>
                      <FormularioItem acao={salvarItem.bind(null, id)} apagar={apagarItem.bind(null, id)} colunas={colunas} valores={valores} />
                    </details>
                  )}
                </li>
              );
            })}
          </ul>
          {!somenteLeitura && (
            <details className="rounded border border-zinc-400 p-3">
              <summary className="flex min-h-11 cursor-pointer items-center font-medium text-blue-800 underline">Incluir item</summary>
              <FormularioItem acao={salvarItem.bind(null, id)} colunas={colunas} valores={undefined} />
            </details>
          )}
        </section>

        {tabela && (
          <section className="flex flex-col gap-3">
            <h2 className="text-xl font-semibold">Tabela da minuta (como o motor montou)</h2>
            <p className="text-sm text-zinc-700">Cada item mantém o seu número; as linhas de cota ficam no fim, com os números seguintes.</p>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-left text-sm">
                <tbody>
                  {tabela.texto.split("\n").map((linha, k) => (
                    <tr key={k} className={k === 0 ? "border-b-2 border-zinc-500 font-semibold" : "border-b border-zinc-200"}>
                      {linha.split(" | ").map((c, j) => (
                        <td key={j} className={`p-2 align-top ${c.includes("[[LACUNA") ? "bg-amber-100 text-amber-950" : ""}`}>
                          {c.replace(/\[\[LACUNA[^\]]*\]\]/g, "⚠ falta")}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {!somenteLeitura && (
          <form action={irParaWizard.bind(null, id)}>
            <button type="submit" className="min-h-11 rounded bg-blue-800 px-4 font-medium text-white hover:bg-blue-900">
              Seguir para o wizard →
            </button>
          </form>
        )}
      </main>
    </>
  );
}
