import { readFileSync } from "node:fs";
import path from "node:path";
import { parse } from "csv-parse/sync";
import { describe, expect, it } from "vitest";
import { ErroDeExpressao, avaliar, avaliarComOcorrencias, type Valor } from "../../src/motor/pacote/avaliador.ts";
import { decimalDeNumero, decimalDeTexto, dividir, numeroDoDecimal, resto, textoDoDecimal } from "../../src/motor/pacote/decimal.ts";

const v = (nome: string, padrao?: Valor) => ({ var: padrao === undefined ? nome : [nome, padrao] });

describe("decimal exato", () => {
  it.each([
    ["80000.00", "80000"],
    ["0.10", "0.1"],
    ["-1.50", "-1.5"],
    ["1e-7", "0.0000001"],
    ["1.5e3", "1500"],
    ["007", "7"],
  ])("lê %s como %s", (texto, esperado) => {
    expect(textoDoDecimal(decimalDeTexto(texto)!)).toBe(esperado);
  });

  it("lê número do JavaScript pela forma escrita mais curta, não pela binária", () => {
    expect(textoDoDecimal(decimalDeNumero(0.1)!)).toBe("0.1");
    expect(textoDoDecimal(decimalDeNumero(1e21)!)).toBe("1000000000000000000000");
    expect(decimalDeNumero(Number.NaN)).toBeUndefined();
    expect(decimalDeNumero(Number.POSITIVE_INFINITY)).toBeUndefined();
  });

  it("divide sem arredondar: 1/3 não tem decimal exato", () => {
    expect(dividir(decimalDeTexto("1")!, decimalDeTexto("3")!)).toBeUndefined();
    expect(textoDoDecimal(dividir(decimalDeTexto("1")!, decimalDeTexto("8")!)!)).toBe("0.125");
  });

  it("resto com o sinal do divisor, como no simulador", () => {
    expect(textoDoDecimal(resto(decimalDeTexto("-7")!, decimalDeTexto("3")!)!)).toBe("2");
    expect(textoDoDecimal(resto(decimalDeTexto("7.5")!, decimalDeTexto("2")!)!)).toBe("1.5");
  });

  it("não devolve número do JavaScript que perderia dígitos", () => {
    expect(numeroDoDecimal(decimalDeTexto("12345678901234567890.123")!)).toBeUndefined();
    expect(numeroDoDecimal(decimalDeTexto("80000.01")!)).toBe(80000.01);
  });
});

describe("avaliador: operadores", () => {
  const dados = { WZ_01: "SIM", VAR_057: 25, lista: ["a", "b"], vazio: null, aninhado: { x: { y: 3 } } };

  it("var lê variável, caminho com ponto e devolve null quando falta", () => {
    expect(avaliar(v("WZ_01"), dados)).toBe("SIM");
    expect(avaliar(v("aninhado.x.y"), dados)).toBe(3);
    expect(avaliar(v("WZ_99"), dados)).toBeNull();
    expect(avaliar(v("aninhado.z.y"), dados)).toBeNull();
  });

  it("var com padrão devolve o padrão só quando a variável falta", () => {
    expect(avaliar(v("WZ_99", []), dados)).toEqual([]);
    expect(avaliar(v("WZ_01", "outro"), dados)).toBe("SIM");
    // presente com null não é "faltando" (igual ao simulador)
    expect(avaliar(v("vazio", "padrao"), dados)).toBeNull();
  });

  it('{"var": ""} é o próprio elemento dentro de some, none e reduce', () => {
    expect(avaliar({ some: [v("lista"), { "==": [v(""), "b"] }] }, dados)).toBe(true);
    expect(avaliar({ none: [v("lista"), { "==": [v(""), "c"] }] }, dados)).toBe(true);
    expect(avaliar({ reduce: [v("lista"), { merge: [v("accumulator"), [v("current")]] }, []] }, dados)).toEqual(["a", "b"]);
    expect(avaliar({ reduce: [[1], v(""), null] }, dados)).toEqual({ current: 1, accumulator: null });
  });

  it("== e != são estritos", () => {
    expect(avaliar({ "==": ["30", 30] }, {})).toBe(false);
    expect(avaliar({ "!=": ["30", 30] }, {})).toBe(true);
    expect(avaliar({ "==": [30, 30.0] }, {})).toBe(true);
    expect(avaliar({ "==": [0.3, { "+": [0.1, 0.2] }] }, {})).toBe(true);
    expect(avaliar({ "==": [null, null] }, {})).toBe(true);
    expect(avaliar({ "==": [v("WZ_99"), null] }, {})).toBe(true);
    expect(avaliar({ "==": [null, 0] }, {})).toBe(false);
    expect(avaliar({ "==": [null, ""] }, {})).toBe(false);
    expect(avaliar({ "==": [false, 0] }, {})).toBe(false);
    expect(avaliar({ "==": [[1, "a"], [1, "a"]] }, {})).toBe(true);
  });

  it.each<[string, Valor, boolean]>([
    ["null", null, false],
    ["false", false, false],
    ["0", 0, false],
    ['""', "", false],
    ["[]", [], false],
    ["lista não vazia", [0], true],
    ['"0"', "0", true],
    ["objeto", {}, true],
    ["número negativo", -1, true],
  ])("verdade de %s em !, !!, if, and e or", (_nome, valor, esperado) => {
    const dadosDoCaso = { x: valor };
    expect(avaliar({ "!!": [v("x")] }, dadosDoCaso)).toBe(esperado);
    expect(avaliar({ "!": [v("x")] }, dadosDoCaso)).toBe(!esperado);
    expect(avaliar({ if: [v("x"), "sim", "nao"] }, dadosDoCaso)).toBe(esperado ? "sim" : "nao");
    expect(avaliar({ and: [true, v("x")] }, dadosDoCaso)).toEqual(valor);
    expect(avaliar({ or: [v("x"), false] }, dadosDoCaso)).toEqual(esperado ? valor : false);
  });

  it("if com vários pares, sem senão devolve null", () => {
    const expressao = { if: [{ "==": [v("x"), 1] }, "um", { "==": [v("x"), 2] }, "dois", "outro"] };
    expect(avaliar(expressao, { x: 2 })).toBe("dois");
    expect(avaliar(expressao, { x: 9 })).toBe("outro");
    expect(avaliar({ if: [false, "a"] }, {})).toBeNull();
  });

  it("and devolve o primeiro falso ou o último; or devolve o primeiro verdadeiro ou false", () => {
    expect(avaliar({ and: [1, "", 2] }, {})).toBe("");
    expect(avaliar({ and: [1, 2] }, {})).toBe(2);
    expect(avaliar({ or: [0, "x"] }, {})).toBe("x");
    expect(avaliar({ or: [0, null] }, {})).toBe(false);
  });

  it("in procura em lista (igualdade estrita) e em texto (trecho)", () => {
    expect(avaliar({ in: ["b", v("lista")] }, dados)).toBe(true);
    expect(avaliar({ in: [30, [30.0]] }, {})).toBe(true);
    expect(avaliar({ in: ["30", [30]] }, {})).toBe(false);
    expect(avaliar({ in: ["10.520", "Lei 10.520/2002"] }, {})).toBe(true);
    expect(avaliar({ in: ["x", null] }, {})).toBe(false);
    expect(avaliar({ in: [null, ["x"]] }, {})).toBe(false);
  });

  it("merge junta listas e valores soltos", () => {
    expect(avaliar({ merge: [["a"], "b", [["c"]]] }, {})).toEqual(["a", "b", ["c"]]);
    expect(avaliar({ merge: [{ if: [false, ["x"], []] }, { if: [true, ["y"], []] }] }, {})).toEqual(["y"]);
  });

  it("some e none sobre lista ausente tratam como lista vazia", () => {
    expect(avaliar({ some: [v("nada"), true] }, {})).toBe(false);
    expect(avaliar({ none: [v("nada"), true] }, {})).toBe(true);
  });

  it("some sobre itens lê o atributo do item", () => {
    const itens = [{ perecivel: "N" }, { perecivel: "S" }];
    expect(avaliar({ some: [v("itens"), { "==": [v("perecivel"), "S"] }] }, { itens })).toBe(true);
    expect(avaliar({ none: [v("itens"), { "==": [v("perecivel"), "S"] }] }, { itens })).toBe(false);
  });

  it("reduce acumula com current e accumulator", () => {
    const itens = [{ quantidade: 2, valor_unitario: 0.1 }, { quantidade: 1, valor_unitario: 0.2 }];
    const soma = { reduce: [v("itens"), { "+": [v("accumulator"), { "*": [v("current.quantidade"), v("current.valor_unitario")] }] }, 0] };
    expect(avaliar(soma, { itens })).toBe(0.4);
    expect(avaliar({ reduce: [v("nada"), { "+": [v("accumulator"), 1] }, 0] }, {})).toBe(0);
  });

  it("<= e > comparam em decimal exato", () => {
    expect(avaliar({ "<=": [{ "+": [0.1, 0.2] }, 0.3] }, {})).toBe(true);
    expect(avaliar({ ">": [{ "+": [0.1, 0.2] }, 0.3] }, {})).toBe(false);
    expect(avaliar({ ">": [3, 2] }, {})).toBe(true);
    expect(avaliar({ "<=": [3, 2] }, {})).toBe(false);
    expect(avaliar({ "<=": ["3", 4] }, {})).toBe(false);
  });

  it("contas: +, -, *, / e % em decimal exato", () => {
    expect(avaliar({ "+": [0.1, 0.2] }, {})).toBe(0.3);
    expect(avaliar({ "+": [1, 2, 3] }, {})).toBe(6);
    expect(avaliar({ "-": [0.3, 0.1] }, {})).toBe(0.2);
    expect(avaliar({ "-": [5] }, {})).toBe(-5);
    expect(avaliar({ "*": [3, 26666.67] }, {})).toBe(80000.01);
    expect(avaliar({ "*": [1.1, 1.1] }, {})).toBe(1.21);
    expect(avaliar({ "/": [1, 8] }, {})).toBe(0.125);
    expect(avaliar({ "%": [7, 3] }, {})).toBe(1);
  });

  it("não arredonda: a parte inteira só sai se a expressão fizer a conta (como a VAR-118 faz com %)", () => {
    // parte inteira de 7 x 25 / 100 = 1,75 -> 1
    const parteInteira = { "/": [{ "-": [{ "*": [7, 25] }, { "%": [{ "*": [7, 25] }, 100] }] }, 100] };
    expect(avaliar(parteInteira, {})).toBe(1);
    expect(avaliar({ "/": [{ "*": [7, 25] }, 100] }, {})).toBe(1.75);
  });
});

describe("avaliador: ausente e divisão por zero", () => {
  it.each(["+", "-", "*", "/", "%"])("conta %s com valor ausente devolve null e registra a ocorrência", (operador) => {
    const { valor, ocorrencias } = avaliarComOcorrencias({ [operador]: [v("falta"), 2] }, {});
    expect(valor).toBeNull();
    expect(ocorrencias).toEqual([{ tipo: "valor_ausente", operador }]);
  });

  it("comparação com valor ausente devolve null (não trata o ausente como 0)", () => {
    const { valor, ocorrencias } = avaliarComOcorrencias({ "<=": [v("falta"), 80000] }, {});
    expect(valor).toBeNull();
    expect(ocorrencias).toEqual([{ tipo: "valor_ausente", operador: "<=" }]);
  });

  it("conta com texto não converte: devolve null", () => {
    const { valor, ocorrencias } = avaliarComOcorrencias({ "+": ["20 dias", 1] }, {});
    expect(valor).toBeNull();
    expect(ocorrencias[0]).toMatchObject({ tipo: "valor_nao_numerico", valor: "20 dias" });
  });

  it.each(["/", "%"])("%s por zero devolve null, nunca NaN nem Infinity", (operador) => {
    const { valor, ocorrencias } = avaliarComOcorrencias({ [operador]: [1, 0] }, {});
    expect(valor).toBeNull();
    expect(ocorrencias).toEqual([{ tipo: "divisao_por_zero", operador }]);
  });

  it("divisão sem decimal exato devolve null", () => {
    const { valor, ocorrencias } = avaliarComOcorrencias({ "/": [1, 3] }, {});
    expect(valor).toBeNull();
    expect(ocorrencias).toEqual([{ tipo: "divisao_sem_decimal_exato", operador: "/" }]);
  });

  it("recusa operador fora da lista e objeto com duas chaves", () => {
    expect(() => avaliar({ "<": [1, 2] }, {})).toThrow(ErroDeExpressao);
    expect(() => avaliar({ "==": [1, 1], "!=": [1, 2] }, {})).toThrow(ErroDeExpressao);
  });
});

describe("limite de ME/EPP com as expressões das matrizes (VAR-119 e VAR-113)", () => {
  const dir = path.resolve(import.meta.dirname, "../../matrizes/v1");
  const ler = (arquivo: string) =>
    parse(readFileSync(path.join(dir, arquivo), "utf8"), { bom: true, columns: true }) as Record<string, string>[];
  const m05 = ler("M05_variaveis.csv");
  const expressao = (id: string) => JSON.parse(m05.find((l) => l.id === id)!.calculo_expr);
  const valorDoGrupo = expressao("VAR-119");
  const tratamento = expressao("VAR-113");
  const limiteTexto = ler("M12_parametros.csv").find((l) => l.nome === "limite_exclusivo_me_epp")!.valor;
  const limite = Number(limiteTexto);

  /** Tratamento do primeiro item de um grupo de dois: 7 unidades a 9.242,20 e 1 unidade com o que falta até o limite. */
  function tratamentoDoGrupo(centavosAcima: number): Valor {
    const [reais, centavos = ""] = limiteTexto.split(".");
    const centavosDoLimite = BigInt(reais + centavos.padEnd(2, "0"));
    const centavosDoSegundo = centavosDoLimite - BigInt(7 * 924220) + BigInt(centavosAcima);
    const itens: Record<string, Valor>[] = [
      { numero: 1, grupo: "G1", quantidade: 7, valor_unitario: 9242.2 },
      { numero: 2, grupo: "G1", quantidade: 1, valor_unitario: Number(centavosDoSegundo) / 100 },
    ];
    const globais = { WZ_01: "LICITACAO", VAR_057: null, parametros: { limite_exclusivo_me_epp: limite, divisor_percentual: 100 } };
    const contexto = (item: Record<string, Valor>) => ({ ...globais, ...item, itens_do_grupo: itens.map((i) => ({ ...globais, ...i })) });
    for (const item of itens) item.valor_unidade_disputa = avaliar(valorDoGrupo, contexto(item));
    return avaliar(tratamento, contexto(itens[0]));
  }

  // Com o limite de 80.000,00, a soma em ponto flutuante de 7 x 9.242,20 + 15.304,60 dá 80.000,00000000001.
  it("soma exatamente igual ao limite dá EXCLUSIVO", () => {
    expect(tratamentoDoGrupo(0)).toBe("EXCLUSIVO");
  });

  it("um centavo acima do limite não dá EXCLUSIVO", () => {
    expect(tratamentoDoGrupo(1)).not.toBe("EXCLUSIVO");
  });
});
