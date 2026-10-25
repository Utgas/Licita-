/**
 * ETP campo a campo e derivação ETP para TR (Marco 3, passos 3 e 4), com um processo fictício quase todo
 * respondido (etp-ficticio.ts).
 */
import { describe, expect, it } from "vitest";
import { derivarEtpParaTr } from "../../src/motor/derivacao/derivacao.ts";
import { gerarMinuta } from "../../src/motor/minuta.ts";
import { type CampoDoEtp, type Etp, gerarEtp } from "../../src/motor/montagem/etp.ts";
import type { EntradaProcesso } from "../../src/motor/entrada.ts";
import { NECESSIDADE_FICTICIA, entradaDoEtpFicticio } from "./etp-ficticio.ts";

function montar(ajuste?: (e: EntradaProcesso) => void) {
  const entrada = entradaDoEtpFicticio();
  ajuste?.(entrada);
  const minuta = gerarMinuta(entrada);
  const etp = gerarEtp(entrada, minuta);
  return { entrada, minuta, etp, derivacao: derivarEtpParaTr(entrada.pacote, minuta, etp) };
}

function campo(etp: Etp, id: string): CampoDoEtp {
  const achado = etp.campos.find((c) => c.id === id);
  if (!achado) throw new Error(`${id} fora do ETP`);
  return achado;
}

const paragrafos = (c: CampoDoEtp) => c.texto.split("\n\n");

describe("ETP campo a campo", () => {
  const { entrada, minuta, etp } = montar();

  it("traz todos os campos do M01, na ordem", () => {
    expect(etp.campos.map((c) => c.id)).toEqual(entrada.pacote.matrizes.M01.map((l) => l.id));
  });

  it("campo sem dado ligado: texto do ETP Digital (TF) ou orientação do M01; nenhum dos dois vai para a cópia", () => {
    expect(campo(etp, "ETP-15.01")).toMatchObject({ situacao: "texto_do_etp_digital", texto: "" });
    expect(campo(etp, "ETP-16.01")).toMatchObject({ situacao: "texto_do_etp_digital", texto: "" });
    expect(campo(etp, "ETP-01.03")).toMatchObject({ situacao: "sem_ligacao", texto: "" });
    expect(campo(etp, "ETP-01.03").orientacao.preenchimento).not.toBe("");
  });

  it("os campos com os dados informados saem preenchidos", () => {
    for (const id of ["ETP-01.01", "ETP-01.02", "ETP-02.01", "ETP-03.01", "ETP-03.02", "ETP-05.01", "ETP-06.01", "ETP-07.01", "ETP-08.01", "ETP-08.02", "ETP-09.01", "ETP-12.01", "ETP-15.02", "ETP-16.02"]) {
      expect(campo(etp, id).situacao, id).toBe("preenchido");
    }
  });

  it("valor sai no formato do tipo do M05; ano sem separador de milhar", () => {
    expect(campo(etp, "ETP-08.01").texto).toBe("Valor total estimado da contratação: R$ 135.000,00");
    expect(campo(etp, "ETP-11.01").texto).toContain(": 2026");
  });

  it("texto corrido entra sozinho; dado curto leva o rótulo", () => {
    const necessidade = paragrafos(campo(etp, "ETP-02.01"));
    expect(necessidade).toContain(NECESSIDADE_FICTICIA);
    expect(necessidade).toContain("Descrição resumida do objeto: Aquisição fictícia de medicamentos");
  });

  it("resposta do checklist que justifica o campo entra; a opção marcada sempre com a pergunta", () => {
    expect(paragrafos(campo(etp, "ETP-07.01"))).toContain("Foi utilizada margem de segurança? Sim. Margem fictícia de dez por cento sobre o consumo médio.");
    expect(paragrafos(campo(etp, "ETP-05.01"))).toEqual(["Solução fictícia escolhida por ser a única que atende ao consumo da unidade."]);
    const soltas = etp.campos.flatMap((c) => c.texto.split("\n")).filter((l) => /^(Sim|Não)\.?$/.test(l.trim()));
    expect(soltas).toEqual([]);
  });

  it("justificativa da equipe no wizard vai para o campo que o M04 cita", () => {
    const parte = campo(etp, "ETP-02.01").partes.find((p) => p.tipo === "justificativa");
    expect(parte).toMatchObject({ regra: "WZ-06", resposta: "COMUM", texto: entrada.justificativas?.WZ_06 });
  });

  it("decisão que o TR repete do campo (M06) entra só quando informada, sem virar lacuna", () => {
    expect(campo(etp, "ETP-06.01").partes).toContainEqual(expect.objectContaining({ regra: "VAR-034", ligacao: "M06", texto: "12" }));
    const sem = montar((e) => delete e.variaveis.VAR_034).etp;
    expect(campo(sem, "ETP-06.01").partes.some((p) => p.regra === "VAR-034")).toBe(false);
    expect(campo(sem, "ETP-06.01").lacunas).toEqual([]);
  });

  it("VAR obrigatória sem valor vira lacuna marcada e deixa o campo obrigatório pendente", () => {
    const sem = montar((e) => delete e.variaveis.VAR_012).etp;
    const memoria = campo(sem, "ETP-07.01");
    expect(memoria.texto).toContain("[[LACUNA VAR-012]]");
    expect(memoria).toMatchObject({ situacao: "incompleto", lacunas: ["VAR-012"] });
    expect(sem.pendencias).toContain("ETP-07.01");
  });

  it("atributo de item sai por item, com o código traduzido pela tabela de itens do TR", () => {
    expect(paragrafos(campo(etp, "ETP-09.01"))).toContain("PARTICIPAÇÃO: item 1: Cota principal (ampla participação); item 2: Exclusiva para ME/EPP");
  });

  it("campo de tabela (TB) traz a mesma tabela de itens do TR", () => {
    const tabela = campo(etp, "ETP-07.02").partes[0];
    const doTr = minuta.trechos.find((t) => t.id === "TR-1.1.TAB1");
    expect(tabela).toMatchObject({ tipo: "tabela", regra: "TR-1.1.TAB1", texto: doTr?.texto });
  });

  it("a minuta do TR é a mesma com ou sem as justificativas do ETP", () => {
    const sem = montar((e) => delete e.justificativas).minuta;
    expect(sem.trechos).toEqual(minuta.trechos);
  });

  it("a mesma entrada dá sempre o mesmo ETP", () => {
    expect(JSON.stringify(montar().etp)).toBe(JSON.stringify(etp));
  });
});

describe("derivação ETP para TR (M06)", () => {
  const { minuta, derivacao, etp } = montar();

  it("bloco do TR que repete um campo preenchido sai derivado, com o número da minuta", () => {
    const vigencia = derivacao.blocos.find((b) => b.bloco === "TR-1.5");
    const naMinuta = minuta.trechos.find((t) => t.id === "TR-1.5");
    expect(vigencia).toMatchObject({ campos: ["ETP-06.01"], situacao: "derivado", numero: naMinuta?.numero });
    expect(vigencia?.variaveis).toContainEqual({ regra: "VAR-034", valor: 12 });
    expect(derivacao.porCampo["ETP-06.01"]).toContainEqual({ bloco: "TR-1.5", numero: naMinuta?.numero });
  });

  it("bloco que repete um campo vazio do ETP avisa qual campo falta", () => {
    expect(campo(etp, "ETP-14.01").situacao).toBe("vazio");
    expect(derivacao.blocos.find((b) => b.bloco === "TR-4.1.1")).toMatchObject({ situacao: "campo_vazio", camposVazios: ["ETP-14.01"] });
  });

  it("o ano do PCA sai sem separador de milhar também no TR (TR-2.2 e TR-2.3)", () => {
    for (const { minuta: m } of [montar(), montar((e) => (e.wizard.WZ_16 = "REMISSAO"))]) {
      const texto = m.trechos.filter((t) => t.id === "TR-2.2" || t.id === "TR-2.3").map((t) => t.texto).join(" ");
      expect(texto).toContain("2026");
      expect(texto).not.toContain("2.026");
    }
  });

  it("só entram blocos que estão na minuta e que o M06 liga ao ETP", () => {
    const naMinuta = new Set(minuta.trechos.map((t) => t.id));
    for (const b of derivacao.blocos) {
      expect(naMinuta.has(b.bloco), b.bloco).toBe(true);
      expect(b.campos.length, b.bloco).toBeGreaterThan(0);
    }
  });
});
