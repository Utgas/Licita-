import Link from "next/link";
import { Aviso, TituloDeSecao, classesDoBotao } from "../../../componentes/ui.tsx";
import { Icone } from "../../../componentes/icones.tsx";
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
      <main className="mx-auto flex w-full max-w-[1400px] flex-col gap-6 px-4 py-6 md:px-6">
        {minuta.bloqueada ? (
          <Aviso tipo="trava" titulo="Exportação bloqueada: a minuta tem travas">
            <p>
              Resolva as travas listadas na{" "}
              <Link href={`/processos/${id}/revisao`} className="underline">
                tela da minuta
              </Link>{" "}
              e volte aqui.
            </p>
          </Aviso>
        ) : (
          <>
            <section className="flex flex-col gap-4 border border-linha bg-folha p-4 md:p-5">
              <TituloDeSecao complemento={`${copiadas.size} de ${secoes.length} copiadas`}>Copiar para o Compras.gov.br</TituloDeSecao>
              <p className="text-sm text-tinta-2">
                Uma linha por seção do modelo de TR da AGU, na ordem do modelo.
                {minuta.lacunasNoTexto.length > 0 && ` Atenção: ${minuta.lacunasNoTexto.length} lacuna(s) seguem marcadas como [LACUNA] no texto.`}
              </p>
              <ol className="flex flex-col border-t border-linha">
                {secoes.map((s, k) => {
                  const texto = textoDaSecao(s);
                  return (
                    <li key={s.titulo} className="flex flex-col border-b border-linha">
                      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 py-2">
                        <span className="w-6 font-mono text-sm text-tinta-2">{String(k + 1).padStart(2, "0")}</span>
                        <strong className="min-w-0 flex-1 text-[0.95rem] font-medium">{s.titulo}</strong>
                        <Copiar texto={texto} secao={s.titulo} copiada={copiadas.has(s.titulo)} registrar={registrarCopia.bind(null, id)} />
                      </div>
                      <details className="pb-2 pl-10">
                        <summary className="flex min-h-9 w-fit cursor-pointer items-center text-sm text-tinta-2 underline">Ver o texto</summary>
                        <textarea readOnly value={texto} rows={8} aria-label={`Texto da seção ${s.titulo}`} className="mt-1 w-full rounded-sm border border-linha-forte bg-papel p-2 font-mono text-sm" />
                      </details>
                    </li>
                  );
                })}
              </ol>
            </section>

            <section className="flex flex-col gap-3 border border-linha bg-folha p-4 md:p-5">
              <TituloDeSecao>PDF</TituloDeSecao>
              <p className="text-sm text-tinta-2">Gerado agora, a partir das respostas atuais; o sistema não guarda o arquivo, só o código de conferência (hash) na auditoria.</p>
              <div>
                <a href={`/processos/${id}/exportar/pdf`} className={classesDoBotao("principal")}>
                  <Icone nome="baixar" tamanho={16} />
                  Baixar o PDF da minuta
                </a>
              </div>
              {pdfs.length > 0 && (
                <p className="flex items-center gap-2 text-sm text-ok">
                  <Icone nome="ok" tamanho={15} />
                  PDF baixado {pdfs.length} vez(es); último em {dataBR(pdfs[pdfs.length - 1].feitoEm)} (hash {pdfs[pdfs.length - 1].hashPdf?.slice(0, 16)}…).
                </p>
              )}
            </section>
          </>
        )}

        <section className="flex flex-col gap-4 border border-linha bg-folha p-4 md:p-5">
          <TituloDeSecao>Concluir</TituloDeSecao>
          {concluido ? (
            <Aviso tipo="ok" titulo={`Processo concluído em ${dataBR(p.processo.concluidoEm as string)}`}>Os dados serão apagados em {expurgo ? dataBR(expurgo) : "—"}; a auditoria fica.</Aviso>
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
