/**
 * Entrada do motor: o pacote e as respostas de um processo.
 *
 * As chaves usam o nome de variável das expressões (README das matrizes): WZ_07, CK_C_14_2 (texto da caixa de
 * resposta em CK_C_14_2_texto), VAR_001. Assim a entrada é lida pelas expressões sem tradução.
 */
import type { Valor } from "./pacote/avaliador.ts";
import type { Pacote } from "./pacote/esquema.ts";

/** Um item da tabela de itens, com os atributos do M05 (tabela_itens.*). */
export type ItemDeEntrada = {
  numero: number;
  /** Respostas de perguntas do checklist marcadas por_item = S, ligadas a este item. */
  respostas_por_item?: Record<string, Valor>;
  [atributo: string]: Valor | Record<string, Valor> | undefined;
};

/**
 * O que a leitura do checklist preenchido produz (Marco 2; nos testes, preenchido à mão).
 * Descrição no README das matrizes (Fase 11, decisão 0009). As respostas em si vão em `checklist`, com os
 * sufixos _texto (texto da caixa de resposta) e _numero (número lido do "Outro", por exemplo CK_C_12_1_numero).
 */
export type LeituraDoChecklist = {
  /** Verdadeiro quando o checklist de consumo foi entregue. */
  consumo?: boolean;
  /** Verdadeiro quando o checklist de permanentes foi entregue. */
  permanentes?: boolean;
  /** IDs (CK-C-3.3...) das perguntas com mais de uma opção marcada. */
  marcas_multiplas?: string[];
  /** IDs das perguntas por item respondidas uma vez só para todos os itens. */
  resposta_unica_por_item?: string[];
  /** IDs das perguntas em que a leitura achou respostas divergentes (por exemplo, caixa e texto). */
  divergencias_leitura?: string[];
  /** Pendências da leitura (pergunta sem marcação clara, duas opções em UNICA, resposta fora da caixa): VAL-037. */
  leitura_pendencias?: string[];
  /** Perguntas que a leitura não achou respondidas. */
  sem_resposta?: string[];
  /** SHA-256 do modelo em branco do checklist usado e o registrado no M11: VAL-036. */
  sha256_modelo?: string;
  sha256_m11?: string;
};

export type Metadados = {
  textos_livres?: Valor;
  importacao?: Record<string, Valor>;
  checklist?: LeituraDoChecklist;
  [outro: string]: Valor | LeituraDoChecklist | undefined;
};

export type EntradaProcesso = {
  pacote: Pacote;
  /** SHA-256 do pacote.json, gravado ao lado dele (pacote.sha256). */
  hashDoPacote: string;
  /** Respostas do checklist: CK_C_12_1, CK_C_12_1_texto... MULTIPLA vira lista. */
  checklist: Record<string, Valor>;
  /** Respostas da equipe no wizard: WZ_01... MULTIPLA vira lista. */
  wizard: Record<string, Valor>;
  itens: ItemDeEntrada[];
  /** Variáveis do M05 informadas: VAR_057... */
  variaveis: Record<string, Valor>;
  /** Metadados das expressões: textos_livres, importacao.* e checklist.* (leitura do Word). */
  metadados?: Metadados;
  /**
   * Perguntas do checklist (IDs CK) cuja revisão o operador já confirmou: a resposta destacada foi conferida
   * e vale como está. Pergunta ao operador sem confirmação bloqueia a minuta.
   */
  revisoes_confirmadas?: string[];
  /** Dados da OM (cabeçalho, endereços, foro); fictícios nos testes. */
  om?: Record<string, Valor>;
};
