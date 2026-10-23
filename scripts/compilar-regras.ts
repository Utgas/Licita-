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

export const NOME_DO_PACOTE = "agu-tr-compras-2025-12";
const VERSAO_DO_FORMATO = 1;

const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
export const DIR_MATRIZES = path.join(RAIZ, "matrizes", "v1");
export const DIR_PACOTE = path.join(RAIZ, "regras", NOME_DO_PACOTE);

const STATUS = ["EXTRAIDO", "INFERIDO", "A_VERIFICAR"] as const;
const VALIDACAO = ["", "OK", "CORRIGIR", "DUVIDA"] as const;
const DOCUMENTO = ["AMBOS", "TR", "ETP"] as const;
const RESULTADO_DE_TESTE = ["NAO_TESTADO", "CONSISTENTE", "PARCIAL", "DIVERGENTE", "NAO_LIDO"] as const;

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

// Colunas exatamente como estão no cabeçalho de cada CSV. Não renomeie.
export const MATRIZES = {
  M00: {
    arquivo: "M00_inventario.csv",
    chave: "arquivo",
    colunas: ["arquivo", "pasta", "tipo_real", "numero_ano", "uasg", "om", "processo", "objeto_resumo", "categoria", "srp", "papel_srp", "formato", "paginas_lidas_total", "par", "problemas", "fonte", "status"],
    noPacote: false,
  },
  M01: {
    arquivo: "M01_etp_campos.csv",
    chave: "id",
    formatoDaChave: /^ETP-\d{2}\.\d{2}$/,
    colunas: ["id", "secao_numero", "secao_nome", "campo", "inciso_art18", "obrigatorio_par2", "dispositivo_in58", "tipo", "regra_preenchimento", "regra_anti_alucinacao", "quando_nao_se_aplica", "destino_tr", "corpus_preenchido_omitido_na", "fonte", "status"],
    dominios: { obrigatorio_par2: ["S", "N"] },
    noPacote: true,
  },
  M02: {
    arquivo: "M02_tr_blocos.csv",
    chave: "id",
    formatoDaChave: /^TR-[A-Za-z0-9]+(?:[.-][A-Za-z0-9]+)*$/,
    colunas: ["id", "secao", "item_modelo", "texto_literal", "formatacao", "tipo", "grupo_alternativa", "opcao", "lacunas", "notas", "condicao_inclusao", "condicao_expr", "origem_dado", "normas", "fonte", "status"],
    dominios: { formatacao: ["PRETO", "VERMELHO_ITALICO", "MISTO", "NOTA_EXPLICATIVA"] },
    noPacote: true,
  },
  M03: {
    arquivo: "M03_notas_explicativas.csv",
    chave: "id",
    formatoDaChave: /^NE-\d{3}$/,
    colunas: ["id", "bloco_ancora", "trecho_ancorado", "texto_integral", "natureza", "regra_derivada", "afeta", "citacoes", "fonte", "status", "validacao", "comentario_validacao"],
    dominios: {
      natureza: ["OBRIGACAO", "ORIENTACAO_REDACAO", "CONDICAO", "VEDACAO", "REMISSAO_NORMATIVA", "PROCEDIMENTO_FORA_DO_TR"],
      validacao: VALIDACAO,
    },
    noPacote: true,
  },
  M04: {
    arquivo: "M04_wizard.csv",
    chave: "id",
    formatoDaChave: /^WZ-\d{2}$/,
    colunas: ["id", "pergunta", "documento", "tipo_resposta", "opcoes", "depende_de", "pre_preenchida_por", "liga_blocos", "liga_expr", "desliga_blocos", "desliga_expr", "exige_justificativa", "coerencia", "fundamento", "fonte", "status", "validacao", "comentario_validacao"],
    dominios: {
      documento: DOCUMENTO,
      tipo_resposta: ["UNICA", "MULTIPLA", "SIM_NAO", "NUMERO", "TEXTO"],
      validacao: VALIDACAO,
    },
    noPacote: true,
  },
  M05: {
    arquivo: "M05_variaveis.csv",
    chave: "id",
    formatoDaChave: /^VAR-\d{3}$/,
    colunas: ["id", "nome", "descricao", "tipo_dado", "validacao", "obrigatoria", "origem", "usada_em", "fonte", "status"],
    dominios: {
      tipo_dado: ["TEXTO", "NUMERO", "MOEDA", "DATA", "LISTA", "TABELA"],
      obrigatoria: ["S", "N", "CONDICIONAL"],
      origem: ["SISTEMA", "CHECKLIST", "WIZARD", "DFD", "PESQUISA_PRECOS"],
    },
    noPacote: true,
  },
  M06: {
    arquivo: "M06_derivacao_etp_tr.csv",
    chave: "bloco_tr",
    colunas: ["bloco_tr", "secao", "campos_etp", "variaveis", "perguntas_wz", "classe_origem", "regra_derivacao", "teste_par_117", "evidencia_par_117", "teste_caso_67_23", "evidencia_caso_67_23", "fonte", "status"],
    dominios: { teste_par_117: RESULTADO_DE_TESTE, teste_caso_67_23: RESULTADO_DE_TESTE },
    noPacote: true,
  },
  M07: {
    arquivo: "M07_normas.csv",
    chave: "id",
    formatoDaChave: /^NRM-\d{3}$/,
    colunas: ["id", "chave", "norma", "tipo", "numero", "ano", "orgao", "dispositivos_citados", "formas_citadas", "onde_citada", "n_citacoes", "origem", "situacao", "verificacao", "fonte", "status"],
    dominios: { situacao: ["VIGENTE", "REVOGADA", "NAO_CONFERIDA"] },
    noPacote: true,
  },
  M08: {
    arquivo: "M08_clausulas_setoriais.csv",
    chave: "id",
    formatoDaChave: /^SET-\d{2}$/,
    colunas: ["id", "tema", "documento", "origem_checklist", "condicao", "condicao_expr", "ponto_insercao", "texto_proposto", "variaveis", "perguntas_wz", "base_no_modelo", "evidencia_corpus", "observacao", "fonte", "status"],
    dominios: { documento: DOCUMENTO },
    noPacote: true,
  },
  M09: {
    arquivo: "M09_desvios.csv",
    chave: "id",
    formatoDaChave: /^DV-\d{2}$/,
    colunas: ["id", "documento", "local", "tipo", "descricao", "referencia", "tratamento_no_sistema", "achado", "fonte", "status"],
    noPacote: false,
  },
  M10: {
    arquivo: "M10_validacoes.csv",
    chave: "id",
    formatoDaChave: /^VAL-\d{3}$/,
    colunas: ["id", "regra", "tipo", "momento", "condicao", "condicao_expr", "mensagem", "afeta", "base", "achado", "fonte", "status"],
    dominios: {
      tipo: ["BLOQUEIO", "ALERTA", "INFORMATIVO"],
      momento: ["CHECKLIST", "IMPORTACAO", "WIZARD", "ITENS", "MINUTA"],
    },
    noPacote: true,
  },
  M11: {
    arquivo: "M11_checklist.csv",
    chave: "id",
    formatoDaChave: /^CK-[CP]-(?:CAB\.\d{2}|\d+(?:\.\d+)*)$/,
    colunas: ["id", "checklist", "secao", "numero", "pergunta", "tipo_resposta", "opcoes", "orientacao", "condicional", "por_item", "destinos", "efeito", "regra", "fonte", "status"],
    dominios: {
      checklist: ["CONSUMO", "PERMANENTES"],
      tipo_resposta: ["UNICA", "MULTIPLA", "SIM_NAO", "NUMERO", "TEXTO", "TABELA"],
      por_item: ["S", "N"],
      efeito: ["PREENCHE", "JUSTIFICA", "SUGERE", "SO_CONTROLE", "ALERTA"],
    },
    noPacote: true,
  },
} as const satisfies Record<string, Definicao>;

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
};
const CITACAO_DE_ID = /\b(ETP|TR|NE|WZ|VAR|NRM|SET|DV|VAL|CK)-[A-Za-z0-9]+(?:[.-][A-Za-z0-9]+)*/g;
/** Todo ID tem algum dígito; sem dígito é notação de formato, como "ETP-SS.CC". */
const TEM_DIGITO = /\d/;

const OPERADORES_PERMITIDOS = new Set(["var", "==", "!=", "!", "!!", "and", "or", "if", "in", "merge", "some", "none", "<=", ">"]);
const VARIAVEIS_LIVRES = new Set(["itens", "textos_livres"]);
const PREFIXOS_LIVRES = ["importacao.", "checklist.", "parametros."];
/** Colunas básicas de cada item, descritas na VAR-011 do M05; as demais vêm das linhas "tabela_itens.*". */
const COLUNAS_BASICAS_DO_ITEM = ["numero", "especificacao", "catmat", "unidade", "quantidade", "valor_unitario"];

export type TipoDeErro =
  | "csv"
  | "cabecalho"
  | "esquema"
  | "id_duplicado"
  | "referencia"
  | "json_invalido"
  | "operador"
  | "variavel"
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

/** Nome da variável de JSON Logic para um ID: WZ-23 -> WZ_23, CK-C-14.2 -> CK_C_14_2, VAR-001 -> VAR_001. */
export function variavelDoId(id: string): string {
  return id.replace(/[-.]/g, "_");
}

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
      for (const [citado, prefixo] of valor.matchAll(CITACAO_DE_ID)) {
        if (!TEM_DIGITO.test(citado)) continue;
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

type Vocabulario = { raiz: Set<string>; item: Set<string> };

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
  return { raiz, item };
}

/** Contexto de uma variável: a raiz dos dados, um item (dentro de some/none sobre itens) ou um elemento de lista. */
type Contexto = "raiz" | "item" | "elemento";

function conferirVariavel(nome: unknown, contexto: Contexto, vocabulario: Vocabulario): string | undefined {
  if (typeof nome !== "string") return `var com nome que não é texto: ${JSON.stringify(nome)}`;
  if (contexto === "elemento") return nome === "" ? undefined : `variável ${nome} dentro de some/none sobre lista que não é itens`;
  if (contexto === "item") return vocabulario.item.has(nome) ? undefined : `atributo de item desconhecido: ${nome}`;
  if (vocabulario.raiz.has(nome)) return undefined;
  if (PREFIXOS_LIVRES.some((prefixo) => nome.startsWith(prefixo) && nome.length > prefixo.length)) return undefined;
  return `variável desconhecida: ${nome}`;
}

/** Percorre a expressão e devolve os problemas encontrados, com o tipo de cada um. */
function conferirExpressao(
  expressao: unknown,
  contexto: Contexto,
  vocabulario: Vocabulario,
): { tipo: "operador" | "variavel"; mensagem: string }[] {
  if (Array.isArray(expressao)) return expressao.flatMap((e) => conferirExpressao(e, contexto, vocabulario));
  if (expressao === null || typeof expressao !== "object") return [];
  const chaves = Object.keys(expressao);
  if (chaves.length !== 1) {
    return [{ tipo: "operador", mensagem: `objeto com ${chaves.length} chaves; cada operação tem exatamente uma` }];
  }
  const operador = chaves[0];
  const argumento = (expressao as Record<string, unknown>)[operador];
  if (!OPERADORES_PERMITIDOS.has(operador)) return [{ tipo: "operador", mensagem: `operador fora da lista: ${operador}` }];
  const argumentos = Array.isArray(argumento) ? argumento : [argumento];
  if (operador === "var") {
    const problema = conferirVariavel(argumentos[0], contexto, vocabulario);
    return problema ? [{ tipo: "variavel", mensagem: problema }] : [];
  }
  if (operador === "some" || operador === "none") {
    if (argumentos.length !== 2) return [{ tipo: "operador", mensagem: `${operador} precisa de 2 argumentos` }];
    const [lista, condicao] = argumentos;
    const sobreItens = contexto === "raiz" && JSON.stringify(lista) === '{"var":"itens"}';
    return [
      ...conferirExpressao(lista, contexto, vocabulario),
      ...conferirExpressao(condicao, sobreItens ? "item" : "elemento", vocabulario),
    ];
  }
  return conferirExpressao(argumentos, contexto, vocabulario);
}

/** Confere as colunas *_expr e devolve as linhas com essas colunas já convertidas para JSON. */
function conferirExpressoes(
  nome: NomeDaMatriz,
  linhas: Linha[],
  vocabulario: Vocabulario,
  erros: Erro[],
): Record<string, unknown>[] {
  return linhas.map((linha, indice) => {
    const convertida: Record<string, unknown> = { ...linha };
    for (const [coluna, valor] of Object.entries(linha)) {
      if (!coluna.endsWith("_expr")) continue;
      if (valor.trim() === "") {
        convertida[coluna] = null;
        continue;
      }
      const onde = { matriz: nome, linha: linhaDaPlanilha(indice), coluna };
      let expressao: unknown;
      try {
        expressao = JSON.parse(valor);
      } catch (e) {
        erros.push({ tipo: "json_invalido", ...onde, mensagem: `JSON inválido: ${(e as Error).message}` });
        continue;
      }
      for (const problema of conferirExpressao(expressao, "raiz", vocabulario)) erros.push({ ...onde, ...problema });
      convertida[coluna] = expressao;
    }
    return convertida;
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

  const ids = {} as Record<NomeDaMatriz, Set<string>>;
  for (const nome of NOMES) ids[nome] = conferirIdsUnicos(nome, linhas[nome], erros);
  let citacoes = 0;
  for (const nome of NOMES) citacoes += conferirReferencias(nome, linhas[nome], ids, erros);

  const vocabulario = montarVocabulario(linhas, erros);
  const convertidas = {} as Record<NomeDaMatriz, Record<string, unknown>[]>;
  for (const nome of NOMES) convertidas[nome] = conferirExpressoes(nome, linhas[nome], vocabulario, erros);

  if (opcoes.piloto) conferirPiloto(linhas, erros);

  const relatorio = montarRelatorio(linhas, citacoes);
  if (erros.length > 0) return { erros, relatorio };

  const json = jsonEstavel({
    pacote: NOME_DO_PACOTE,
    versao_do_formato: VERSAO_DO_FORMATO,
    arquivos_de_origem: Object.fromEntries(
      NOMES.map((n) => [MATRIZES[n].arquivo, sha256(conteudos[MATRIZES[n].arquivo])]),
    ),
    matrizes: Object.fromEntries(NOMES.filter((n) => MATRIZES[n].noPacote).map((n) => [n, convertidas[n]])),
  });
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
