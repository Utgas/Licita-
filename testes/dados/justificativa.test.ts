/** Leitura da coluna exige_justificativa do M04 na tela do wizard (passo 9), com os textos reais do pacote. */
import { describe, expect, it } from "vitest";
import { justificativaObrigatoria } from "../../src/app/processos/[id]/wizard/regras.ts";
import { carregarPacote } from "../../src/dados/pacote.ts";

const m04 = new Map(carregarPacote().pacote.matrizes.M04.map((l) => [l.id, l.exige_justificativa]));
const regra = (id: string) => m04.get(id) as string;

describe("justificativa obrigatória", () => {
  it.each([
    ["WZ-02", "PREGAO", false],
    ["WZ-01", "LICITACAO", false],
    ["WZ-01", "CONTRATACAO_DIRETA", true],
    ["WZ-04", "ART75_II_VALOR", true],
    ["WZ-22", "NAO", false],
    ["WZ-22", "SIM_EXIGIDA_ME_EPP", true],
    ["WZ-51", "NAO", true],
    ["WZ-38", ["ATESTADOS"], true],
    ["WZ-17", "SIM", false],
    ["WZ-17", "NAO", true],
  ])("%s = %s: %s", (id, valor, esperado) => {
    expect(justificativaObrigatoria(regra(id), valor)).toBe(esperado);
  });
});
