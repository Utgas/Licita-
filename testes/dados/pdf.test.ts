/**
 * PDF da minuta (passo 11): gerado em memória, sem fonte nem imagem de fora, para os cenários fictícios. Não
 * precisa de banco.
 */
import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { carregarPacote } from "../../src/dados/pacote.ts";
import { gerarPdf } from "../../src/exportacao/pdf.tsx";
import type { EntradaProcesso } from "../../src/motor/entrada.ts";
import { gerarMinuta } from "../../src/motor/minuta.ts";

const { pacote, hash } = carregarPacote();
const minuta = (id: string) =>
  gerarMinuta({ pacote, hashDoPacote: hash, ...JSON.parse(readFileSync(path.resolve(import.meta.dirname, `../../matrizes/v1/cenarios/${id}.json`), "utf8")).entrada } as EntradaProcesso);

describe("PDF da minuta", () => {
  for (const id of ["C1", "C8", "R1"]) {
    it(`${id}: gera um PDF de várias páginas só com as fontes padrão`, async () => {
      const pdf = await gerarPdf({ minuta: minuta(id), numeroDoProcesso: "00000.000000/0000-00", cabecalhoDaOm: ["OM Fictícia"] });
      const texto = pdf.toString("latin1");
      expect(texto.startsWith("%PDF-")).toBe(true);
      expect(Number(/\/Count (\d+)/.exec(texto)?.[1])).toBeGreaterThan(3);
      const fontes = [...texto.matchAll(/\/BaseFont \/([A-Za-z-]+)/g)].map((m) => m[1]);
      expect(fontes.length).toBeGreaterThan(0);
      expect(fontes.every((f) => f.startsWith("Helvetica"))).toBe(true);
      expect(texto).not.toMatch(/\/Subtype \/Image/);
    }, 30000);
  }
});
