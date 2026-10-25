"use server";
/**
 * Pedidos do titular (LGPD, art. 18; decisão 0017). O usuário pede em nome próprio; o administrador da TI da mesma
 * OM responde. O RLS e a trava da tabela conferem as duas coisas de novo no banco. A auditoria guarda só o tipo e o
 * número do pedido, nunca o texto.
 */
import { and, eq, sql } from "drizzle-orm";
import { revalidatePath } from "next/cache";
import { z } from "zod";
import { registrar } from "../auditoria/registrar.ts";
import { bancoDaAplicacao, comoUsuario } from "../dados/conexao.ts";
import { TIPOS_DE_SOLICITACAO, solicitacaoTitular } from "../dados/esquema.ts";
import type { Resultado } from "./acoes.ts";
import { exigirUsuario } from "./sessao.ts";

const pedido = z.object({
  tipo: z.enum(TIPOS_DE_SOLICITACAO, { message: "Escolha o tipo do pedido." }),
  descricao: z.string().trim().min(5, "Descreva o pedido em poucas palavras.").max(2000, "Use até 2.000 caracteres."),
});

export async function fazerSolicitacao(_anterior: Resultado, dados: FormData): Promise<Resultado> {
  const u = await exigirUsuario();
  const lido = pedido.safeParse({ tipo: dados.get("tipo"), descricao: dados.get("descricao") });
  if (!lido.success) return { erro: lido.error.issues[0].message };
  await comoUsuario(bancoDaAplicacao(), u.id, async (tx) => {
    const [linha] = await tx.insert(solicitacaoTitular).values({ usuarioId: u.id, omId: u.omId, ...lido.data }).returning({ id: solicitacaoTitular.id });
    await registrar(tx, { usuarioId: u.id, omId: u.omId, acao: "SOLICITACAO_TITULAR_CRIADA", detalhes: { solicitacao: linha.id, tipo: lido.data.tipo } });
  });
  revalidatePath("/meus-dados");
  return { aviso: "Pedido registrado. A TI responde por esta tela; a resposta aparece na lista abaixo." };
}

const resposta = z.object({
  id: z.coerce.number().int().positive(),
  resposta: z.string().trim().min(5, "Escreva a resposta ao pedido.").max(2000, "Use até 2.000 caracteres."),
});

export async function responderSolicitacao(_anterior: Resultado, dados: FormData): Promise<Resultado> {
  const admin = await exigirUsuario("ADMINISTRADOR");
  const lido = resposta.safeParse({ id: dados.get("id"), resposta: dados.get("resposta") });
  if (!lido.success) return { erro: lido.error.issues[0].message };
  const feitas = await comoUsuario(bancoDaAplicacao(), admin.id, async (tx) => {
    const linhas = await tx
      .update(solicitacaoTitular)
      .set({ situacao: "RESPONDIDA", resposta: lido.data.resposta, respondidaEm: sql`now()`, respondidaPor: admin.id })
      .where(and(eq(solicitacaoTitular.id, lido.data.id), eq(solicitacaoTitular.situacao, "ABERTA")))
      .returning({ id: solicitacaoTitular.id });
    if (linhas.length) await registrar(tx, { usuarioId: admin.id, omId: admin.omId, acao: "SOLICITACAO_TITULAR_RESPONDIDA", detalhes: { solicitacao: lido.data.id } });
    return linhas.length;
  });
  if (!feitas) return { erro: "Pedido não encontrado ou já respondido." };
  revalidatePath("/admin/pedidos");
  return { aviso: "Resposta registrada. O usuário a vê na tela Meus dados." };
}
