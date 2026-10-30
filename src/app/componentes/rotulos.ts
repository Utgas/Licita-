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

/**
 * Pergunta do checklist em linguagem de tela: CK-P-2.4 -> "Permanentes 2.4", CK-C-CAB.01 -> "Consumo, cabeçalho",
 * CK-X-07 -> "Complemento 7". O ID continua guardado e aparece ao passar o mouse (rastreabilidade); aqui só muda o
 * que se lê. Outro código volta como está.
 */
export function nomeDaPergunta(id: string): string {
  const ck = /^CK-([CP])-(.+)$/.exec(id);
  if (ck) {
    const checklist = ck[1] === "C" ? "Consumo" : "Permanentes";
    return ck[2].startsWith("CAB.") ? `${checklist}, cabeçalho` : `${checklist} ${ck[2]}`;
  }
  const complemento = /^CK-X-0*(\d+)$/.exec(id);
  if (complemento) return `Complemento ${complemento[1]}`;
  return id;
}
