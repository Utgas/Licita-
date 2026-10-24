/**
 * Cláusulas setoriais do M08: entram as de documento TR ou AMBOS cuja condicao_expr é verdadeira
 * (condicao_expr vazia ou false nunca entra).
 *
 * Posição e numeração (Fase 13 das matrizes): inserir_apos é o bloco do M02 depois do qual a cláusula entra, com os
 * subitens dele; nivel diz como ela é numerada (MESMO_NIVEL: item seguinte no nível do bloco; SUBITEM: último subitem
 * do bloco; PREENCHE_BLOCO: não entra como texto, só preenche as lacunas do bloco). Se o bloco não está na minuta,
 * vale o primeiro de inserir_apos_alternativo ("TR-5.4 (SUBITEM); TR-5.2 (MESMO_NIVEL)") que estiver. Sem nenhum,
 * a cláusula vai para o fim do corpo do TR, sem número.
 */
import { type Valor, avaliar, verdadeiro } from "../pacote/avaliador.ts";
import type { LinhaM08 } from "../pacote/esquema.ts";

const DOCUMENTOS_DO_TR = new Set(["TR", "AMBOS"]);
const ALTERNATIVA = /(TR-[A-Za-z0-9]+(?:[.-][A-Za-z0-9]+)*)\s*\((MESMO_NIVEL|SUBITEM)\)/g;

export type Insercao =
  | { tipo: "preenche_bloco"; bloco: string }
  | { tipo: "apos"; bloco: string; nivel: "MESMO_NIVEL" | "SUBITEM"; alternativa: boolean }
  | { tipo: "fim_do_corpo" };

export function clausulasQueEntram(m08: readonly LinhaM08[], dados: Record<string, Valor>): LinhaM08[] {
  return m08.filter(
    (l) => DOCUMENTOS_DO_TR.has(l.documento) && l.condicao_expr !== null && l.condicao_expr !== false && verdadeiro(avaliar(l.condicao_expr, dados)),
  );
}

export function insercaoDaClausula(linha: LinhaM08, blocosNaMinuta: ReadonlySet<string>): Insercao {
  if (linha.nivel === "PREENCHE_BLOCO") return { tipo: "preenche_bloco", bloco: linha.inserir_apos };
  if (linha.inserir_apos && blocosNaMinuta.has(linha.inserir_apos) && linha.nivel !== "") {
    return { tipo: "apos", bloco: linha.inserir_apos, nivel: linha.nivel, alternativa: false };
  }
  for (const [, bloco, nivel] of linha.inserir_apos_alternativo.matchAll(ALTERNATIVA)) {
    if (blocosNaMinuta.has(bloco)) return { tipo: "apos", bloco, nivel: nivel as "MESMO_NIVEL" | "SUBITEM", alternativa: true };
  }
  return { tipo: "fim_do_corpo" };
}
