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

/** Entrada recusada dentro da gravação: desfaz a transação (nada gravado, nem auditoria) e volta como mensagem. */
export class EntradaRecusada extends Error {}

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

const ORDEM_DAS_ETAPAS = ["CHECKLIST", "ITENS", "WIZARD", "MINUTA", "EXPORTACAO"] as const;

/** Leva o processo à etapa indicada, se ele ainda não passou dela (o painel mostra a etapa mais adiantada). */
export async function avancarEtapa(tx: Transacao, p: ProcessoCompleto, etapa: (typeof ORDEM_DAS_ETAPAS)[number]): Promise<void> {
  if (ORDEM_DAS_ETAPAS.indexOf(etapa) > ORDEM_DAS_ETAPAS.indexOf(p.processo.etapa)) {
    await tx.update(processo).set({ etapa }).where(eq(processo.id, p.processo.id));
  }
}

/** Mensagem de erro de uma ação: processo concluído ou falha inesperada (sem detalhes internos na tela). */
export function mensagemDeErro(e: unknown): string {
  if (e instanceof ProcessoConcluido || e instanceof EntradaRecusada) return e.message;
  if (e && typeof e === "object" && "digest" in e) throw e; // redirect e notFound seguem adiante
  console.error(e);
  return "Não foi possível salvar. Tente de novo.";
}
