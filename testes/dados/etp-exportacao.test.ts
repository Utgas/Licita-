/**
 * ETP para o ETP Digital e PDF do ETP (Marco 3, passo 7), com o processo fictício dos testes do motor. Não precisa
 * de banco.
 */
import { describe, expect, it } from "vitest";
import { blocosDoCampo, camposParaCopiar, etpLiberado, hashDoEtp, textoDoCampo } from "../../src/exportacao/etp.ts";
import { gerarPdfDoEtp } from "../../src/exportacao/pdf.tsx";
import { gerarMinuta } from "../../src/motor/minuta.ts";
import { gerarEtp } from "../../src/motor/montagem/etp.ts";
import { entradaDoEtpFicticio } from "../motor/etp-ficticio.ts";

const entrada = entradaDoEtpFicticio();
const minuta = gerarMinuta(entrada);
const etp = gerarEtp(entrada, minuta);
const campo = (id: string) => etp.campos.find((c) => c.id === id) ?? (null as never);

describe("ETP para colar no ETP Digital", () => {
  it("só os campos com texto vão para a cópia, na ordem do M01", () => {
    const ids = camposParaCopiar(etp).map((c) => c.id);
    expect(ids).not.toContain("ETP-15.01");
    expect(ids).not.toContain("ETP-16.01");
    expect(ids).not.toContain("ETP-01.03");
    expect(ids).toEqual(etp.campos.filter((c) => ids.includes(c.id)).map((c) => c.id));
  });

  it("lacuna continua marcada no texto final", () => {
    const sem = { ...entrada, variaveis: { ...entrada.variaveis } };
    delete sem.variaveis.VAR_012;
    const etpSem = gerarEtp(sem, gerarMinuta(sem));
    expect(textoDoCampo(etpSem.campos.find((c) => c.id === "ETP-07.01") ?? (null as never))).toContain("[LACUNA: VAR-012]");
  });

  it("a tabela de itens sai com as colunas separadas por tabulação", () => {
    const tabela = campo("ETP-07.02");
    expect(blocosDoCampo(tabela)[0].tipo).toBe("tabela");
    expect(textoDoCampo(tabela).split("\n")[0]).toBe("ITEM\tESPECIFICAÇÃO\tCATMAT\tUNIDADE DE MEDIDA\tQUANTIDADE\tVALOR UNITÁRIO\tVALOR TOTAL\tPARTICIPAÇÃO");
  });

  it("o hash é o mesmo para o mesmo ETP e muda quando um dado muda", () => {
    expect(hashDoEtp(gerarEtp(entrada, minuta))).toBe(hashDoEtp(etp));
    const outra = { ...entrada, variaveis: { ...entrada.variaveis, VAR_014: 135000.01 } };
    expect(hashDoEtp(gerarEtp(outra, gerarMinuta(outra)))).not.toBe(hashDoEtp(etp));
  });

  it("só as dúvidas da leitura do checklist seguram o ETP", () => {
    expect(etpLiberado(minuta)).toBe(true);
    expect(etpLiberado({ ...minuta, revisao: { ...minuta.revisao, perguntasAoOperador: [{ pergunta: "CK-C-3.3" } as never] } })).toBe(false);
  });

  it("gera o PDF do ETP só com as fontes padrão", async () => {
    const pdf = await gerarPdfDoEtp({ etp, numeroDoProcesso: "00000.000000/0000-00", cabecalhoDaOm: ["OM Fictícia"] });
    const texto = pdf.toString("latin1");
    expect(texto.startsWith("%PDF-")).toBe(true);
    const fontes = [...texto.matchAll(/\/BaseFont \/([A-Za-z-]+)/g)].map((m) => m[1]);
    expect(fontes.length).toBeGreaterThan(0);
    expect(fontes.every((f) => f.startsWith("Helvetica"))).toBe(true);
    expect(texto).not.toMatch(/\/Subtype \/Image/);
  }, 30000);
});
