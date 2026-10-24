/**
 * ETP para colar no ETP Digital e para o PDF (Marco 3, passo 7): um campo por linha, na ordem do M01. As marcas do
 * motor seguem a regra da minuta do TR (secoes.ts): lacuna continua marcada no texto final, para ninguém publicar
 * sem ver. Campo que o próprio ETP Digital imprime, ou sem dado ligado, não entra na cópia.
 */
import { createHash } from "node:crypto";
import type { CampoDoEtp, Etp } from "../motor/montagem/etp.ts";
import type { Minuta } from "../motor/minuta.ts";
import { linhasDaTabela, tabelaNaoMontada, textoFinal } from "./secoes.ts";

/** Campos que vão para a cópia: os que têm texto. */
export function camposParaCopiar(etp: Etp): CampoDoEtp[] {
  return etp.campos.filter((c) => c.texto !== "");
}

/** Parte de um campo: tabela (colunas separadas por " | ") ou parágrafo. */
export type BlocoDoCampo = { tipo: "tabela"; texto: string } | { tipo: "paragrafo"; texto: string };

/** O texto do campo dividido em parágrafos e tabelas, na ordem das partes. */
export function blocosDoCampo(campo: CampoDoEtp): BlocoDoCampo[] {
  const tabelas = new Set(campo.partes.filter((p) => p.tipo === "tabela").map((p) => p.texto));
  return campo.texto
    .split("\n\n")
    .filter((t) => t !== "")
    .map((t) => (tabelas.has(t) ? { tipo: "tabela", texto: t } : { tipo: "paragrafo", texto: t }));
}

/** Texto final do campo para colar: lacuna marcada; tabela com colunas separadas por tabulação. */
export function textoDoCampo(campo: CampoDoEtp): string {
  return blocosDoCampo(campo)
    .map((b) => {
      if (b.tipo === "paragrafo") return textoFinal(b.texto);
      const tabela = linhasDaTabela(b.texto).map((l) => l.map(textoFinal).join("\t")).join("\n");
      return tabelaNaoMontada(b.texto).naoMontada ? `[LACUNA: tabela não montada]\n${tabela}` : tabela;
    })
    .join("\n\n");
}

/**
 * O ETP só sai com as dúvidas da leitura do checklist resolvidas (perguntas ao operador): elas mudam o próprio dado.
 * As travas do TR (validações de bloqueio e grupos de alternativas) não seguram o ETP.
 */
export function etpLiberado(minuta: Minuta): boolean {
  return minuta.revisao.perguntasAoOperador.length === 0;
}

/** Hash do ETP montado (texto de todos os campos, na ordem), para a auditoria. */
export function hashDoEtp(etp: Etp): string {
  const conteudo = etp.campos.map((c) => `${c.id}\u0000${c.situacao}\u0000${c.texto}`).join("\u0001");
  return createHash("sha256").update(conteudo).digest("hex");
}
