/**
 * Dados que as expressões leem (README das matrizes, "Contexto de item").
 *
 * - Globais: respostas do wizard e do checklist, variáveis, metadados e parametros.
 * - Item: os atributos do item mais os globais; a resposta de pergunta por item (por_item = S) é só a ligada
 *   àquele item (ausente se o item não foi indicado).
 * - itens_do_grupo: os itens com o mesmo rótulo de grupo, ou só o próprio item.
 */
import type { Valor } from "../pacote/avaliador.ts";
import type { LinhaM11 } from "../pacote/esquema.ts";
import { variavelDoId } from "../pacote/nomes.ts";

/** Item já com os atributos do M05 (de entrada, do checklist ou calculados). */
export type Item = {
  numero: number;
  respostas_por_item?: Record<string, Valor>;
  [atributo: string]: Valor | Record<string, Valor> | undefined;
};

export type Globais = Record<string, Valor>;

/** Variáveis das perguntas do checklist respondidas por item (CK_C_9_2...). */
export function variaveisPorItem(m11: readonly LinhaM11[]): Set<string> {
  return new Set(m11.filter((l) => l.por_item === "S").map((l) => variavelDoId(l.id)));
}

/** Contexto de um item: globais (sem as respostas por item dos outros itens) + atributos + respostas do item. */
export function contextoDoItem(globais: Globais, item: Item, porItem: Set<string>): Record<string, Valor> {
  const contexto: Record<string, Valor> = {};
  for (const [chave, valor] of Object.entries(globais)) {
    if (chave === "itens" || porItem.has(chave) || porItem.has(chave.replace(/_(texto|numero)$/, ""))) continue;
    contexto[chave] = valor;
  }
  for (const [chave, valor] of Object.entries(item)) {
    if (chave !== "respostas_por_item" && valor !== undefined) contexto[chave] = valor as Valor;
  }
  Object.assign(contexto, item.respostas_por_item ?? {});
  return contexto;
}

/** Itens do mesmo grupo do item (rótulo de grupo não vazio e igual), ou só o próprio item. */
export function itensDoGrupo(item: Item, itens: readonly Item[]): Item[] {
  const grupo = item.grupo;
  if (grupo === null || grupo === undefined || grupo === "") return [item];
  return itens.filter((outro) => outro === item || outro.grupo === grupo);
}

/** Dados globais com a lista `itens` em contexto de item (para some, none e reduce sobre itens). */
export function dadosGlobais(globais: Globais, itens: readonly Item[], porItem: Set<string>): Record<string, Valor> {
  return { ...globais, itens: itens.map((item) => contextoDoItem(globais, item, porItem)) };
}

/** Dados de uma expressão avaliada item a item: o item é o topo, com itens_do_grupo e itens. */
export function dadosDoItem(globais: Globais, item: Item, itens: readonly Item[], porItem: Set<string>): Record<string, Valor> {
  return {
    ...contextoDoItem(globais, item, porItem),
    itens_do_grupo: itensDoGrupo(item, itens).map((outro) => contextoDoItem(globais, outro, porItem)),
    itens: itens.map((outro) => contextoDoItem(globais, outro, porItem)),
  };
}
