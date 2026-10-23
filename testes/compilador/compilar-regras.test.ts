import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import {
  DIR_PACOTE,
  compilar,
  compilarConteudos,
  variavelDoId,
  type TipoDeErro,
} from "../../scripts/compilar-regras.ts";

const FIXTURES = path.join(import.meta.dirname, "fixtures");

function lerPasta(dir: string): Record<string, string> {
  return Object.fromEntries(readdirSync(dir).map((arquivo) => [arquivo, readFileSync(path.join(dir, arquivo), "utf8")]));
}

/** Matrizes fictícias válidas, com os arquivos de um caso quebrado no lugar dos originais. */
function matrizesDoCaso(caso?: string): Record<string, string> {
  const validas = lerPasta(path.join(FIXTURES, "validas"));
  return caso ? { ...validas, ...lerPasta(path.join(FIXTURES, "quebradas", caso)) } : validas;
}

function tiposDeErro(conteudos: Record<string, string>, piloto = false): TipoDeErro[] {
  return compilarConteudos(conteudos, { piloto }).erros.map((e) => e.tipo);
}

describe("matrizes atuais (matrizes/v1)", () => {
  const resultado = compilar();

  it("compilam sem erro", () => {
    expect(resultado.erros).toEqual([]);
    expect(resultado.pacote).toBeDefined();
  });

  it("geram o mesmo hash a cada compilação", () => {
    expect(compilar().pacote?.sha256).toBe(resultado.pacote?.sha256);
  });

  it("correspondem ao pacote gravado em regras/ (se falhar, rode npm run compilar)", () => {
    const gravado = readFileSync(path.join(DIR_PACOTE, "pacote.sha256"), "utf8");
    expect(gravado).toBe(`${resultado.pacote?.sha256}  pacote.json\n`);
    expect(readFileSync(path.join(DIR_PACOTE, "pacote.json"), "utf8")).toBe(resultado.pacote?.json);
  });

  it("deixam M00 e M09 fora do pacote", () => {
    const pacote = JSON.parse(resultado.pacote?.json ?? "{}");
    expect(Object.keys(pacote.matrizes)).not.toContain("M00");
    expect(Object.keys(pacote.matrizes)).not.toContain("M09");
  });
});

describe("matrizes fictícias", () => {
  it("válidas compilam sem erro", () => {
    expect(compilarConteudos(matrizesDoCaso()).erros).toEqual([]);
  });

  it("geram JSON sem data e com chaves em ordem", () => {
    const { pacote } = compilarConteudos(matrizesDoCaso());
    const json = pacote?.json ?? "";
    expect(json).not.toMatch(/\d{4}-\d{2}-\d{2}T/);
    const chaves = Object.keys(JSON.parse(json));
    expect(chaves).toEqual([...chaves].sort());
  });

  it.each<[string, TipoDeErro]>([
    ["id-duplicado", "id_duplicado"],
    ["referencia-quebrada", "referencia"],
    ["json-invalido", "json_invalido"],
    ["operador-fora-da-lista", "operador"],
    ["variavel-desconhecida", "variavel"],
    ["atributo-de-item-desconhecido", "variavel"],
  ])("falham com %s", (caso, tipo) => {
    const resultado = compilarConteudos(matrizesDoCaso(caso));
    expect(resultado.erros.map((e) => e.tipo)).toEqual([tipo]);
    expect(resultado.pacote).toBeUndefined();
  });

  it("falham quando uma coluna é renomeada", () => {
    const conteudos = matrizesDoCaso();
    conteudos["M05_variaveis.csv"] = conteudos["M05_variaveis.csv"].replace('"nome"', '"nome_da_variavel"');
    expect(tiposDeErro(conteudos)).toEqual(["cabecalho"]);
  });

  it("falham com status fora do domínio", () => {
    const conteudos = matrizesDoCaso();
    conteudos["M07_normas.csv"] = conteudos["M07_normas.csv"].replace('"EXTRAIDO"', '"CONFERIDO"');
    expect(tiposDeErro(conteudos)).toEqual(["esquema"]);
  });

  it("aceitam notação de formato sem dígito, como ETP-SS.CC", () => {
    const conteudos = matrizesDoCaso();
    conteudos["M10_validacoes.csv"] = conteudos["M10_validacoes.csv"].replace("Mensagem fictícia.", "Formato ETP-SS.CC.");
    expect(tiposDeErro(conteudos)).toEqual([]);
  });

  describe("no modo piloto", () => {
    it("falham se uma regra CONDICAO do M03 ou uma pergunta do M04 não tiver validacao = OK", () => {
      expect(tiposDeErro(matrizesDoCaso(), true)).toEqual(["piloto", "piloto"]);
    });

    it("passam quando tudo está validado", () => {
      const conteudos = matrizesDoCaso();
      for (const arquivo of ["M03_notas_explicativas.csv", "M04_wizard.csv"]) {
        conteudos[arquivo] = conteudos[arquivo].replace(/"INFERIDO","",""/, '"INFERIDO","OK",""');
      }
      expect(tiposDeErro(conteudos, true)).toEqual([]);
    });
  });
});

describe("variavelDoId", () => {
  it.each([
    ["WZ-23", "WZ_23"],
    ["CK-C-14.2", "CK_C_14_2"],
    ["CK-P-CAB.01", "CK_P_CAB_01"],
    ["VAR-001", "VAR_001"],
  ])("%s vira %s", (id, variavel) => {
    expect(variavelDoId(id)).toBe(variavel);
  });
});
