/** Regras de senha (decisão 0012): senha provisória gerada pelo sistema e senha nova escolhida pelo usuário. */
import { randomInt } from "node:crypto";

export const TAMANHO_MINIMO = 10;

// Sem caracteres que se confundem ao ditar ou ler (0/O, 1/l/I).
const LETRAS = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ";
const DIGITOS = "23456789";

/** Senha provisória de 12 caracteres, com letras e dígitos, para a TI entregar ao usuário. */
export function gerarSenhaProvisoria(): string {
  const todos = LETRAS + DIGITOS;
  const caracteres = Array.from({ length: 11 }, () => todos[randomInt(todos.length)]);
  caracteres.splice(randomInt(12), 0, DIGITOS[randomInt(DIGITOS.length)]);
  return caracteres.join("");
}

/** Problema da senha nova, ou null quando ela serve. */
export function problemaDaSenhaNova(nova: string, confirmacao: string, atual: string): string | null {
  if (nova.length < TAMANHO_MINIMO) return `A senha nova precisa ter pelo menos ${TAMANHO_MINIMO} caracteres.`;
  if (!/[A-Za-z]/.test(nova) || !/[0-9]/.test(nova)) return "A senha nova precisa ter letras e números.";
  if (nova !== confirmacao) return "A confirmação não é igual à senha nova.";
  if (nova === atual) return "A senha nova precisa ser diferente da atual.";
  return null;
}
