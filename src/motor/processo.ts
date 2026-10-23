/**
 * Prepara os dados de um processo na ordem do README das matrizes: entrada; M11 (preenche, na ordem das linhas);
 * M05 por calculo_ordem; M04 calculo_expr (derivadas); M04 depende_de_expr (perguntas pendentes).
 * A montagem (M02, M04 liga/desliga, M08) e as validações (M10) leem os `dados` devolvidos aqui.
 */
import type { AvisoDoMotor, Lacuna } from "./avisos.ts";
import type { EntradaProcesso } from "./entrada.ts";
import { type Calculado, calcularM05 } from "./itens/calculo.ts";
import { type Globais, type Item, dadosGlobais, variaveisPorItem } from "./itens/contexto.ts";
import type { Valor } from "./pacote/avaliador.ts";
import { type OrigemDaResposta, type Sugestao, aplicarChecklist } from "./wizard/checklist.ts";
import { type SituacaoDoWizard, calcularDerivadas, situacaoDoWizard } from "./wizard/perguntas.ts";

export type ProcessoPreparado = {
  /** Globais finais: respostas, variáveis, metadados e parametros. */
  globais: Globais;
  itens: Item[];
  /** Globais com `itens` em contexto de item: o que as condições do M02, M04, M08 e M10 leem. */
  dados: Record<string, Valor>;
  porItem: Set<string>;
  preenchidoPeloChecklist: Record<string, Valor>;
  origens: Record<string, OrigemDaResposta>;
  origensDeItem: Record<string, string>;
  sugestoes: Sugestao[];
  calculados: Calculado[];
  derivadas: Record<string, Valor>;
  wizard: SituacaoDoWizard;
  avisos: AvisoDoMotor[];
  lacunas: Lacuna[];
};

export function prepararProcesso(entrada: EntradaProcesso): ProcessoPreparado {
  const { M04, M05, M11 } = entrada.pacote.matrizes;
  const porItem = variaveisPorItem(M11);
  const globaisDeEntrada: Globais = {
    ...entrada.checklist,
    ...(entrada.metadados as Record<string, Valor> | undefined),
    parametros: entrada.pacote.parametros,
  };
  const checklist = aplicarChecklist(M11, M04, M05, globaisDeEntrada, entrada.wizard, entrada.variaveis, entrada.itens as Item[], porItem);
  const calculo = calcularM05(M05, checklist.globais, checklist.itens, porItem);
  const derivadas = calcularDerivadas(M04, calculo.globais, calculo.itens, porItem);
  const dados = dadosGlobais(derivadas.globais, calculo.itens, porItem);
  return {
    globais: derivadas.globais,
    itens: calculo.itens,
    dados,
    porItem,
    preenchidoPeloChecklist: checklist.preenchidoPeloChecklist,
    origens: checklist.origens,
    origensDeItem: checklist.origensDeItem,
    sugestoes: checklist.sugestoes,
    calculados: calculo.calculados,
    derivadas: derivadas.derivadas,
    wizard: situacaoDoWizard(M04, dados),
    avisos: [...checklist.avisos, ...calculo.avisos, ...derivadas.avisos],
    lacunas: checklist.lacunas,
  };
}
