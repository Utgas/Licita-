/**
 * Derivação ETP para TR no par 117/2025 (critério de saída do Marco 3, com a decisão 0008: sem o DFD do processo,
 * testa-se só a derivação). A fonte é o próprio M06: as colunas teste_par_117 e evidencia_par_117 dizem, bloco a
 * bloco, se o ETP e o TR reais saíram iguais.
 *
 * - CONSISTENTE: com um processo fictício que tem os mesmos fatos do par (registro de preços, vigência, PCA citado,
 *   validade comum dos perecíveis, valor total), o bloco tem de entrar na minuta, sair derivado do campo do ETP que
 *   o M06 indica, e cada VAR que o M06 diz que ele repete tem de aparecer no campo do ETP e preencher o TR, sem
 *   lacuna: os dois documentos saem das mesmas respostas.
 * - DIVERGENTE, PARCIAL e NAO_LIDO: classificados em derivacao-117-classificacao.ts; o sistema não reproduz a
 *   divergência porque lê a mesma fonte nos dois lados, e o teste confere essa fonte.
 */
import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { derivarEtpParaTr } from "../../src/motor/derivacao/derivacao.ts";
import { gerarMinuta } from "../../src/motor/minuta.ts";
import { camposCitados, gerarEtp } from "../../src/motor/montagem/etp.ts";
import { variavelDoId } from "../../src/motor/pacote/nomes.ts";
import { vazia } from "../../src/motor/wizard/checklist.ts";
import { entradaDoEtpFicticio } from "../motor/etp-ficticio.ts";
import { CLASSIFICACAO_117 } from "./derivacao-117-classificacao.ts";

const entrada = entradaDoEtpFicticio();
// Fatos do par 117/2025 que o M06 registra como consistentes, com valores fictícios: o PCA é citado por remissão
// (opção B do GA-03, TR-2.3) e os perecíveis têm a mesma validade mínima (TR-5.4.1).
entrada.wizard.WZ_16 = "REMISSAO";
for (const item of entrada.itens) item.validade_minima = "75% do prazo total";

const { pacote } = entrada;
const minuta = gerarMinuta(entrada);
const etp = gerarEtp(entrada, minuta);
const derivacao = derivarEtpParaTr(pacote, minuta, etp);
const { M04, M05, M06 } = pacote.matrizes;

const testados = M06.filter((l) => l.teste_par_117 !== "NAO_TESTADO");
const consistentes = testados.filter((l) => l.teste_par_117 === "CONSISTENTE");

/** VAR ligadas a um campo do ETP: M05.usada_em ou linha do M06 ligada só a ele. */
function ligadasAoCampo(campo: string): Set<string> {
  const ligadas = new Set(M05.filter((l) => camposCitados(l.usada_em).includes(campo)).map((l) => l.id));
  for (const l of M06) if (camposCitados(l.campos_etp).length === 1 && camposCitados(l.campos_etp)[0] === campo) for (const v of l.variaveis.match(/VAR-\d{3}/g) ?? []) ligadas.add(v);
  return ligadas;
}

describe("derivação no par 117/2025", () => {
  it("o M06 testou o par em 14 blocos: 5 consistentes e 9 classificados", () => {
    expect(testados).toHaveLength(14);
    expect(consistentes.map((l) => l.bloco_tr)).toEqual(["TR-CAB.04", "TR-1.5", "TR-2.3", "TR-5.4.1", "TR-10.1"]);
    expect(Object.keys(CLASSIFICACAO_117).sort()).toEqual(testados.filter((l) => l.teste_par_117 !== "CONSISTENTE").map((l) => l.bloco_tr).sort());
  });

  it.each(consistentes.map((l) => [l.bloco_tr, l] as const))("%s: derivado do mesmo campo e das mesmas respostas", (bloco, linha) => {
    expect(minuta.blocos).toContain(bloco);
    const campos = camposCitados(linha.campos_etp);
    const derivado = derivacao.blocos.find((b) => b.bloco === bloco);
    expect(derivado).toMatchObject({ campos, situacao: "derivado" });

    const conferidas: string[] = [];
    for (const id of linha.variaveis.match(/VAR-\d{3}/g) ?? []) {
      if (vazia(minuta.processo.globais[variavelDoId(id)])) continue;
      const doCampo = campos.find((c) => ligadasAoCampo(c).has(id));
      if (!doCampo) continue;
      const parte = etp.campos.find((c) => c.id === doCampo)?.partes.find((p) => p.tipo === "dado" && p.regra === id);
      expect(parte, `${bloco}: ${id} no ${doCampo}`).toMatchObject({ tipo: "dado" });
      expect(parte?.tipo === "dado" && parte.texto, `${bloco}: ${id} com valor no ETP`).toBeTruthy();
      expect(minuta.lacunasNoTexto.filter((l) => l.trecho === bloco && l.fonte === id), `${bloco}: ${id} sem lacuna no TR`).toEqual([]);
      conferidas.push(id);
    }
    expect(conferidas.length, `${bloco}: ao menos uma VAR conferida nos dois documentos`).toBeGreaterThan(0);
  });

  it.each(Object.entries(CLASSIFICACAO_117))("%s: classificado, com a mesma fonte lida pelo ETP e pelo TR", (bloco, classe) => {
    const evidencia = testados.find((l) => l.bloco_tr === bloco);
    expect(evidencia?.teste_par_117).toEqual(classe.tipo === "não comparado" ? "NAO_LIDO" : expect.stringMatching(/^(DIVERGENTE|PARCIAL)$/));
    // O bloco e os filhos dele no M06 (o TR-9.34 lê os atestados pelos subitens).
    const doBloco = M06.filter((l) => l.bloco_tr === bloco || l.bloco_tr.startsWith(`${bloco}.`));
    for (const fonte of classe.mesmaFonte) {
      if (fonte.startsWith("VAR-")) {
        const noEtp = M05.some((l) => l.id === fonte && camposCitados(l.usada_em).length > 0) || M06.some((l) => camposCitados(l.campos_etp).length === 1 && l.variaveis.includes(fonte));
        expect(noEtp, `${bloco}: ${fonte} vai para o ETP`).toBe(true);
        expect(doBloco.some((l) => l.variaveis.includes(fonte)), `${bloco}: ${fonte} é lida pelo TR`).toBe(true);
      } else {
        expect(camposCitados(M04.find((l) => l.id === fonte)?.exige_justificativa ?? "").length, `${bloco}: ${fonte} vai para o ETP`).toBeGreaterThan(0);
        expect(doBloco.some((l) => l.perguntas_wz.includes(fonte)), `${bloco}: ${fonte} é lida pelo TR`).toBe(true);
      }
    }
  });

  it("toda divergência citada existe no M09", () => {
    const m09 = readFileSync(path.resolve(import.meta.dirname, "../../matrizes/v1/M09_desvios.csv"), "utf8");
    for (const classe of Object.values(CLASSIFICACAO_117)) if (classe.dv) expect(m09).toContain(`"${classe.dv}"`);
  });
});
