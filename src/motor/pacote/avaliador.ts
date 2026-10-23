/**
 * Avaliador de JSON Logic do motor: só os operadores das matrizes (operadores.ts), sem eval e sem biblioteca.
 *
 * A semântica segue o simulador das matrizes (matrizes/v1/scripts/jlogic.py), que gerou os cenários de ouro,
 * e não a biblioteca json-logic-js. Diferenças deliberadas em relação ao simulador (tarefa do Marco 1):
 * conta e comparação com valor ausente dão ausente (null), em vez de tratar o ausente como 0, e as contas
 * são feitas em decimal exato, sem ponto flutuante.
 */
import {
  type Decimal,
  comparar,
  decimalDeNumero,
  dividir,
  multiplicar,
  negar,
  numeroDoDecimal,
  resto,
  somar,
  subtrair,
} from "./decimal.ts";

/** Valor que entra e sai do avaliador: o mesmo universo do JSON. */
export type Valor = null | boolean | number | string | Valor[] | { [chave: string]: Valor };

/**
 * O que aconteceu de anormal durante a avaliação. Quem chamou decide o que fazer
 * (por exemplo, transformar o resultado em lacuna e gerar alerta).
 */
export type Ocorrencia =
  | { tipo: "valor_ausente"; operador: string }
  | { tipo: "valor_nao_numerico"; operador: string; valor: Valor }
  | { tipo: "divisao_por_zero"; operador: string }
  | { tipo: "divisao_sem_decimal_exato"; operador: string }
  | { tipo: "resultado_sem_precisao"; operador: string };

export type Avaliacao = { valor: Valor; ocorrencias: Ocorrencia[] };

/** Expressão malformada (o compilador não deixa passar; isto protege o motor de pacote adulterado). */
export class ErroDeExpressao extends Error {}

/** Falso: null, false, 0, "" e lista vazia. Todo o resto é verdadeiro, inclusive lista não vazia e objeto. */
export function verdadeiro(v: Valor | undefined): boolean {
  if (v === null || v === undefined || v === false || v === 0 || v === "") return false;
  if (Array.isArray(v)) return v.length > 0;
  return true;
}

/** Igualdade estrita: sem conversão de tipo; números por valor; listas e objetos elemento a elemento. */
export function iguais(a: Valor | undefined, b: Valor | undefined): boolean {
  const x = a ?? null;
  const y = b ?? null;
  if (x === null || y === null) return x === y;
  if (typeof x === "number" && typeof y === "number") {
    const dx = decimalDeNumero(x);
    const dy = decimalDeNumero(y);
    return dx !== undefined && dy !== undefined && comparar(dx, dy) === 0;
  }
  if (Array.isArray(x) || Array.isArray(y)) {
    return Array.isArray(x) && Array.isArray(y) && x.length === y.length && x.every((e, i) => iguais(e, y[i]));
  }
  if (typeof x === "object" && typeof y === "object") {
    const cx = Object.keys(x);
    const cy = Object.keys(y);
    return cx.length === cy.length && cx.every((c) => c in y && iguais(x[c], y[c]));
  }
  return x === y;
}

type Estado = { ocorrencias: Ocorrencia[] };

function ehObjeto(v: Valor | undefined): v is { [chave: string]: Valor } {
  return v !== null && typeof v === "object" && !Array.isArray(v);
}

/** {"var": "a.b"} percorre objetos; {"var": ""} é o próprio dado; {"var": ["x", padrão]} devolve o padrão se x faltar. */
function lerVariavel(argumento: unknown, dados: Valor, estado: Estado): Valor {
  const args = Array.isArray(argumento) ? argumento : [argumento];
  const nome = args[0];
  const padrao = args.length > 1 ? avaliarNo(args[1], dados, estado) : null;
  if (nome === "" || nome === null || nome === undefined) return dados;
  if (typeof nome !== "string") throw new ErroDeExpressao(`var com nome que não é texto: ${JSON.stringify(nome)}`);
  let atual: Valor | undefined = dados;
  for (const parte of nome.split(".")) {
    if (!ehObjeto(atual) || !Object.hasOwn(atual, parte)) return padrao;
    atual = atual[parte];
  }
  return atual ?? null;
}

/** Converte os operandos de uma conta; undefined quando algum falta ou não é número (e registra o motivo). */
function operandos(operador: string, valores: Valor[], estado: Estado): Decimal[] | undefined {
  const decimais: Decimal[] = [];
  for (const v of valores) {
    if (v === null) {
      estado.ocorrencias.push({ tipo: "valor_ausente", operador });
      return undefined;
    }
    const d = typeof v === "number" ? decimalDeNumero(v) : undefined;
    if (d === undefined) {
      estado.ocorrencias.push({ tipo: "valor_nao_numerico", operador, valor: v });
      return undefined;
    }
    decimais.push(d);
  }
  return decimais;
}

function paraNumero(operador: string, d: Decimal | undefined, estado: Estado, motivo: Ocorrencia["tipo"]): Valor {
  if (d === undefined) {
    estado.ocorrencias.push({ tipo: motivo, operador } as Ocorrencia);
    return null;
  }
  const n = numeroDoDecimal(d);
  if (n === undefined) {
    estado.ocorrencias.push({ tipo: "resultado_sem_precisao", operador });
    return null;
  }
  return n;
}

function conta(operador: string, valores: Valor[], estado: Estado): Valor {
  const ds = operandos(operador, valores, estado);
  if (ds === undefined) return null;
  switch (operador) {
    case "+":
      return paraNumero(operador, ds.reduce(somar, decimalDeNumero(0) as Decimal), estado, "valor_ausente");
    case "*":
      return paraNumero(operador, ds.reduce(multiplicar, decimalDeNumero(1) as Decimal), estado, "valor_ausente");
    case "-":
      if (ds.length === 1) return paraNumero(operador, negar(ds[0]), estado, "valor_ausente");
      exigirAridade(operador, ds, 2);
      return paraNumero(operador, subtrair(ds[0], ds[1]), estado, "valor_ausente");
    case "/":
      exigirAridade(operador, ds, 2);
      if (ds[1].inteiro === BigInt(0)) return paraNumero(operador, undefined, estado, "divisao_por_zero");
      return paraNumero(operador, dividir(ds[0], ds[1]), estado, "divisao_sem_decimal_exato");
    case "%":
      exigirAridade(operador, ds, 2);
      return paraNumero(operador, resto(ds[0], ds[1]), estado, "divisao_por_zero");
    default:
      throw new ErroDeExpressao(`operador de conta desconhecido: ${operador}`);
  }
}

/** <= e >: compara números em decimal exato; ausente dá ausente; o que não é número dá falso. */
function comparacao(operador: "<=" | ">", valores: Valor[], estado: Estado): Valor {
  exigirAridade(operador, valores, 2);
  const ds = operandos(operador, valores, estado);
  if (ds === undefined) return valores.some((v) => v === null) ? null : false;
  const c = comparar(ds[0], ds[1]);
  return operador === "<=" ? c <= 0 : c > 0;
}

function exigirAridade(operador: string, args: unknown[], n: number): void {
  if (args.length !== n) throw new ErroDeExpressao(`${operador} precisa de ${n} argumentos, recebeu ${args.length}`);
}

function lista(v: Valor): Valor[] {
  return Array.isArray(v) ? v : [];
}

function avaliarNo(expressao: unknown, dados: Valor, estado: Estado): Valor {
  if (Array.isArray(expressao)) return expressao.map((e) => avaliarNo(e, dados, estado));
  if (expressao === null || typeof expressao !== "object") {
    if (expressao === null || expressao === undefined) return null;
    if (typeof expressao === "number" || typeof expressao === "string" || typeof expressao === "boolean") return expressao;
    throw new ErroDeExpressao(`valor literal inválido: ${String(expressao)}`);
  }
  const chaves = Object.keys(expressao);
  if (chaves.length !== 1) throw new ErroDeExpressao(`objeto com ${chaves.length} chaves; cada operação tem exatamente uma`);
  const operador = chaves[0];
  const argumento = (expressao as Record<string, unknown>)[operador];
  const args = Array.isArray(argumento) ? argumento : [argumento];
  const avaliar = (e: unknown, d: Valor = dados) => avaliarNo(e, d, estado);

  switch (operador) {
    case "var":
      return lerVariavel(argumento, dados, estado);
    case "if": {
      for (let i = 0; i + 1 < args.length; i += 2) {
        if (verdadeiro(avaliar(args[i]))) return avaliar(args[i + 1]);
      }
      return args.length % 2 === 1 ? avaliar(args[args.length - 1]) : null;
    }
    case "and": {
      let resultado: Valor = true;
      for (const a of args) {
        resultado = avaliar(a);
        if (!verdadeiro(resultado)) return resultado;
      }
      return resultado;
    }
    case "or": {
      for (const a of args) {
        const resultado = avaliar(a);
        if (verdadeiro(resultado)) return resultado;
      }
      return false;
    }
    case "!":
      return !verdadeiro(avaliar(args[0]));
    case "!!":
      return verdadeiro(avaliar(args[0]));
    case "some":
    case "none": {
      exigirAridade(operador, args, 2);
      const algum = lista(avaliar(args[0])).some((elemento) => verdadeiro(avaliar(args[1], elemento)));
      return operador === "some" ? algum : !algum;
    }
    case "reduce": {
      exigirAridade(operador, args, 3);
      let acumulado = avaliar(args[2]);
      for (const elemento of lista(avaliar(args[0]))) {
        acumulado = avaliar(args[1], { current: elemento, accumulator: acumulado });
      }
      return acumulado;
    }
  }

  const valores = args.map((a) => avaliar(a));
  switch (operador) {
    case "==":
      exigirAridade(operador, valores, 2);
      return iguais(valores[0], valores[1]);
    case "!=":
      exigirAridade(operador, valores, 2);
      return !iguais(valores[0], valores[1]);
    case "in": {
      exigirAridade(operador, valores, 2);
      const [procurado, onde] = valores;
      if (procurado === null || onde === null) return false;
      if (typeof onde === "string") return typeof procurado === "string" && onde.includes(procurado);
      if (Array.isArray(onde)) return onde.some((e) => iguais(e, procurado));
      return false;
    }
    case "merge":
      return valores.flatMap((v) => (Array.isArray(v) ? v : [v]));
    case "<=":
    case ">":
      return comparacao(operador, valores, estado);
    case "+":
    case "-":
    case "*":
    case "/":
    case "%":
      return conta(operador, valores, estado);
    default:
      throw new ErroDeExpressao(`operador fora da lista: ${operador}`);
  }
}

/** Avalia a expressão sobre os dados e devolve o valor e as ocorrências (ausentes, divisão por zero...). */
export function avaliarComOcorrencias(expressao: unknown, dados: Valor): Avaliacao {
  const estado: Estado = { ocorrencias: [] };
  const valor = avaliarNo(expressao, dados, estado);
  return { valor, ocorrencias: estado.ocorrencias };
}

/** Avalia a expressão sobre os dados e devolve só o valor. */
export function avaliar(expressao: unknown, dados: Valor): Valor {
  return avaliarComOcorrencias(expressao, dados).valor;
}
