import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import type { EntradaProcesso } from "../../src/motor/entrada.ts";
import type { Valor } from "../../src/motor/pacote/avaliador.ts";
import { prepararProcesso } from "../../src/motor/processo.ts";
import { revisarChecklist } from "../../src/motor/wizard/checklist.ts";
import { pacoteDasMatrizes } from "./pacote-das-matrizes.ts";

const { pacote, hash } = pacoteDasMatrizes();
const CENARIOS = ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"];

function cenario(id: string) {
  return JSON.parse(readFileSync(path.resolve(import.meta.dirname, `../../matrizes/v1/cenarios/${id}.json`), "utf8"));
}

function entradaDe(dados: Omit<EntradaProcesso, "pacote" | "hashDoPacote">): EntradaProcesso {
  return { pacote, hashDoPacote: hash, ...structuredClone(dados) };
}

/** Entrada mínima fictícia: licitação de consumo com um item. */
function entradaFicticia(extra: Partial<EntradaProcesso> = {}): EntradaProcesso {
  return entradaDe({
    checklist: {},
    wizard: { WZ_01: "LICITACAO" },
    itens: [{ numero: 1, quantidade: 10, valor_unitario: 2.5, categoria: "CONSUMO", catmat: "000000", classe_pdm: "" }],
    variaveis: {},
    metadados: {},
    ...extra,
  });
}

describe.each(CENARIOS)("cenário %s: checklist, itens e wizard", (id) => {
  const { entrada, esperado, referencia } = cenario(id);
  const processo = prepararProcesso(entradaDe(entrada));

  it("o checklist preenche as mesmas perguntas do wizard que o simulador", () => {
    expect(processo.preenchidoPeloChecklist).toEqual(referencia.preenchido_pelo_checklist);
  });

  it("os itens saem com os mesmos atributos calculados", () => {
    for (const esperadoDoItem of referencia.itens_calculados as Record<string, Valor>[]) {
      const item = processo.itens.find((i) => i.numero === esperadoDoItem.numero);
      const obtido = Object.fromEntries(Object.keys(esperadoDoItem).map((a) => [a, item?.[a] ?? null]));
      expect(obtido).toEqual(esperadoDoItem);
    }
  });

  // A referência só lista as derivadas que se aplicam; as demais o motor deixa em null.
  it("as perguntas derivadas dão o mesmo resultado", () => {
    const aplicaveis = Object.fromEntries(Object.entries(processo.derivadas).filter(([, v]) => v !== null));
    expect(aplicaveis).toEqual(referencia.derivadas);
  });

  it("as sugestões são as mesmas", () => {
    const obtidas: Record<string, [string, Valor][]> = {};
    for (const s of processo.sugestoes) {
      const chave = s.item === undefined ? s.destino : `item ${s.item}.${s.destino.slice("itens.".length)}`;
      (obtidas[chave] ??= []).push([s.pergunta, s.valor]);
    }
    expect(obtidas).toEqual(referencia.sugestoes);
  });

  it("as perguntas sem resposta são as esperadas", () => {
    expect(processo.wizard.pendentes.map((p) => p.id)).toEqual(esperado.perguntas_sem_resposta);
  });
});

describe("do checklist para o wizard", () => {
  it("PREENCHE responde a pergunta do wizard e guarda a pergunta de origem", () => {
    const processo = prepararProcesso(entradaFicticia({ checklist: { CK_C_12_3: "Parcelada" } }));
    expect(processo.globais.WZ_26).toBe("PARCELADA");
    expect(processo.origens.WZ_26).toEqual({ origem: "CHECKLIST", perguntas: ["CK-C-12.3"] });
  });

  it("a equipe respondeu outra coisa: vale a equipe, com aviso", () => {
    const processo = prepararProcesso(entradaFicticia({ checklist: { CK_C_12_3: "Parcelada" }, wizard: { WZ_01: "LICITACAO", WZ_26: "REMESSA_UNICA" } }));
    expect(processo.globais.WZ_26).toBe("REMESSA_UNICA");
    expect(processo.origens.WZ_26).toEqual({ origem: "EQUIPE" });
    expect(processo.avisos.map((a) => [a.codigo, a.origem.regra])).toContainEqual(["EQUIPE_DIVERGE_DO_CHECKLIST", "CK-C-12.3"]);
  });

  it("duas perguntas que preenchem a mesma WZ com valores diferentes deixam a WZ para a equipe", () => {
    // CK-C-12.3 e CK-P-8.3 preenchem a WZ-26 (processo com os dois checklists).
    const processo = prepararProcesso(entradaFicticia({ checklist: { CK_C_12_3: "Parcelada", CK_P_8_3: "Em remessa única por item" } }));
    expect(processo.globais.WZ_26).toBeUndefined();
    expect(processo.preenchidoPeloChecklist).not.toHaveProperty("WZ_26");
    expect(processo.avisos.map((a) => [a.codigo, a.origem.regra])).toContainEqual(["CONFLITO_NO_CHECKLIST", "CK-P-8.3"]);
    expect(processo.wizard.pendentes.map((p) => p.id)).toContain("WZ-26");
  });

  it("prazo 'Outro' em texto (\"20 dias\") não vira número: a VAR-060 fica em lacuna, com aviso", () => {
    const processo = prepararProcesso(entradaFicticia({ checklist: { CK_C_12_1: "Outro", CK_C_12_1_numero: "20 dias" } }));
    expect(processo.globais.VAR_060).toBeUndefined();
    expect(processo.lacunas).toContainEqual(expect.objectContaining({ destino: "VAR_060", origem: "CK-C-12.1" }));
    expect(processo.avisos.map((a) => a.codigo)).toContain("TIPO_INCOMPATIVEL");
  });

  it("prazo 'Outro' com número lido preenche a VAR-060", () => {
    const processo = prepararProcesso(entradaFicticia({ checklist: { CK_C_12_1: "Outro", CK_C_12_1_numero: 20 } }));
    expect(processo.globais.VAR_060).toBe(20);
    expect(processo.lacunas).toEqual([]);
  });

  it("decisão jurídica nunca é preenchida pelo checklist: só sugestão, e a pergunta fica pendente", () => {
    const sugereDecisao = pacote.matrizes.M11.find((l) => l.id === "CK-C-7.6");
    expect(sugereDecisao?.sugere_expr).toHaveProperty("WZ_11");
    const decisoes = pacote.matrizes.M04.filter((l) => l.pre_preenchida_por.startsWith("DECISAO_JURIDICA")).map((l) => l.id.replace("-", "_"));
    const processo = prepararProcesso(entradaFicticia());
    for (const wz of decisoes) expect(Object.keys(processo.preenchidoPeloChecklist)).not.toContain(wz);
    expect(processo.wizard.pendentes.filter((p) => p.decisaoJuridica).length).toBeGreaterThan(0);
  });

  it("pergunta desligada (WZ-56) nunca é oferecida e a resposta é descartada", () => {
    const processo = prepararProcesso(entradaFicticia({ wizard: { WZ_01: "LICITACAO", WZ_56: "SIM" } }));
    expect(processo.wizard.desligadas).toContain("WZ-56");
    expect(processo.wizard.habilitadas).not.toContain("WZ-56");
    expect(processo.globais.WZ_56).toBeUndefined();
    expect(processo.avisos.map((a) => a.codigo)).toContain("PERGUNTA_DESLIGADA");
  });

  it("complemento do operador (CK-X-01) entra como resposta de checklist", () => {
    const processo = prepararProcesso(
      entradaFicticia({ checklist: { CK_X_01: "Endereço fictício de entrega" }, metadados: { checklist: { consumo: true } } }),
    );
    expect(processo.globais.VAR_064).toBe("Endereço fictício de entrega");
  });
});

describe("revisão das respostas do checklist", () => {
  const m11 = pacote.matrizes.M11;

  it("marca múltipla vira destaque e pergunta ao operador; confirmada, deixa de bloquear", () => {
    const dados = { CK_C_3_3: "Sim", checklist: { consumo: true, marcas_multiplas: ["CK-C-3.3"] } };
    const revisao = revisarChecklist(m11, dados);
    expect(revisao.destaques).toContain("CK-C-3.3");
    expect(revisao.perguntasAoOperador.map((p) => p.pergunta)).toContain("CK-C-3.3");
    expect(revisarChecklist(m11, dados, ["CK-C-3.3"]).perguntasAoOperador.map((p) => p.pergunta)).not.toContain("CK-C-3.3");
  });

  it("prazo 'Outro' sem número lido pede o prazo ao operador", () => {
    const revisao = revisarChecklist(m11, { CK_C_12_1: "Outro", checklist: { consumo: true } });
    expect(revisao.perguntasAoOperador.find((p) => p.pergunta === "CK-C-12.1")?.texto).toMatch(/dias/);
  });

  it("perguntas do checklist que não foi entregue não são revisadas", () => {
    const revisao = revisarChecklist(m11, { checklist: { consumo: true, permanentes: false } });
    expect(revisao.destaques.some((id) => id.startsWith("CK-P-"))).toBe(false);
  });
});
