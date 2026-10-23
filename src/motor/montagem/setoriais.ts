/**
 * Cláusulas setoriais do M08: entram as de documento TR ou AMBOS cuja condicao_expr é verdadeira
 * (condicao_expr vazia ou false nunca entra).
 *
 * Ponto de inserção: a coluna ponto_insercao é texto. O motor lê dela só a parte do TR (antes de "ETP:") e o
 * primeiro bloco citado: a cláusula vai logo depois desse bloco e dos subitens dele. Sem bloco citado, ou com o
 * bloco fora da minuta, vai no fim da seção citada ("seção 5"); sem nada disso, no fim do corpo do TR.
 * O texto original do ponto de inserção acompanha a cláusula, para a revisão humana.
 */
import { type Valor, avaliar, verdadeiro } from "../pacote/avaliador.ts";
import type { LinhaM08 } from "../pacote/esquema.ts";

const DOCUMENTOS_DO_TR = new Set(["TR", "AMBOS"]);
const BLOCO_CITADO = /TR-[A-Za-z0-9]+(?:[.-][A-Za-z0-9]+)*/;
const SECAO_CITADA = /seção (\d+)/;

export type Ancora = { tipo: "depois_do_bloco"; bloco: string } | { tipo: "fim_da_secao"; secao: string } | { tipo: "fim_do_corpo" };

export function clausulasQueEntram(m08: readonly LinhaM08[], dados: Record<string, Valor>): LinhaM08[] {
  return m08.filter(
    (l) => DOCUMENTOS_DO_TR.has(l.documento) && l.condicao_expr !== null && l.condicao_expr !== false && verdadeiro(avaliar(l.condicao_expr, dados)),
  );
}

/** Parte do ponto de inserção que fala do TR. */
function parteDoTr(ponto: string): string {
  return ponto.split("ETP:")[0];
}

/**
 * Âncora da cláusula, dado o conjunto de blocos na minuta.
 * A seção do corpo do TR é o número antes do primeiro ponto do item ("5." em "5. CONDIÇÕES...").
 */
export function ancoraDaClausula(linha: LinhaM08, blocosNaMinuta: ReadonlySet<string>): Ancora {
  const parte = parteDoTr(linha.ponto_insercao);
  const bloco = BLOCO_CITADO.exec(parte)?.[0];
  if (bloco !== undefined && blocosNaMinuta.has(bloco)) return { tipo: "depois_do_bloco", bloco };
  const secao = SECAO_CITADA.exec(parte)?.[1] ?? (bloco !== undefined ? /^TR-(\d+)/.exec(bloco)?.[1] : undefined);
  return secao !== undefined ? { tipo: "fim_da_secao", secao } : { tipo: "fim_do_corpo" };
}
