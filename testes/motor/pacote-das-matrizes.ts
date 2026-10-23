/** Pacote compilado das matrizes atuais, para os testes do motor. Qualquer erro de compilação falha aqui. */
import { compilar } from "../../scripts/compilar-regras.ts";
import { type Pacote, esquemaDoPacote } from "../../src/motor/pacote/esquema.ts";

let cache: { pacote: Pacote; hash: string } | undefined;

export function pacoteDasMatrizes(): { pacote: Pacote; hash: string } {
  if (cache) return cache;
  const resultado = compilar();
  if (!resultado.pacote) throw new Error(`matrizes não compilam: ${JSON.stringify(resultado.erros.slice(0, 5))}`);
  cache = { pacote: esquemaDoPacote.parse(JSON.parse(resultado.pacote.json)), hash: resultado.pacote.sha256 };
  return cache;
}
