/**
 * Avisos que o próprio motor gera (diferentes das validações do M10, que vêm do pacote).
 * A mensagem é técnica e descreve o que aconteceu com o dado; nunca traz texto jurídico.
 */
export type CodigoDeAviso =
  /** Um cálculo do M05 encontrou valor ausente, texto no lugar de número ou divisão impossível: o resultado virou lacuna. */
  | "CALCULO_SEM_DADO"
  /** A entrada trazia um valor diferente do calculado; vale o calculado. */
  | "VALOR_INFORMADO_SUBSTITUIDO"
  /** O checklist indica um valor diferente do que a equipe respondeu; vale a resposta da equipe. */
  | "EQUIPE_DIVERGE_DO_CHECKLIST"
  /** Duas perguntas do checklist preenchem o mesmo destino com valores diferentes. */
  | "CONFLITO_NO_CHECKLIST"
  /** O checklist trouxe um valor que não bate com o tipo do M05; não foi convertido e virou lacuna. */
  | "TIPO_INCOMPATIVEL"
  /** Resposta para uma pergunta desligada no pacote (depende_de_expr = false); foi descartada. */
  | "PERGUNTA_DESLIGADA";

export type AvisoDoMotor = {
  codigo: CodigoDeAviso;
  mensagem: string;
  /** De onde veio: ID da regra (VAR-113...) e, quando for o caso, o número do item. */
  origem: { regra: string; item?: number };
};

/** Dado que falta para a minuta: aparece marcado no texto e pede a informação. */
export type Lacuna = {
  /** Variável que ficou sem valor (VAR_060) ou destino de item (itens.garantia_minima_meses). */
  destino: string;
  item?: number;
  motivo: string;
  /** Regra ou pergunta de onde o dado viria (CK-C-12.1, VAR-119...). */
  origem: string;
};
