/**
 * Wizard na tela (passo 9): estado das perguntas, justificativa pedida pelo M04 e campos extras que a minuta pede,
 * sobre o cenário fictício C8. Não precisa de banco.
 */
import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { carregarPacote } from "../../src/dados/pacote.ts";
import type { ProcessoCompleto } from "../../src/dados/processos.ts";
import { type CampoDaMinuta, camposDaMinuta, codigosDaValidacao, justificativaDoM04, justificativaObrigatoria, numeroDigitado, perguntasDoWizard, proximaPendente, textoDoCampo, valorDoCampo } from "../../src/dados/wizard.ts";
import type { EntradaProcesso } from "../../src/motor/entrada.ts";
import { gerarMinuta } from "../../src/motor/minuta.ts";

const { pacote, hash } = carregarPacote();
const m04 = new Map(pacote.matrizes.M04.map((l) => [l.id, l]));
const C8 = JSON.parse(readFileSync(path.resolve(import.meta.dirname, "../../matrizes/v1/cenarios/C8.json"), "utf8")).entrada as Omit<EntradaProcesso, "pacote" | "hashDoPacote">;

const vazio = { respostasWizard: [] } as unknown as ProcessoCompleto;
const minuta = (variaveis: Record<string, unknown> = {}) => gerarMinuta({ pacote, hashDoPacote: hash, ...C8, variaveis: { ...C8.variaveis, ...variaveis } } as EntradaProcesso);

function formulario(campos: Record<string, string>): FormData {
  const f = new FormData();
  for (const [k, v] of Object.entries(campos)) f.set(k, v);
  return f;
}

describe("justificativa pelo M04", () => {
  it("lê 'N', 'S se X ou Y' e 'S:' sem interpretar o texto jurídico", () => {
    expect(justificativaDoM04(m04.get("WZ-02")!)).toBeNull();
    expect(justificativaDoM04(m04.get("WZ-01")!)?.obrigatoriaCom).toEqual(["CONTRATACAO_DIRETA"]);
    expect(justificativaDoM04(m04.get("WZ-22")!)?.obrigatoriaCom).toEqual(["SIM", "SIM_EXIGIDA_ME_EPP"]);
    expect(justificativaDoM04(m04.get("WZ-04")!)?.obrigatoriaCom).toBe("sempre");
  });

  it("obriga só com a resposta indicada", () => {
    const j = justificativaDoM04(m04.get("WZ-17")!);
    expect(justificativaObrigatoria(j, "NAO")).toBe(true);
    expect(justificativaObrigatoria(j, "SIM")).toBe(false);
    expect(justificativaObrigatoria(justificativaDoM04(m04.get("WZ-38")!), ["ATESTADOS"])).toBe(true);
  });
});

describe("perguntas do wizard", () => {
  const perguntas = perguntasDoWizard(pacote, minuta(), vazio);
  const de = (id: string) => perguntas.find((x) => x.id === id);

  it("segue a ordem do M04 e mostra derivadas como calculadas", () => {
    const ordem = pacote.matrizes.M04.map((l) => l.id).filter((id) => de(id));
    expect(perguntas.map((x) => x.id)).toEqual(ordem);
    expect(de("WZ-09")?.estado).toBe("calculada");
  });

  it("separa respondida, pendente e decisão jurídica pendente", () => {
    expect(de("WZ-01")?.estado).toBe("respondida");
    expect(de("WZ-01")?.opcoes).toEqual(["LICITACAO", "CONTRATACAO_DIRETA"]);
    expect(de("WZ-36")?.estado).toBe("decisao_pendente");
    expect(de("WZ-27")?.estado).toBe("pendente");
    expect(de("WZ-27")?.opcoes).toEqual([]);
    expect(de("WZ-27")?.orientacao).not.toBe("");
  });

  it("mostra a sugestão do checklist sem responder por ela", () => {
    expect(de("WZ-47")?.sugestoes).toEqual([{ valor: "SIM", pergunta: "CK-C-20.2" }]);
    expect(de("WZ-47")?.estado).not.toBe("respondida");
  });

  it("anda para a próxima pendente", () => {
    const abertas = perguntas.filter((x) => x.estado === "pendente" || x.estado === "decisao_pendente").map((x) => x.id);
    expect(proximaPendente(perguntas)).toBe(abertas[0]);
    expect(proximaPendente(perguntas, abertas[0])).toBe(abertas[1]);
    expect(proximaPendente(perguntas, abertas[abertas.length - 1])).toBe(abertas[0]);
  });
});

describe("campos extras que a minuta pede", () => {
  const { campos, doChecklist } = camposDaMinuta(pacote, minuta(), vazio);
  const campo = (id: string) => campos.find((c) => c.id === id) as CampoDaMinuta;

  it("lista as VAR que faltam, com a unidade junto do prazo", () => {
    expect(campo("VAR-034").trechos).toContain("TR-1.5");
    expect(campo("VAR-034").forma).toEqual({ tipo: "simples", numerico: true, data: false });
    expect(campo("VAR-163").codigos).toEqual(["DIAS", "MESES", "ANOS"]);
  });

  it("dados do checklist e complementos ficam para a tela do checklist", () => {
    expect(campos.some((c) => c.id.startsWith("CK-"))).toBe(false);
    expect(doChecklist.map((c) => c.id)).toContain("CK-X-10");
    expect(campos.find((c) => c.id === "VAR-008")).toBeUndefined();
  });

  it("monta a forma pelas partes do mapa e pelas colunas da tabela", () => {
    const multas = campo("VAR-071");
    expect(multas.forma.tipo).toBe("partes");
    const lido = valorDoCampo(multas, formulario({ "parte:a.minimo": "0,5", "parte:a.maximo": "10" }));
    expect(lido).toEqual({ valor: { a: { minimo: 0.5, maximo: 10 } } });
    expect(textoDoCampo({ ...multas, valor: { a: { minimo: 0.5, maximo: 10 } } })["parte:a.minimo"]).toBe("0,5");

    const parcelas = campo("VAR-062");
    expect(parcelas.forma.tipo).toBe("tabela");
    if (parcelas.forma.tipo !== "tabela") return;
    const n = parcelas.forma.colunas.length;
    const linha = Array.from({ length: n }, (_, k) => (k === 0 ? "1" : `x${k}`)).join("; ");
    expect(valorDoCampo(parcelas, formulario({ valor: linha }))).toEqual({ valor: [Object.fromEntries(parcelas.forma.colunas.map((c, k) => [c.campo, k === 0 ? 1 : `x${k}`]))] });
    expect(valorDoCampo(parcelas, formulario({ valor: "só uma coluna" }))).toHaveProperty("erro");
  });

  it("confere número, data e código", () => {
    expect(valorDoCampo(campo("VAR-034"), formulario({ valor: "doze" }))).toHaveProperty("erro");
    expect(valorDoCampo(campo("VAR-034"), formulario({ valor: "12" }))).toEqual({ valor: 12 });
    expect(valorDoCampo(campo("VAR-163"), formulario({ valor: "SEMANAS" }))).toHaveProperty("erro");
    expect(valorDoCampo(campo("VAR-163"), formulario({ valor: "MESES" }))).toEqual({ valor: "MESES" });
    expect(valorDoCampo(campo("VAR-015"), formulario({ valor: "2026-01-01" }))).toHaveProperty("erro");
    expect(valorDoCampo(campo("VAR-034"), formulario({ valor: "" }))).toEqual({ valor: null });
  });

  it("o valor informado tira a lacuna da minuta", () => {
    const depois = minuta({ VAR_034: 12, VAR_163: "MESES" });
    expect(depois.lacunasNoTexto.some((l) => l.fonte === "VAR-034")).toBe(false);
    expect(depois.trechos.find((t) => t.id === "TR-1.5")?.texto).toContain("12 (doze) meses");
  });

  it("lê número com vírgula, ponto de milhar e símbolos", () => {
    expect(numeroDigitado("1.234,56")).toBe(1234.56);
    expect(numeroDigitado("R$ 10")).toBe(10);
    expect(numeroDigitado("2,5%")).toBe(2.5);
    expect(numeroDigitado("abc")).toBeNull();
    expect(codigosDaValidacao("SIM ou NAO")).toEqual(["SIM", "NAO"]);
    expect(codigosDaValidacao("não vazio")).toEqual([]);
  });
});
