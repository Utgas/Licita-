/**
 * Registro de auditoria (passo 4): toda escrita grava uma linha, dentro da mesma transação da escrita. A tabela só
 * aceita inclusão; o RLS confere que a linha é do próprio usuário e da própria OM.
 */
import type { Transacao } from "../dados/conexao.ts";
import { auditoria } from "../dados/esquema.ts";

export type Acao =
  | "LOGIN"
  | "SAIDA"
  | "SENHA_TROCADA"
  | "USUARIO_CRIADO"
  | "SENHA_PROVISORIA_DEFINIDA"
  | "USUARIO_DESATIVADO"
  | "USUARIO_REATIVADO"
  | "PROCESSO_CRIADO"
  | "PROCESSO_ALTERADO"
  | "CHECKLIST_LIDO"
  | "RESPOSTA_CHECKLIST"
  | "REVISAO_CONFIRMADA"
  | "COMPLEMENTO_OPERADOR"
  | "ITENS_ALTERADOS"
  | "ITENS_IMPORTADOS"
  | "RESPOSTA_WIZARD"
  | "MINUTA_GERADA"
  | "SECAO_COPIADA"
  | "PDF_BAIXADO"
  | "PROCESSO_CONCLUIDO";

export type Registro = {
  usuarioId: string;
  omId: string;
  acao: Acao;
  processoId?: string;
  /** Só identificadores e hashes: nunca senha, texto de resposta nem conteúdo do processo. */
  detalhes?: Record<string, string | number | boolean | null>;
  hashArquivo?: string;
  hashPacote?: string;
  hashPdf?: string;
};

export async function registrar(tx: Transacao, r: Registro): Promise<void> {
  await tx.insert(auditoria).values({
    usuarioId: r.usuarioId,
    omId: r.omId,
    acao: r.acao,
    processoId: r.processoId ?? null,
    detalhes: r.detalhes ?? {},
    hashArquivo: r.hashArquivo ?? null,
    hashPacote: r.hashPacote ?? null,
    hashPdf: r.hashPdf ?? null,
  });
}
