import path from "node:path";
import { ESLint } from "eslint";
import { describe, expect, it } from "vitest";

const raiz = path.resolve(import.meta.dirname, "../..");
const eslint = new ESLint({ cwd: raiz });

const REGRAS_DE_ISOLAMENTO = new Set([
  "no-restricted-imports",
  "no-restricted-syntax",
  "no-restricted-globals",
  "no-restricted-properties",
]);

/** Roda o lint num arquivo que não existe em disco e devolve só as violações de isolamento. */
async function violacoes(arquivo: string, codigo: string): Promise<string[]> {
  const [resultado] = await eslint.lintText(codigo, { filePath: path.join(raiz, arquivo) });
  return resultado.messages
    .filter((m) => m.ruleId !== null && REGRAS_DE_ISOLAMENTO.has(m.ruleId))
    .map((m) => m.ruleId as string);
}

// A primeira chamada ao ESLint carrega a configuração inteira e passa dos 5 s quando roda junto com os outros testes.
describe("isolamento de src/motor", { timeout: 30_000 }, () => {
  const arquivoDoMotor = "src/motor/wizard/proibido.ts";

  it.each([
    ['import { x } from "../../app/page";'],
    ['import { x } from "../../dados/consultas";'],
    ['import { x } from "../../auth/sessao";'],
    ['import { x } from "../../ia/redacao";'],
    ['import { x } from "../../auditoria/eventos";'],
    ['import { x } from "../../exportacao/pdf";'],
    ['import { x } from "@/dados/consultas";'],
    ['import { x } from "src/app/page";'],
    ['import Link from "next/link";'],
    ['import { useState } from "react";'],
    ['import { createClient } from "@supabase/supabase-js";'],
    ['import { readFileSync } from "fs";'],
    ['import { readFile } from "node:fs/promises";'],
    ['import net from "net";'],
    ['import http from "node:http";'],
    ['import https from "https";'],
  ])("quebra o lint com %s", async (importacao) => {
    const codigo = `${importacao}\nexport const usar = [${importacao.match(/import \{? ?(\w+)/)?.[1]}];\n`;
    expect(await violacoes(arquivoDoMotor, codigo)).toContain("no-restricted-imports");
  });

  it.each([
    ["fetch", 'export const r = fetch("https://exemplo.invalid");'],
    ["data atual", "export const d = new Date();"],
    ["aleatoriedade", "export const n = Math.random();"],
    ["importação dinâmica", 'export const m = await import("node:fs");'],
  ])("quebra o lint com %s", async (_nome, codigo) => {
    expect(await violacoes(arquivoDoMotor, codigo)).not.toHaveLength(0);
  });

  it("aceita importações de dentro do motor e de bibliotecas puras", async () => {
    const codigo = [
      'import { z } from "zod";',
      'import { pacote } from "../pacote/leitura";',
      'import { itens } from "@/motor/itens/regras";',
      "export const usar = [z, pacote, itens];",
    ].join("\n");
    expect(await violacoes(arquivoDoMotor, codigo)).toEqual([]);
  });

  it("não restringe arquivos fora de src/motor", async () => {
    const codigo = 'import { readFileSync } from "node:fs";\nexport const ler = readFileSync;\n';
    expect(await violacoes("scripts/qualquer.ts", codigo)).toEqual([]);
  });
});
