/**
 * A minuta do motor organizada pelas seções do modelo de TR da AGU (decisão 0010): mesma ordem e mesmos títulos do
 * M02 (coluna secao). A cláusula setorial do M08 fica na seção do bloco depois do qual o motor a pôs.
 *
 * Marcas do motor no texto: [[LACUNA ...]] (dado que falta), [[PADRÃO: texto]] (valor padrão do pacote, não
 * informado) e [[TABELA NÃO MONTADA]]. A tela mostra as três; o texto para colar e o PDF mantêm a lacuna marcada e
 * levam o valor padrão sem a marca.
 */
import { createHash } from "node:crypto";
import type { Minuta, TrechoDaMinuta } from "../motor/minuta.ts";

export type Secao = { titulo: string; trechos: TrechoDaMinuta[] };

export function secoesDaMinuta(m: Minuta): Secao[] {
  const secoes: Secao[] = [];
  let atual: Secao | undefined;
  for (const t of m.trechos) {
    const titulo = t.tipo === "bloco" ? t.secao : (atual?.titulo ?? "");
    if (!atual || atual.titulo !== titulo) secoes.push((atual = { titulo, trechos: [] }));
    atual.trechos.push(t);
  }
  return secoes;
}

export type ParteDoTexto = { tipo: "texto" | "lacuna" | "padrao"; texto: string };

const MARCA = /\[\[(LACUNA[^\]]*|PADRÃO: [^\]]*|TABELA NÃO MONTADA)\]\]/g;

/** Texto partido nas marcas, para a tela pintar lacuna (amarelo) e valor padrão (azul). */
export function partesDoTexto(texto: string): ParteDoTexto[] {
  const partes: ParteDoTexto[] = [];
  let ultimo = 0;
  for (const achado of texto.matchAll(MARCA)) {
    const i = achado.index ?? 0;
    if (i > ultimo) partes.push({ tipo: "texto", texto: texto.slice(ultimo, i) });
    const dentro = achado[1];
    if (dentro.startsWith("PADRÃO: ")) partes.push({ tipo: "padrao", texto: dentro.slice("PADRÃO: ".length) });
    else partes.push({ tipo: "lacuna", texto: dentro === "TABELA NÃO MONTADA" ? "tabela não montada" : dentro.replace(/^LACUNA\s*/, "") || "falta dado" });
    ultimo = i + achado[0].length;
  }
  if (ultimo < texto.length) partes.push({ tipo: "texto", texto: texto.slice(ultimo) });
  return partes;
}

/** Texto final de um trecho: valor padrão sem a marca; lacuna continua marcada, para ninguém publicar sem ver. */
export function textoFinal(texto: string): string {
  return partesDoTexto(texto)
    .map((p) => (p.tipo === "texto" || p.tipo === "padrao" ? p.texto : `[LACUNA${p.texto === "falta dado" ? "" : `: ${p.texto}`}]`))
    .join("");
}

/** Tabela do motor: primeira linha é o cabeçalho, colunas separadas por " | ". */
export function ehTabela(t: TrechoDaMinuta): boolean {
  return t.tipo === "bloco" && /\.TAB\d+$/.test(t.id);
}

const TABELA_NAO_MONTADA = "[[TABELA NÃO MONTADA]]";

/** Tabela que o motor não montou vem com a marca na primeira linha e o texto do modelo embaixo. */
export function tabelaNaoMontada(texto: string): { naoMontada: boolean; texto: string } {
  return texto.startsWith(`${TABELA_NAO_MONTADA}\n`) ? { naoMontada: true, texto: texto.slice(TABELA_NAO_MONTADA.length + 1) } : { naoMontada: false, texto };
}

export function linhasDaTabela(texto: string): string[][] {
  return tabelaNaoMontada(texto)
    .texto.split("\n")
    .map((l) => l.split(" | "));
}

/** Um trecho como linha de texto corrido: número e texto; tabela com colunas separadas por tabulação. */
export function textoDoTrecho(t: TrechoDaMinuta): string {
  if (ehTabela(t)) {
    const tabela = linhasDaTabela(t.texto).map((l) => l.map(textoFinal).join("\t")).join("\n");
    return tabelaNaoMontada(t.texto).naoMontada ? `[LACUNA: tabela não montada]\n${tabela}` : tabela;
  }
  const texto = textoFinal(t.texto);
  return t.numero ? `${t.numero} ${texto}` : texto;
}

/** Texto de uma seção para colar no Compras.gov.br. */
export function textoDaSecao(s: Secao): string {
  return s.trechos.map(textoDoTrecho).join("\n\n");
}

/** Hash da minuta montada (texto de todos os trechos, na ordem), para a auditoria. */
export function hashDaMinuta(m: Minuta): string {
  const conteudo = m.trechos.map((t) => `${t.id}\u0000${t.numero ?? ""}\u0000${t.texto}`).join("\u0001");
  return createHash("sha256").update(conteudo).digest("hex");
}
