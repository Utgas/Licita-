/**
 * Reprodução do par ETP e TR 117/2025 a partir das mesmas respostas (caso R3; critério de saída do Marco 3).
 * O caso é feito pelo agente das matrizes, porque as respostas vêm dos documentos reais, que ficam fora do
 * repositório. Formato: o do R1 e do R2, com `esperado.campos_etp` (campos do ETP com conteúdo no ETP real) além
 * de `esperado.blocos`. Enquanto o arquivo não existe, o teste aparece como pulado.
 */
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { gerarMinuta } from "../../src/motor/minuta.ts";
import { gerarEtp } from "../../src/motor/montagem/etp.ts";
import { pacoteDasMatrizes } from "../motor/pacote-das-matrizes.ts";
import { CLASSIFICACAO_R3 } from "./reproducao-etp-classificacao.ts";

const ARQUIVO = path.resolve(import.meta.dirname, "../../matrizes/v1/cenarios/R3.json");
const chegou = existsSync(ARQUIVO);

describe("reprodução do par 117/2025 (R3)", () => {
  it.skipIf(!chegou)("toda diferença no ETP e no TR está classificada, e nenhuma é do tipo motor", () => {
    const { pacote, hash } = pacoteDasMatrizes();
    const caso = JSON.parse(readFileSync(ARQUIVO, "utf8"));
    const entrada = { pacote, hashDoPacote: hash, ...structuredClone(caso.entrada) };
    const minuta = gerarMinuta(entrada);
    const etp = gerarEtp(entrada, minuta);
    const comConteudo = etp.campos.filter((c) => c.situacao === "preenchido" || c.situacao === "incompleto").map((c) => c.id);
    const naoComparados = new Set<string>(caso.blocos_nao_comparados ?? []);
    const lados = (categoria: string, real: string[], sistema: string[]) => [
      ...real.filter((x) => !sistema.includes(x)).map((x) => `${categoria}:real:${x}`),
      ...sistema.filter((x) => !real.includes(x)).map((x) => `${categoria}:sistema:${x}`),
    ];
    const diferencas = [
      ...lados("etp", caso.esperado.campos_etp, comConteudo),
      ...lados("bloco", caso.esperado.blocos, minuta.blocos.filter((b) => !naoComparados.has(b))),
    ];
    expect(diferencas.filter((d) => !(d in CLASSIFICACAO_R3))).toEqual([]);
    expect(Object.values(CLASSIFICACAO_R3).filter((c) => c.tipo === "motor")).toEqual([]);
  });
});
