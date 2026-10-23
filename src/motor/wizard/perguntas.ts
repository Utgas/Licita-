/**
 * Wizard (M04): perguntas derivadas dos itens, perguntas habilitadas e pendentes.
 *
 * - Derivada: a pergunta com calculo_expr (WZ-09, 13, 18, 20, 24, 50) é calculada a partir dos itens e nunca
 *   fica pendente. Com dado ausente na conta, fica sem resposta, com aviso.
 * - Habilitada: depende_de_expr vazia ou verdadeira.
 * - Desligada: depende_de_expr igual a false (por exemplo, a WZ-56, comodato fora do sistema). Nunca é oferecida,
 *   e resposta que chegue para ela é descartada, com aviso.
 * - Pendente: habilitada e sem resposta. O motor nunca responde sozinho uma pergunta DECISAO_JURIDICA: ela fica
 *   pendente até a equipe responder (o checklist, no máximo, sugere).
 */
import type { AvisoDoMotor } from "../avisos.ts";
import { type Valor, avaliarComOcorrencias, iguais, verdadeiro } from "../pacote/avaliador.ts";
import type { LinhaM04 } from "../pacote/esquema.ts";
import { variavelDoId } from "../pacote/nomes.ts";
import { type Globais, type Item, dadosGlobais } from "../itens/contexto.ts";
import { vazia } from "./checklist.ts";

const MARCA_DE_DECISAO_JURIDICA = "DECISAO_JURIDICA";

export function ehDesligada(linha: LinhaM04): boolean {
  return linha.depende_de_expr === false;
}

export function ehDerivada(linha: LinhaM04): boolean {
  return linha.calculo_expr !== null;
}

/** Tira das respostas as perguntas desligadas e calcula as derivadas. */
export function calcularDerivadas(
  m04: readonly LinhaM04[],
  globaisDeEntrada: Globais,
  itens: readonly Item[],
  porItem: Set<string>,
): { globais: Globais; derivadas: Record<string, Valor>; avisos: AvisoDoMotor[] } {
  const globais: Globais = { ...globaisDeEntrada };
  const derivadas: Record<string, Valor> = {};
  const avisos: AvisoDoMotor[] = [];
  for (const linha of m04.filter(ehDesligada)) {
    const variavel = variavelDoId(linha.id);
    if (!vazia(globais[variavel])) {
      avisos.push({
        codigo: "PERGUNTA_DESLIGADA",
        mensagem: `${linha.id} está desligada no pacote; a resposta ${JSON.stringify(globais[variavel])} foi descartada.`,
        origem: { regra: linha.id },
      });
    }
    delete globais[variavel];
  }
  for (const linha of m04.filter(ehDerivada)) {
    const variavel = variavelDoId(linha.id);
    const { valor, ocorrencias } = avaliarComOcorrencias(linha.calculo_expr, dadosGlobais(globais, itens, porItem));
    const calculado = ocorrencias.length > 0 ? null : valor;
    if (ocorrencias.length > 0) {
      avisos.push({
        codigo: "CALCULO_SEM_DADO",
        mensagem: `${linha.id} ficou sem resposta: faltou dado dos itens para o cálculo.`,
        origem: { regra: linha.id },
      });
    }
    const informado = globais[variavel];
    if (!vazia(informado) && !iguais(informado, calculado)) {
      avisos.push({
        codigo: "VALOR_INFORMADO_SUBSTITUIDO",
        mensagem: `${linha.id}: informado ${JSON.stringify(informado)}, calculado pelos itens ${JSON.stringify(calculado)}; vale o calculado.`,
        origem: { regra: linha.id },
      });
    }
    globais[variavel] = calculado;
    derivadas[linha.id] = calculado;
  }
  return { globais, derivadas, avisos };
}

export type PerguntaPendente = { id: string; decisaoJuridica: boolean };

export type SituacaoDoWizard = {
  /** Perguntas que se aplicam ao processo (sem as derivadas), na ordem do M04. */
  habilitadas: string[];
  /** Habilitadas e sem resposta. */
  pendentes: PerguntaPendente[];
  desligadas: string[];
};

/** Perguntas habilitadas e pendentes, sobre os dados já com checklist, itens e derivadas. */
export function situacaoDoWizard(m04: readonly LinhaM04[], dados: Record<string, Valor>): SituacaoDoWizard {
  const habilitadas: string[] = [];
  const pendentes: PerguntaPendente[] = [];
  const desligadas: string[] = [];
  for (const linha of m04) {
    if (ehDesligada(linha)) {
      desligadas.push(linha.id);
      continue;
    }
    if (ehDerivada(linha)) continue;
    if (linha.depende_de_expr !== null && !verdadeiro(avaliarComOcorrencias(linha.depende_de_expr, dados).valor)) continue;
    habilitadas.push(linha.id);
    if (vazia(dados[variavelDoId(linha.id)])) {
      pendentes.push({ id: linha.id, decisaoJuridica: linha.pre_preenchida_por.startsWith(MARCA_DE_DECISAO_JURIDICA) });
    }
  }
  return { habilitadas, pendentes, desligadas };
}
