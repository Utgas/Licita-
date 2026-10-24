/**
 * Cenários de ouro C1 a C8 (matrizes/v1/cenarios/): a minuta montada pelo motor tem de dar exatamente os blocos,
 * as cláusulas do M08, as validações do M10, as perguntas sem resposta e os bloqueios de alternativas esperados.
 * O esperado vem do simulador do agente das matrizes, uma implementação independente: diferença aponta erro num
 * dos dois e é investigada, nunca ajustada só para passar.
 */
import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { gerarMinuta } from "../../src/motor/minuta.ts";
import { semNumeracaoDigitada } from "../../src/motor/montagem/numeracao.ts";
import { pacoteDasMatrizes } from "../motor/pacote-das-matrizes.ts";

const { pacote, hash } = pacoteDasMatrizes();
const DIR = path.resolve(import.meta.dirname, "../../matrizes/v1/cenarios");
const CENARIOS = ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"];

describe.each(CENARIOS)("cenário de ouro %s", (id) => {
  const { entrada, esperado, referencia } = JSON.parse(readFileSync(path.join(DIR, `${id}.json`), "utf8"));
  const minuta = gerarMinuta({ pacote, hashDoPacote: hash, ...structuredClone(entrada) });

  it("blocos do M02, na ordem do modelo", () => {
    expect(minuta.blocos).toEqual(esperado.blocos);
  });

  it("cláusulas setoriais do M08", () => {
    expect(minuta.clausulasSetoriais).toEqual(esperado.clausulas_m08);
  });

  it("validações do M10", () => {
    expect(minuta.validacoes.disparadas.map((v) => v.id)).toEqual(esperado.validacoes_m10);
  });

  it("perguntas sem resposta", () => {
    expect(minuta.perguntasSemResposta.map((p) => p.id)).toEqual(esperado.perguntas_sem_resposta);
  });

  it("bloqueios de grupo de alternativas", () => {
    expect(minuta.bloqueiosGrupoAlternativas).toEqual(esperado.bloqueios_grupo_alternativas);
  });

  it("trechos que saem sem lacuna (texto_sem_lacuna)", () => {
    const comLacuna = new Set(minuta.lacunasNoTexto.map((l) => l.trecho));
    const semLacuna = minuta.trechos.filter((t) => !comLacuna.has(t.id)).map((t) => t.id);
    // O simulador lista os blocos na ordem do M02 e depois as cláusulas na ordem do M08; o motor põe a cláusula no
    // ponto de inserção.
    const naOrdemDoM08 = pacote.matrizes.M08.map((l) => l.id);
    const ordem = (ids: string[]) => [...ids.filter((x) => x.startsWith("TR-")), ...naOrdemDoM08.filter((x) => ids.includes(x))];
    expect(ordem(semLacuna)).toEqual(esperado.texto_sem_lacuna);
  });

  it("texto montado igual ao do simulador (referencia.texto_montado)", () => {
    // Diferenças deliberadas, que a comparação desfaz: lacuna com o ID da regra (o simulador usa o nome da
    // variável), valor padrão marcado (P37), tabela sem linhas marcada e o "1.6.1" do TR-1.7 fora (P18).
    const normalizar = (t: string) =>
      t.replace(/\[\[PADRÃO: (.*?)\]\]/g, "$1").replace(/^\[\[TABELA NÃO MONTADA\]\]\n/, "").replace(/\[\[LACUNA[^\]]*\]\]/g, "[[LACUNA]]");
    const textos = new Map(minuta.trechos.map((t) => [t.id, normalizar(t.texto)]));
    for (const [trecho, texto] of Object.entries(referencia.texto_montado as Record<string, string>)) {
      expect(textos.get(trecho), trecho).toBe(normalizar(semNumeracaoDigitada(texto)));
    }
  });

  it("todo trecho é rastreável até o ID e o pacote", () => {
    for (const trecho of minuta.trechos) {
      expect(trecho.id).toMatch(/^(TR|SET)-/);
      expect(trecho.origem).toMatchObject({ pacote: pacote.pacote, hash });
    }
    // Bloco de série sem elemento (lista_blocos) sai do texto, mas continua entre os blocos escolhidos.
    expect(minuta.trechos.filter((t) => t.tipo === "bloco").map((t) => t.id)).toEqual(esperado.blocos.filter((b: string) => !minuta.blocosOmitidos.includes(b)));
  });

  it("complementos CK-X-10 a CK-X-19 pedidos exatamente quando a cláusula do M08 entra (Fase 15)", () => {
    for (const linha of pacote.matrizes.M11.filter((l) => l.checklist === "COMPLEMENTO" && l.id >= "CK-X-10")) {
      const clausula = linha.destinos.split("; ").find((d) => d.startsWith("SET-")) as string;
      expect(minuta.complementosDoOperador.includes(linha.id), `${linha.id} (${clausula})`).toBe(minuta.clausulasSetoriais.includes(clausula));
    }
  });

  it("a mesma entrada gera a mesma minuta", () => {
    const outra = gerarMinuta({ pacote, hashDoPacote: hash, ...structuredClone(entrada) });
    expect(JSON.stringify(outra.trechos)).toBe(JSON.stringify(minuta.trechos));
  });
});
