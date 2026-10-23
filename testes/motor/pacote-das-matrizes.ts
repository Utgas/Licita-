/**
 * Pacote compilado das matrizes atuais, para os testes do motor.
 *
 * Enquanto o agente das matrizes não corrige a citação a VAR-160 na fonte do PAR-03 (M12), o compilador recusa
 * as matrizes. Só para os testes, essa citação é trocada em memória; qualquer outro erro de compilação falha aqui.
 * Quando a matriz for corrigida, o primeiro compilar() passa e a troca deixa de ser usada.
 */
import { readFileSync } from "node:fs";
import path from "node:path";
import { DIR_MATRIZES, MATRIZES, compilar, compilarConteudos } from "../../scripts/compilar-regras.ts";
import { type Pacote, esquemaDoPacote } from "../../src/motor/pacote/esquema.ts";

const CITACAO_CONHECIDA = "VAR-160";

let cache: { pacote: Pacote; hash: string } | undefined;

export function pacoteDasMatrizes(): { pacote: Pacote; hash: string } {
  if (cache) return cache;
  let resultado = compilar();
  if (!resultado.pacote) {
    const soCitacaoConhecida = resultado.erros.every(
      (e) => e.tipo === "referencia" && e.matriz === "M12" && e.mensagem.includes(CITACAO_CONHECIDA),
    );
    if (!soCitacaoConhecida) throw new Error(`matrizes não compilam: ${JSON.stringify(resultado.erros.slice(0, 5))}`);
    const conteudos = Object.fromEntries(
      Object.values(MATRIZES).map((d) => [d.arquivo, readFileSync(path.join(DIR_MATRIZES, d.arquivo), "utf8")]),
    );
    conteudos["M12_parametros.csv"] = conteudos["M12_parametros.csv"].replaceAll(CITACAO_CONHECIDA, "VAR-118");
    resultado = compilarConteudos(conteudos);
    if (!resultado.pacote) throw new Error(`matrizes não compilam: ${JSON.stringify(resultado.erros.slice(0, 5))}`);
  }
  cache = { pacote: esquemaDoPacote.parse(JSON.parse(resultado.pacote.json)), hash: resultado.pacote.sha256 };
  return cache;
}
