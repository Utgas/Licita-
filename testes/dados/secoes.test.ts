/**
 * Minuta pelas seções do modelo AGU (passos 10 e 11): ordem e títulos do M02, marcas de lacuna e de valor padrão,
 * texto para colar e hash. Sobre os cenários fictícios; não precisa de banco.
 */
import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { carregarPacote } from "../../src/dados/pacote.ts";
import { hashDaMinuta, partesDoTexto, secoesDaMinuta, textoDaSecao, textoFinal, tabelaNaoMontada } from "../../src/exportacao/secoes.ts";
import type { EntradaProcesso } from "../../src/motor/entrada.ts";
import { gerarMinuta } from "../../src/motor/minuta.ts";

const { pacote, hash } = carregarPacote();
const cenario = (id: string) => JSON.parse(readFileSync(path.resolve(import.meta.dirname, `../../matrizes/v1/cenarios/${id}.json`), "utf8")).entrada;
const minuta = (id: string) => gerarMinuta({ pacote, hashDoPacote: hash, ...cenario(id) } as EntradaProcesso);
const ordemDoModelo = [...new Set(pacote.matrizes.M02.map((l) => l.secao))];

describe("seções do modelo AGU", () => {
  for (const id of ["C1", "C7", "C8", "R1"]) {
    it(`${id}: títulos e ordem do M02, sem perder nem repetir trecho`, () => {
      const m = minuta(id);
      const secoes = secoesDaMinuta(m);
      const titulos = secoes.map((s) => s.titulo);
      expect(new Set(titulos).size).toBe(titulos.length);
      expect(titulos.every((t) => ordemDoModelo.includes(t))).toBe(true);
      expect(titulos.map((t) => ordemDoModelo.indexOf(t))).toEqual([...titulos.map((t) => ordemDoModelo.indexOf(t))].sort((a, b) => a - b));
      expect(secoes.flatMap((s) => s.trechos)).toEqual(m.trechos);
    });
  }

  it("cláusula setorial fica na seção do bloco depois do qual entrou", () => {
    const m = minuta("C8");
    const secoes = secoesDaMinuta(m);
    const comClausula = secoes.filter((s) => s.trechos.some((t) => t.tipo === "clausula_setorial"));
    expect(comClausula.length).toBeGreaterThan(0);
    for (const s of comClausula) expect(s.trechos[0].tipo).toBe("bloco");
  });
});

describe("marcas do texto", () => {
  it("separa lacuna, valor padrão e texto", () => {
    expect(partesDoTexto("Prazo de [[LACUNA VAR-060]] dias, [[PADRÃO: em parcela única]].")).toEqual([
      { tipo: "texto", texto: "Prazo de " },
      { tipo: "lacuna", texto: "VAR-060" },
      { tipo: "texto", texto: " dias, " },
      { tipo: "padrao", texto: "em parcela única" },
      { tipo: "texto", texto: "." },
    ]);
  });

  it("no texto final, a lacuna continua marcada e o valor padrão perde a marca", () => {
    expect(textoFinal("a [[LACUNA VAR-060]] b [[PADRÃO: c]] [[LACUNA]] [[LACUNA EQUIPE]]")).toBe("a [LACUNA: VAR-060] b c [LACUNA] [LACUNA: EQUIPE]");
    expect(tabelaNaoMontada("[[TABELA NÃO MONTADA]]\nA | B")).toEqual({ naoMontada: true, texto: "A | B" });
  });

  it("texto para colar leva número, tabela com tabulação e nenhuma marca [[ ]]", () => {
    const m = minuta("C8");
    for (const s of secoesDaMinuta(m)) {
      const texto = textoDaSecao(s);
      expect(texto).not.toContain("[[");
    }
    const primeira = secoesDaMinuta(m).find((s) => s.titulo.startsWith("1."));
    const texto = textoDaSecao(primeira!);
    expect(texto).toMatch(/^1\. /);
    expect(texto).toContain("\t");
  });

  it("hash da minuta é o mesmo para a mesma entrada e muda com a resposta", () => {
    expect(hashDaMinuta(minuta("C8"))).toBe(hashDaMinuta(minuta("C8")));
    const outra = cenario("C8");
    const m2 = gerarMinuta({ pacote, hashDoPacote: hash, ...outra, variaveis: { ...outra.variaveis, VAR_034: 12, VAR_163: "MESES" } } as EntradaProcesso);
    expect(hashDaMinuta(m2)).not.toBe(hashDaMinuta(minuta("C8")));
  });
});
