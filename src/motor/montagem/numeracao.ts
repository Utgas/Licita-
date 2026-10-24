/**
 * Numeração da minuta, refeita depois das exclusões, nível a nível (tarefa do Marco 1, passo 6).
 *
 * - Item numerado: item_modelo começa com número ("1.", "4.3.1.1.", "4.24 (numeração digitada na nota...)").
 *   O nível é a quantidade de partes; o número novo conta os itens que entraram, por nível.
 * - Corpo do TR e Anexo I (secao começando por "Anexo I") são numerados à parte.
 * - Incisos romanos ("I)") e alíneas ("a)") são renumerados em sequência dentro do item a que pertencem.
 * - O resto (subtítulo, tabela, cabeçalho, fecho, Anexo II) fica sem número.
 * - P18 das matrizes: numeração digitada no começo do texto (o "1.6.1" do TR-1.7) é tratada como numeração e não
 *   é impressa; o número que vale é o recalculado.
 */
import type { LinhaM02 } from "../pacote/esquema.ts";

const ITEM_NUMERADO = /^(\d+(?:\.\d+)*)(\.?)/;
const INCISO = /^([IVXLC]+)\)$/;
const ALINEA = /^([a-z])\)$/;
const NUMERACAO_DIGITADA = /^\s*\d+(?:\.\d+)+\.?\s+/;
const PREFIXO_DO_ANEXO_I = "Anexo I ";

const ROMANOS: [number, string][] = [
  [100, "C"],
  [90, "XC"],
  [50, "L"],
  [40, "XL"],
  [10, "X"],
  [9, "IX"],
  [5, "V"],
  [4, "IV"],
  [1, "I"],
];

function romano(n: number): string {
  let resto = n;
  let saida = "";
  for (const [valor, simbolo] of ROMANOS) {
    while (resto >= valor) {
      saida += simbolo;
      resto -= valor;
    }
  }
  return saida;
}

function alinea(n: number): string {
  return String.fromCharCode("a".charCodeAt(0) + n - 1);
}

/** O que a numeração lê de cada linha (bloco do M02 ou cláusula do M08 posta no lugar dela). */
export type LinhaNumeravel = Pick<LinhaM02, "id" | "item_modelo" | "secao">;

/** Corpo do TR ou Anexo I: cada um tem a própria numeração. */
function documentoDoBloco(linha: LinhaNumeravel): string {
  return linha.secao.startsWith(PREFIXO_DO_ANEXO_I) || linha.secao === "Anexo I" ? "ANEXO_I" : "CORPO";
}

/** Número recalculado de cada bloco (ID -> número), na ordem dada; bloco sem número fica de fora. */
export function numerar(linhas: readonly LinhaNumeravel[]): Map<string, string> {
  const numeros = new Map<string, string>();
  const contadores = new Map<string, number[]>();
  let ultimoItem = "";
  let incisos = 0;
  let alineas = 0;
  for (const linha of linhas) {
    const modelo = linha.item_modelo.trim();
    const item = ITEM_NUMERADO.exec(modelo);
    if (item) {
      const documento = documentoDoBloco(linha);
      const nivel = item[1].split(".").length;
      const contador = contadores.get(documento) ?? [];
      // Salto de nível (4.3 seguido de 4.3.1.1): o nível intermediário conta como 1.
      for (let i = 0; i < nivel - 1; i++) contador[i] ||= 1;
      contador[nivel - 1] = (contador[nivel - 1] ?? 0) + 1;
      contador.length = nivel;
      contadores.set(documento, contador);
      ultimoItem = contador.join(".");
      // Ponto final como no modelo; numeração digitada em nota ("4.24 (numeração...)") segue o padrão do
      // modelo: ponto até o segundo nível.
      const digitadaEmNota = modelo.length > item[0].length;
      numeros.set(linha.id, `${ultimoItem}${item[2] === "." || nivel === 1 || (digitadaEmNota && nivel <= 2) ? "." : ""}`);
      incisos = 0;
      alineas = 0;
      continue;
    }
    if (INCISO.test(modelo)) {
      numeros.set(linha.id, `${romano(++incisos)})`);
      continue;
    }
    if (ALINEA.test(modelo)) numeros.set(linha.id, `${alinea(++alineas)})`);
  }
  return numeros;
}

/** P18: tira a numeração digitada no começo do texto (só o TR-1.7 tem, no modelo DEZ/2025). */
export function semNumeracaoDigitada(texto: string): string {
  return texto.replace(NUMERACAO_DIGITADA, "");
}

export function temNumeracaoDigitada(texto: string): boolean {
  return NUMERACAO_DIGITADA.test(texto);
}
