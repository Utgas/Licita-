/** Planilha de itens (passo 8): modelo, leitura e recusa da planilha inteira quando há erro. Sem banco. */
import ExcelJS from "exceljs";
import { describe, expect, it } from "vitest";
import { COLUNAS, lerPlanilha, modeloDaPlanilha, numeroDaCelula } from "../../src/dados/planilha-itens.ts";

async function planilha(linhas: (string | number | null)[][], cabecalho = COLUNAS.map((c) => c.titulo)): Promise<Uint8Array> {
  const livro = new ExcelJS.Workbook();
  const aba = livro.addWorksheet("Itens");
  aba.addRow(cabecalho);
  for (const l of linhas) aba.addRow(l);
  return new Uint8Array(await livro.xlsx.writeBuffer());
}

describe("planilha de itens", () => {
  it("o modelo baixado é lido de volta", async () => {
    const { itens, erros } = await lerPlanilha(await modeloDaPlanilha());
    expect(erros).toEqual([]);
    expect(itens).toEqual([expect.objectContaining({ numero: 1, especificacao: "Item fictício de exemplo", quantidade: 100, valorUnitario: 10.5, categoria: "CONSUMO", exigeAmostra: "N" })]);
  });

  it("valor como texto brasileiro e 'Sim' viram número e S; linha vazia é ignorada", async () => {
    const { itens, erros } = await lerPlanilha(await planilha([[2, "Item B", "", "caixa", "1.000", "R$ 1.234,56", "", "permanente", "", "Sim"], [], [3, "Item C", "", "un", 5]]));
    expect(erros).toEqual([]);
    expect(itens.map((i) => [i.numero, i.quantidade, i.valorUnitario, i.categoria, i.exigeAmostra])).toEqual([
      [2, 1000, 1234.56, "PERMANENTE", "S"],
      [3, 5, null, null, null],
    ]);
  });

  it("com erro, nada entra e cada linha é apontada", async () => {
    const { erros } = await lerPlanilha(await planilha([[1, "A", "", "un", "dez"], [1, "", "", "un", 0], [2.5, "B", "", "un", 1, "", "", "TALVEZ"]]));
    expect(erros).toEqual([
      'Linha 2: Quantidade não é número ("dez").',
      "Linha 3: falta Especificação.",
      "Linha 3: Quantidade precisa ser maior que zero.",
      "Linha 3: o item 1 aparece mais de uma vez.",
      "Linha 4: Item precisa ser número inteiro.",
      "Linha 4: Categoria (CONSUMO ou PERMANENTE) deve ser CONSUMO ou PERMANENTE.",
    ]);
  });

  it("colunas fora do modelo e arquivo que não é planilha", async () => {
    expect((await lerPlanilha(await planilha([], ["Número", "Descrição"]))).erros[0]).toMatch(/não são as do modelo/);
    expect((await lerPlanilha(new TextEncoder().encode("texto"))).erros[0]).toMatch(/não é uma planilha/);
  });

  it.each([
    ["10,5", 10.5],
    ["1.234", 1234],
    ["10.5", 10.5],
    ["abc", Number.NaN],
  ])("número %s", (t, n) => {
    expect(numeroDaCelula(t)).toEqual(n);
  });
});
