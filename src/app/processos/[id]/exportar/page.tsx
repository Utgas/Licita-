import Link from "next/link";
import { Suspense } from "react";
import { abrirProcesso } from "@/dados/acesso-processo.ts";
import { dataDoExpurgo, minutaDoProcesso, pendenciasDaMinuta } from "@/dados/processos.ts";
import { secoesDaMinuta, textoDaSecao } from "@/exportacao/secoes.ts";
import { Carregando } from "../../../componentes/cabecalho.tsx";
import { dataBR } from "../../../componentes/rotulos.ts";
import { CabecalhoDoProcesso } from "../processo.tsx";
import { concluirProcesso, registrarCopia } from "./acoes.ts";
import { Concluir, Copiar } from "./formularios.tsx";

/**
 * Exportar (passo 11): uma linha por seção do modelo de TR da AGU, na ordem e com os títulos do modelo (decisão
 * 0010), com "Copiar" e marca de copiado; PDF baixado na hora; conclusão do processo. Tudo só sem travas.
 */
export default function TelaDeExportacao(props: PageProps<"/processos/[id]/exportar">) {
  return (
    <Suspense fallback={<Carregando />}>
      <Conteudo {...props} />
    </Suspense>
  );
}

async function Conteudo({ params }: PageProps<"/processos/[id]/exportar">) {
  const { id } = await params;
  const { usuario, p } = await abrirProcesso(id);
  const minuta = minutaDoProcesso(p);
  const concluido = p.processo.situacao === "CONCLUIDO";
  const copiadas = new Set(p.exportacoes.filter((e) => e.tipo === "COPIA_SECAO").map((e) => e.secao));
  const pdfs = p.exportacoes.filter((e) => e.tipo === "PDF");
  const secoes = secoesDaMinuta(minuta);
  const expurgo = dataDoExpurgo(p.processo.concluidoEm);

  return (
    <>
      <CabecalhoDoProcesso usuario={usuario} p={p} pendencias={pendenciasDaMinuta(minuta)} atual="exportar" />
      <main className="flex flex-col gap-6 p-6">
        {minuta.bloqueada ? (
          <section className="flex flex-col gap-2 rounded border border-red-800 bg-red-50 p-4 text-red-950">
            <h2 className="text-lg font-semibold">⛔ Exportação bloqueada: a minuta tem travas</h2>
            <p>
              Resolva as travas listadas na{" "}
              <Link href={`/processos/${id}/revisao`} className="underline">
                tela da minuta
              </Link>{" "}
              e volte aqui.
            </p>
          </section>
        ) : (
          <>
            <section className="flex flex-col gap-2">
              <h2 className="text-xl font-semibold">Copiar para o Compras.gov.br</h2>
              <p className="text-sm text-zinc-700">
                Uma linha por seção do modelo de TR da AGU, na ordem do modelo. {copiadas.size} de {secoes.length} seção(ões) copiada(s).
                {minuta.lacunasNoTexto.length > 0 && ` Atenção: ${minuta.lacunasNoTexto.length} lacuna(s) seguem marcadas como [LACUNA] no texto.`}
              </p>
              <ol className="flex flex-col gap-2">
                {secoes.map((s) => {
                  const texto = textoDaSecao(s);
                  return (
                    <li key={s.titulo} className="flex flex-col gap-2 rounded border border-zinc-400 p-3">
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <strong>{s.titulo}</strong>
                        <Copiar texto={texto} secao={s.titulo} copiada={copiadas.has(s.titulo)} registrar={registrarCopia.bind(null, id)} />
                      </div>
                      <details>
                        <summary className="flex min-h-11 cursor-pointer items-center text-blue-800 underline">Ver o texto</summary>
                        <textarea readOnly value={texto} rows={8} aria-label={`Texto da seção ${s.titulo}`} className="w-full rounded border border-zinc-500 p-2 font-mono text-sm" />
                      </details>
                    </li>
                  );
                })}
              </ol>
            </section>

            <section className="flex flex-col gap-2">
              <h2 className="text-xl font-semibold">PDF</h2>
              <p className="text-sm text-zinc-700">Gerado agora, a partir das respostas atuais; o sistema não guarda o arquivo, só o código de conferência (hash) na auditoria.</p>
              <div>
                <a href={`/processos/${id}/exportar/pdf`} className="inline-flex min-h-11 items-center rounded bg-blue-800 px-4 font-medium text-white hover:bg-blue-900">
                  Baixar o PDF da minuta
                </a>
              </div>
              {pdfs.length > 0 && (
                <p className="text-sm">
                  ✓ PDF baixado {pdfs.length} vez(es); último em {dataBR(pdfs[pdfs.length - 1].feitoEm)} (hash {pdfs[pdfs.length - 1].hashPdf?.slice(0, 16)}…).
                </p>
              )}
            </section>
          </>
        )}

        <section className="flex max-w-3xl flex-col gap-2">
          <h2 className="text-xl font-semibold">Concluir</h2>
          {concluido ? (
            <p className="rounded border border-zinc-600 bg-zinc-50 p-3">✓ Processo concluído em {dataBR(p.processo.concluidoEm as string)}. Os dados serão apagados em {expurgo ? dataBR(expurgo) : "—"}; a auditoria fica.</p>
          ) : minuta.bloqueada ? (
            <p>Só depois de resolver as travas.</p>
          ) : (
            <Concluir acao={concluirProcesso.bind(null, id)} />
          )}
        </section>
      </main>
    </>
  );
}
