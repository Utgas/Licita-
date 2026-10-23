/**
 * Cenários de ouro C1 a C8 (matrizes/v1/cenarios/): a minuta montada pelo motor tem de dar exatamente os blocos,
 * as cláusulas do M08, as validações do M10, as perguntas sem resposta e os bloqueios de alternativas esperados.
 * O esperado vem do simulador do agente das matrizes, uma implementação independente: diferença aponta erro num
 * dos dois e é investigada, nunca ajustada só para passar.
 */
import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { gerarMinuta } from "../../src/motor/minuta.ts";
import { pacoteDasMatrizes } from "../motor/pacote-das-matrizes.ts";

const { pacote, hash } = pacoteDasMatrizes();
const DIR = path.resolve(import.meta.dirname, "../../matrizes/v1/cenarios");
const CENARIOS = ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"];

describe.each(CENARIOS)("cenário de ouro %s", (id) => {
  const { entrada, esperado } = JSON.parse(readFileSync(path.join(DIR, `${id}.json`), "utf8"));
  const minuta = gerarMinuta({ pacote, hashDoPacote: hash, ...structuredClone(entrada) });

  it("blocos do M02, na ordem do modelo", () => {
    expect(minuta.blocos).toEqual(esperado.blocos);
  });

  it("cláusulas setoriais do M08", () => {
    expect(minuta.clausulasSetoriais).toEqual(esperado.clausulas_m08);
  });

  it("validações do M10", () => {
    expect(minuta.validacoes.disparadas.map((v) => v.id)).toEqual(esperado.validacoes_m10);
  });

  it("perguntas sem resposta", () => {
    expect(minuta.perguntasSemResposta.map((p) => p.id)).toEqual(esperado.perguntas_sem_resposta);
  });

  it("bloqueios de grupo de alternativas", () => {
    expect(minuta.bloqueiosGrupoAlternativas).toEqual(esperado.bloqueios_grupo_alternativas);
  });

  it("todo trecho é rastreável até o ID e o pacote", () => {
    for (const trecho of minuta.trechos) {
      expect(trecho.id).toMatch(/^(TR|SET)-/);
      expect(trecho.origem).toMatchObject({ pacote: pacote.pacote, hash });
    }
    expect(minuta.trechos.filter((t) => t.tipo === "bloco").map((t) => t.id)).toEqual(esperado.blocos);
  });

  it("a mesma entrada gera a mesma minuta", () => {
    const outra = gerarMinuta({ pacote, hashDoPacote: hash, ...structuredClone(entrada) });
    expect(JSON.stringify(outra.trechos)).toBe(JSON.stringify(minuta.trechos));
  });
});
