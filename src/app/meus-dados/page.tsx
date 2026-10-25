import Link from "next/link";
import { Suspense } from "react";
import { exigirUsuario } from "@/auth/sessao.ts";
import { bancoDaAplicacao, comoUsuario } from "@/dados/conexao.ts";
import { dadosPessoais } from "@/dados/dados-pessoais.ts";
import { Cabecalho, Carregando, Conteudo } from "../componentes/cabecalho.tsx";
import { TIPOS_DE_SOLICITACAO, dataHoraBR, legivel } from "../componentes/rotulos.ts";
import { Selo, TituloDeSecao, classesDoBotao } from "../componentes/ui.tsx";
import { NovoPedido } from "./formulario.tsx";

const LIMITE = 50;

/** Meus dados (LGPD, art. 18; decisão 0017): o que o sistema guarda sobre o usuário, a cópia em JSON e os pedidos. */
export default function MeusDados() {
  return (
    <Suspense fallback={<Carregando />}>
      <Tela />
    </Suspense>
  );
}

async function Tela() {
  const u = await exigirUsuario();
  const { cadastro, acoes, pedidos } = await comoUsuario(bancoDaAplicacao(), u.id, (tx) => dadosPessoais(tx, u, LIMITE));
  const linhas: [string, string][] = [
    ["Nome", cadastro.nome],
    ["E-mail", cadastro.email],
    ["Perfil", cadastro.perfil === "ADMINISTRADOR" ? "Administrador da TI" : "Operador"],
    ["OM", cadastro.om],
    ["Situação", cadastro.ativo ? "Ativo" : "Desativado"],
    ["Cadastrado em", dataHoraBR(cadastro.criadoEm)],
  ];
  return (
    <>
      <Cabecalho usuario={u} />
      <Conteudo>
        <div className="flex flex-col gap-2">
          <h1 className="text-2xl font-semibold">Meus dados</h1>
          <p className="max-w-3xl text-tinta-2">
            Tudo o que o Licita+ guarda sobre você. A senha não aparece: o sistema guarda só um resumo cifrado dela
            (hash), que nem a TI consegue ler. Saiba mais na{" "}
            <Link href="/privacidade" className="underline">
              Política de Privacidade
            </Link>
            .
          </p>
        </div>

        <section className="flex flex-col gap-4">
          <TituloDeSecao>Cadastro</TituloDeSecao>
          <dl className="grid max-w-2xl grid-cols-[max-content_1fr] gap-x-6 gap-y-2">
            {linhas.map(([rotulo, valor]) => (
              <div key={rotulo} className="contents">
                <dt className="font-medium">{rotulo}</dt>
                <dd>{valor}</dd>
              </div>
            ))}
          </dl>
          <p className="text-tinta-2">Algum dado errado? Peça a correção abaixo.</p>
          <a href="/meus-dados/exportar" className={`${classesDoBotao("secundario")} w-fit`} download>
            Baixar uma cópia dos meus dados (JSON)
          </a>
        </section>

        <section className="flex flex-col gap-4">
          <TituloDeSecao complemento={`últimas ${LIMITE}`}>Minhas ações registradas</TituloDeSecao>
          {acoes.length === 0 ? (
            <p className="text-tinta-2">Nenhuma ação registrada.</p>
          ) : (
            <table className="w-full max-w-3xl border-collapse border border-linha bg-folha text-left text-sm">
              <caption className="sr-only">Ações registradas na auditoria em seu nome</caption>
              <thead>
                <tr className="border-b border-linha-forte bg-papel text-xs uppercase tracking-wide text-tinta-2">
                  <th scope="col" className="px-3 py-2.5 font-medium">Quando</th>
                  <th scope="col" className="px-3 py-2.5 font-medium">Ação</th>
                </tr>
              </thead>
              <tbody>
                {acoes.map((a, i) => (
                  <tr key={i} className="border-b border-linha">
                    <td className="px-3 py-2">{dataHoraBR(a.em)}</td>
                    <td className="px-3 py-2">{legivel(a.acao)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        <section className="flex flex-col gap-4">
          <TituloDeSecao>Fazer um pedido sobre meus dados</TituloDeSecao>
          <p className="max-w-3xl text-tinta-2">
            Pela Lei Geral de Proteção de Dados (Lei nº 13.709/2018, art. 18), você pode pedir confirmação, acesso,
            correção, eliminação de dado desnecessário, cópia e informações sobre o uso dos seus dados. A TI da OM
            recebe o pedido e responde nesta tela.
          </p>
          <NovoPedido />
        </section>

        <section className="flex flex-col gap-4">
          <TituloDeSecao>Meus pedidos</TituloDeSecao>
          {pedidos.length === 0 ? (
            <p className="text-tinta-2">Você ainda não fez pedidos.</p>
          ) : (
            <ul className="flex max-w-3xl flex-col gap-3">
              {pedidos.map((p) => (
                <li key={p.id} className="flex flex-col gap-2 border border-linha bg-folha p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="font-medium">{TIPOS_DE_SOLICITACAO[p.tipo]}</p>
                    <Selo tipo={p.situacao === "RESPONDIDA" ? "ok" : "pendente"}>{p.situacao === "RESPONDIDA" ? "Respondido" : "Aguardando a TI"}</Selo>
                  </div>
                  <p className="text-sm text-tinta-2">Feito em {dataHoraBR(p.criadaEm)}</p>
                  <p className="whitespace-pre-wrap">{p.descricao}</p>
                  {p.resposta && (
                    <div className="border-l-4 border-ok bg-ok-fundo p-3">
                      <p className="text-sm font-medium">Resposta da TI{p.respondidaEm ? `, em ${dataHoraBR(p.respondidaEm)}` : ""}</p>
                      <p className="whitespace-pre-wrap">{p.resposta}</p>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </section>
      </Conteudo>
    </>
  );
}
