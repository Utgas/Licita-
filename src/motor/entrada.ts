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
  /** Metadados das expressões: textos_livres, importacao.*, checklist.* */
  metadados?: Record<string, Valor>;
  /** Dados da OM (cabeçalho, endereços, foro); fictícios nos testes. */
  om?: Record<string, Valor>;
};
