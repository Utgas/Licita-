/**
 * Avisos que o próprio motor gera (diferentes das validações do M10, que vêm do pacote).
 * A mensagem é técnica e descreve o que aconteceu com o dado; nunca traz texto jurídico.
 */
export type CodigoDeAviso =
  /** Um cálculo do M05 encontrou valor ausente, texto no lugar de número ou divisão impossível: o resultado virou lacuna. */
  | "CALCULO_SEM_DADO"
  /** A entrada trazia um valor diferente do calculado; vale o calculado. */
  | "VALOR_INFORMADO_SUBSTITUIDO";

export type AvisoDoMotor = {
  codigo: CodigoDeAviso;
  mensagem: string;
  /** De onde veio: ID da regra (VAR-113...) e, quando for o caso, o número do item. */
  origem: { regra: string; item?: number };
};
