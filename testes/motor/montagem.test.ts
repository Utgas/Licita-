import { describe, expect, it } from "vitest";
import { codigoDoGrupo, escolherBlocos, paiDoBloco } from "../../src/motor/montagem/blocos.ts";
import { preencherBloco, preencherClausula, textoDoValor, variaveisPorBloco } from "../../src/motor/montagem/lacunas.ts";
import { numerar, semNumeracaoDigitada, temNumeracaoDigitada } from "../../src/motor/montagem/numeracao.ts";
import { ancoraDaClausula } from "../../src/motor/montagem/setoriais.ts";
import type { LinhaM02, LinhaM04, LinhaM08, LinhaM10 } from "../../src/motor/pacote/esquema.ts";
import { validar } from "../../src/motor/validacao/validacoes.ts";
import { pacoteDasMatrizes } from "./pacote-das-matrizes.ts";

const { pacote } = pacoteDasMatrizes();

/** Bloco fictício do M02. */
function bloco(id: string, extra: Partial<LinhaM02> = {}): LinhaM02 {
  return {
    id,
    secao: "1. SEÇÃO FICTÍCIA",
    item_modelo: `${id.replace(/^TR-/, "")}.`,
    texto_literal: `Texto fictício de ${id}.`,
    formatacao: "PRETO",
    tipo: "TF",
    grupo_alternativa: "",
    opcao: "",
    grupo_ativo_expr: null,
    lacunas: "",
    notas: "",
    condicao_inclusao: "",
    condicao_expr: true,
    origem_dado: "",
    normas: "",
    fonte: "teste",
    status: "INFERIDO",
    ...extra,
  };
}

function pergunta(id: string, extra: Partial<LinhaM04> = {}): LinhaM04 {
  return {
    id,
    pergunta: "Pergunta fictícia?",
    documento: "TR",
    tipo_resposta: "SIM_NAO",
    opcoes: "SIM; NAO",
    depende_de: "",
    depende_de_expr: null,
    pre_preenchida_por: "",
    calculo_expr: null,
    liga_blocos: "",
    liga_expr: null,
    desliga_blocos: "",
    desliga_expr: null,
    exige_justificativa: "N",
    coerencia: "",
    fundamento: "",
    fonte: "teste",
    status: "INFERIDO",
    validacao: "",
    comentario_validacao: "",
    ...extra,
  };
}

const ids = (escolha: ReturnType<typeof escolherBlocos>) => escolha.blocos.map((b) => b.linha.id);
const se = (variavel: string, valor: string) => ({ "==": [{ var: variavel }, valor] });

describe("quais blocos entram", () => {
  it("pela condicao_expr; separador OU e condição false ficam fora", () => {
    const m02 = [bloco("TR-1"), bloco("TR-1.1", { condicao_expr: se("WZ_01", "SIM") }), bloco("TR-1.1.OU", { item_modelo: "OU" }), bloco("TR-1.2", { condicao_expr: false })];
    expect(ids(escolherBlocos(m02, [], { WZ_01: "SIM" }))).toEqual(["TR-1", "TR-1.1"]);
    expect(ids(escolherBlocos(m02, [], { WZ_01: "NAO" }))).toEqual(["TR-1"]);
  });

  it("desligar vence ligar", () => {
    const m02 = [bloco("TR-1"), bloco("TR-1.1")];
    const m04 = [
      pergunta("WZ-01", { liga_expr: { merge: [{ if: [se("WZ_01", "SIM"), ["TR-1.1"], []] }] } }),
      pergunta("WZ-02", { desliga_expr: { merge: [{ if: [se("WZ_02", "SIM"), ["TR-1.1"], []] }] } }),
    ];
    const escolha = escolherBlocos(m02, m04, { WZ_01: "SIM", WZ_02: "SIM" });
    expect(ids(escolha)).toEqual(["TR-1"]);
    expect(escolha.excluidos).toEqual([{ id: "TR-1.1", motivo: "desligado" }]);
  });

  it("guarda a origem: quem ligou e as respostas que a condição usou", () => {
    const m02 = [bloco("TR-1", { condicao_expr: se("WZ_01", "SIM") })];
    const m04 = [pergunta("WZ-01", { liga_expr: { merge: [{ if: [se("WZ_01", "SIM"), ["TR-1"], []] }] } })];
    expect(escolherBlocos(m02, m04, { WZ_01: "SIM", WZ_02: "X" }).blocos[0].origem).toEqual({ ligadoPor: ["WZ-01"], respostas: { WZ_01: "SIM" } });
  });

  it("filho sem o pai não entra, em cascata", () => {
    const m02 = [bloco("TR-4"), bloco("TR-4.41", { condicao_expr: false }), bloco("TR-4.41.1"), bloco("TR-4.41.1.a"), bloco("TR-4.42")];
    const escolha = escolherBlocos(m02, [], {});
    expect(ids(escolha)).toEqual(["TR-4", "TR-4.42"]);
    expect(escolha.excluidos.map((e) => [e.id, e.motivo])).toEqual([
      ["TR-4.41.1", "sem_pai"],
      ["TR-4.41.1.a", "sem_pai"],
    ]);
  });

  it("pai pelo M02: ID sem o último segmento numérico, de letra ou romano, se existir", () => {
    const todos = new Set(["TR-4.41", "TR-7.1", "TR-2.2", "TR-AI-1.3"]);
    expect(paiDoBloco("TR-4.41.1", todos)).toBe("TR-4.41");
    expect(paiDoBloco("TR-7.1.a", todos)).toBe("TR-7.1");
    expect(paiDoBloco("TR-2.2.IV", todos)).toBe("TR-2.2");
    expect(paiDoBloco("TR-AI-1.3.1", todos)).toBe("TR-AI-1.3");
    expect(paiDoBloco("TR-4.3.1.1", todos)).toBeUndefined();
    expect(paiDoBloco("TR-1.1.TAB1", todos)).toBeUndefined();
  });

  describe("grupo de alternativas", () => {
    const grupo = (ativo: LinhaM02["grupo_ativo_expr"]) => [
      bloco("TR-1"),
      bloco("TR-1.2", { grupo_alternativa: "GA-01 (fictício)", opcao: "A", grupo_ativo_expr: ativo, condicao_expr: se("WZ_01", "A") }),
      bloco("TR-1.3", { grupo_alternativa: "GA-01 (fictício)", opcao: "B", grupo_ativo_expr: ativo, condicao_expr: se("WZ_02", "B") }),
    ];

    it("ativo com exatamente uma opção: sem bloqueio", () => {
      expect(escolherBlocos(grupo(null), [], { WZ_01: "A" }).bloqueiosGrupoAlternativas).toEqual([]);
    });

    it("ativo com nenhuma ou com duas opções: bloqueio", () => {
      expect(escolherBlocos(grupo(null), [], {}).bloqueiosGrupoAlternativas).toEqual(["GA-01"]);
      expect(escolherBlocos(grupo(null), [], { WZ_01: "A", WZ_02: "B" }).bloqueiosGrupoAlternativas).toEqual(["GA-01"]);
    });

    it("grupo inativo não bloqueia; grupo_ativo_expr vazia = sempre ativo", () => {
      expect(escolherBlocos(grupo(se("WZ_09", "SIM")), [], {}).bloqueiosGrupoAlternativas).toEqual([]);
      expect(escolherBlocos(grupo(se("WZ_09", "SIM")), [], { WZ_09: "SIM" }).bloqueiosGrupoAlternativas).toEqual(["GA-01"]);
    });

    it("o código do grupo é a primeira palavra", () => {
      expect(codigoDoGrupo("GA-02 (vigência)")).toBe("GA-02");
    });
  });
});

describe("numeração", () => {
  it("é refeita depois das exclusões, nível a nível", () => {
    const linhas = [
      bloco("TR-1", { item_modelo: "1." }),
      bloco("TR-1.3", { item_modelo: "1.3." }),
      bloco("TR-1.3.2", { item_modelo: "1.3.2" }),
      bloco("TR-1.H01", { item_modelo: "subtítulo" }),
      bloco("TR-1.5", { item_modelo: "1.5." }),
      bloco("TR-1.5.1.1", { item_modelo: "1.5.1.1." }),
      bloco("TR-2", { item_modelo: "2." }),
      bloco("TR-2.4", { item_modelo: "2.4." }),
    ];
    expect(Object.fromEntries(numerar(linhas))).toEqual({
      "TR-1": "1.",
      "TR-1.3": "1.1.",
      "TR-1.3.2": "1.1.1",
      "TR-1.5": "1.2.",
      "TR-1.5.1.1": "1.2.1.1.",
      "TR-2": "2.",
      "TR-2.4": "2.1.",
    });
  });

  it("o Anexo I é numerado à parte", () => {
    const linhas = [
      bloco("TR-11", { item_modelo: "11." }),
      bloco("TR-AI-1", { item_modelo: "1.", secao: "Anexo I - 1. FICTÍCIA" }),
      bloco("TR-AI-1.2", { item_modelo: "1.2.", secao: "Anexo I - 1. FICTÍCIA" }),
    ];
    expect(Object.fromEntries(numerar(linhas))).toEqual({ "TR-11": "1.", "TR-AI-1": "1.", "TR-AI-1.2": "1.1." });
  });

  it("incisos e alíneas são renumerados dentro do item", () => {
    const linhas = [
      bloco("TR-2.2", { item_modelo: "2.2." }),
      bloco("TR-2.2.II", { item_modelo: "II)" }),
      bloco("TR-2.2.IV", { item_modelo: "IV)" }),
      bloco("TR-7.1", { item_modelo: "7.1." }),
      bloco("TR-7.1.b", { item_modelo: "b)" }),
    ];
    const numeros = numerar(linhas);
    expect([numeros.get("TR-2.2.II"), numeros.get("TR-2.2.IV"), numeros.get("TR-7.1.b")]).toEqual(["I)", "II)", "a)"]);
  });

  it("P18: a numeração digitada no texto não é impressa; no modelo, só o TR-1.7 tem", () => {
    expect(semNumeracaoDigitada("1.6.1 O fornecimento fictício")).toBe("O fornecimento fictício");
    expect(semNumeracaoDigitada("Lei nº 14.133 fictícia")).toBe("Lei nº 14.133 fictícia");
    expect(pacote.matrizes.M02.filter((l) => temNumeracaoDigitada(l.texto_literal)).map((l) => l.id)).toEqual(["TR-1.7"]);
  });
});

describe("lacunas", () => {
  it("um marcador e uma variável: preenche; sem valor, marca a lacuna", () => {
    const linha = bloco("TR-5.3", { texto_literal: "Antecedência de (...) dias.", lacunas: "(...)" });
    expect(preencherBloco(linha, linha.texto_literal, ["VAR-063"], { VAR_063: 5 }).texto).toBe("Antecedência de 5 dias.");
    const vazio = preencherBloco(linha, linha.texto_literal, ["VAR-063"], {});
    expect(vazio.texto).toBe("Antecedência de [[LACUNA VAR-063]] dias.");
    expect(vazio.lacunas).toEqual([{ trecho: "TR-5.3", marcador: "(...)", candidatas: ["VAR-063"], motivo: "sem_valor" }]);
  });

  it("sem ligação única entre marcador e variável: não adivinha, marca com as candidatas", () => {
    const linha = bloco("TR-1.5", { texto_literal: "Prazo de [a] a partir de [b].", lacunas: "[a] | [b]" });
    const resultado = preencherBloco(linha, linha.texto_literal, ["VAR-033", "VAR-034"], { VAR_033: 12, VAR_034: "assinatura" });
    expect(resultado.texto).toBe("Prazo de [[LACUNA VAR-033, VAR-034]] a partir de [[LACUNA VAR-033, VAR-034]].");
    expect(resultado.lacunas.map((l) => l.motivo)).toEqual(["sem_ligacao_unica", "sem_ligacao_unica"]);
  });

  it("tabela do modelo (tipo TB) não é montada: fica marcada, com a lacuna própria", () => {
    const linha = bloco("TR-1.1.TAB1", { tipo: "TB", texto_literal: "ITEM | VALOR", lacunas: "R$ ...." });
    const resultado = preencherBloco(linha, linha.texto_literal, ["VAR-011"], {});
    expect(resultado.texto).toBe("[[TABELA NÃO MONTADA]]\nITEM | VALOR");
    expect(resultado.lacunas.map((l) => l.motivo)).toEqual(["tabela_nao_montada"]);
  });

  it("marcador repetido é tratado uma ocorrência de cada vez", () => {
    const linha = bloco("TR-4.18.1", { texto_literal: "[...] e [...]", lacunas: "[...] | [...]" });
    expect(preencherBloco(linha, linha.texto_literal, ["VAR-054"], {}).texto).toBe("[[LACUNA VAR-054]] e [[LACUNA VAR-054]]");
  });

  it("cláusula do M08: [VAR-xxx: ...] com uma variável é preenchido; com duas, fica marcado", () => {
    const resultado = preencherClausula("SET-99", "Itens [VAR-130: itens] com [VAR-122 e VAR-128: cuidados].", { VAR_130: ["1", "2"] });
    expect(resultado.texto).toBe("Itens 1; 2 com [[LACUNA VAR-122, VAR-128]].");
  });

  it("valor no texto: número com vírgula decimal e lista separada por ponto e vírgula", () => {
    expect(textoDoValor(12.5)).toBe("12,5");
    expect(textoDoValor(["a", "b"])).toBe("a; b");
  });

  it("a ligação vem da coluna usada_em do M05", () => {
    expect(variaveisPorBloco(pacote.matrizes.M05).get("TR-5.3")).toEqual(["VAR-063"]);
  });
});

describe("ponto de inserção das cláusulas setoriais", () => {
  const clausula = (ponto: string) => ({ ponto_insercao: ponto }) as LinhaM08;

  it("depois do bloco citado na parte do TR", () => {
    expect(ancoraDaClausula(clausula("TR: seção 5, depois de TR-5.4; ETP: ETP-04.01"), new Set(["TR-5.4"]))).toEqual({ tipo: "depois_do_bloco", bloco: "TR-5.4" });
  });

  it("bloco fora da minuta: fim da seção; sem nada: fim do corpo", () => {
    expect(ancoraDaClausula(clausula("TR: seção 5, depois de TR-5.4"), new Set())).toEqual({ tipo: "fim_da_secao", secao: "5" });
    expect(ancoraDaClausula(clausula("TR: complementa TR-8.2"), new Set())).toEqual({ tipo: "fim_da_secao", secao: "8" });
    expect(ancoraDaClausula(clausula("ETP: ETP-13.01; TR: providências"), new Set())).toEqual({ tipo: "fim_do_corpo" });
  });
});

describe("validações do M10", () => {
  const regra = (id: string, condicao_expr: unknown, tipo: LinhaM10["tipo"] = "ALERTA") =>
    ({ id, regra: "Regra fictícia", tipo, momento: "WIZARD", condicao: "", condicao_expr, mensagem: `Mensagem ${id}.` }) as LinhaM10;

  it("com expressão verdadeira dispara; sem expressão vai para conferência manual; false nunca", () => {
    const resultado = validar([regra("VAL-901", se("WZ_01", "SIM"), "BLOQUEIO"), regra("VAL-902", null), regra("VAL-903", false), regra("VAL-904", se("WZ_01", "NAO"))], { WZ_01: "SIM" });
    expect(resultado.disparadas.map((v) => [v.id, v.tipo])).toEqual([["VAL-901", "BLOQUEIO"]]);
    expect(resultado.conferenciaManual.map((v) => v.id)).toEqual(["VAL-902"]);
  });

  it("as regras sem expressão das matrizes atuais são as da P27", () => {
    const manuais = validar(pacote.matrizes.M10, {}).conferenciaManual.map((v) => v.id);
    expect(manuais).toEqual(pacote.matrizes.M10.filter((l) => l.condicao_expr === null).map((l) => l.id));
    expect(manuais.length).toBeGreaterThan(0);
  });
});
