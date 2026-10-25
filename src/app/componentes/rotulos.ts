/** Rótulos de interface para os códigos guardados no banco (não é texto jurídico). */
export const ETAPAS = [
  { codigo: "CHECKLIST", rotulo: "Checklist", caminho: "checklist" },
  { codigo: "ITENS", rotulo: "Itens", caminho: "itens" },
  { codigo: "WIZARD", rotulo: "Wizard", caminho: "wizard" },
  { codigo: "MINUTA", rotulo: "Minuta", caminho: "revisao" },
  { codigo: "EXPORTACAO", rotulo: "Exportar", caminho: "exportar" },
] as const;

export const SITUACOES: Record<string, string> = {
  RASCUNHO: "Rascunho",
  EM_REVISAO: "Em revisão",
  LIBERADO: "Liberado",
  CONCLUIDO: "Concluído",
};

export const MODALIDADES: Record<string, string> = {
  PREGAO: "Pregão",
  CONCORRENCIA: "Concorrência",
  CONTRATACAO_DIRETA: "Contratação direta (dispensa ou inexigibilidade)",
};

export const CHECKLISTS: Record<string, string> = { CONSUMO: "Consumo", PERMANENTES: "Permanentes" };

/** Pedidos do titular (LGPD, art. 18). */
export const TIPOS_DE_SOLICITACAO: Record<string, string> = {
  CONFIRMACAO_ACESSO: "Confirmar se tratamos meus dados e ter acesso a eles",
  CORRECAO: "Corrigir dado incompleto, errado ou desatualizado",
  ANONIMIZACAO_BLOQUEIO_ELIMINACAO: "Anonimizar, bloquear ou eliminar dado desnecessário ou excessivo",
  PORTABILIDADE: "Receber meus dados em formato aberto",
  INFORMACAO_COMPARTILHAMENTO: "Saber com quem meus dados são compartilhados",
  OPOSICAO: "Opor-me a um tratamento",
  OUTRO: "Outro pedido ou dúvida sobre meus dados",
};

export const dataHoraBR = (d: Date | string) => new Date(d).toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" });

export const dataBR = (d: Date | string) => new Date(d).toLocaleDateString("pt-BR", { timeZone: "America/Sao_Paulo" });

/** Código do pacote em texto legível: MENOR_PRECO -> Menor preco. Só para opções sem rótulo próprio. */
export function legivel(codigo: string): string {
  const s = codigo.replaceAll("_", " ").toLowerCase();
  return s.slice(0, 1).toUpperCase() + s.slice(1);
}
