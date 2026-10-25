import { asc, desc } from "drizzle-orm";
import { Suspense } from "react";
import { exigirUsuario } from "@/auth/sessao.ts";
import { bancoDaAplicacao, comoUsuario } from "@/dados/conexao.ts";
import { solicitacaoTitular, usuario } from "@/dados/esquema.ts";
import { Cabecalho, Carregando, Conteudo } from "../../componentes/cabecalho.tsx";
import { TIPOS_DE_SOLICITACAO, dataHoraBR } from "../../componentes/rotulos.ts";
import { Selo, TituloDeSecao } from "../../componentes/ui.tsx";
import { ResponderPedido } from "../../meus-dados/formulario.tsx";

/** Pedidos dos usuários sobre os próprios dados (LGPD, art. 18; decisão 0017): a TI da OM lê e responde. */
export default function Pedidos() {
  return (
    <Suspense fallback={<Carregando />}>
      <Tela />
    </Suspense>
  );
}

async function Tela() {
  const admin = await exigirUsuario("ADMINISTRADOR");
  const { pedidos, nomes } = await comoUsuario(bancoDaAplicacao(), admin.id, async (tx) => ({
    pedidos: await tx.select().from(solicitacaoTitular).orderBy(asc(solicitacaoTitular.situacao), desc(solicitacaoTitular.id)),
    nomes: new Map((await tx.select({ id: usuario.id, nome: usuario.nome }).from(usuario)).map((u) => [u.id, u.nome])),
  }));
  const abertos = pedidos.filter((p) => p.situacao === "ABERTA").length;
  return (
    <>
      <Cabecalho usuario={admin} />
      <Conteudo>
        <div className="flex flex-col gap-2">
          <h1 className="text-2xl font-semibold">Pedidos sobre dados pessoais</h1>
          <p className="max-w-3xl text-tinta-2">
            Pedidos dos usuários da OM com base na LGPD (art. 18). Responda em até 15 dias (art. 19, II) e, quando o
            pedido envolver decisão sobre o tratamento, consulte o encarregado de dados da OM antes de responder.
          </p>
        </div>
        <TituloDeSecao complemento={`${abertos} aguardando resposta`}>Pedidos</TituloDeSecao>
        {pedidos.length === 0 ? (
          <p className="text-tinta-2">Nenhum pedido.</p>
        ) : (
          <ul className="flex max-w-3xl flex-col gap-3">
            {pedidos.map((p) => (
              <li key={p.id} className="flex flex-col gap-2 border border-linha bg-folha p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="font-medium">
                    Nº {p.id} · {TIPOS_DE_SOLICITACAO[p.tipo]}
                  </p>
                  <Selo tipo={p.situacao === "RESPONDIDA" ? "ok" : "pendente"}>{p.situacao === "RESPONDIDA" ? "Respondido" : "Aguardando resposta"}</Selo>
                </div>
                <p className="text-sm text-tinta-2">
                  {nomes.get(p.usuarioId) ?? "Usuário"}, em {dataHoraBR(p.criadaEm)}
                </p>
                <p className="whitespace-pre-wrap">{p.descricao}</p>
                {p.resposta ? (
                  <div className="border-l-4 border-ok bg-ok-fundo p-3">
                    <p className="text-sm font-medium">
                      Resposta de {p.respondidaPor ? (nomes.get(p.respondidaPor) ?? "TI") : "TI"}
                      {p.respondidaEm ? `, em ${dataHoraBR(p.respondidaEm)}` : ""}
                    </p>
                    <p className="whitespace-pre-wrap">{p.resposta}</p>
                  </div>
                ) : (
                  <ResponderPedido id={p.id} />
                )}
              </li>
            ))}
          </ul>
        )}
      </Conteudo>
    </>
  );
}
