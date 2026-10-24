/**
 * Acesso do operador a um processo: abre com o RLS dele e grava sempre na mesma transação que a auditoria (passo 4).
 * Processo concluído não aceita escrita: espera o expurgo.
 */
import { eq, sql } from "drizzle-orm";
import { notFound } from "next/navigation";
import { type Acao, registrar } from "../auditoria/registrar.ts";
import { type UsuarioLogado, exigirUsuario } from "../auth/sessao.ts";
import { type Transacao, bancoDaAplicacao, comoUsuario } from "./conexao.ts";
import { processo } from "./esquema.ts";
import { type ProcessoCompleto, carregarProcesso } from "./processos.ts";

export async function abrirProcesso(id: string): Promise<{ usuario: UsuarioLogado; p: ProcessoCompleto }> {
  const usuario = await exigirUsuario("OPERADOR");
  const p = await comoUsuario(bancoDaAplicacao(), usuario.id, (tx) => carregarProcesso(tx, id));
  if (!p) notFound();
  return { usuario, p };
}

export class ProcessoConcluido extends Error {}

/**
 * Grava no processo: confere sessão e perfil, abre o processo com o RLS, roda a escrita e registra a ação na
 * auditoria, tudo numa transação. `detalhes` não leva texto de resposta, só identificadores e hashes.
 */
export async function gravarNoProcesso<T>(
  id: string,
  acao: Acao,
  escrever: (tx: Transacao, p: ProcessoCompleto, usuario: UsuarioLogado) => Promise<{ resultado: T; detalhes?: Record<string, string | number | boolean | null>; hashArquivo?: string; hashPdf?: string }>,
): Promise<T> {
  const usuario = await exigirUsuario("OPERADOR");
  return comoUsuario(bancoDaAplicacao(), usuario.id, async (tx) => {
    const p = await carregarProcesso(tx, id);
    if (!p) notFound();
    if (p.processo.situacao === "CONCLUIDO") throw new ProcessoConcluido("Processo concluído: não aceita alterações.");
    const { resultado, detalhes, hashArquivo, hashPdf } = await escrever(tx, p, usuario);
    await tx.update(processo).set({ atualizadoEm: sql`now()` }).where(eq(processo.id, id));
    await registrar(tx, { usuarioId: usuario.id, omId: usuario.omId, processoId: id, acao, detalhes, hashArquivo, hashPdf, hashPacote: p.processo.pacoteHash });
    return resultado;
  });
}
