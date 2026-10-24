/**
 * ETP dos cenários de ouro (C1 a C8) e da reprodução (R1 e R2), Marco 3. Os cenários não trazem esperado de ETP:
 * aqui se conferem as garantias que valem para qualquer processo. O TR dos mesmos cenários continua conferido em
 * cenarios.test.ts e reproducao.test.ts, sem mudança.
 */
import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { derivarEtpParaTr } from "../../src/motor/derivacao/derivacao.ts";
import { gerarMinuta } from "../../src/motor/minuta.ts";
import { gerarEtp } from "../../src/motor/montagem/etp.ts";
import { variavelDoId } from "../../src/motor/pacote/nomes.ts";
import { vazia } from "../../src/motor/wizard/checklist.ts";
import { pacoteDasMatrizes } from "../motor/pacote-das-matrizes.ts";

const { pacote, hash } = pacoteDasMatrizes();
const DIR = path.resolve(import.meta.dirname, "../../matrizes/v1/cenarios");
const CASOS = ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "R1", "R2"];
const m06 = new Map(pacote.matrizes.M06.map((l) => [l.bloco_tr, l]));
const m05 = new Map(pacote.matrizes.M05.map((l) => [l.id, l]));

describe.each(CASOS)("ETP do caso %s", (id) => {
  const { entrada } = JSON.parse(readFileSync(path.join(DIR, `${id}.json`), "utf8"));
  const e = { pacote, hashDoPacote: hash, ...structuredClone(entrada) };
  const minuta = gerarMinuta(e);
  const etp = gerarEtp(e, minuta);
  const derivacao = derivarEtpParaTr(pacote, minuta, etp);

  it("os 24 campos do M01, na ordem", () => {
    expect(etp.campos.map((c) => c.id)).toEqual(pacote.matrizes.M01.map((l) => l.id));
  });

  it("nada inventado: todo dado que aparece veio do processo", () => {
    for (const campo of etp.campos) {
      for (const parte of campo.partes) {
        if (parte.tipo !== "dado" || parte.texto === null) continue;
        const nome = m05.get(parte.regra)?.nome ?? "";
        if (nome.startsWith("tabela_itens.")) {
          const atributo = nome.slice("tabela_itens.".length);
          expect(minuta.processo.itens.some((item) => !vazia(item[atributo] as never)), `${campo.id} ${parte.regra}`).toBe(true);
        } else {
          expect(vazia(minuta.processo.globais[variavelDoId(parte.regra)]), `${campo.id} ${parte.regra}`).toBe(false);
        }
      }
    }
  });

  it("toda lacuna fora da tabela traz o ID da regra; nenhum Sim ou Não solto", () => {
    for (const campo of etp.campos) {
      for (const parte of campo.partes) {
        if (parte.tipo === "tabela") continue;
        const marcas = [...(parte.texto ?? "").matchAll(/\[\[LACUNA ?([^\]]*)\]\]/g)].map((m) => m[1]);
        for (const marca of marcas) expect(marca, campo.id).toMatch(/^VAR-\d{3}$/);
      }
      const soltas = campo.texto.split("\n").filter((l) => /^(Sim|Não)\.?$/.test(l.trim()));
      expect(soltas, campo.id).toEqual([]);
    }
  });

  it("derivação: só blocos da minuta, com os campos que o M06 indica", () => {
    const naMinuta = new Map(minuta.trechos.map((t) => [t.id, t.numero]));
    for (const b of derivacao.blocos) {
      expect(naMinuta.get(b.bloco), b.bloco).toBe(b.numero);
      for (const c of b.campos) expect(m06.get(b.bloco)?.campos_etp, b.bloco).toContain(c);
    }
  });
});
