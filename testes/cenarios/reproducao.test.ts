/**
 * Reprodução dos TRs reais feitos sobre o modelo DEZ/2025 (R1 e R2). A minuta do motor é comparada com o que a
 * comparação de texto achou no TR real; cada diferença tem de estar classificada em reproducao-classificacao.ts,
 * e nenhuma pode ser do tipo "motor".
 */
import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { gerarMinuta } from "../../src/motor/minuta.ts";
import { pacoteDasMatrizes } from "../motor/pacote-das-matrizes.ts";
import { CLASSIFICACAO } from "./reproducao-classificacao.ts";

const { pacote, hash } = pacoteDasMatrizes();
const DIR = path.resolve(import.meta.dirname, "../../matrizes/v1/cenarios");

/** Chaves "<categoria>:<lado>:<ID>" das diferenças entre o esperado (TR real) e a minuta. */
function diferencas(id: "R1" | "R2"): string[] {
  const caso = JSON.parse(readFileSync(path.join(DIR, `${id}.json`), "utf8"));
  const minuta = gerarMinuta({ pacote, hashDoPacote: hash, ...structuredClone(caso.entrada) });
  const naoComparados = new Set<string>(caso.blocos_nao_comparados);
  const lados = (categoria: string, doTr: string[], daMinuta: string[]) => [
    ...doTr.filter((x) => !daMinuta.includes(x)).map((x) => `${categoria}:tr:${x}`),
    ...daMinuta.filter((x) => !doTr.includes(x)).map((x) => `${categoria}:minuta:${x}`),
  ];
  const { esperado } = caso;
  return [
    ...lados("bloco", esperado.blocos, minuta.blocos.filter((b) => !naoComparados.has(b))),
    ...lados("m08", esperado.clausulas_m08, minuta.clausulasSetoriais),
    ...lados("m10", esperado.validacoes_m10, minuta.validacoes.disparadas.map((v) => v.id)),
    ...lados("pendente", esperado.perguntas_sem_resposta, minuta.perguntasSemResposta.map((p) => p.id)),
    ...lados("grupo", esperado.bloqueios_grupo_alternativas, minuta.bloqueiosGrupoAlternativas),
  ];
}

describe.each(["R1", "R2"] as const)("reprodução %s", (id) => {
  const caso = JSON.parse(readFileSync(path.join(DIR, `${id}.json`), "utf8"));
  const encontradas = diferencas(id);
  const classificacao = CLASSIFICACAO[id];

  it("toda diferença está classificada, e a classificação não tem sobra", () => {
    expect(encontradas.filter((d) => !(d in classificacao))).toEqual([]);
    expect(Object.keys(classificacao).filter((d) => !encontradas.includes(d))).toEqual([]);
  });

  it("nenhuma diferença é do tipo motor", () => {
    expect(Object.entries(classificacao).filter(([, c]) => c.tipo === "motor")).toEqual([]);
  });

  it("toda diferença do tipo TR real aponta uma divergência conhecida do caso", () => {
    const conhecidas = new Set(caso.divergencias_conhecidas.map((d: { dv: string }) => d.dv));
    for (const [chave, c] of Object.entries(classificacao)) {
      if (c.tipo === "TR real") expect(conhecidas.has(c.dv), `${chave} cita ${c.dv}`).toBe(true);
    }
  });

  it("os blocos da minuta são os mesmos da simulação do agente das matrizes", () => {
    const { no_tr_e_fora_da_simulacao: soTr, na_simulacao_e_ausentes_no_tr: soSimulacao } = caso.referencia.diferencas_simulacao;
    const blocos = encontradas.filter((d) => d.startsWith("bloco:"));
    expect(blocos.filter((d) => d.startsWith("bloco:tr:")).map((d) => d.slice("bloco:tr:".length))).toEqual(soTr);
    expect(blocos.filter((d) => d.startsWith("bloco:minuta:")).map((d) => d.slice("bloco:minuta:".length))).toEqual(soSimulacao);
  });
});
