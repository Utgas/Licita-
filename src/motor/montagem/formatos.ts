/**
 * Formatos de valor no texto da minuta (coluna formato do lacunas_mapa; README das matrizes, "Texto da minuta").
 * Números em decimal exato; nada é arredondado: valor que o formato não comporta (moeda com mais de dois decimais,
 * extenso de número não inteiro) devolve undefined e vira lacuna.
 */
import type { Valor } from "../pacote/avaliador.ts";
import { type Decimal, decimalDeNumero, decimalDeTexto, textoDoDecimal } from "../pacote/decimal.ts";

const UNIDADES = ["", "um", "dois", "três", "quatro", "cinco", "seis", "sete", "oito", "nove", "dez", "onze", "doze", "treze", "quatorze", "quinze", "dezesseis", "dezessete", "dezoito", "dezenove"];
const DEZENAS = ["", "", "vinte", "trinta", "quarenta", "cinquenta", "sessenta", "setenta", "oitenta", "noventa"];
const CENTENAS = ["", "cento", "duzentos", "trezentos", "quatrocentos", "quinhentos", "seiscentos", "setecentos", "oitocentos", "novecentos"];
const MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"];
/** Unidade escrita depois do número (chave unidade do mapa): singular e plural. */
const NOMES_DE_UNIDADE: Record<string, [string, string]> = { DIAS: ["dia", "dias"], MESES: ["mês", "meses"], ANOS: ["ano", "anos"] };
const LIMITE_DO_EXTENSO = 999_999_999;

export class FormatoInvalido extends Error {}

function ateMil(n: number): string {
  if (n === 0) return "";
  if (n === 100) return "cem";
  const centena = Math.floor(n / 100);
  const resto = n % 100;
  const partes = centena ? [CENTENAS[centena]] : [];
  if (resto) {
    if (resto < 20) partes.push(UNIDADES[resto]);
    else partes.push(DEZENAS[Math.floor(resto / 10)] + (resto % 10 ? ` e ${UNIDADES[resto % 10]}` : ""));
  }
  return partes.join(" e ");
}

/** Inteiro não negativo por extenso, até 999.999.999 ("mil e quinhentos", "mil duzentos e cinquenta"). */
export function extenso(n: number): string {
  if (!Number.isInteger(n) || n < 0 || n > LIMITE_DO_EXTENSO) throw new FormatoInvalido(`extenso de ${n}`);
  if (n === 0) return "zero";
  const milhoes = Math.floor(n / 1_000_000);
  const milhares = Math.floor((n % 1_000_000) / 1000);
  const unidades = n % 1000;
  const grupos: [string, number][] = [];
  if (milhoes) grupos.push([milhoes === 1 ? "um milhão" : `${ateMil(milhoes)} milhões`, milhoes]);
  if (milhares) grupos.push([milhares === 1 ? "mil" : `${ateMil(milhares)} mil`, milhares]);
  if (unidades) grupos.push([ateMil(unidades), unidades]);
  if (grupos.length === 1) return grupos[0][0];
  const [textoDoUltimo, ultimo] = grupos[grupos.length - 1];
  const separador = ultimo < 100 || ultimo % 100 === 0 ? " e " : " ";
  return grupos.slice(0, -1).map(([t]) => t).join(" ") + separador + textoDoUltimo;
}

/** Número da entrada (número, ou texto como "30" e "1.234,56") em decimal exato. */
export function decimalDoValor(v: Valor): Decimal {
  let d: Decimal | undefined;
  if (typeof v === "number") d = decimalDeNumero(v);
  else if (typeof v === "string") d = decimalDeTexto(v.includes(",") ? v.replaceAll(".", "").replace(",", ".") : v.trim());
  if (d === undefined) throw new FormatoInvalido(`não é número: ${JSON.stringify(v)}`);
  return d;
}

function partes(d: Decimal): { negativo: boolean; inteira: string; fracao: string } {
  const texto = textoDoDecimal(d);
  const negativo = texto.startsWith("-");
  const [inteira, fracao = ""] = (negativo ? texto.slice(1) : texto).split(".");
  return { negativo, inteira, fracao };
}

function milhares(inteira: string): string {
  return inteira.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
}

/** "15.000", "1.234,5". */
export function textoDoNumero(v: Valor): string {
  const { negativo, inteira, fracao } = partes(decimalDoValor(v));
  return `${negativo ? "-" : ""}${milhares(inteira)}${fracao ? `,${fracao}` : ""}`;
}

/** Inteira e centavos, sem arredondar. */
function centavos(v: Valor): { inteira: string; cents: string } {
  const { negativo, inteira, fracao } = partes(decimalDoValor(v));
  if (negativo || fracao.length > 2) throw new FormatoInvalido(`moeda sem dois decimais exatos: ${JSON.stringify(v)}`);
  return { inteira, cents: fracao.padEnd(2, "0") };
}

export function moeda(v: Valor): string {
  const { inteira, cents } = centavos(v);
  return `R$ ${milhares(inteira)},${cents}`;
}

export function moedaPorExtenso(v: Valor): string {
  const { inteira, cents } = centavos(v);
  const reais = Number(inteira);
  const c = Number(cents);
  const textos: string[] = [];
  if (reais) textos.push(`${extenso(reais)}${reais % 1_000_000 === 0 ? " de" : ""}${reais === 1 ? " real" : " reais"}`);
  if (c) textos.push(`${extenso(c)}${c === 1 ? " centavo" : " centavos"}`);
  return `(${textos.length ? textos.join(" e ") : "zero real"})`;
}

function percentualPorExtenso(v: Valor): string {
  const { negativo, inteira, fracao } = partes(decimalDoValor(v));
  if (negativo) throw new FormatoInvalido("percentual negativo");
  const porExtenso = fracao ? `${extenso(Number(inteira))} vírgula ${[...fracao].map((x) => extenso(Number(x))).join(" ")}` : extenso(Number(inteira));
  return `${textoDoNumero(v)}% (${porExtenso} por cento)`;
}

function percentualComDuasCasas(v: Valor): string {
  const { negativo, inteira, fracao } = partes(decimalDoValor(v));
  if (fracao.length > 2) throw new FormatoInvalido("percentual com mais de dois decimais");
  return `${negativo ? "-" : ""}${inteira},${fracao.padEnd(2, "0")}%`;
}

function partesDaData(v: Valor): [string, string, string] {
  const texto = String(v);
  const br = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(texto);
  if (br) return [br[1], br[2], br[3]];
  const iso = /^(\d{4})-(\d{2})-(\d{2})$/.exec(texto);
  if (iso) return [iso[3], iso[2], iso[1]];
  throw new FormatoInvalido(`data fora do formato: ${texto}`);
}

/** Valor como texto, sem formato: número com milhar e vírgula, lista separada por "; ". */
export function textoDoValor(v: Valor): string {
  if (Array.isArray(v)) return v.map(textoDoValor).join("; ");
  if (typeof v === "number") return textoDoNumero(v);
  if (v !== null && typeof v === "object") return JSON.stringify(v);
  return String(v);
}

/** "a, b e c". */
export function listaEmTexto(valores: Valor[]): string {
  const textos = valores.map(textoDoValor);
  return textos.length === 1 ? textos[0] : `${textos.slice(0, -1).join(", ")} e ${textos[textos.length - 1]}`;
}

/** Aplica o formato; lança FormatoInvalido quando o valor não cabe nele. */
export function formatar(v: Valor, formato: string | undefined, unidade?: Valor): string {
  let s: string;
  switch (formato ?? "TEXTO") {
    case "TEXTO":
      s = textoDoValor(v);
      break;
    case "NUMERO":
      s = textoDoNumero(v);
      break;
    case "NUMERO_EXTENSO": {
      const { fracao } = partes(decimalDoValor(v));
      if (fracao) throw new FormatoInvalido("extenso de número não inteiro");
      s = `${textoDoNumero(v)} (${extenso(Number(textoDoDecimal(decimalDoValor(v))))})`;
      break;
    }
    case "PERCENTUAL_EXTENSO":
      s = percentualPorExtenso(v);
      break;
    case "PERCENTUAL_2":
      s = percentualComDuasCasas(v);
      break;
    case "MOEDA":
      s = moeda(v);
      break;
    case "MOEDA_POR_EXTENSO":
      s = moedaPorExtenso(v);
      break;
    case "DATA":
      s = partesDaData(v).join("/");
      break;
    case "DIA":
      s = String(Number(partesDaData(v)[0]));
      break;
    case "MES_EXTENSO":
      s = MESES[Number(partesDaData(v)[1]) - 1] ?? "";
      if (!s) throw new FormatoInvalido("mês inválido");
      break;
    case "ANO":
      // Data (o ano dela) ou o próprio ano, como número ou texto de quatro dígitos (VAR-038, ano do PCA).
      s = /^\d{4}$/.test(String(v)) ? String(v) : partesDaData(v)[2];
      break;
    case "LISTA_TEXTO":
      s = listaEmTexto(Array.isArray(v) ? v : [v]);
      break;
    case "LISTA_LINHAS":
      s = (Array.isArray(v) ? v : [v]).map(textoDoValor).join("\n");
      break;
    case "MINUSCULA":
      s = textoDoValor(v).toLowerCase();
      break;
    case "INICIAL_MINUSCULA":
      s = textoDoValor(v);
      s = s.slice(0, 1).toLowerCase() + s.slice(1);
      break;
    case "ITEM":
      s = `item ${textoDoValor(v)}`;
      break;
    default:
      throw new FormatoInvalido(`formato desconhecido: ${formato}`);
  }
  if (unidade !== undefined) {
    const nomes = NOMES_DE_UNIDADE[String(unidade)];
    if (!nomes) throw new FormatoInvalido(`unidade desconhecida: ${String(unidade)}`);
    const ehUm = textoDoDecimal(decimalDoValor(v)) === "1";
    s += ` ${ehUm ? nomes[0] : nomes[1]}`;
  }
  return s;
}
