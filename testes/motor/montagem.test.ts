import { describe, expect, it } from "vitest";
import { codigoDoGrupo, escolherBlocos, paiDoBloco } from "../../src/motor/montagem/blocos.ts";
import { extenso, formatar, moedaPorExtenso, textoDoValor } from "../../src/motor/montagem/formatos.ts";
import { Montagem, pontuarSeries } from "../../src/motor/montagem/lacunas.ts";
import { numerar, semNumeracaoDigitada, temNumeracaoDigitada } from "../../src/motor/montagem/numeracao.ts";
import { insercaoDaClausula } from "../../src/motor/montagem/setoriais.ts";
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
    lacunas_mapa: null,
    tabela_colunas: null,
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

describe("formatos do texto", () => {
  it.each([
    [1, "um"],
    [30, "trinta"],
    [100, "cem"],
    [101, "cento e um"],
    [1000, "mil"],
    [1500, "mil e quinhentos"],
    [1250, "mil duzentos e cinquenta"],
    [2000000, "dois milhões"],
  ])("%d por extenso: %s", (n, texto) => {
    expect(extenso(n)).toBe(texto);
  });

  it("número, moeda, percentual e data", () => {
    expect(formatar(30, "NUMERO_EXTENSO")).toBe("30 (trinta)");
    expect(formatar(1234.5, "MOEDA")).toBe("R$ 1.234,50");
    expect(moedaPorExtenso(1234.56)).toBe("(mil duzentos e trinta e quatro reais e cinquenta e seis centavos)");
    expect(formatar(5, "PERCENTUAL_EXTENSO")).toBe("5% (cinco por cento)");
    expect(formatar(12.5, "PERCENTUAL_EXTENSO")).toBe("12,5% (doze vírgula cinco por cento)");
    expect(formatar(25, "PERCENTUAL_2")).toBe("25,00%");
    expect(formatar("2026-10-23", "DATA")).toBe("23/10/2026");
    expect(formatar("23/10/2026", "MES_EXTENSO")).toBe("outubro");
    expect(formatar(["a", "b", "c"], "LISTA_TEXTO")).toBe("a, b e c");
    expect(formatar(1, "TEXTO", "MESES")).toBe("1 mês");
    expect(formatar(12, "NUMERO_EXTENSO", "MESES")).toBe("12 (doze) meses");
    expect(textoDoValor(15000)).toBe("15.000");
  });

  it("não arredonda: moeda com mais de dois decimais e extenso de número quebrado não são aceitos", () => {
    expect(() => formatar(1.005, "MOEDA")).toThrow();
    expect(() => formatar(2.5, "NUMERO_EXTENSO")).toThrow();
  });
});

describe("texto pelo lacunas_mapa", () => {
  const nome = (v: string) => v.replace("_", "-");
  const montar = (texto: string, mapa: unknown[], dados: Record<string, unknown> = {}) =>
    new Montagem(dados as never, nome).texto("TR-9.9", texto, mapa);

  it("PREENCHER com formato e unidade; sem valor, lacuna com o ID da regra", () => {
    const mapa = [{ marcador: "[prazo]", ocorrencia: 1, fonte: "VAR_034", formato: "NUMERO_EXTENSO", unidade: "VAR_163" }];
    expect(montar("Vigência de [prazo].", mapa, { VAR_034: 12, VAR_163: "MESES" }).texto).toBe("Vigência de 12 (doze) meses.");
    const vazio = montar("Vigência de [prazo].", mapa);
    expect(vazio.texto).toBe("Vigência de [[LACUNA VAR-034]].");
    expect(vazio.lacunas).toEqual([{ trecho: "TR-9.9", marcador: "[prazo]", fonte: "VAR-034", motivo: "sem_valor" }]);
  });

  it("marcador repetido: cada entrada do mapa troca a sua ocorrência", () => {
    const mapa = [
      { marcador: "[...]", ocorrencia: 1, fonte: "VAR_001" },
      { marcador: "[...]", ocorrencia: 2, fonte: "VAR_002" },
    ];
    expect(montar("[...] e [...]", mapa, { VAR_001: "a", VAR_002: "b" }).texto).toBe("a e b");
  });

  it("ESCOLHA: fica a opção verdadeira do grupo; opção padrão sai marcada e listada", () => {
    const mapa = [
      { marcador: "[A]", ocorrencia: 1, fonte: null, acao: "ESCOLHA", grupo: "g", opcoes: [{ quando: { "==": [{ var: "WZ_01" }, "A"] }, texto: "opção A" }] },
      { marcador: "[B]", ocorrencia: 1, fonte: null, acao: "ESCOLHA", grupo: "g", opcoes: [{ quando: true, texto: "opção B", padrao: true }] },
    ];
    expect(montar("Conforme [A] OU [B].", mapa, { WZ_01: "A" }).texto).toBe("Conforme opção A.");
    const montagem = new Montagem({} as never, nome);
    expect(montagem.texto("TR-9.9", "Conforme [A] OU [B].", mapa).texto).toBe("Conforme [[PADRÃO: opção B]].");
    expect(montagem.padroes).toEqual([{ trecho: "TR-9.9", marcador: "[B]", texto: "opção B" }]);
  });

  it("OPCIONAL: entra sem os colchetes, ou sai junto com o texto de antes", () => {
    const mapa = [{ marcador: "[incluindo X]", ocorrencia: 1, fonte: "VAR_009", acao: "OPCIONAL", quando: { "==": [{ var: "WZ_08" }, "SIM"] }, texto: "incluindo {valor}", remove_antes: ", ", formato: "LISTA_TEXTO" }];
    expect(montar("Aquisição de bens, [incluindo X], nos termos.", mapa, { WZ_08: "SIM", VAR_009: ["instalação", "treinamento"] }).texto).toBe("Aquisição de bens, incluindo instalação e treinamento, nos termos.");
    expect(montar("Aquisição de bens, [incluindo X], nos termos.", mapa, { WZ_08: "NAO" }).texto).toBe("Aquisição de bens, nos termos.");
  });

  it("EQUIPE e REMOVER", () => {
    const mapa = [
      { marcador: "[norma]", ocorrencia: 1, fonte: null, acao: "EQUIPE", comentario: "cita norma" },
      { marcador: "(instrução)", ocorrencia: 1, fonte: null, acao: "REMOVER" },
    ];
    const resultado = montar("Conforme [norma] (instrução).", mapa);
    expect(resultado.texto).toBe("Conforme [[LACUNA EQUIPE]].");
    expect(resultado.lacunas.map((l) => l.motivo)).toEqual(["equipe"]);
  });

  it("série de blocos-lista: bloco sem elemento sai, e a pontuação final é refeita", () => {
    const blocos = ["TR-4.1.1", "TR-4.1.2", "TR-4.1.3"];
    const entrada = (i: number) => ({ marcador: "[...]", ocorrencia: 1, fonte: "VAR_044", indice: i, lista_blocos: blocos, ...(i > 0 ? { se_vazio: "OMITE_BLOCO" } : {}) });
    const montagem = new Montagem({ VAR_044: ["a", "b"] } as never, nome);
    const textos = new Map<string, string>();
    blocos.forEach((b, i) => {
      const r = montagem.texto(b, i === 2 ? "[...]." : "[...];", [entrada(i)]);
      if (!r.omitido) textos.set(b, r.texto);
    });
    expect([...textos.keys()]).toEqual(["TR-4.1.1", "TR-4.1.2"]);
    pontuarSeries(textos, blocos.map((id, i) => bloco(id, { lacunas_mapa: [entrada(i)] })));
    expect([...textos.values()]).toEqual(["a; e", "b."]);
  });

  it("concordância pelo número de itens (Fase 15): singular, plural e, sem valor, o texto do modelo", () => {
    const mapa = [{ marcador: "[itens]", ocorrencia: 1, fonte: "CK_X_17", formato: "LISTA_TEXTO", estende_desde: "Para os itens ", concordancia: { singular: "Para o item {valor}", plural: "Para os itens {valor}" } }];
    expect(montar("Para os itens [itens], prazo menor.", mapa, { CK_X_17: [3] }).texto).toBe("Para o item 3, prazo menor.");
    expect(montar("Para os itens [itens], prazo menor.", mapa, { CK_X_17: [1, 3] }).texto).toBe("Para os itens 1 e 3, prazo menor.");
    expect(montar("Para os itens [itens], prazo menor.", mapa).texto).toBe("Para os itens [[LACUNA CK-X_17]], prazo menor.");
  });

  it("concordância com NUMEROS_DOS_ITENS e estende_ate: o verbo depois do marcador também concorda", () => {
    const mapa = [{
      marcador: "[itens]", ocorrencia: 1, fonte: "itens.faixa_temperatura", formato: "NUMEROS_DOS_ITENS", estende_desde: "Os itens ", estende_ate: " serão entregues",
      concordancia: { singular: "O item {valor} será entregue", plural: "Os itens {valor} serão entregues" },
    }];
    const itens = (...faixas: (string | null)[]) => faixas.map((f, i) => ({ numero: i + 1, faixa_temperatura: f }));
    expect(montar("Os itens [itens] serão entregues refrigerados.", mapa, { itens: itens("2 a 8 °C", null) }).texto).toBe("O item 1 será entregue refrigerados.");
    expect(montar("Os itens [itens] serão entregues refrigerados.", mapa, { itens: itens("2 a 8 °C", "15 a 30 °C") }).texto).toBe("Os itens 1 e 2 serão entregues refrigerados.");
  });

  it("POR_ITEM_AGRUPADO (Fase 15): itens com o mesmo valor ficam juntos, na ordem em que aparecem", () => {
    const mapa = [{ marcador: "[faixa]", ocorrencia: 1, fonte: "itens.faixa_temperatura", formato: "POR_ITEM_AGRUPADO", modelo_por_item: { singular: "de {valor} para o item {itens}", plural: "de {valor} para os itens {itens}" } }];
    const itens = [
      { numero: 1, faixa_temperatura: "2 a 8 °C" },
      { numero: 2, faixa_temperatura: "15 a 30 °C" },
      { numero: 3, faixa_temperatura: "2 a 8 °C" },
      { numero: 4, faixa_temperatura: null },
    ];
    expect(montar("Faixa [faixa].", mapa, { itens }).texto).toBe("Faixa de 2 a 8 °C para os itens 1 e 3; de 15 a 30 °C para o item 2.");
    expect(montar("Faixa [faixa].", mapa, { itens: [{ numero: 1 }] }).texto).toBe("Faixa [[LACUNA itens.faixa-temperatura]].");
  });

  it("bloco com marcadores e sem mapa: lacuna sem_mapa", () => {
    const r = new Montagem({} as never, nome).texto("TR-9.9", "Texto [x].", null, "[x]");
    expect(r.lacunas.map((l) => l.motivo)).toEqual(["sem_mapa"]);
  });
});

describe("tabela pelo tabela_colunas", () => {
  const tabela = {
    linhas: "itens",
    colunas: [
      { cabecalho: "ITEM", fonte: "itens.numero" },
      { cabecalho: "ESPECIFICAÇÃO", fonte: "itens.especificacao" },
      { cabecalho: "QUANTIDADE", fonte: "itens.quantidade_principal", formato: "NUMERO" },
      { cabecalho: "VALOR UNITÁRIO", fonte: "itens.valor_unitario", formato: "MOEDA", sigiloso: "SIGILOSO" },
    ],
    orcamento_sigiloso: { quando: { "==": [{ var: "WZ_40" }, "SIM"] }, colunas: ["VALOR UNITÁRIO"], texto: "SIGILOSO" },
    linha_cota: {
      quando: { "==": [{ var: "tratamento_me_epp" }, "COTA"] },
      valores: { ITEM: "numero", "ESPECIFICAÇÃO": "Cota fictícia do item {itens.numero}", QUANTIDADE: "itens.quantidade_cota", "VALOR UNITÁRIO": "itens.valor_unitario" },
    },
  };
  const itens = [
    { numero: 2, especificacao: "Item fictício B", quantidade_principal: 1000, valor_unitario: 1.5, tratamento_me_epp: "AMPLA" },
    { numero: 1, especificacao: "Item fictício A", quantidade_principal: 75, valor_unitario: 10, tratamento_me_epp: "COTA", quantidade_cota: 25 },
  ];

  it("itens com o próprio número e as cotas no fim, sem renumerar (P35)", () => {
    const r = new Montagem({ itens } as never, (v) => v).tabela("TR-1.1.TAB1", "", tabela);
    expect(r.texto.split("\n")).toEqual([
      "ITEM | ESPECIFICAÇÃO | QUANTIDADE | VALOR UNITÁRIO",
      "1 | Item fictício A | 75 | R$ 10,00",
      "2 | Item fictício B | 1.000 | R$ 1,50",
      "3 | Cota fictícia do item 1 | 25 | R$ 10,00",
    ]);
    expect(r.lacunas).toEqual([]);
  });

  it("orçamento sigiloso: as colunas de valor trazem SIGILOSO", () => {
    const r = new Montagem({ itens, WZ_40: "SIM" } as never, (v) => v).tabela("TR-1.1.TAB1", "", tabela);
    expect(r.texto).not.toContain("R$");
    expect(r.texto.split("\n")[3]).toBe("3 | Cota fictícia do item 1 | 25 | SIGILOSO");
  });

  it("coluna com quando e textos (PARTICIPAÇÃO, Fase 15): só entra quando vale; código fora da lista é lacuna; texto fixo na cota", () => {
    const participacao = {
      cabecalho: "PARTICIPAÇÃO", fonte: "itens.tratamento_me_epp", acrescentada: true, quando: { "==": [{ var: "WZ_01" }, "LICITACAO"] },
      textos: { AMPLA: "Ampla participação", COTA: "Cota principal (ampla participação)" },
    };
    const comColuna = { ...tabela, colunas: [...tabela.colunas, participacao], linha_cota: { ...tabela.linha_cota, valores: { ...tabela.linha_cota.valores, "PARTICIPAÇÃO": { texto: "Cota reservada para ME/EPP" } } } };
    const r = new Montagem({ itens, WZ_01: "LICITACAO", WZ_40: "SIM" } as never, (v) => v).tabela("TR-1.1.TAB1", "", comColuna);
    expect(r.texto.split("\n")).toEqual([
      "ITEM | ESPECIFICAÇÃO | QUANTIDADE | VALOR UNITÁRIO | PARTICIPAÇÃO",
      "1 | Item fictício A | 75 | SIGILOSO | Cota principal (ampla participação)",
      "2 | Item fictício B | 1.000 | SIGILOSO | Ampla participação",
      "3 | Cota fictícia do item 1 | 25 | SIGILOSO | Cota reservada para ME/EPP",
    ]);
    const direta = new Montagem({ itens, WZ_01: "CONTRATACAO_DIRETA" } as never, (v) => v).tabela("TR-1.1.TAB1", "", comColuna);
    expect(direta.texto).not.toContain("PARTICIPAÇÃO");
    const semCodigo = new Montagem({ itens: [{ ...itens[0], tratamento_me_epp: "EXCLUSIVO" }], WZ_01: "LICITACAO" } as never, (v) => v).tabela("TR-1.1.TAB1", "", comColuna);
    expect(semCodigo.lacunas.map((l) => l.marcador)).toEqual(["PARTICIPAÇÃO do item 2"]);
  });

  it("célula sem dado vira lacuna; tabela sem itens não é montada", () => {
    const r = new Montagem({ itens: [{ numero: 1 }] } as never, (v) => v).tabela("TR-1.1.TAB1", "", tabela);
    expect(r.lacunas.map((l) => l.marcador)).toEqual(["ESPECIFICAÇÃO do item 1", "QUANTIDADE do item 1", "VALOR UNITÁRIO do item 1"]);
    const vazia = new Montagem({ itens: [] } as never, (v) => v).tabela("TR-1.1.TAB1", "MODELO", tabela);
    expect(vazia.texto).toBe("[[TABELA NÃO MONTADA]]\nMODELO");
    expect(vazia.lacunas.map((l) => l.motivo)).toEqual(["tabela_nao_montada"]);
  });
});

describe("posição das cláusulas setoriais (inserir_apos, nivel, alternativo)", () => {
  const clausula = (extra: Partial<LinhaM08>) => ({ inserir_apos: "TR-5.4", nivel: "MESMO_NIVEL", inserir_apos_alternativo: "", ...extra }) as LinhaM08;

  it("depois do bloco, no nível indicado", () => {
    expect(insercaoDaClausula(clausula({ nivel: "SUBITEM" }), new Set(["TR-5.4"]))).toEqual({ tipo: "apos", bloco: "TR-5.4", nivel: "SUBITEM", alternativa: false });
  });

  it("bloco fora da minuta: o primeiro alternativo presente; sem nenhum, fim do corpo", () => {
    const c = clausula({ inserir_apos: "TR-5.4.1", inserir_apos_alternativo: "TR-5.9 (MESMO_NIVEL); TR-5.4 (SUBITEM)" });
    expect(insercaoDaClausula(c, new Set(["TR-5.4"]))).toEqual({ tipo: "apos", bloco: "TR-5.4", nivel: "SUBITEM", alternativa: true });
    expect(insercaoDaClausula(c, new Set())).toEqual({ tipo: "fim_do_corpo" });
  });

  it("PREENCHE_BLOCO não entra como texto", () => {
    expect(insercaoDaClausula(clausula({ inserir_apos: "TR-9.35", nivel: "PREENCHE_BLOCO" }), new Set(["TR-9.35"]))).toEqual({ tipo: "preenche_bloco", bloco: "TR-9.35" });
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
