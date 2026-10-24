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

export const dataBR = (d: Date | string) => new Date(d).toLocaleDateString("pt-BR", { timeZone: "America/Sao_Paulo" });

/** Código do pacote em texto legível: MENOR_PRECO -> Menor preco. Só para opções sem rótulo próprio. */
export function legivel(codigo: string): string {
  const s = codigo.replaceAll("_", " ").toLowerCase();
  return s.slice(0, 1).toUpperCase() + s.slice(1);
}
