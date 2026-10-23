/**
 * Esquema do pacote de regras (regras/<pacote>/pacote.json) e os tipos que o motor usa.
 *
 * O compilador (scripts/compilar-regras.ts) confere o pacote contra este esquema antes de gravá-lo,
 * e a ordem das colunas de cada linha é a ordem do cabeçalho do CSV correspondente.
 * Quem lê o arquivo do pacote é o script ou a aplicação; o motor só recebe o objeto já lido.
 */
import { z } from "zod";

export const VERSAO_DO_FORMATO = 2;

export const STATUS = ["EXTRAIDO", "INFERIDO", "A_VERIFICAR"] as const;
export const VALIDACAO = ["", "OK", "CORRIGIR", "DUVIDA"] as const;
export const DOCUMENTO = ["AMBOS", "TR", "ETP"] as const;
export const RESULTADO_DE_TESTE = ["NAO_TESTADO", "CONSISTENTE", "PARCIAL", "DIVERGENTE", "NAO_LIDO"] as const;
export const TIPO_DE_RESPOSTA_DO_WIZARD = ["UNICA", "MULTIPLA", "SIM_NAO", "NUMERO", "TEXTO"] as const;
export const TIPO_DE_RESPOSTA_DO_CHECKLIST = ["UNICA", "MULTIPLA", "SIM_NAO", "NUMERO", "TEXTO", "TABELA"] as const;
export const TIPO_DE_DADO = ["TEXTO", "NUMERO", "MOEDA", "DATA", "LISTA", "TABELA"] as const;
export const TIPO_DE_VALIDACAO = ["BLOQUEIO", "ALERTA", "INFORMATIVO"] as const;
export const MOMENTO_DE_VALIDACAO = ["CHECKLIST", "IMPORTACAO", "WIZARD", "ITENS", "MINUTA"] as const;
export const EFEITO_DO_CHECKLIST = ["PREENCHE", "JUSTIFICA", "SUGERE", "SO_CONTROLE", "ALERTA"] as const;
export const TIPO_DE_PARAMETRO = ["numero", "lista", "texto"] as const;

/** Expressão em JSON Logic; `null` quando a coluna está vazia no CSV. */
const expressao = z.json().nullable();
/** Objeto {destino: expressão} das colunas preenche_expr e sugere_expr do M11. */
const expressoesPorDestino = z.record(z.string(), z.json()).nullable();
const texto = z.string();
const status = z.enum(STATUS);
const validacao = z.enum(VALIDACAO);

export const linhaM01 = z.strictObject({
  id: texto,
  secao_numero: texto,
  secao_nome: texto,
  campo: texto,
  inciso_art18: texto,
  obrigatorio_par2: z.enum(["S", "N"]),
  dispositivo_in58: texto,
  tipo: texto,
  regra_preenchimento: texto,
  regra_anti_alucinacao: texto,
  quando_nao_se_aplica: texto,
  destino_tr: texto,
  corpus_preenchido_omitido_na: texto,
  fonte: texto,
  status,
});

export const linhaM02 = z.strictObject({
  id: texto,
  secao: texto,
  item_modelo: texto,
  texto_literal: texto,
  formatacao: z.enum(["PRETO", "VERMELHO_ITALICO", "MISTO", "NOTA_EXPLICATIVA"]),
  tipo: texto,
  grupo_alternativa: texto,
  opcao: texto,
  lacunas: texto,
  notas: texto,
  condicao_inclusao: texto,
  condicao_expr: expressao,
  origem_dado: texto,
  normas: texto,
  fonte: texto,
  status,
});

export const linhaM03 = z.strictObject({
  id: texto,
  bloco_ancora: texto,
  trecho_ancorado: texto,
  texto_integral: texto,
  natureza: z.enum(["OBRIGACAO", "ORIENTACAO_REDACAO", "CONDICAO", "VEDACAO", "REMISSAO_NORMATIVA", "PROCEDIMENTO_FORA_DO_TR"]),
  regra_derivada: texto,
  afeta: texto,
  citacoes: texto,
  fonte: texto,
  status,
  validacao,
  comentario_validacao: texto,
});

export const linhaM04 = z.strictObject({
  id: texto,
  pergunta: texto,
  documento: z.enum(DOCUMENTO),
  tipo_resposta: z.enum(TIPO_DE_RESPOSTA_DO_WIZARD),
  opcoes: texto,
  depende_de: texto,
  depende_de_expr: expressao,
  pre_preenchida_por: texto,
  calculo_expr: expressao,
  liga_blocos: texto,
  liga_expr: expressao,
  desliga_blocos: texto,
  desliga_expr: expressao,
  exige_justificativa: texto,
  coerencia: texto,
  fundamento: texto,
  fonte: texto,
  status,
  validacao,
  comentario_validacao: texto,
});

export const linhaM05 = z.strictObject({
  id: texto,
  nome: texto,
  descricao: texto,
  tipo_dado: z.enum(TIPO_DE_DADO),
  validacao: texto,
  calculo_expr: expressao,
  /** Ordem de cálculo; `null` quando a variável não é calculada. */
  calculo_ordem: z.number().int().positive().nullable(),
  obrigatoria: z.enum(["S", "N", "CONDICIONAL"]),
  origem: z.enum(["SISTEMA", "CHECKLIST", "WIZARD", "DFD", "PESQUISA_PRECOS"]),
  usada_em: texto,
  fonte: texto,
  status,
});

export const linhaM06 = z.strictObject({
  bloco_tr: texto,
  secao: texto,
  campos_etp: texto,
  variaveis: texto,
  perguntas_wz: texto,
  classe_origem: texto,
  regra_derivacao: texto,
  teste_par_117: z.enum(RESULTADO_DE_TESTE),
  evidencia_par_117: texto,
  teste_caso_67_23: z.enum(RESULTADO_DE_TESTE),
  evidencia_caso_67_23: texto,
  fonte: texto,
  status,
});

export const linhaM07 = z.strictObject({
  id: texto,
  chave: texto,
  norma: texto,
  tipo: texto,
  numero: texto,
  ano: texto,
  orgao: texto,
  dispositivos_citados: texto,
  formas_citadas: texto,
  onde_citada: texto,
  n_citacoes: texto,
  origem: texto,
  situacao: z.enum(["VIGENTE", "REVOGADA", "NAO_CONFERIDA"]),
  verificacao: texto,
  fonte: texto,
  status,
});

export const linhaM08 = z.strictObject({
  id: texto,
  tema: texto,
  documento: z.enum(DOCUMENTO),
  origem_checklist: texto,
  condicao: texto,
  condicao_expr: expressao,
  ponto_insercao: texto,
  texto_proposto: texto,
  variaveis: texto,
  perguntas_wz: texto,
  base_no_modelo: texto,
  evidencia_corpus: texto,
  observacao: texto,
  fonte: texto,
  status,
});

export const linhaM10 = z.strictObject({
  id: texto,
  regra: texto,
  tipo: z.enum(TIPO_DE_VALIDACAO),
  momento: z.enum(MOMENTO_DE_VALIDACAO),
  condicao: texto,
  condicao_expr: expressao,
  mensagem: texto,
  afeta: texto,
  base: texto,
  achado: texto,
  fonte: texto,
  status,
});

export const linhaM11 = z.strictObject({
  id: texto,
  checklist: z.enum(["CONSUMO", "PERMANENTES"]),
  secao: texto,
  numero: texto,
  pergunta: texto,
  tipo_resposta: z.enum(TIPO_DE_RESPOSTA_DO_CHECKLIST),
  opcoes: texto,
  orientacao: texto,
  condicional: texto,
  condicional_expr: expressao,
  por_item: z.enum(["S", "N"]),
  destinos: texto,
  efeito: z.enum(EFEITO_DO_CHECKLIST),
  regra: texto,
  preenche_expr: expressoesPorDestino,
  sugere_expr: expressoesPorDestino,
  fonte: texto,
  status,
});

export const linhaM12 = z.strictObject({
  id: texto,
  nome: texto,
  /** Valor como está no CSV; o valor já tipado fica em `pacote.parametros`. */
  valor: texto,
  unidade: texto,
  base: texto,
  vigencia: texto,
  usado_em: texto,
  fonte: texto,
  status,
});

/** Valor de um parâmetro do M12: número, lista ou texto. */
export const valorDeParametro = z.union([z.number(), z.array(z.json()), z.string()]);

export const esquemaDoPacote = z.strictObject({
  pacote: z.string(),
  versao_do_formato: z.literal(VERSAO_DO_FORMATO),
  /** SHA-256 de cada CSV de origem. */
  arquivos_de_origem: z.record(z.string(), z.string().regex(/^[0-9a-f]{64}$/)),
  /** `parametros.<nome>` das expressões: nome do M12 -> valor tipado. */
  parametros: z.record(z.string(), valorDeParametro),
  matrizes: z.strictObject({
    M01: z.array(linhaM01),
    M02: z.array(linhaM02),
    M03: z.array(linhaM03),
    M04: z.array(linhaM04),
    M05: z.array(linhaM05),
    M06: z.array(linhaM06),
    M07: z.array(linhaM07),
    M08: z.array(linhaM08),
    M10: z.array(linhaM10),
    M11: z.array(linhaM11),
    M12: z.array(linhaM12),
  }),
});

export type Pacote = z.infer<typeof esquemaDoPacote>;
export type MatrizesDoPacote = Pacote["matrizes"];
export type ValorDeParametro = z.infer<typeof valorDeParametro>;
export type LinhaM01 = z.infer<typeof linhaM01>;
export type LinhaM02 = z.infer<typeof linhaM02>;
export type LinhaM03 = z.infer<typeof linhaM03>;
export type LinhaM04 = z.infer<typeof linhaM04>;
export type LinhaM05 = z.infer<typeof linhaM05>;
export type LinhaM06 = z.infer<typeof linhaM06>;
export type LinhaM07 = z.infer<typeof linhaM07>;
export type LinhaM08 = z.infer<typeof linhaM08>;
export type LinhaM10 = z.infer<typeof linhaM10>;
export type LinhaM11 = z.infer<typeof linhaM11>;
export type LinhaM12 = z.infer<typeof linhaM12>;
/** Expressão em JSON Logic, como vem do pacote. */
export type Expressao = z.infer<ReturnType<typeof z.json>>;
