/**
 * Dados pessoais do usuário logado (LGPD, art. 18, I, II e V; decisão 0017): o cadastro, as linhas da auditoria
 * feitas por ele e os pedidos que ele fez. Lido com o RLS do próprio usuário.
 */
import { desc, eq } from "drizzle-orm";
import type { UsuarioLogado } from "../auth/sessao.ts";
import { type Transacao } from "./conexao.ts";
import { auditoria, om, solicitacaoTitular, usuario } from "./esquema.ts";

export async function dadosPessoais(tx: Transacao, u: UsuarioLogado, limiteDaAuditoria?: number) {
  const [cadastro] = await tx
    .select({ nome: usuario.nome, email: usuario.email, perfil: usuario.perfil, ativo: usuario.ativo, criadoEm: usuario.criadoEm, om: om.nome })
    .from(usuario)
    .innerJoin(om, eq(om.id, usuario.omId))
    .where(eq(usuario.id, u.id));
  const consulta = tx
    .select({ em: auditoria.em, acao: auditoria.acao, processoId: auditoria.processoId })
    .from(auditoria)
    .where(eq(auditoria.usuarioId, u.id))
    .orderBy(desc(auditoria.id));
  const acoes = limiteDaAuditoria ? await consulta.limit(limiteDaAuditoria) : await consulta;
  const pedidos = await tx.select().from(solicitacaoTitular).where(eq(solicitacaoTitular.usuarioId, u.id)).orderBy(desc(solicitacaoTitular.id));
  return { cadastro, acoes, pedidos };
}
