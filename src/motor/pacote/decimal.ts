/**
 * Decimal exato para as contas do avaliador: um inteiro grande e uma escala (valor = inteiro / 10^escala).
 *
 * Os números chegam do pacote e das entradas como número do JavaScript. A conversão usa a forma escrita mais
 * curta do número (String(n)), que é o que estava escrito no CSV ou na entrada, e nunca a representação binária.
 * Nada aqui arredonda: divisão que não dá decimal exato devolve undefined, e quem chamou trata como ausente.
 */

export type Decimal = { readonly inteiro: bigint; readonly escala: number };

const DEZ = BigInt(10);
const ZERO = BigInt(0);

function potenciaDeDez(expoente: number): bigint {
  return DEZ ** BigInt(expoente);
}

/** Tira os zeros à direita da parte decimal, para que cada valor tenha uma forma só. */
function normalizar(d: Decimal): Decimal {
  let { inteiro, escala } = d;
  while (escala > 0 && inteiro % DEZ === ZERO) {
    inteiro /= DEZ;
    escala--;
  }
  return { inteiro, escala };
}

/** Converte um texto como "80000.00", "-1.5" ou "1e-7" em decimal; undefined se não for número. */
export function decimalDeTexto(texto: string): Decimal | undefined {
  const partes = /^([+-]?)(\d+)(?:\.(\d*))?(?:[eE]([+-]?\d+))?$/.exec(texto);
  if (!partes) return undefined;
  const [, sinal, inteira, fracao = "", expoenteTexto = "0"] = partes;
  let inteiro = BigInt(inteira + fracao);
  let escala = fracao.length - Number(expoenteTexto);
  if (escala < 0) {
    inteiro *= potenciaDeDez(-escala);
    escala = 0;
  }
  return normalizar({ inteiro: sinal === "-" ? -inteiro : inteiro, escala });
}

/** Converte um número do JavaScript pela forma escrita mais curta; undefined para NaN e infinito. */
export function decimalDeNumero(n: number): Decimal | undefined {
  return Number.isFinite(n) ? decimalDeTexto(String(n)) : undefined;
}

export function textoDoDecimal(d: Decimal): string {
  const { inteiro, escala } = normalizar(d);
  const negativo = inteiro < ZERO;
  const digitos = (negativo ? -inteiro : inteiro).toString().padStart(escala + 1, "0");
  const corpo = escala === 0 ? digitos : `${digitos.slice(0, -escala)}.${digitos.slice(-escala)}`;
  return negativo ? `-${corpo}` : corpo;
}

/**
 * Volta para número do JavaScript só quando a ida e a volta dão o mesmo decimal.
 * Se o número do JavaScript não guarda o valor exato (dígitos demais), devolve undefined em vez de aproximar.
 */
export function numeroDoDecimal(d: Decimal): number | undefined {
  const n = Number(textoDoDecimal(d));
  const volta = decimalDeNumero(n);
  return volta && comparar(volta, d) === 0 ? n : undefined;
}

/** Os dois na mesma escala. */
function alinhar(a: Decimal, b: Decimal): [bigint, bigint, number] {
  const escala = Math.max(a.escala, b.escala);
  return [a.inteiro * potenciaDeDez(escala - a.escala), b.inteiro * potenciaDeDez(escala - b.escala), escala];
}

export function somar(a: Decimal, b: Decimal): Decimal {
  const [x, y, escala] = alinhar(a, b);
  return normalizar({ inteiro: x + y, escala });
}

export function subtrair(a: Decimal, b: Decimal): Decimal {
  const [x, y, escala] = alinhar(a, b);
  return normalizar({ inteiro: x - y, escala });
}

export function multiplicar(a: Decimal, b: Decimal): Decimal {
  return normalizar({ inteiro: a.inteiro * b.inteiro, escala: a.escala + b.escala });
}

export function negar(a: Decimal): Decimal {
  return { inteiro: -a.inteiro, escala: a.escala };
}

/** -1, 0 ou 1. */
export function comparar(a: Decimal, b: Decimal): number {
  const [x, y] = alinhar(a, b);
  return x < y ? -1 : x > y ? 1 : 0;
}

/**
 * Divisão exata. undefined quando o divisor é zero ou quando o resultado não tem representação decimal finita
 * (por exemplo, 1/3): o avaliador não arredonda.
 */
export function dividir(a: Decimal, b: Decimal): Decimal | undefined {
  if (b.inteiro === ZERO) return undefined;
  // a/b = (a.inteiro * 10^b.escala) / (b.inteiro * 10^a.escala)
  let numerador = a.inteiro * potenciaDeDez(b.escala);
  let denominador = b.inteiro * potenciaDeDez(a.escala);
  if (denominador < ZERO) {
    numerador = -numerador;
    denominador = -denominador;
  }
  const divisor = mdc(numerador < ZERO ? -numerador : numerador, denominador);
  numerador /= divisor;
  denominador /= divisor;
  // Decimal finito só se o denominador tiver apenas os fatores 2 e 5.
  let resto = denominador;
  let doisOuCinco = 0;
  for (const fator of [BigInt(2), BigInt(5)]) {
    let vezes = 0;
    while (resto % fator === ZERO) {
      resto /= fator;
      vezes++;
    }
    doisOuCinco = Math.max(doisOuCinco, vezes);
  }
  if (resto !== BigInt(1)) return undefined;
  const escala = doisOuCinco;
  return normalizar({ inteiro: (numerador * potenciaDeDez(escala)) / denominador, escala });
}

/** Resto da divisão com o sinal do divisor, como no simulador das matrizes (Python). undefined com divisor zero. */
export function resto(a: Decimal, b: Decimal): Decimal | undefined {
  if (b.inteiro === ZERO) return undefined;
  const [x, y, escala] = alinhar(a, b);
  let r = x % y;
  if (r !== ZERO && r < ZERO !== y < ZERO) r += y;
  return normalizar({ inteiro: r, escala });
}

function mdc(a: bigint, b: bigint): bigint {
  while (b !== ZERO) [a, b] = [b, a % b];
  return a;
}
