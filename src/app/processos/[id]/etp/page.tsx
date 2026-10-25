import Link from "next/link";
import { Suspense } from "react";
import { abrirProcesso } from "@/dados/acesso-processo.ts";
import { type CampoDoEtpParaInformar, camposParaInformar, documentosDoProcesso } from "@/dados/etp.ts";
import { carregarPacote } from "@/dados/pacote.ts";
import { pendenciasDaMinuta } from "@/dados/processos.ts";
import { textoDoCampo as valoresDoFormulario } from "@/dados/wizard.ts";
import { blocosDoCampo, camposParaCopiar, etpLiberado, textoDoCampo } from "@/exportacao/etp.ts";
import type { Derivacao } from "@/motor/derivacao/derivacao.ts";
import type { CampoDoEtp, OrigemDaParte, SituacaoDoCampo } from "@/motor/montagem/etp.ts";
import { textoDoValor } from "@/motor/montagem/formatos.ts";
import { Carregando } from "../../../componentes/cabecalho.tsx";
import { Icone } from "../../../componentes/icones.tsx";
import { TabelaMarcada, TextoMarcado } from "../../../componentes/texto-marcado.tsx";
import { Aviso, Codigo, Selo, type TipoDeEstado, TituloDeSecao, classesDoBotao } from "../../../componentes/ui.tsx";
import { Copiar } from "../exportar/formularios.tsx";
import { CabecalhoDoProcesso } from "../processo.tsx";
import { FormularioCampo } from "../wizard/formularios.tsx";
import { registrarCopiaDoEtp, salvarCampoDoEtp } from "./acoes.ts";

/**
 * Tela do ETP (Marco 3, passo 8; decisão 0015): o ETP montado das mesmas respostas do TR, campo a campo, na ordem do
 * ETP Digital (M01). Cada campo mostra de onde veio cada parte, a orientação do M01 e os blocos do TR que o repetem;
 * a equipe completa o que falta, copia campo a campo e baixa o PDF. O texto não se edita aqui: muda-se o dado.
 */
export default function TelaDoEtp(props: PageProps<"/processos/[id]/etp">) {
  return (
    <Suspense fallback={<Carregando />}>
      <Conteudo {...props} />
    </Suspense>
  );
}

const SITUACAO: Record<SituacaoDoCampo, [TipoDeEstado, string]> = {
  preenchido: ["ok", "Preenchido"],
  incompleto: ["atencao", "Com lacuna"],
  vazio: ["atencao", "Vazio"],
  texto_do_etp_digital: ["vazio", "Texto do próprio ETP Digital"],
  sem_ligacao: ["vazio", "Sem dado ligado"],
};

async function Conteudo({ params }: PageProps<"/processos/[id]/etp">) {
  const { id } = await params;
  const { usuario, p } = await abrirProcesso(id);
  const { pacote } = carregarPacote(p.processo.pacote, p.processo.pacoteHash);
  const documentos = documentosDoProcesso(p);
  const { minuta, etp, derivacao } = documentos;
  const somenteLeitura = p.processo.situacao === "CONCLUIDO";
  const liberado = etpLiberado(minuta);
  const paraCopiar = camposParaCopiar(etp);
  const ids = new Set(paraCopiar.map((c) => c.id));
  const copiados = new Set(p.exportacoes.filter((e) => e.tipo === "COPIA_SECAO" && e.secao && ids.has(e.secao)).map((e) => e.secao));
  const informar = camposParaInformar(pacote, documentos, p);
  const campoVazioNoTr = derivacao.blocos.filter((b) => b.situacao === "campo_vazio");
  const lacunas = etp.campos.reduce((n, c) => n + c.lacunas.length, 0);

  return (
    <>
      <CabecalhoDoProcesso usuario={usuario} p={p} pendencias={pendenciasDaMinuta(minuta)} atual="etp" />
      <main className="mx-auto grid w-full max-w-[1400px] grid-cols-[minmax(0,1fr)] gap-6 px-4 py-6 md:px-6 xl:grid-cols-[minmax(0,1fr)_22rem]">
        <aside className="flex flex-col gap-4 xl:sticky xl:top-4 xl:order-2 xl:max-h-[calc(100vh-2rem)] xl:self-start xl:overflow-y-auto">
          {!liberado ? (
            <Aviso tipo="trava" titulo="O ETP espera as dúvidas da leitura do checklist">
              <p>
                {minuta.revisao.perguntasAoOperador.length} pergunta(s) da leitura do checklist mudam o próprio dado do ETP.{" "}
                <Link href={`/processos/${id}/checklist`} className="underline">
                  Resolver no checklist
                </Link>
                .
              </p>
            </Aviso>
          ) : (
            <Aviso tipo={etp.pendencias.length ? "atencao" : "ok"} titulo={etp.pendencias.length ? `${etp.pendencias.length} campo(s) obrigatório(s) pendente(s)` : "Campos obrigatórios com conteúdo"}>
              {etp.pendencias.length > 0 && (
                <p>
                  Elementos obrigatórios do ETP (art. 18, § 2º) vazios ou com lacuna: <Codigo>{etp.pendencias.join(", ")}</Codigo>. Complete os dados no campo.
                </p>
              )}
            </Aviso>
          )}

          <section className="flex flex-col gap-3 border border-linha bg-folha p-4 text-sm">
            <TituloDeSecao complemento={`${copiados.size} de ${paraCopiar.length} copiados`} nivel={3}>
              Copiar para o ETP Digital
            </TituloDeSecao>
            <p className="text-tinta-2">
              Um botão &quot;Copiar&quot; em cada campo, na ordem das telas do ETP Digital.{lacunas > 0 && ` ${lacunas} lacuna(s) seguem marcadas como [LACUNA] no texto.`}
            </p>
            {liberado && (
              <a href={`/processos/${id}/etp/pdf`} className={classesDoBotao("principal")}>
                <Icone nome="baixar" tamanho={16} />
                Baixar o PDF do ETP
              </a>
            )}
            <p className="text-tinta-2">O PDF é gerado agora e não fica guardado; só o código de conferência (hash) vai para a auditoria.</p>
          </section>

          {campoVazioNoTr.length > 0 && (
            <Aviso tipo="atencao" titulo="O TR repete campos vazios do ETP">
              <ul className="flex flex-col gap-1">
                {campoVazioNoTr.map((b) => (
                  <li key={b.bloco}>
                    {b.numero ? `${b.numero} ` : ""}
                    <Codigo>{b.bloco}</Codigo> repete <Codigo>{b.camposVazios.join(", ")}</Codigo>
                  </li>
                ))}
              </ul>
              <p>Complete o ETP antes: o TR não reescreve nem contradiz o ETP (M06).</p>
            </Aviso>
          )}

          {etp.justificativasSemCampo.length > 0 && (
            <Aviso tipo="atencao" titulo="Justificativas pedidas no ETP sem campo definido">
              <ul className="flex flex-col gap-2">
                {etp.justificativasSemCampo.map((j) => (
                  <li key={j.regra}>
                    <Codigo>{j.regra}</Codigo> {j.rotulo}
                    <br />
                    <span className="text-tinta-2">{j.texto}</span>
                  </li>
                ))}
              </ul>
              <p>O M04 manda pôr estas justificativas no ETP sem dizer o campo: cole-as no campo que couber.</p>
            </Aviso>
          )}

          <div className="flex flex-col gap-2 border border-linha bg-folha p-4 text-sm">
            <p className="font-semibold">Como ler o ETP</p>
            <p className="text-tinta-2">
              O ETP sai das mesmas respostas do TR. Texto escrito pelo requisitante ou pela equipe entra como está; dado curto leva o rótulo; resposta de opção do checklist leva a
              pergunta. Campo marcado &quot;IA&quot; no M01 fica para a equipe escrever: a primeira versão não usa IA.
            </p>
          </div>
        </aside>

        <article aria-label="Estudo Técnico Preliminar" className="mx-auto flex w-full max-w-[52rem] flex-col gap-2 border border-linha bg-folha px-5 py-8 leading-relaxed md:px-12 md:py-12 xl:order-1">
          {etp.campos.map((c, k) => (
            <Campo
              key={c.id}
              id={id}
              c={c}
              novaSecao={k === 0 || etp.campos[k - 1].secao.numero !== c.secao.numero}
              derivacao={derivacao}
              informar={informar.filter((x) => x.camposDoEtp[0] === c.id)}
              copiado={copiados.has(c.id)}
              podeCopiar={liberado && ids.has(c.id)}
              somenteLeitura={somenteLeitura}
            />
          ))}
        </article>
      </main>
    </>
  );
}

function Campo(props: {
  id: string;
  c: CampoDoEtp;
  novaSecao: boolean;
  derivacao: Derivacao;
  informar: CampoDoEtpParaInformar[];
  copiado: boolean;
  podeCopiar: boolean;
  somenteLeitura: boolean;
}) {
  const { id, c } = props;
  const [tipo, rotulo] = SITUACAO[c.situacao];
  const noTr = props.derivacao.porCampo[c.id] ?? [];
  return (
    <>
      {props.novaSecao && (
        <h2 className="mt-6 border-b border-linha-forte pb-1 text-lg font-semibold first:mt-0">
          {c.secao.numero}. {c.secao.nome}
        </h2>
      )}
      <section aria-labelledby={`campo-${c.id}`} className="flex flex-col gap-2 border-l-2 border-transparent py-2 pl-3 -ml-3">
        <div className="flex flex-wrap items-center gap-2">
          <h3 id={`campo-${c.id}`} className="min-w-0 flex-1 font-medium">
            {c.campo} <span className="font-mono text-xs text-tinta-2">{c.id}</span>
          </h3>
          {c.obrigatorio && <Selo tipo="padrao">Obrigatório</Selo>}
          <Selo tipo={tipo}>{rotulo}</Selo>
        </div>
        {c.texto ? (
          <div className="flex flex-col gap-2">
            {blocosDoCampo(c).map((b, k) =>
              b.tipo === "tabela" ? (
                <TabelaMarcada key={k} texto={b.texto} />
              ) : (
                <p key={k} className="whitespace-pre-line">
                  <TextoMarcado texto={b.texto} />
                </p>
              ),
            )}
          </div>
        ) : (
          <p className="text-sm text-tinta-2">{c.situacao === "texto_do_etp_digital" ? "O próprio ETP Digital imprime este texto; não há o que copiar." : c.orientacao.preenchimento}</p>
        )}
        {props.podeCopiar && <Copiar texto={textoDoCampo(c)} secao={c.id} copiada={props.copiado} registrar={registrarCopiaDoEtp.bind(null, id)} />}
        <details className="text-sm">
          <summary className="flex min-h-9 w-fit cursor-pointer items-center gap-1.5 text-tinta-2 underline">
            <Icone nome="origem" tamanho={14} />
            Origem e orientação
          </summary>
          <div className="mt-1 flex flex-col gap-1.5 border border-linha bg-papel p-3 leading-normal">
            {c.inciso && <p>Lei 14.133/2021, art. 18, inciso {c.inciso}.</p>}
            {c.partes.length > 0 && (
              <ul className="flex flex-col gap-1">
                {c.partes.map((parte, k) => (
                  <li key={k}>
                    <Codigo>{parte.regra}</Codigo> {parte.tipo === "tabela" ? "tabela de itens do TR" : parte.rotulo}
                    {parte.tipo === "dado" && <> · {origemDaParte(parte.origem, parte.texto)}</>}
                    {parte.tipo === "dado" && parte.ligacao === "M06" && " · decisão que o TR repete (M06)"}
                    {parte.tipo === "checklist" && " · resposta do checklist"}
                    {parte.tipo === "justificativa" && ` · justificativa da equipe (resposta ${textoDoValor(parte.resposta)})`}
                  </li>
                ))}
              </ul>
            )}
            {noTr.length > 0 && <p>No TR: {noTr.map((b) => (b.numero ? `${b.numero} (${b.bloco})` : b.bloco)).join(", ")}</p>}
            {c.validacoes.length > 0 && <p>Validações disparadas: {c.validacoes.join(", ")}</p>}
            <p>Como preencher: {c.orientacao.preenchimento}</p>
            {c.orientacao.quandoNaoSeAplica && <p>Quando não se aplica: {c.orientacao.quandoNaoSeAplica}</p>}
            {c.orientacao.antiAlucinacao && <p>Cuidado: {c.orientacao.antiAlucinacao}</p>}
          </div>
        </details>
        {!props.somenteLeitura && props.informar.length > 0 && (
          <details className="text-sm" open={c.situacao === "vazio" || c.situacao === "incompleto"}>
            <summary className="flex min-h-9 w-fit cursor-pointer items-center gap-1.5 text-tinta-2 underline">Informar os dados deste campo ({props.informar.length})</summary>
            <ul className="mt-1 grid gap-3 md:grid-cols-2">
              {props.informar.map((x) => (
                <li key={x.id} className={`flex flex-col gap-2 border border-l-4 border-linha bg-folha p-3 ${x.valorAtual === null ? "border-l-atencao" : "border-l-ok"}`}>
                  <p>
                    <Codigo>{x.id}</Codigo> · {x.descricao}
                  </p>
                  {x.doChecklist.length > 0 && x.valor === null && (
                    <p className="text-tinta-2">
                      Veio do checklist ({x.doChecklist.join(", ")}). O que a equipe informar aqui vale sobre o checklist.
                    </p>
                  )}
                  <FormularioCampo
                    acao={salvarCampoDoEtp.bind(null, id)}
                    c={{ id: x.id, descricao: x.descricao, validacao: x.validacao, codigos: x.codigos, forma: x.forma, valores: valoresDoFormulario(x), falta: x.valorAtual === null, multilinha: x.tipoDeDado === "TEXTO" }}
                  />
                </li>
              ))}
            </ul>
          </details>
        )}
      </section>
    </>
  );
}

function origemDaParte(origem: OrigemDaParte | null, texto: string | null): string {
  if (texto === null || origem === null) return "não informado";
  if (origem.de === "checklist") return `do checklist (${origem.perguntas.join(", ")})`;
  if (origem.de === "equipe") return "informado pela equipe";
  if (origem.de === "calculo") return "calculado pelo sistema";
  return "da entrada do processo";
}
