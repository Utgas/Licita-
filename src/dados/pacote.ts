/**
 * Pacote de regras no servidor: lido de regras/<nome>/pacote.json uma vez por instância, conferido pelo esquema do
 * motor e pelo hash gravado ao lado (pacote.sha256). Hash diferente é erro: o processo nunca roda com regra
 * adulterada.
 *
 * O processo guarda o hash do pacote com que nasceu. Depois de uma correção nas matrizes, ele continua com o pacote
 * dele, guardado pelo compilador em regras/<nome>/historico/<hash>.json (arquitetura, princípio 5).
 */
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import path from "node:path";
import { type Pacote, esquemaDoPacote } from "../motor/pacote/esquema.ts";

/** Pacote em uso para processos novos (arquitetura, princípio 5: o processo guarda o seu). */
export const PACOTE_ATUAL = "agu-tr-compras-2025-12";

export type PacoteCarregado = { pacote: Pacote; hash: string };

const carregados = new Map<string, PacoteCarregado>();

/**
 * Pacote atual (sem `hash`) ou o de um processo: com o `hash` gravado no processo, vem o pacote exato com que ele
 * nasceu, do histórico quando as matrizes já mudaram. Hash que não está em lugar nenhum é erro.
 */
export function carregarPacote(nome: string = PACOTE_ATUAL, hash?: string): PacoteCarregado {
  if (!/^[a-z0-9-]+$/.test(nome)) throw new Error(`nome de pacote inválido: ${nome}`);
  const pasta = path.join(process.cwd(), "regras", nome);
  const atual = carregados.get(nome) ?? lerPacote(path.join(pasta, "pacote.json"), readFileSync(path.join(pasta, "pacote.sha256"), "utf8").split(/\s+/)[0]);
  carregados.set(nome, atual);
  if (hash === undefined || hash === atual.hash) return atual;
  if (!/^[0-9a-f]{64}$/.test(hash)) throw new Error(`hash de pacote inválido: ${hash}`);
  const chave = `${nome}@${hash}`;
  const antigo = carregados.get(chave) ?? lerPacote(path.join(pasta, "historico", `${hash}.json`), hash);
  carregados.set(chave, antigo);
  return antigo;
}

function lerPacote(arquivo: string, hashEsperado: string): PacoteCarregado {
  const bruto = readFileSync(arquivo);
  const hash = createHash("sha256").update(bruto).digest("hex");
  if (hash !== hashEsperado) throw new Error(`pacote ${arquivo} não confere com o hash ${hashEsperado}`);
  return { pacote: esquemaDoPacote.parse(JSON.parse(bruto.toString("utf8"))), hash };
}
