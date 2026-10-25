import Link from "next/link";
import { Suspense } from "react";
import { abrirProcesso } from "@/dados/acesso-processo.ts";
import { carregarPacote } from "@/dados/pacote.ts";
import { documentosDoProcesso } from "@/dados/etp.ts";
import { pendenciasDaMinuta } from "@/dados/processos.ts";
import { ehTabela, secoesDaMinuta } from "@/exportacao/secoes.ts";
import type { TrechoDaMinuta } from "@/motor/minuta.ts";
import { textoDoValor } from "@/motor/montagem/formatos.ts";
import type { Pacote } from "@/motor/pacote/esquema.ts";
import { Carregando } from "../../../componentes/cabecalho.tsx";
import { Icone } from "../../../componentes/icones.tsx";
import { TabelaMarcada, TextoMarcado } from "../../../componentes/texto-marcado.tsx";
import { Aviso, Codigo, classesDoBotao } from "../../../componentes/ui.tsx";
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
  const { pacote } = carregarPacote(p.processo.pacote, p.processo.pacoteHash);
  const { minuta, etp, derivacao } = documentosDoProcesso(p);
  const nomesDosCampos = new Map(etp.campos.map((c) => [c.id, c.campo]));
  const doEtp = new Map(derivacao.blocos.map((b) => [b.bloco, b.campos.map((c) => `${c} (${nomesDosCampos.get(c)})`)]));
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
      <main id="conteudo" className="mx-auto grid w-full max-w-[1400px] grid-cols-[minmax(0,1fr)] gap-6 px-4 py-6 md:px-6 xl:grid-cols-[minmax(0,1fr)_22rem]">
        <aside className="flex flex-col gap-4 xl:sticky xl:top-4 xl:order-2 xl:max-h-[calc(100vh-2rem)] xl:self-start xl:overflow-y-auto">
          <Aviso tipo={travada ? "trava" : "ok"} titulo={travada ? "A minuta tem travas: a exportação fica bloqueada até resolvê-las" : "Sem travas: a minuta pode ser exportada"}>
            {bloqueios.length > 0 && (
              <ul className="flex flex-col gap-1.5">
                {bloqueios.map((v) => (
                  <li key={v.id}>
                    <Codigo>{v.id}</Codigo>: {v.mensagem} <OndeResolver id={id} momento={v.momento} />
                  </li>
                ))}
              </ul>
            )}
            {minuta.bloqueiosGrupoAlternativas.length > 0 && (
              <p>
                Grupos de alternativas do modelo sem uma opção escolhida: <Codigo>{minuta.bloqueiosGrupoAlternativas.join(", ")}</Codigo>. Responda as perguntas pendentes no{" "}
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
          </Aviso>

          {alertas.length > 0 && (
            <Aviso tipo="atencao" titulo={`Alertas (${alertas.length})`}>
              <ul className="flex flex-col gap-1.5">
                {alertas.map((v) => (
                  <li key={v.id}>
                    <Codigo>{v.id}</Codigo>: {v.mensagem} <OndeResolver id={id} momento={v.momento} />
                  </li>
                ))}
              </ul>
            </Aviso>
          )}

          <div className="flex flex-col gap-2 border border-linha bg-folha p-4 text-sm">
            <p className="font-semibold">Como ler a minuta</p>
            <p className="flex items-center gap-2">
              <mark className="inline-flex items-center gap-1 bg-atencao-marca px-1 text-atencao">
                <Icone nome="lacuna" tamanho={14} />
                lacuna
              </mark>
              falta dado: {minuta.lacunasNoTexto.length}
            </p>
            <p className="flex items-center gap-2">
              <mark className="inline-flex items-center gap-1 bg-padrao-fundo px-1 text-padrao underline decoration-dotted">
                <Icone nome="padrao" tamanho={14} />
                valor padrão
              </mark>
              do pacote, confira: {minuta.valoresPadrao.length}
            </p>
            <p className="text-tinta-2">Clique num trecho para ver de onde ele veio. O texto não se edita aqui: corrija as respostas e os dados, e a minuta é montada de novo. Lacuna não trava a exportação, mas sai marcada.</p>
          </div>

          {minuta.validacoes.conferenciaManual.length > 0 && (
            <details className="border border-linha bg-folha p-4 text-sm">
              <summary className="flex min-h-11 cursor-pointer items-center gap-2 font-semibold">
                <Icone nome="vazio" tamanho={16} />
                Conferência manual ({minuta.validacoes.conferenciaManual.length} regras que o sistema não confere sozinho)
              </summary>
              <ul className="mt-2 flex flex-col gap-3">
                {minuta.validacoes.conferenciaManual.map((v) => (
                  <li key={v.id}>
                    <Codigo>{v.id}</Codigo> ({m10.get(v.id)?.tipo ?? ""}): {v.regra}
                    <br />
                    <span className="text-tinta-2">{v.mensagem}</span>
                  </li>
                ))}
              </ul>
            </details>
          )}

          {!somenteLeitura && (
            <form action={irParaExportar.bind(null, id)}>
              <button type="submit" className={`${classesDoBotao("principal")} w-full`}>
                Seguir para exportar <Icone nome="avancar" tamanho={16} />
              </button>
            </form>
          )}
        </aside>

        <article aria-label="Minuta do Termo de Referência" className="mx-auto w-full max-w-[52rem] border border-linha bg-folha px-5 py-8 leading-relaxed md:px-16 md:py-14 xl:order-1">
          {secoesDaMinuta(minuta).map((s, k) => (
            <section key={`${s.titulo}-${k}`} className="flex flex-col gap-1">
              <h2 className="sr-only">{s.titulo}</h2>
              {s.trechos.map((t) => (
                <Trecho key={t.id} t={t} pacote={pacote} id={id} doEtp={doEtp.get(t.id) ?? []} />
              ))}
            </section>
          ))}
        </article>
      </main>
    </>
  );
}

/** Tela onde se corrige o dado que a validação confere (coluna momento do M10). */
const TELA_DO_MOMENTO: Record<string, [string, string]> = {
  CHECKLIST: ["checklist", "corrigir no checklist"],
  IMPORTACAO: ["itens", "corrigir nos itens"],
  ITENS: ["itens", "corrigir nos itens"],
  WIZARD: ["wizard", "corrigir no wizard"],
  MINUTA: ["wizard", "completar no wizard"],
};

function OndeResolver({ id, momento }: { id: string; momento: string }) {
  const tela = TELA_DO_MOMENTO[momento];
  if (!tela) return null;
  return (
    <Link href={`/processos/${id}/${tela[0]}`} className="underline">
      ({tela[1]})
    </Link>
  );
}

function Trecho({ t, pacote, id, doEtp }: { t: TrechoDaMinuta; pacote: Pacote; id: string; doEtp: string[] }) {
  return (
    <details className="group relative -mx-3 border-l-2 border-transparent px-3 transition-colors open:border-l-marca hover:border-l-linha-forte">
      <summary className="cursor-pointer list-none py-1.5">
        {ehTabela(t) ? (
          <TabelaMarcada texto={t.texto} />
        ) : (
          <p className="whitespace-pre-line">
            {t.numero && <strong>{t.numero} </strong>}
            <TextoMarcado texto={t.texto} />
          </p>
        )}
      </summary>
      <Origem t={t} pacote={pacote} id={id} doEtp={doEtp} />
    </details>
  );
}

const valor = (v: unknown) => (v === null || v === undefined || v === "" ? "sem resposta" : textoDoValor(v as never));

function Origem({ t, pacote, id, doEtp }: { t: TrechoDaMinuta; pacote: Pacote; id: string; doEtp: string[] }) {
  const caixa = "mb-3 mt-1 flex flex-col gap-1.5 border border-linha bg-papel p-3 text-sm leading-normal text-tinta";
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
      {doEtp.length > 0 && (
        <p>
          Repete o ETP (M06):{" "}
          <Link href={`/processos/${id}/etp`} className="underline">
            {doEtp.join("; ")}
          </Link>
        </p>
      )}
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
