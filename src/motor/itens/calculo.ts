/**
 * Cálculos do M05 (calculo_expr), na ordem de calculo_ordem.
 *
 * Linha "tabela_itens.<atributo>": avaliada item a item, com o item no topo, itens_do_grupo e itens.
 * Demais linhas: avaliadas uma vez, sobre os globais, e gravadas como VAR_xxx.
 * Os números de lei e os valores monetários vêm do M12 (parametros); nada disso está aqui.
 *
 * Resultado que dependeu de dado ausente (conta ou comparação com ausente, texto no lugar de número,
 * divisão impossível) vira lacuna: o valor fica null e sai um aviso CALCULO_SEM_DADO.
 */
import type { AvisoDoMotor } from "../avisos.ts";
import { type Ocorrencia, type Valor, avaliarComOcorrencias, iguais } from "../pacote/avaliador.ts";
import type { LinhaM05 } from "../pacote/esquema.ts";
import { variavelDoId } from "../pacote/nomes.ts";
import { type Globais, type Item, dadosDoItem, dadosGlobais } from "./contexto.ts";

const PREFIXO_DE_ITEM = "tabela_itens.";

/**
 * Cota igual a zero (decisão do Gabriel, 23/10/2026; docs/decisoes/0008): o item deve ficar sem cota, com alerta.
 * Enquanto a regra não entra na matriz, o motor só avisa e não muda o tratamento.
 * Os nomes abaixo são os do M05 (VAR-113 e VAR-118) e o valor COTA é o da VAR-113.
 */
const ATRIBUTO_DO_TRATAMENTO = "tratamento_me_epp";
const ATRIBUTO_DA_QUANTIDADE_DA_COTA = "quantidade_cota";
const TRATAMENTO_COM_COTA = "COTA";

/** De onde veio cada valor calculado (para rastrear o trecho da minuta até a regra). */
export type Calculado = { regra: string; destino: string; item?: number; valor: Valor };

export type ResultadoDoCalculo = {
  itens: Item[];
  globais: Globais;
  calculados: Calculado[];
  avisos: AvisoDoMotor[];
};

function descreverOcorrencias(ocorrencias: Ocorrencia[]): string {
  const textos = ocorrencias.map((o) => {
    switch (o.tipo) {
      case "valor_ausente":
        return `valor ausente em "${o.operador}"`;
      case "valor_nao_numerico":
        return `valor ${JSON.stringify(o.valor)} não é número em "${o.operador}"`;
      case "divisao_por_zero":
        return `divisão por zero em "${o.operador}"`;
      case "divisao_sem_decimal_exato":
        return `divisão sem resultado decimal exato em "${o.operador}"`;
      case "resultado_sem_precisao":
        return `resultado com dígitos demais em "${o.operador}"`;
    }
  });
  return [...new Set(textos)].join("; ");
}

/** Avalia e aplica a regra da lacuna: com ocorrência, o resultado é null e sai um aviso. */
function calcular(linha: LinhaM05, dados: Valor, avisos: AvisoDoMotor[], item?: number): Valor {
  const { valor, ocorrencias } = avaliarComOcorrencias(linha.calculo_expr, dados);
  if (ocorrencias.length === 0) return valor;
  const onde = item === undefined ? "" : ` no item ${item}`;
  avisos.push({
    codigo: "CALCULO_SEM_DADO",
    mensagem: `${linha.id} (${linha.nome})${onde} ficou sem valor: ${descreverOcorrencias(ocorrencias)}.`,
    origem: { regra: linha.id, item },
  });
  return null;
}

function avisarSeSubstituiu(anterior: Valor | undefined, novo: Valor, linha: LinhaM05, avisos: AvisoDoMotor[], item?: number) {
  if (anterior === undefined || anterior === null || iguais(anterior, novo)) return;
  const onde = item === undefined ? "" : ` do item ${item}`;
  avisos.push({
    codigo: "VALOR_INFORMADO_SUBSTITUIDO",
    mensagem: `${linha.id} (${linha.nome})${onde}: informado ${JSON.stringify(anterior)}, calculado ${JSON.stringify(novo)}; vale o calculado.`,
    origem: { regra: linha.id, item },
  });
}

/** Linhas do M05 com cálculo, na ordem de cálculo. */
export function linhasDeCalculo(m05: readonly LinhaM05[]): LinhaM05[] {
  return m05
    .filter((l) => l.calculo_expr !== null && l.calculo_ordem !== null)
    .sort((a, b) => (a.calculo_ordem as number) - (b.calculo_ordem as number));
}

/**
 * Calcula os atributos de item e as variáveis do M05.
 * Não altera a entrada: devolve itens e globais novos.
 */
export function calcularM05(
  m05: readonly LinhaM05[],
  globaisDeEntrada: Globais,
  itensDeEntrada: readonly Item[],
  porItem: Set<string>,
): ResultadoDoCalculo {
  let itens: Item[] = itensDeEntrada.map((item) => ({ ...item }));
  const globais: Globais = { ...globaisDeEntrada };
  const calculados: Calculado[] = [];
  const avisos: AvisoDoMotor[] = [];

  for (const linha of linhasDeCalculo(m05)) {
    if (linha.nome.startsWith(PREFIXO_DE_ITEM)) {
      const atributo = linha.nome.slice(PREFIXO_DE_ITEM.length);
      // Todos os itens leem o mesmo retrato: o valor novo de um item não entra no cálculo do outro.
      const novos = itens.map((item) => calcular(linha, dadosDoItem(globais, item, itens, porItem), avisos, item.numero));
      itens = itens.map((item, i) => {
        avisarSeSubstituiu(item[atributo] as Valor | undefined, novos[i], linha, avisos, item.numero);
        calculados.push({ regra: linha.id, destino: `itens.${atributo}`, item: item.numero, valor: novos[i] });
        return { ...item, [atributo]: novos[i] };
      });
    } else {
      const variavel = variavelDoId(linha.id);
      const valor = calcular(linha, dadosGlobais(globais, itens, porItem), avisos);
      avisarSeSubstituiu(globais[variavel], valor, linha, avisos);
      globais[variavel] = valor;
      calculados.push({ regra: linha.id, destino: variavel, valor });
    }
  }

  const regraDaCota = m05.find((l) => l.nome === PREFIXO_DE_ITEM + ATRIBUTO_DA_QUANTIDADE_DA_COTA)?.id ?? ATRIBUTO_DA_QUANTIDADE_DA_COTA;
  for (const item of itens) {
    if (item[ATRIBUTO_DO_TRATAMENTO] === TRATAMENTO_COM_COTA && item[ATRIBUTO_DA_QUANTIDADE_DA_COTA] === 0) {
      avisos.push({
        codigo: "COTA_ZERO",
        mensagem: `Item ${item.numero}: tratamento ${TRATAMENTO_COM_COTA} com quantidade da cota igual a zero. Pela decisão de 23/10/2026 o item fica sem cota, em ampla participação; a regra ainda não está na matriz, e o tratamento não foi alterado.`,
        origem: { regra: regraDaCota, item: item.numero },
      });
    }
  }
  return { itens, globais, calculados, avisos };
}
