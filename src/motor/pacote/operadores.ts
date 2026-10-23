/**
 * Operadores de JSON Logic aceitos nas matrizes (matrizes/v1/README.md, P31).
 * O compilador recusa qualquer outro, e o avaliador só implementa estes.
 */

/** Aceitos em qualquer coluna *_expr. */
export const OPERADORES_PERMITIDOS = ["var", "==", "!=", "!", "!!", "and", "or", "if", "in", "merge", "some", "none", "<=", ">"] as const;

/** Aceitos só nas colunas de cálculo (decisão P31): conta e acumulação. */
export const OPERADORES_DE_CALCULO = ["reduce", "+", "-", "*", "/", "%"] as const;

/** Colunas onde os operadores de cálculo valem, no formato "matriz.coluna". */
export const COLUNAS_DE_CALCULO = ["M04.calculo_expr", "M05.calculo_expr"] as const;

export type Operador = (typeof OPERADORES_PERMITIDOS)[number] | (typeof OPERADORES_DE_CALCULO)[number];
