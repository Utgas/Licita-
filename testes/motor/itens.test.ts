import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import type { Valor } from "../../src/motor/pacote/avaliador.ts";
import type { LinhaM05 } from "../../src/motor/pacote/esquema.ts";
import { calcularM05, linhasDeCalculo } from "../../src/motor/itens/calculo.ts";
import { type Item, contextoDoItem, itensDoGrupo, variaveisPorItem } from "../../src/motor/itens/contexto.ts";
import { pacoteDasMatrizes } from "./pacote-das-matrizes.ts";

const { pacote } = pacoteDasMatrizes();
const porItem = variaveisPorItem(pacote.matrizes.M11);

function cenario(id: string) {
  return JSON.parse(readFileSync(path.resolve(import.meta.dirname, `../../matrizes/v1/cenarios/${id}.json`), "utf8"));
}

function globaisDe(entrada: { wizard: object; checklist: object; variaveis: object; metadados: object }): Record<string, Valor> {
  return { ...entrada.checklist, ...entrada.variaveis, ...entrada.metadados, ...entrada.wizard, parametros: pacote.parametros } as Record<string, Valor>;
}

describe("contexto de item", () => {
  it("resposta por item só aparece no item indicado", () => {
    const globais = { CK_C_9_2: "texto global", WZ_01: "LICITACAO" };
    const item: Item = { numero: 2, respostas_por_item: { CK_C_9_2: "amostra" } };
    expect(contextoDoItem(globais, item, porItem)).toMatchObject({ CK_C_9_2: "amostra", WZ_01: "LICITACAO" });
    expect(contextoDoItem(globais, { numero: 1 }, porItem)).not.toHaveProperty("CK_C_9_2");
  });

  it("itens_do_grupo junta os itens com o mesmo rótulo, ou só o próprio item", () => {
    const itens: Item[] = [{ numero: 1, grupo: "G1" }, { numero: 2, grupo: null }, { numero: 3, grupo: "G1" }, { numero: 4, grupo: "" }];
    expect(itensDoGrupo(itens[0], itens).map((i) => i.numero)).toEqual([1, 3]);
    expect(itensDoGrupo(itens[1], itens).map((i) => i.numero)).toEqual([2]);
    expect(itensDoGrupo(itens[3], itens).map((i) => i.numero)).toEqual([4]);
  });
});

describe("cálculo do M05 com as matrizes atuais", () => {
  it("segue calculo_ordem", () => {
    const ordens = linhasDeCalculo(pacote.matrizes.M05).map((l) => l.calculo_ordem);
    expect(ordens).toEqual([...ordens].sort((a, b) => (a as number) - (b as number)));
    expect(ordens.length).toBeGreaterThan(0);
  });

  it("C6: tratamento ME/EPP, valor da unidade de disputa e cota por item e por grupo", () => {
    const { entrada, referencia } = cenario("C6");
    // O grupo G1 dos itens 5 e 6 vem do checklist (CK-C-8.2), aplicado no passo 4; aqui entra direto.
    const itens: Item[] = entrada.itens.map((i: Item) => ({ ...i, grupo: i.numero === 5 || i.numero === 6 ? "G1" : null }));
    const resultado = calcularM05(pacote.matrizes.M05, globaisDe(entrada), itens, porItem);
    const obtido = resultado.itens.map((i) => [i.numero, i.tratamento_me_epp, i.valor_unidade_disputa, i.quantidade_cota]);
    const esperado = referencia.itens_calculados.map((i: Record<string, Valor>) => [i.numero, i.tratamento_me_epp, i.valor_unidade_disputa, i.quantidade_cota]);
    expect(obtido).toEqual(esperado);
    expect(resultado.avisos).toEqual([]);
  });

  it("não altera a entrada", () => {
    const { entrada } = cenario("C6");
    const copia = structuredClone(entrada.itens);
    calcularM05(pacote.matrizes.M05, globaisDe(entrada), entrada.itens, porItem);
    expect(entrada.itens).toEqual(copia);
  });

  // A VAR-113 já devolve null quando falta o valor da disputa; os avisos vêm da VAR-119 e do valor total (VAR-175).
  it("item sem valor unitário: valor da disputa e tratamento viram lacuna, com aviso", () => {
    const { entrada } = cenario("C6");
    const itens: Item[] = entrada.itens.map((i: Item) => (i.numero === 4 ? { ...i, valor_unitario: null } : i));
    const resultado = calcularM05(pacote.matrizes.M05, globaisDe(entrada), itens, porItem);
    const item4 = resultado.itens.find((i) => i.numero === 4);
    expect(item4?.valor_unidade_disputa).toBeNull();
    expect(item4?.tratamento_me_epp).toBeNull();
    expect(resultado.avisos.filter((a) => a.origem.item === 4).map((a) => [a.codigo, a.origem.regra])).toEqual([
      ["CALCULO_SEM_DADO", "VAR-119"],
      ["CALCULO_SEM_DADO", "VAR-175"],
    ]);
  });
});

describe("cálculo do M05 com regras fictícias", () => {
  const base = { descricao: "", validacao: "", obrigatoria: "N", origem: "SISTEMA", usada_em: "", fonte: "teste", status: "INFERIDO" } as const;
  const linha = (id: string, nome: string, ordem: number, calculo_expr: unknown, tipo_dado: LinhaM05["tipo_dado"] = "LISTA"): LinhaM05 => ({
    ...base,
    id,
    nome,
    tipo_dado,
    calculo_expr: calculo_expr as LinhaM05["calculo_expr"],
    calculo_ordem: ordem,
  });

  it("lê o que foi calculado antes e registra de onde veio cada valor", () => {
    const m05 = [
      linha("VAR-902", "tabela_itens.total", 2, { "*": [{ var: "dobro" }, 10] }, "NUMERO"),
      linha("VAR-901", "tabela_itens.dobro", 1, { "*": [{ var: "quantidade" }, 2] }, "NUMERO"),
      linha("VAR-903", "soma", 3, { reduce: [{ var: "itens" }, { "+": [{ var: "accumulator" }, { var: "current.total" }] }, 0] }, "NUMERO"),
    ];
    const resultado = calcularM05(m05, {}, [{ numero: 1, quantidade: 3 }, { numero: 2, quantidade: 0.5 }], new Set());
    expect(resultado.itens.map((i) => i.total)).toEqual([60, 10]);
    expect(resultado.globais.VAR_903).toBe(70);
    expect(resultado.calculados.map((c) => [c.regra, c.destino, c.item ?? null])).toEqual([
      ["VAR-901", "itens.dobro", 1],
      ["VAR-901", "itens.dobro", 2],
      ["VAR-902", "itens.total", 1],
      ["VAR-902", "itens.total", 2],
      ["VAR-903", "VAR_903", null],
    ]);
  });

  it("valor informado diferente do calculado: vale o calculado, com aviso", () => {
    const m05 = [linha("VAR-901", "tabela_itens.dobro", 1, { "*": [{ var: "quantidade" }, 2] }, "NUMERO")];
    const resultado = calcularM05(m05, {}, [{ numero: 1, quantidade: 3, dobro: 5 }], new Set());
    expect(resultado.itens[0].dobro).toBe(6);
    expect(resultado.avisos.map((a) => a.codigo)).toEqual(["VALOR_INFORMADO_SUBSTITUIDO"]);
  });
});
