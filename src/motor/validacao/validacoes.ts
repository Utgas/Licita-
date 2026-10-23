/**
 * Validações do M10 (tarefa do Marco 1, passo 7).
 *
 * - Regra com condicao_expr verdadeira: dispara, como ALERTA, BLOQUEIO ou INFORMATIVO (coluna tipo).
 * - Regra sem condicao_expr (P27 das matrizes): não é avaliada; vai para a lista de conferência manual.
 * - Regra com condicao_expr false (linha desligada, como a VAL-027): nunca dispara nem é listada.
 */
import { type Valor, avaliar, verdadeiro } from "../pacote/avaliador.ts";
import type { LinhaM10 } from "../pacote/esquema.ts";

export type ValidacaoDisparada = {
  id: string;
  tipo: LinhaM10["tipo"];
  momento: LinhaM10["momento"];
  mensagem: string;
};

export type ResultadoDasValidacoes = {
  /** Disparadas, na ordem do M10. */
  disparadas: ValidacaoDisparada[];
  /** Regras sem expressão: alguém confere à mão. */
  conferenciaManual: { id: string; regra: string; mensagem: string }[];
};

export function validar(m10: readonly LinhaM10[], dados: Record<string, Valor>): ResultadoDasValidacoes {
  const disparadas: ValidacaoDisparada[] = [];
  const conferenciaManual: ResultadoDasValidacoes["conferenciaManual"] = [];
  for (const linha of m10) {
    if (linha.condicao_expr === false) continue;
    if (linha.condicao_expr === null) {
      conferenciaManual.push({ id: linha.id, regra: linha.regra, mensagem: linha.mensagem });
      continue;
    }
    if (verdadeiro(avaliar(linha.condicao_expr, dados))) {
      disparadas.push({ id: linha.id, tipo: linha.tipo, momento: linha.momento, mensagem: linha.mensagem });
    }
  }
  return { disparadas, conferenciaManual };
}
