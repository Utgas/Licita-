/**
 * Pacote de regras no servidor: lido de regras/<nome>/pacote.json uma vez por instância, conferido pelo esquema do
 * motor e pelo hash gravado ao lado (pacote.sha256). Hash diferente é erro: o processo nunca roda com regra
 * adulterada.
 */
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import path from "node:path";
import { type Pacote, esquemaDoPacote } from "../motor/pacote/esquema.ts";

/** Pacote em uso para processos novos (arquitetura, princípio 5: o processo guarda o seu). */
export const PACOTE_ATUAL = "agu-tr-compras-2025-12";

export type PacoteCarregado = { pacote: Pacote; hash: string };

const carregados = new Map<string, PacoteCarregado>();

export function carregarPacote(nome: string = PACOTE_ATUAL): PacoteCarregado {
  const pronto = carregados.get(nome);
  if (pronto) return pronto;
  if (!/^[a-z0-9-]+$/.test(nome)) throw new Error(`nome de pacote inválido: ${nome}`);
  const pasta = path.join(process.cwd(), "regras", nome);
  const bruto = readFileSync(path.join(pasta, "pacote.json"));
  const hash = createHash("sha256").update(bruto).digest("hex");
  const gravado = readFileSync(path.join(pasta, "pacote.sha256"), "utf8").split(/\s+/)[0];
  if (hash !== gravado) throw new Error(`pacote ${nome} não confere com o hash gravado`);
  const carregado = { pacote: esquemaDoPacote.parse(JSON.parse(bruto.toString("utf8"))), hash };
  carregados.set(nome, carregado);
  return carregado;
}
