/**
 * Do checklist para o wizard (M11): preenchimento, sugestões e revisão das respostas.
 *
 * Regras (README das matrizes, colunas da Fase 10 e 11; tarefa do Marco 1, passo 4):
 * - preenche_expr e sugere_expr só valem com a pergunta respondida e a condicional verdadeira; resultado null
 *   não conta. As perguntas são lidas na ordem das linhas do M11, e o que uma preenche a seguinte já enxerga.
 * - PREENCHE nunca passa por cima da equipe: se a equipe respondeu outra coisa, vale a equipe, com aviso.
 * - Duas perguntas que preenchem a mesma WZ com valores diferentes deixam a WZ sem resposta, com aviso.
 * - Destino VAR_xxx com várias contribuições: TEXTO junta em linhas, LISTA e TABELA juntam em lista, os demais
 *   ficam com a primeira e acusam conflito se outra for diferente.
 * - Valor que não bate com o tipo do M05 (texto numa variável NUMERO ou MOEDA) não é convertido: vira lacuna.
 * - Pergunta do wizard marcada DECISAO_JURIDICA nunca é preenchida pelo checklist: no máximo recebe sugestão.
 * - SUGERE só mostra; quem decide é a equipe.
 */
import type { AvisoDoMotor, Lacuna } from "../avisos.ts";
import { type Valor, avaliar, iguais, verdadeiro } from "../pacote/avaliador.ts";
import type { LinhaM04, LinhaM05, LinhaM11 } from "../pacote/esquema.ts";
import { variavelDoId } from "../pacote/nomes.ts";
import { type Globais, type Item, dadosDoItem, dadosGlobais } from "../itens/contexto.ts";

const MARCA_DE_DECISAO_JURIDICA = "DECISAO_JURIDICA";
const TIPOS_NUMERICOS = new Set(["NUMERO", "MOEDA"]);
const TIPOS_DE_LISTA = new Set(["LISTA", "TABELA"]);

export type Sugestao = { destino: string; item?: number; valor: Valor; pergunta: string };

/** De onde veio a resposta de uma WZ ou o valor de uma VAR. */
export type OrigemDaResposta = { origem: "EQUIPE" | "ENTRADA" } | { origem: "CHECKLIST"; perguntas: string[] };

export type ResultadoDoChecklist = {
  /** Globais com as respostas do wizard e as variáveis já preenchidas pelo checklist. */
  globais: Globais;
  itens: Item[];
  /** WZ preenchidas pelo checklist (destino -> valor), como em referencia.preenchido_pelo_checklist. */
  preenchidoPeloChecklist: Record<string, Valor>;
  origens: Record<string, OrigemDaResposta>;
  /** Atributo de item preenchido pelo checklist: "numero.atributo" -> pergunta. */
  origensDeItem: Record<string, string>;
  sugestoes: Sugestao[];
  avisos: AvisoDoMotor[];
  lacunas: Lacuna[];
};

/** Resposta vazia: ausente, null, texto vazio ou lista vazia. */
export function vazia(v: Valor | undefined): boolean {
  return v === undefined || v === null || v === "" || (Array.isArray(v) && v.length === 0);
}

function tipoCompativel(valor: Valor, tipo: string | undefined): boolean {
  return !TIPOS_NUMERICOS.has(tipo ?? "") || typeof valor === "number";
}

function juntar(atual: Valor, novo: Valor, tipo: string): { valor: Valor; conflito: boolean } {
  if (vazia(atual)) return { valor: novo, conflito: false };
  if (tipo === "TEXTO") {
    return { valor: Array.isArray(atual) ? [...atual, novo] : `${String(atual)}\n${String(novo)}`, conflito: false };
  }
  if (TIPOS_DE_LISTA.has(tipo)) {
    const lista = Array.isArray(atual) ? atual : [atual];
    return { valor: [...lista, ...(Array.isArray(novo) ? novo : [novo])], conflito: false };
  }
  return { valor: atual, conflito: !iguais(atual, novo) };
}

export function aplicarChecklist(
  m11: readonly LinhaM11[],
  m04: readonly LinhaM04[],
  m05: readonly LinhaM05[],
  globaisDeEntrada: Globais,
  respostasDaEquipe: Record<string, Valor>,
  variaveisDeEntrada: Record<string, Valor>,
  itensDeEntrada: readonly Item[],
  porItem: Set<string>,
): ResultadoDoChecklist {
  const tipoDaVariavel = new Map(m05.map((l) => [variavelDoId(l.id), l.tipo_dado]));
  const tipoDoAtributo = new Map(
    m05.filter((l) => l.nome.startsWith("tabela_itens.")).map((l) => [l.nome.slice("tabela_itens.".length), l.tipo_dado]),
  );
  const decisoesJuridicas = new Set(m04.filter((l) => l.pre_preenchida_por.startsWith(MARCA_DE_DECISAO_JURIDICA)).map((l) => variavelDoId(l.id)));

  const globais: Globais = { ...globaisDeEntrada, ...variaveisDeEntrada, ...respostasDaEquipe };
  const itens: Item[] = itensDeEntrada.map((i) => ({ ...i }));
  const informadosNoItem = itensDeEntrada.map((i) => new Set(Object.keys(i).filter((k) => i[k] !== null && i[k] !== undefined)));
  const preenchido: Record<string, Valor> = {};
  const origens: Record<string, OrigemDaResposta> = {};
  const origensDeItem: Record<string, string> = {};
  const sugestoes: Sugestao[] = [];
  const avisos: AvisoDoMotor[] = [];
  const lacunas: Lacuna[] = [];
  const conflitosDeWz = new Set<string>();
  for (const chave of Object.keys(respostasDaEquipe)) origens[chave] = { origem: "EQUIPE" };
  for (const chave of Object.keys(variaveisDeEntrada)) origens[chave] = { origem: "ENTRADA" };

  const contribuir = (destino: string, pergunta: string) => {
    const atual = origens[destino];
    origens[destino] = { origem: "CHECKLIST", perguntas: atual?.origem === "CHECKLIST" ? [...atual.perguntas, pergunta] : [pergunta] };
  };

  for (const linha of m11) {
    const resposta = globais[variavelDoId(linha.id)];
    if (vazia(resposta)) continue;
    if (linha.condicional_expr !== null && !verdadeiro(avaliar(linha.condicional_expr, dadosGlobais(globais, itens, porItem)))) continue;

    for (const [coluna, sugere] of [["preenche_expr", false], ["sugere_expr", true]] as const) {
      const destinos = linha[coluna];
      if (!destinos) continue;
      for (const [destino, expressao] of Object.entries(destinos)) {
        if (destino.startsWith("itens.")) {
          const atributo = destino.slice("itens.".length);
          const valores = itens.map((item) => avaliar(expressao, dadosDoItem(globais, item, itens, porItem)));
          itens.forEach((item, k) => {
            const valor = valores[k];
            if (valor === null) return;
            if (sugere) {
              sugestoes.push({ destino, item: item.numero, valor, pergunta: linha.id });
              return;
            }
            if (informadosNoItem[k].has(atributo)) {
              if (!iguais(item[atributo] as Valor, valor)) {
                avisos.push({
                  codigo: "EQUIPE_DIVERGE_DO_CHECKLIST",
                  mensagem: `Item ${item.numero}, ${atributo}: a entrada traz ${JSON.stringify(item[atributo])} e a ${linha.id} indica ${JSON.stringify(valor)}; vale a entrada.`,
                  origem: { regra: linha.id, item: item.numero },
                });
              }
              return;
            }
            if (!tipoCompativel(valor, tipoDoAtributo.get(atributo))) {
              avisos.push({
                codigo: "TIPO_INCOMPATIVEL",
                mensagem: `Item ${item.numero}, ${atributo}: a ${linha.id} trouxe ${JSON.stringify(valor)}, que não é número; informe o número.`,
                origem: { regra: linha.id, item: item.numero },
              });
              lacunas.push({ destino, item: item.numero, motivo: `valor ${JSON.stringify(valor)} não é número`, origem: linha.id });
              return;
            }
            item[atributo] = valor;
            origensDeItem[`${item.numero}.${atributo}`] = linha.id;
          });
          continue;
        }

        const valor = avaliar(expressao, dadosGlobais(globais, itens, porItem));
        if (valor === null) continue;
        if (sugere || decisoesJuridicas.has(destino)) {
          sugestoes.push({ destino, valor, pergunta: linha.id });
          continue;
        }
        const daEquipe = destino.startsWith("WZ_") ? respostasDaEquipe : variaveisDeEntrada;
        if (Object.hasOwn(daEquipe, destino) && !vazia(daEquipe[destino])) {
          if (!iguais(daEquipe[destino], valor)) {
            avisos.push({
              codigo: "EQUIPE_DIVERGE_DO_CHECKLIST",
              mensagem: `${destino}: a equipe respondeu ${JSON.stringify(daEquipe[destino])} e a ${linha.id} indica ${JSON.stringify(valor)}; vale a resposta da equipe.`,
              origem: { regra: linha.id },
            });
          }
          continue;
        }
        if (destino.startsWith("WZ_")) {
          if (conflitosDeWz.has(destino)) continue;
          if (Object.hasOwn(preenchido, destino) && !iguais(preenchido[destino], valor)) {
            conflitosDeWz.add(destino);
            avisos.push({
              codigo: "CONFLITO_NO_CHECKLIST",
              mensagem: `${destino}: o checklist indica ${JSON.stringify(preenchido[destino])} e ${JSON.stringify(valor)} (${linha.id}); a pergunta fica para a equipe responder.`,
              origem: { regra: linha.id },
            });
            continue;
          }
          preenchido[destino] = valor;
          globais[destino] = valor;
          contribuir(destino, linha.id);
          continue;
        }
        const tipo = tipoDaVariavel.get(destino) ?? "TEXTO";
        if (!tipoCompativel(valor, tipo)) {
          avisos.push({
            codigo: "TIPO_INCOMPATIVEL",
            mensagem: `${destino} é ${tipo}, mas a ${linha.id} trouxe ${JSON.stringify(valor)}; o valor não foi convertido. Informe o número.`,
            origem: { regra: linha.id },
          });
          lacunas.push({ destino, motivo: `valor ${JSON.stringify(valor)} não é número`, origem: linha.id });
          continue;
        }
        const { valor: junto, conflito } = juntar(globais[destino] ?? null, valor, tipo);
        if (conflito) {
          avisos.push({
            codigo: "CONFLITO_NO_CHECKLIST",
            mensagem: `${destino}: o checklist indica ${JSON.stringify(globais[destino])} e ${JSON.stringify(valor)} (${linha.id}); fica o primeiro.`,
            origem: { regra: linha.id },
          });
          continue;
        }
        globais[destino] = junto;
        contribuir(destino, linha.id);
      }
    }
  }

  for (const destino of conflitosDeWz) {
    delete globais[destino];
    delete preenchido[destino];
    delete origens[destino];
  }
  // Lacuna de tipo só fica se nenhuma outra pergunta trouxe o valor.
  const lacunasRestantes = lacunas.filter((l) =>
    l.item === undefined ? vazia(globais[l.destino]) : vazia(itens.find((i) => i.numero === l.item)?.[l.destino.slice("itens.".length)] as Valor),
  );
  return { globais, itens, preenchidoPeloChecklist: preenchido, origens, origensDeItem, sugestoes, avisos, lacunas: lacunasRestantes };
}

export type Revisao = {
  /** Respostas destacadas para o operador revisar (IDs CK). */
  destaques: string[];
  /** Perguntas ao operador ainda sem confirmação: bloqueiam a minuta. */
  perguntasAoOperador: { pergunta: string; texto: string }[];
};

/**
 * Revisão das respostas do checklist (revisao_expr), avaliada no fim, com os mesmos dados das validações do M10.
 * Só entram as perguntas do checklist em uso (consumo ou permanentes; complementos sempre) cuja condicional vale:
 * pergunta de um checklist que não foi entregue, ou que não se aplica, não tem o que revisar.
 */
export function revisarChecklist(m11: readonly LinhaM11[], dados: Record<string, Valor>, confirmadas: readonly string[] = []): Revisao {
  const emUso = checklistsEmUso(m11, dados);
  const destaques: string[] = [];
  const perguntasAoOperador: Revisao["perguntasAoOperador"] = [];
  for (const linha of m11) {
    if (linha.revisao_expr === null || !emUso.has(linha.checklist)) continue;
    if (linha.condicional_expr !== null && !verdadeiro(avaliar(linha.condicional_expr, dados))) continue;
    if (!verdadeiro(avaliar(linha.revisao_expr, dados))) continue;
    destaques.push(linha.id);
    if (linha.revisao_pergunta !== "" && !confirmadas.includes(linha.id)) {
      perguntasAoOperador.push({ pergunta: linha.id, texto: linha.revisao_pergunta });
    }
  }
  return { destaques, perguntasAoOperador };
}

/**
 * Checklists em uso: pelos metadados da leitura (checklist.consumo e checklist.permanentes); sem eles, pelas
 * respostas presentes. Os complementos do operador valem sempre.
 */
function checklistsEmUso(m11: readonly LinhaM11[], dados: Record<string, Valor>): Set<string> {
  const leitura = dados.checklist;
  const emUso = new Set(["COMPLEMENTO"]);
  if (leitura !== null && typeof leitura === "object" && !Array.isArray(leitura) && ("consumo" in leitura || "permanentes" in leitura)) {
    if (verdadeiro(leitura.consumo)) emUso.add("CONSUMO");
    if (verdadeiro(leitura.permanentes)) emUso.add("PERMANENTES");
    return emUso;
  }
  for (const linha of m11) {
    if (!vazia(dados[variavelDoId(linha.id)])) emUso.add(linha.checklist);
  }
  return emUso;
}
