/**
 * Leitura da coluna exige_justificativa do M04 para a tela do wizard: "N" não exige; "S" ou "S: ..." exige sempre;
 * "S se A ou B: ..." exige só com a resposta A ou B. O texto mostrado ao operador é o da própria coluna.
 */
export function justificativaObrigatoria(regra: string, valor: unknown): boolean {
  const r = regra.trim();
  if (/^S(\s*:|$)/.test(r)) return true;
  const se = /^S se ([A-Z_]+(?:\s+ou\s+[A-Z_]+)*)\s*:/.exec(r);
  if (!se) return false;
  const valores = se[1].split(/\s+ou\s+/);
  return (Array.isArray(valor) ? valor : [valor]).some((v) => valores.includes(String(v)));
}

export const pedeJustificativa = (regra: string) => regra.trim().startsWith("S");

/** Opções do M04 ("SIM; NAO"); vazio para pergunta de número ou texto. */
export function opcoesDaPergunta(tipo: string, opcoes: string): string[] {
  if (tipo !== "UNICA" && tipo !== "SIM_NAO" && tipo !== "MULTIPLA") return [];
  return opcoes
    .split(/;\s*/)
    .map((o) => o.trim())
    .filter(Boolean);
}
