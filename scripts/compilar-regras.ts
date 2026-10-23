/**
 * Compilador de regras: lê as matrizes (CSV), confere tudo e gera o pacote em JSON com hash.
 *
 * Uso: npm run compilar            (desenvolvimento: validação vazia gera aviso)
 *      npm run compilar:piloto     (falha se faltar validacao = OK no M03 CONDICAO ou no M04)
 *
 * Nada de texto jurídico aqui: o compilador só confere formato, IDs, referências e JSON Logic.
 */
import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parse } from "csv-parse/sync";
import { z } from "zod";
import {
  STATUS,
  TIPO_DE_PARAMETRO,
  VALIDACAO,
  VERSAO_DO_FORMATO,
  esquemaDoPacote,
  linhaM01,
  linhaM02,
  linhaM03,
  linhaM04,
  linhaM05,
  linhaM06,
  linhaM07,
  linhaM08,
  linhaM10,
  linhaM11,
  linhaM12,
  type ValorDeParametro,
} from "../src/motor/pacote/esquema.ts";
import { variavelDoId } from "../src/motor/pacote/nomes.ts";
import { COLUNAS_DE_CALCULO, OPERADORES_DE_CALCULO, OPERADORES_PERMITIDOS } from "../src/motor/pacote/operadores.ts";

export const NOME_DO_PACOTE = "agu-tr-compras-2025-12";

const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
export const DIR_MATRIZES = path.join(RAIZ, "matrizes", "v1");
export const DIR_PACOTE = path.join(RAIZ, "regras", NOME_DO_PACOTE);

type Definicao = {
  arquivo: string;
  /** Coluna que identifica a linha. */
  chave: string;
  /** Formato do identificador, quando ele é um ID citado por outras matrizes. */
  formatoDaChave?: RegExp;
  colunas: readonly string[];
  /** Colunas de domínio fechado. */
  dominios?: Record<string, readonly string[]>;
  /** M00 e M09 descrevem os documentos reais da base: são conferidos, mas não entram no pacote. */
  noPacote: boolean;
};

/**
 * Definição de uma matriz que entra no pacote, tirada do esquema em src/motor/pacote/esquema.ts:
 * as colunas são as chaves do esquema, na ordem do CSV, e os domínios são as colunas com enum.
 */
function doEsquema(arquivo: string, chave: string, formatoDaChave: RegExp | undefined, esquema: z.ZodObject): Definicao {
  const dominios: Record<string, readonly string[]> = {};
  for (const [coluna, tipo] of Object.entries(esquema.shape)) {
    if (coluna !== "status" && tipo instanceof z.ZodEnum) dominios[coluna] = tipo.options as string[];
  }
  return { arquivo, chave, formatoDaChave, colunas: Object.keys(esquema.shape), dominios, noPacote: true };
}

// Colunas exatamente como estão no cabeçalho de cada CSV. Não renomeie.
export const MATRIZES = {
  M00: {
    arquivo: "M00_inventario.csv",
    chave: "arquivo",
    colunas: ["arquivo", "pasta", "tipo_real", "numero_ano", "uasg", "om", "processo", "objeto_resumo", "categoria", "srp", "papel_srp", "formato", "paginas_lidas_total", "par", "problemas", "fonte", "status"],
    noPacote: false,
  },
  M01: doEsquema("M01_etp_campos.csv", "id", /^ETP-\d{2}\.\d{2}$/, linhaM01),
  M02: doEsquema("M02_tr_blocos.csv", "id", /^TR-[A-Za-z0-9]+(?:[.-][A-Za-z0-9]+)*$/, linhaM02),
  M03: doEsquema("M03_notas_explicativas.csv", "id", /^NE-\d{3}$/, linhaM03),
  M04: doEsquema("M04_wizard.csv", "id", /^WZ-\d{2}$/, linhaM04),
  M05: doEsquema("M05_variaveis.csv", "id", /^VAR-\d{3}$/, linhaM05),
  M06: doEsquema("M06_derivacao_etp_tr.csv", "bloco_tr", undefined, linhaM06),
  M07: doEsquema("M07_normas.csv", "id", /^NRM-\d{3}$/, linhaM07),
  M08: doEsquema("M08_clausulas_setoriais.csv", "id", /^SET-\d{2}$/, linhaM08),
  M09: {
    arquivo: "M09_desvios.csv",
    chave: "id",
    formatoDaChave: /^DV-\d{2}$/,
    colunas: ["id", "documento", "local", "tipo", "descricao", "referencia", "tratamento_no_sistema", "achado", "fonte", "status"],
    noPacote: false,
  },
  M10: doEsquema("M10_validacoes.csv", "id", /^VAL-\d{3}$/, linhaM10),
  M11: doEsquema("M11_checklist.csv", "id", /^CK-[CP]-(?:CAB\.\d{2}|\d+(?:\.\d+)*)$/, linhaM11),
  M12: doEsquema("M12_parametros.csv", "id", /^PAR-\d{2}$/, linhaM12),
} satisfies Record<string, Definicao>;

export type NomeDaMatriz = keyof typeof MATRIZES;
const NOMES = Object.keys(MATRIZES) as NomeDaMatriz[];

/** Matriz de origem de cada prefixo de ID. */
const ORIGEM_DO_PREFIXO: Record<string, NomeDaMatriz> = {
  ETP: "M01",
  TR: "M02",
  NE: "M03",
  WZ: "M04",
  VAR: "M05",
  NRM: "M07",
  SET: "M08",
  DV: "M09",
  VAL: "M10",
  CK: "M11",
  PAR: "M12",
};
const CITACAO_DE_ID = /\b(ETP|TR|NE|WZ|VAR|NRM|SET|DV|VAL|CK|PAR)-[A-Za-z0-9]+(?:[.-][A-Za-z0-9]+)*/g;
/** "VAR-113.calculo_expr" cita a coluna de um ID: o sufixo com duas ou mais minúsculas não faz parte do ID. */
const SUFIXO_DE_COLUNA = /\.[a-z]{2,}.*$/;
/** Todo ID tem algum dígito; sem dígito é notação de formato, como "ETP-SS.CC". */
const TEM_DIGITO = /\d/;

const OPERADORES = new Set<string>(OPERADORES_PERMITIDOS);
const OPERADORES_SO_DE_CALCULO = new Set<string>(OPERADORES_DE_CALCULO);
const VARIAVEIS_LIVRES = new Set(["itens", "textos_livres"]);
const PREFIXOS_LIVRES = ["importacao.", "checklist."];
/** Colunas básicas de cada item, descritas na VAR-011 do M05; as demais vêm das linhas "tabela_itens.*". */
const COLUNAS_BASICAS_DO_ITEM = ["numero", "especificacao", "catmat", "unidade", "quantidade", "valor_unitario"];
/** Lista dos itens do mesmo grupo, disponível no contexto de item (README das matrizes). */
const ITENS_DO_GRUPO = "itens_do_grupo";
/** Colunas do M11 cujo valor é um objeto {destino: expressão}. */
const COLUNAS_POR_DESTINO = new Set(["preenche_expr", "sugere_expr"]);
/** Tipo do valor declarado na fonte de cada linha do M12 ("Tipo do valor: numero."). */
const TIPO_DECLARADO = /Tipo do valor: (\w+)\./;
const NUMERO = /^-?\d+(?:\.\d+)?$/;

export type TipoDeErro =
  | "csv"
  | "cabecalho"
  | "esquema"
  | "id_duplicado"
  | "referencia"
  | "json_invalido"
  | "operador"
  | "variavel"
  | "ordem"
  | "parametro"
  | "pacote"
  | "piloto";

export type Erro = { tipo: TipoDeErro; matriz: NomeDaMatriz; linha?: number; coluna?: string; mensagem: string };

type Linha = Record<string, string>;

export type Relatorio = {
  linhas: Record<NomeDaMatriz, number>;
  citacoesConferidas: number;
  status: Record<NomeDaMatriz, Record<(typeof STATUS)[number], number>>;
  validacao: Record<"M03" | "M04", Record<"vazia" | "OK" | "CORRIGIR" | "DUVIDA", number>>;
};

export type Resultado = {
  erros: Erro[];
  relatorio: Relatorio;
  /** Conteúdo do pacote.json e o hash dele; ausentes quando há erro. */
  pacote?: { json: string; sha256: string };
};

export type Opcoes = { piloto?: boolean };

/** Número da linha como aparece na planilha: o cabeçalho é a linha 1. */
const linhaDaPlanilha = (indice: number) => indice + 2;

function sha256(conteudo: string | Buffer): string {
  return createHash("sha256").update(conteudo).digest("hex");
}

export { variavelDoId };

function esquemaDaLinha(def: Definicao) {
  const forma: Record<string, z.ZodType> = {};
  for (const coluna of def.colunas) forma[coluna] = z.string();
  forma.status = z.enum(STATUS);
  for (const [coluna, valores] of Object.entries(def.dominios ?? {})) {
    forma[coluna] = z.enum(valores as [string, ...string[]]);
  }
  forma[def.chave] = def.formatoDaChave
    ? z.string().regex(def.formatoDaChave, "identificador fora do formato")
    : z.string().min(1, "identificador vazio");
  return z.strictObject(forma);
}

function lerCsv(nome: NomeDaMatriz, conteudo: string, erros: Erro[]): Linha[] {
  const def: Definicao = MATRIZES[nome];
  let registros: string[][];
  try {
    registros = parse(conteudo, { bom: true, delimiter: ",", quote: '"', skip_empty_lines: true });
  } catch (e) {
    erros.push({ tipo: "csv", matriz: nome, mensagem: `CSV ilegível: ${(e as Error).message}` });
    return [];
  }
  const [cabecalho = [], ...dados] = registros;
  if (cabecalho.join(",") !== def.colunas.join(",")) {
    erros.push({
      tipo: "cabecalho",
      matriz: nome,
      mensagem: `cabeçalho diferente do esperado. Esperado: ${def.colunas.join(", ")}. Encontrado: ${cabecalho.join(", ")}`,
    });
    return [];
  }
  const esquema = esquemaDaLinha(def);
  const linhas: Linha[] = [];
  dados.forEach((campos, indice) => {
    const linha = Object.fromEntries(def.colunas.map((coluna, i) => [coluna, campos[i]]));
    const conferida = esquema.safeParse(linha);
    if (!conferida.success) {
      for (const problema of conferida.error.issues) {
        erros.push({
          tipo: "esquema",
          matriz: nome,
          linha: linhaDaPlanilha(indice),
          coluna: problema.path.join("."),
          mensagem: problema.message,
        });
      }
    }
    linhas.push(linha);
  });
  return linhas;
}

function conferirIdsUnicos(nome: NomeDaMatriz, linhas: Linha[], erros: Erro[]): Set<string> {
  const chave = MATRIZES[nome].chave;
  const primeiraLinha = new Map<string, number>();
  linhas.forEach((linha, indice) => {
    const id = linha[chave];
    const anterior = primeiraLinha.get(id);
    if (anterior === undefined) {
      primeiraLinha.set(id, indice);
    } else {
      erros.push({
        tipo: "id_duplicado",
        matriz: nome,
        linha: linhaDaPlanilha(indice),
        coluna: chave,
        mensagem: `${id} repetido (já aparece na linha ${linhaDaPlanilha(anterior)})`,
      });
    }
  });
  return new Set(primeiraLinha.keys());
}

/** Confere toda citação de ID em qualquer coluna e devolve quantas citações conferiu. */
function conferirReferencias(
  nome: NomeDaMatriz,
  linhas: Linha[],
  ids: Record<NomeDaMatriz, Set<string>>,
  erros: Erro[],
): number {
  let conferidas = 0;
  linhas.forEach((linha, indice) => {
    for (const [coluna, valor] of Object.entries(linha)) {
      for (const [encontrado, prefixo] of valor.matchAll(CITACAO_DE_ID)) {
        if (!TEM_DIGITO.test(encontrado)) continue;
        const citado = encontrado.replace(SUFIXO_DE_COLUNA, "");
        conferidas++;
        const origem = ORIGEM_DO_PREFIXO[prefixo];
        if (!ids[origem].has(citado)) {
          erros.push({
            tipo: "referencia",
            matriz: nome,
            linha: linhaDaPlanilha(indice),
            coluna,
            mensagem: `cita ${citado}, que não existe no ${origem}`,
          });
        }
      }
    }
  });
  return conferidas;
}

/**
 * Converte o valor de uma linha do M12 pelo tipo declarado na fonte ("Tipo do valor: numero.").
 * Número com ponto decimal, lista JSON ou texto; o que não se encaixa no tipo declarado é erro.
 */
function valorDoParametro(linha: Linha): { valor: ValorDeParametro } | { problema: string } {
  const tipo = TIPO_DECLARADO.exec(linha.fonte)?.[1];
  if (!tipo || !(TIPO_DE_PARAMETRO as readonly string[]).includes(tipo)) {
    return { problema: `fonte sem "Tipo do valor: ${TIPO_DE_PARAMETRO.join(" | ")}."` };
  }
  const valor = linha.valor;
  if (tipo === "numero") {
    return NUMERO.test(valor) ? { valor: Number(valor) } : { problema: `valor "${valor}" não é número (use ponto decimal, sem unidade)` };
  }
  if (tipo === "lista") {
    try {
      const lista: unknown = JSON.parse(valor);
      if (Array.isArray(lista)) return { valor: lista as ValorDeParametro };
    } catch {
      // cai no problema abaixo
    }
    return { problema: `valor "${valor}" não é lista JSON` };
  }
  return valor.trim() === "" ? { problema: "valor de texto vazio" } : { valor };
}

function lerParametros(linhas: Linha[], erros: Erro[]): Record<string, ValorDeParametro> {
  const parametros: Record<string, ValorDeParametro> = {};
  linhas.forEach((linha, indice) => {
    const onde = { tipo: "parametro" as const, matriz: "M12" as const, linha: linhaDaPlanilha(indice) };
    if (!/^[a-z][a-z0-9_]*$/.test(linha.nome)) {
      erros.push({ ...onde, coluna: "nome", mensagem: `nome "${linha.nome}" fora do formato (minúsculas, dígitos e _)` });
      return;
    }
    if (linha.nome in parametros) {
      erros.push({ ...onde, coluna: "nome", mensagem: `nome ${linha.nome} repetido` });
      return;
    }
    const lido = valorDoParametro(linha);
    if ("problema" in lido) {
      erros.push({ ...onde, coluna: "valor", mensagem: `${linha.id} (${linha.nome}): ${lido.problema}` });
      return;
    }
    parametros[linha.nome] = lido.valor;
  });
  return parametros;
}

type Vocabulario = {
  /** Variáveis globais: respostas do wizard e do checklist, variáveis do M05, metadados. */
  raiz: Set<string>;
  /** Atributos de item. */
  item: Set<string>;
  /** Nomes do M12. */
  parametros: Set<string>;
};

function montarVocabulario(linhas: Record<NomeDaMatriz, Linha[]>, erros: Erro[]): Vocabulario {
  const raiz = new Set(VARIAVEIS_LIVRES);
  const origemDaVariavel = new Map<string, string>();
  const registrar = (nome: NomeDaMatriz, id: string, variavel: string) => {
    const outro = origemDaVariavel.get(variavel);
    if (outro !== undefined && outro !== id) {
      erros.push({ tipo: "variavel", matriz: nome, mensagem: `${id} e ${outro} viram a mesma variável ${variavel}` });
    }
    origemDaVariavel.set(variavel, id);
    raiz.add(variavel);
  };
  for (const linha of linhas.M04) registrar("M04", linha.id, variavelDoId(linha.id));
  for (const linha of linhas.M05) registrar("M05", linha.id, variavelDoId(linha.id));
  for (const linha of linhas.M11) {
    registrar("M11", linha.id, variavelDoId(linha.id));
    registrar("M11", linha.id, `${variavelDoId(linha.id)}_texto`);
  }
  const item = new Set(COLUNAS_BASICAS_DO_ITEM);
  for (const linha of linhas.M05) {
    if (linha.nome.startsWith("tabela_itens.")) item.add(linha.nome.slice("tabela_itens.".length));
  }
  return { raiz, item, parametros: new Set(linhas.M12.map((l) => l.nome)) };
}

/**
 * Onde a expressão está sendo lida:
 * - raiz: dados globais;
 * - item: um item (some/none/reduce sobre itens, cálculo por item): atributos do item mais os globais;
 * - elemento: some/none sobre lista que não é de itens; só vale {"var": ""};
 * - reduce: passo do reduce; só valem accumulator e current (current.<x> quando a lista é de itens).
 */
type Contexto = { tipo: "raiz" } | { tipo: "item" } | { tipo: "elemento" } | { tipo: "reduce"; sobreItens: boolean };

type Problema = { tipo: "operador" | "variavel"; mensagem: string };

/** Resultado da leitura de uma expressão: problemas e variáveis usadas (para a ordem de cálculo). */
type Leitura = { problemas: Problema[]; usadas: { nome: string; deItem: boolean }[] };

const ehReservadaDoReduce = (nome: string) =>
  nome === "accumulator" || nome === "current" || nome.startsWith("accumulator.") || nome.startsWith("current.");

/** Nome de uma variável global ou de item, fora do reduce. */
function conferirNome(nome: string, noItem: boolean, vocabulario: Vocabulario, leitura: Leitura): string | undefined {
  if (ehReservadaDoReduce(nome)) return `${nome.split(".")[0]} só vale dentro de reduce`;
  if (vocabulario.item.has(nome)) {
    if (!noItem) return `atributo de item ${nome} fora de some, none ou reduce sobre itens`;
    leitura.usadas.push({ nome, deItem: true });
    return undefined;
  }
  if (nome === ITENS_DO_GRUPO) return noItem ? undefined : `${ITENS_DO_GRUPO} só vale no contexto de item`;
  if (vocabulario.raiz.has(nome)) {
    leitura.usadas.push({ nome, deItem: false });
    return undefined;
  }
  if (nome.startsWith("parametros.")) {
    const parametro = nome.slice("parametros.".length);
    return vocabulario.parametros.has(parametro) ? undefined : `parâmetro ${parametro} sem linha no M12`;
  }
  if (PREFIXOS_LIVRES.some((prefixo) => nome.startsWith(prefixo) && nome.length > prefixo.length)) return undefined;
  return `variável desconhecida: ${nome}`;
}

function conferirVariavel(nome: unknown, contexto: Contexto, vocabulario: Vocabulario, leitura: Leitura): string | undefined {
  if (typeof nome !== "string") return `var com nome que não é texto: ${JSON.stringify(nome)}`;
  switch (contexto.tipo) {
    case "elemento":
      return nome === "" ? undefined : `variável ${nome} dentro de some/none sobre lista que não é de itens`;
    case "reduce":
      if (nome === "accumulator" || nome === "current") return undefined;
      if (nome.startsWith("current.")) {
        if (!contexto.sobreItens) return `${nome}: current só tem atributos quando o reduce é sobre itens`;
        return conferirNome(nome.slice("current.".length), true, vocabulario, leitura);
      }
      return `dentro de reduce só valem accumulator e current (encontrado: ${nome})`;
    default:
      if (nome === "") return `{"var": ""} só vale dentro de some/none sobre lista`;
      return conferirNome(nome, contexto.tipo === "item", vocabulario, leitura);
  }
}

/** Nome da variável em {"var": "x"} ou {"var": ["x", padrão]}; undefined se não for var. */
function nomeDoVar(expressao: unknown): unknown {
  if (expressao === null || typeof expressao !== "object" || Array.isArray(expressao)) return undefined;
  const registro = expressao as Record<string, unknown>;
  if (Object.keys(registro).length !== 1 || !("var" in registro)) return undefined;
  return Array.isArray(registro.var) ? registro.var[0] : registro.var;
}

/** A lista é de itens quando é {"var": "itens"}, ou {"var": "itens_do_grupo"} no contexto de item. */
function ehListaDeItens(lista: unknown, contexto: Contexto): boolean {
  const nome = nomeDoVar(lista);
  if (contexto.tipo !== "raiz" && contexto.tipo !== "item") return false;
  return nome === "itens" || (contexto.tipo === "item" && nome === ITENS_DO_GRUPO);
}

/** Percorre a expressão e registra problemas e variáveis usadas. */
function lerExpressao(expressao: unknown, contexto: Contexto, calculo: boolean, vocabulario: Vocabulario, leitura: Leitura): void {
  if (Array.isArray(expressao)) {
    for (const e of expressao) lerExpressao(e, contexto, calculo, vocabulario, leitura);
    return;
  }
  if (expressao === null || typeof expressao !== "object") return;
  const chaves = Object.keys(expressao);
  if (chaves.length !== 1) {
    leitura.problemas.push({ tipo: "operador", mensagem: `objeto com ${chaves.length} chaves; cada operação tem exatamente uma` });
    return;
  }
  const operador = chaves[0];
  const argumento = (expressao as Record<string, unknown>)[operador];
  if (OPERADORES_SO_DE_CALCULO.has(operador) && !calculo) {
    leitura.problemas.push({
      tipo: "operador",
      mensagem: `operador ${operador} só é aceito em ${COLUNAS_DE_CALCULO.join(" e ")} (P31)`,
    });
    return;
  }
  if (!OPERADORES.has(operador) && !OPERADORES_SO_DE_CALCULO.has(operador)) {
    leitura.problemas.push({ tipo: "operador", mensagem: `operador fora da lista: ${operador}` });
    return;
  }
  const argumentos = Array.isArray(argumento) ? argumento : [argumento];
  const ler = (e: unknown, c: Contexto = contexto) => lerExpressao(e, c, calculo, vocabulario, leitura);
  if (operador === "var") {
    if (argumentos.length < 1 || argumentos.length > 2) {
      leitura.problemas.push({ tipo: "operador", mensagem: "var precisa de 1 ou 2 argumentos (nome e padrão)" });
      return;
    }
    const problema = conferirVariavel(argumentos[0], contexto, vocabulario, leitura);
    if (problema) leitura.problemas.push({ tipo: "variavel", mensagem: problema });
    if (argumentos.length === 2) ler(argumentos[1]);
    return;
  }
  if (operador === "some" || operador === "none") {
    if (argumentos.length !== 2) {
      leitura.problemas.push({ tipo: "operador", mensagem: `${operador} precisa de 2 argumentos` });
      return;
    }
    const [lista, condicao] = argumentos;
    ler(lista);
    ler(condicao, ehListaDeItens(lista, contexto) ? { tipo: "item" } : { tipo: "elemento" });
    return;
  }
  if (operador === "reduce") {
    if (argumentos.length !== 3) {
      leitura.problemas.push({ tipo: "operador", mensagem: "reduce precisa de 3 argumentos (lista, passo e valor inicial)" });
      return;
    }
    const [lista, passo, inicial] = argumentos;
    ler(lista);
    ler(inicial);
    ler(passo, { tipo: "reduce", sobreItens: ehListaDeItens(lista, contexto) });
    return;
  }
  ler(argumentos);
}

/** Contexto de partida de cada coluna: cálculo por item no M05 (tabela_itens.*) e destinos itens.* no M11. */
function contextoInicial(nome: NomeDaMatriz, linha: Linha): Contexto {
  return nome === "M05" && linha.nome.startsWith("tabela_itens.") ? { tipo: "item" } : { tipo: "raiz" };
}

type ExpressaoLida = { valor: unknown; leitura: Leitura };

/** Lê o objeto {destino: expressão} de preenche_expr e sugere_expr. */
function lerPorDestino(objeto: unknown, vocabulario: Vocabulario, leitura: Leitura): void {
  if (objeto === null || typeof objeto !== "object" || Array.isArray(objeto)) {
    leitura.problemas.push({ tipo: "operador", mensagem: "esperado um objeto {destino: expressão}" });
    return;
  }
  for (const [destino, expressao] of Object.entries(objeto)) {
    if (destino.startsWith("itens.")) {
      const atributo = destino.slice("itens.".length);
      if (!vocabulario.item.has(atributo)) leitura.problemas.push({ tipo: "variavel", mensagem: `destino com atributo de item desconhecido: ${destino}` });
      lerExpressao(expressao, { tipo: "item" }, false, vocabulario, leitura);
      continue;
    }
    if (!/^(WZ|VAR)_/.test(destino) || !vocabulario.raiz.has(destino)) {
      leitura.problemas.push({ tipo: "variavel", mensagem: `destino desconhecido: ${destino} (use WZ_xx, VAR_xxx ou itens.<atributo>)` });
    }
    lerExpressao(expressao, { tipo: "raiz" }, false, vocabulario, leitura);
  }
}

/** Confere as colunas *_expr e devolve, por linha, as expressões já convertidas e o que cada uma usa. */
function conferirExpressoes(
  nome: NomeDaMatriz,
  linhas: Linha[],
  vocabulario: Vocabulario,
  erros: Erro[],
): Record<string, ExpressaoLida | null>[] {
  return linhas.map((linha, indice) => {
    const lidas: Record<string, ExpressaoLida | null> = {};
    for (const [coluna, valor] of Object.entries(linha)) {
      if (!coluna.endsWith("_expr")) continue;
      if (valor.trim() === "") {
        lidas[coluna] = null;
        continue;
      }
      const onde = { matriz: nome, linha: linhaDaPlanilha(indice), coluna };
      let expressao: unknown;
      try {
        expressao = JSON.parse(valor);
      } catch (e) {
        erros.push({ tipo: "json_invalido", ...onde, mensagem: `JSON inválido: ${(e as Error).message}` });
        lidas[coluna] = null;
        continue;
      }
      const leitura: Leitura = { problemas: [], usadas: [] };
      if (nome === "M11" && COLUNAS_POR_DESTINO.has(coluna)) {
        lerPorDestino(expressao, vocabulario, leitura);
      } else {
        const calculo = (COLUNAS_DE_CALCULO as readonly string[]).includes(`${nome}.${coluna}`);
        lerExpressao(expressao, contextoInicial(nome, linha), calculo, vocabulario, leitura);
      }
      for (const problema of leitura.problemas) erros.push({ ...onde, ...problema });
      lidas[coluna] = { valor: expressao, leitura };
    }
    return lidas;
  });
}

/**
 * M05: calculo_ordem é inteiro positivo, único e presente só junto com calculo_expr,
 * e cada cálculo só lê variável ou atributo calculado antes dele.
 */
function conferirOrdemDeCalculo(linhas: Linha[], expressoes: Record<string, ExpressaoLida | null>[], erros: Erro[]): void {
  const ordemPorVariavel = new Map<string, number>();
  const ordemPorAtributo = new Map<string, number>();
  const vistas = new Map<number, string>();
  linhas.forEach((linha, indice) => {
    const onde = { tipo: "ordem" as const, matriz: "M05" as const, linha: linhaDaPlanilha(indice), coluna: "calculo_ordem" };
    const temExpressao = linha.calculo_expr.trim() !== "";
    if (linha.calculo_ordem === "") {
      if (temExpressao) erros.push({ ...onde, mensagem: `${linha.id} tem calculo_expr sem calculo_ordem` });
      return;
    }
    if (!/^[1-9]\d*$/.test(linha.calculo_ordem)) {
      erros.push({ ...onde, mensagem: `${linha.id}: calculo_ordem "${linha.calculo_ordem}" não é inteiro positivo` });
      return;
    }
    if (!temExpressao) erros.push({ ...onde, mensagem: `${linha.id} tem calculo_ordem sem calculo_expr` });
    const ordem = Number(linha.calculo_ordem);
    const outra = vistas.get(ordem);
    if (outra) erros.push({ ...onde, mensagem: `${linha.id} e ${outra} têm a mesma calculo_ordem ${ordem}` });
    vistas.set(ordem, linha.id);
    ordemPorVariavel.set(variavelDoId(linha.id), ordem);
    if (linha.nome.startsWith("tabela_itens.")) ordemPorAtributo.set(linha.nome.slice("tabela_itens.".length), ordem);
  });
  linhas.forEach((linha, indice) => {
    const lida = expressoes[indice].calculo_expr;
    if (!lida || !/^[1-9]\d*$/.test(linha.calculo_ordem)) return;
    const ordem = Number(linha.calculo_ordem);
    const problemas = new Set<string>();
    for (const { nome, deItem } of lida.leitura.usadas) {
      const usada = (deItem ? ordemPorAtributo : ordemPorVariavel).get(nome);
      if (usada !== undefined && usada >= ordem) {
        problemas.add(`${linha.id} (ordem ${ordem}) usa ${deItem ? `o atributo ${nome}` : nome}, que tem ordem ${usada}`);
      }
    }
    for (const mensagem of problemas) {
      erros.push({ tipo: "ordem", matriz: "M05", linha: linhaDaPlanilha(indice), coluna: "calculo_expr", mensagem });
    }
  });
}

function conferirPiloto(linhas: Record<NomeDaMatriz, Linha[]>, erros: Erro[]): void {
  const pendentes = (nome: "M03" | "M04", filtro: (linha: Linha) => boolean) => {
    const ids = linhas[nome].filter((l) => filtro(l) && l.validacao !== "OK").map((l) => l.id);
    if (ids.length > 0) {
      const descricao = nome === "M03" ? "regras CONDICAO" : "perguntas";
      erros.push({
        tipo: "piloto",
        matriz: nome,
        coluna: "validacao",
        mensagem: `${ids.length} ${descricao} sem validacao = OK: ${ids.join(", ")}`,
      });
    }
  };
  pendentes("M03", (l) => l.natureza === "CONDICAO");
  pendentes("M04", () => true);
}

function contar<T extends string>(valores: string[], categorias: readonly T[]): Record<T, number> {
  return Object.fromEntries(categorias.map((c) => [c, valores.filter((v) => v === c).length])) as Record<T, number>;
}

function montarRelatorio(linhas: Record<NomeDaMatriz, Linha[]>, citacoesConferidas: number): Relatorio {
  const porMatriz = <T>(f: (l: Linha[]) => T) =>
    Object.fromEntries(NOMES.map((n) => [n, f(linhas[n])])) as Record<NomeDaMatriz, T>;
  const validacao = (l: Linha[]) => {
    const { "": vazia, ...resto } = contar(l.map((x) => x.validacao), VALIDACAO);
    return { vazia, ...resto };
  };
  return {
    linhas: porMatriz((l) => l.length),
    citacoesConferidas,
    status: porMatriz((l) => contar(l.map((x) => x.status), STATUS)),
    validacao: { M03: validacao(linhas.M03), M04: validacao(linhas.M04) },
  };
}

/** JSON com chaves em ordem alfabética em todos os níveis; listas mantêm a ordem do CSV. */
export function jsonEstavel(valor: unknown): string {
  const ordenar = (v: unknown): unknown => {
    if (Array.isArray(v)) return v.map(ordenar);
    if (v !== null && typeof v === "object") {
      return Object.fromEntries(
        Object.keys(v)
          .sort()
          .map((k) => [k, ordenar((v as Record<string, unknown>)[k])]),
      );
    }
    return v;
  };
  return `${JSON.stringify(ordenar(valor), null, 2)}\n`;
}

/** Linha como vai para o pacote: expressões em JSON e calculo_ordem em número. */
function linhaDoPacote(linha: Linha, expressoes: Record<string, ExpressaoLida | null>): Record<string, unknown> {
  const convertida: Record<string, unknown> = { ...linha };
  for (const [coluna, lida] of Object.entries(expressoes)) convertida[coluna] = lida ? lida.valor : null;
  if ("calculo_ordem" in linha) convertida.calculo_ordem = linha.calculo_ordem === "" ? null : Number(linha.calculo_ordem);
  return convertida;
}

/** Compila a partir do conteúdo de cada CSV (nome do arquivo -> texto). Não lê nem grava nada. */
export function compilarConteudos(conteudos: Record<string, string>, opcoes: Opcoes = {}): Resultado {
  const erros: Erro[] = [];
  const linhas = {} as Record<NomeDaMatriz, Linha[]>;
  for (const nome of NOMES) {
    const conteudo = conteudos[MATRIZES[nome].arquivo];
    if (conteudo === undefined) {
      erros.push({ tipo: "csv", matriz: nome, mensagem: `arquivo ${MATRIZES[nome].arquivo} não encontrado` });
      linhas[nome] = [];
      continue;
    }
    linhas[nome] = lerCsv(nome, conteudo, erros);
  }
  // Sem todas as matrizes lidas, as demais conferências só repetiriam o mesmo problema.
  if (erros.some((e) => e.tipo === "csv" || e.tipo === "cabecalho")) {
    return { erros, relatorio: montarRelatorio(linhas, 0) };
  }

  const ids = {} as Record<NomeDaMatriz, Set<string>>;
  for (const nome of NOMES) ids[nome] = conferirIdsUnicos(nome, linhas[nome], erros);
  let citacoes = 0;
  for (const nome of NOMES) citacoes += conferirReferencias(nome, linhas[nome], ids, erros);

  const parametros = lerParametros(linhas.M12, erros);
  const vocabulario = montarVocabulario(linhas, erros);
  const expressoes = {} as Record<NomeDaMatriz, Record<string, ExpressaoLida | null>[]>;
  for (const nome of NOMES) expressoes[nome] = conferirExpressoes(nome, linhas[nome], vocabulario, erros);
  conferirOrdemDeCalculo(linhas.M05, expressoes.M05, erros);

  if (opcoes.piloto) conferirPiloto(linhas, erros);

  const relatorio = montarRelatorio(linhas, citacoes);
  if (erros.length > 0) return { erros, relatorio };

  const pacote = {
    pacote: NOME_DO_PACOTE,
    versao_do_formato: VERSAO_DO_FORMATO,
    arquivos_de_origem: Object.fromEntries(
      NOMES.map((n) => [MATRIZES[n].arquivo, sha256(conteudos[MATRIZES[n].arquivo])]),
    ),
    parametros,
    matrizes: Object.fromEntries(
      NOMES.filter((n) => MATRIZES[n].noPacote).map((n) => [n, linhas[n].map((l, i) => linhaDoPacote(l, expressoes[n][i]))]),
    ),
  };
  // O pacote tem de bater com os tipos que o motor usa (src/motor/pacote/esquema.ts).
  const conferido = esquemaDoPacote.safeParse(pacote);
  if (!conferido.success) {
    for (const problema of conferido.error.issues.slice(0, 20)) {
      const [, matriz, linha, coluna] = problema.path;
      erros.push({
        tipo: "pacote",
        matriz: (typeof matriz === "string" && matriz in MATRIZES ? matriz : "M00") as NomeDaMatriz,
        linha: typeof linha === "number" ? linhaDaPlanilha(linha) : undefined,
        coluna: typeof coluna === "string" ? coluna : problema.path.join("."),
        mensagem: problema.message,
      });
    }
    return { erros, relatorio };
  }
  const json = jsonEstavel(pacote);
  return { erros, relatorio, pacote: { json, sha256: sha256(json) } };
}

/** Lê os CSV de uma pasta e compila. */
export function compilar(dirMatrizes: string = DIR_MATRIZES, opcoes: Opcoes = {}): Resultado {
  const conteudos: Record<string, string> = {};
  for (const nome of NOMES) {
    const arquivo = MATRIZES[nome].arquivo;
    try {
      conteudos[arquivo] = readFileSync(path.join(dirMatrizes, arquivo), "utf8");
    } catch {
      // compilarConteudos registra o arquivo ausente
    }
  }
  return compilarConteudos(conteudos, opcoes);
}

export function gravarPacote(pacote: { json: string; sha256: string }, dirSaida: string = DIR_PACOTE): void {
  mkdirSync(dirSaida, { recursive: true });
  writeFileSync(path.join(dirSaida, "pacote.json"), pacote.json);
  writeFileSync(path.join(dirSaida, "pacote.sha256"), `${pacote.sha256}  pacote.json\n`);
}

export function formatarRelatorio(resultado: Resultado, opcoes: Opcoes = {}): string {
  const { relatorio, erros } = resultado;
  const saida: string[] = [];
  const tabela = (cabecalho: string[], linhas: (string | number)[][]) => {
    const todas = [cabecalho, ...linhas.map((l) => l.map(String))];
    const larguras = cabecalho.map((_, i) => Math.max(...todas.map((l) => l[i].length)));
    for (const l of todas) saida.push(`  ${l.map((c, i) => (i === 0 ? c.padEnd(larguras[i]) : c.padStart(larguras[i]))).join("  ")}`);
  };

  saida.push(`Compilador de regras: ${NOME_DO_PACOTE} (modo ${opcoes.piloto ? "piloto" : "desenvolvimento"})`, "");
  saida.push("Linhas e status por matriz:");
  tabela(
    ["matriz", "linhas", ...STATUS],
    NOMES.map((n) => [n, relatorio.linhas[n], ...STATUS.map((s) => relatorio.status[n][s])]),
  );
  saida.push("", "Validação do Gabriel (M03 e M04):");
  tabela(
    ["matriz", "vazia", "OK", "CORRIGIR", "DUVIDA"],
    (["M03", "M04"] as const).map((n) => {
      const v = relatorio.validacao[n];
      return [n, v.vazia, v.OK, v.CORRIGIR, v.DUVIDA];
    }),
  );

  const soma = (f: (n: NomeDaMatriz) => number) => NOMES.reduce((total, n) => total + f(n), 0);
  const inferidas = soma((n) => relatorio.status[n].INFERIDO);
  const aVerificar = soma((n) => relatorio.status[n].A_VERIFICAR);
  const semValidacao = relatorio.validacao.M03.vazia + relatorio.validacao.M04.vazia;
  saida.push("", `Citações de ID conferidas: ${relatorio.citacoesConferidas}`);
  saida.push("", "Avisos (não impedem a compilação em desenvolvimento):");
  saida.push(`  ${inferidas} linhas com status INFERIDO e ${aVerificar} com status A_VERIFICAR`);
  saida.push(`  ${semValidacao} linhas do M03 e do M04 com validacao vazia`);

  saida.push("", `Erros: ${erros.length}`);
  for (const e of erros) {
    const onde = [e.matriz, e.linha && `linha ${e.linha}`, e.coluna && `coluna ${e.coluna}`].filter(Boolean).join(", ");
    saida.push(`  [${e.tipo}] ${onde}: ${e.mensagem}`);
  }

  saida.push("");
  if (resultado.pacote) {
    saida.push(`Pacote: regras/${NOME_DO_PACOTE}/pacote.json`, `SHA-256: ${resultado.pacote.sha256}`);
  } else {
    saida.push("Pacote NÃO gerado: corrija os erros acima nas matrizes e compile de novo.");
  }
  return saida.join("\n");
}

function principal(): void {
  const opcoes: Opcoes = { piloto: process.argv.includes("--piloto") };
  const resultado = compilar(DIR_MATRIZES, opcoes);
  if (resultado.pacote) gravarPacote(resultado.pacote);
  console.log(formatarRelatorio(resultado, opcoes));
  if (!resultado.pacote) process.exitCode = 1;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) principal();
