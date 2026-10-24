import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { textoDaSimulacao } from "../../scripts/simular-wizard.ts";
import { gerarMinuta } from "../../src/motor/minuta.ts";
import { pacoteDasMatrizes } from "../motor/pacote-das-matrizes.ts";

const { pacote, hash } = pacoteDasMatrizes();

describe("simulação legível (npm run simular -- C1)", () => {
  const caso = JSON.parse(readFileSync(path.resolve(import.meta.dirname, "../../matrizes/v1/cenarios/C1.json"), "utf8"));
  const minuta = gerarMinuta({ pacote, hashDoPacote: hash, ...caso.entrada });
  const texto = textoDaSimulacao("C1", caso.descricao, minuta);

  it("imprime o TR numerado, com as lacunas marcadas", () => {
    expect(texto).toMatch(/^1\. CONDIÇÕES GERAIS DA CONTRATAÇÃO$/m);
    expect(texto).toMatch(/^1\.1\. Aquisição de \[\[LACUNA /m);
    expect(texto).toMatch(/^ITEM \| ESPECIFICAÇÃO \| CATMAT/m);
  });

  it("termina com a contagem de lacunas por motivo, que soma o total", () => {
    const [, total] = /Lacunas por motivo \(total (\d+)\)/.exec(texto) ?? [];
    const partes = ["falta de dado", "ligação ambígua do marcador", "tabela não montada", "preenchimento da equipe"].map((rotulo) => {
      const [, n] = new RegExp(`${rotulo}\\s+(\\d+)`).exec(texto) ?? [];
      return Number(n);
    });
    expect(partes.every((n) => Number.isInteger(n))).toBe(true);
    expect(partes.reduce((a, b) => a + b, 0)).toBe(Number(total));
    // Com o lacunas_mapa, nenhum marcador fica sem ligação.
    expect(partes[1]).toBe(0);
  });
});
