/**
 * Processo continua com o pacote com que nasceu depois de uma correção nas matrizes (arquitetura, princípio 5):
 * o compilador guarda cada pacote em regras/<nome>/historico/<hash>.json. Não precisa de banco.
 */
import { readdirSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { carregarPacote } from "../../src/dados/pacote.ts";

const HISTORICO = path.resolve(import.meta.dirname, "../../regras/agu-tr-compras-2025-12/historico");

describe("histórico de pacotes", () => {
  const atual = carregarPacote();

  it("o pacote atual também está no histórico", () => {
    expect(readdirSync(HISTORICO)).toContain(`${atual.hash}.json`);
  });

  it("todo pacote do histórico abre pelo hash, conferido", () => {
    for (const arquivo of readdirSync(HISTORICO)) {
      const hash = arquivo.replace(/\.json$/, "");
      expect(carregarPacote(undefined, hash).hash).toBe(hash);
    }
  });

  it("o processo com o hash atual recebe o pacote atual", () => {
    expect(carregarPacote(undefined, atual.hash)).toBe(atual);
  });

  it("hash que não existe é erro, nunca outro pacote", () => {
    expect(() => carregarPacote(undefined, "0".repeat(64))).toThrow();
    expect(() => carregarPacote(undefined, "../pacote")).toThrow(/hash de pacote inválido/);
  });
});
