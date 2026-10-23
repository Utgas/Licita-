/**
 * Quais blocos do M02 entram na minuta (tarefa do Marco 1, passo 6; README das matrizes).
 *
 * - Um bloco entra quando a condicao_expr dele é verdadeira e nenhuma pergunta do M04 o desliga (desliga_expr):
 *   desligar vence ligar. A condicao_expr do M02 já traz "alguma condição que liga e nenhuma que desliga";
 *   o motor confere os desliga_expr de novo para que um bloco desligado nunca entre.
 * - Ficam fora os separadores "OU" (item_modelo = OU) e tudo com condicao_expr false (cabeçalho do modelo e o que
 *   o M02 marca como "não entra na minuta").
 * - Filho sem o pai não entra: pai é o ID sem o último segmento numérico, de letra ou romano (TR-4.41.1 tem pai
 *   TR-4.41), quando esse ID existe no M02; vale em cascata, na ordem do M02.
 * - Grupo de alternativas ativo (grupo_ativo_expr verdadeira, ou vazia): exatamente uma opção entra; nenhuma ou
 *   mais de uma vai para os bloqueios.
 */
import { type Valor, avaliar, verdadeiro } from "../pacote/avaliador.ts";
import type { LinhaM02, LinhaM04 } from "../pacote/esquema.ts";

const SEPARADOR = "OU";
const PAI = /^(TR-(?:AI-)?[\d.]+?)\.(\d+|[a-z]|[IVX]+)$/;

/** Pai do bloco no M02, ou undefined. */
export function paiDoBloco(id: string, ids: ReadonlySet<string>): string | undefined {
  const pai = PAI.exec(id)?.[1];
  return pai !== undefined && ids.has(pai) ? pai : undefined;
}

/** Código do grupo de alternativas: "GA-01 (natureza do bem)" -> "GA-01". */
export function codigoDoGrupo(grupo: string): string {
  return grupo.split(" ")[0];
}

/** Nomes das variáveis lidas por uma expressão (para a origem do bloco). */
export function variaveisLidas(expressao: unknown, saida = new Set<string>()): Set<string> {
  if (Array.isArray(expressao)) {
    for (const e of expressao) variaveisLidas(e, saida);
  } else if (expressao !== null && typeof expressao === "object") {
    for (const [operador, argumento] of Object.entries(expressao)) {
      if (operador === "var") {
        const nome = Array.isArray(argumento) ? argumento[0] : argumento;
        if (typeof nome === "string" && nome !== "") saida.add(nome.split(".")[0]);
      } else {
        variaveisLidas(argumento, saida);
      }
    }
  }
  return saida;
}

/** Blocos ligados e desligados por cada pergunta do M04 (resultado de liga_expr e desliga_expr). */
export function efeitosDoWizard(m04: readonly LinhaM04[], dados: Record<string, Valor>) {
  const ligadoPor = new Map<string, string[]>();
  const desligadoPor = new Map<string, string[]>();
  const registrar = (mapa: Map<string, string[]>, expressao: unknown, pergunta: string) => {
    if (expressao === null || expressao === false) return;
    const blocos = avaliar(expressao, dados);
    for (const bloco of Array.isArray(blocos) ? blocos : []) {
      if (typeof bloco === "string") mapa.set(bloco, [...(mapa.get(bloco) ?? []), pergunta]);
    }
  };
  for (const linha of m04) {
    registrar(ligadoPor, linha.liga_expr, linha.id);
    registrar(desligadoPor, linha.desliga_expr, linha.id);
  }
  return { ligadoPor, desligadoPor };
}

export type OrigemDoBloco = {
  /** Perguntas do M04 cujo liga_expr inclui o bloco. */
  ligadoPor: string[];
  /** Variáveis lidas pela condicao_expr e o valor de cada uma (itens fica de fora: é a lista inteira). */
  respostas: Record<string, Valor>;
};

export type BlocoEscolhido = { linha: LinhaM02; origem: OrigemDoBloco };

export type Exclusao = { id: string; motivo: "desligado" | "sem_pai" };

export type EscolhaDosBlocos = {
  blocos: BlocoEscolhido[];
  /** Blocos com condição verdadeira que ficaram fora (desligados ou sem o pai). */
  excluidos: Exclusao[];
  /** Códigos dos grupos de alternativas ativos sem exatamente uma opção (GA-01...), em ordem. */
  bloqueiosGrupoAlternativas: string[];
};

export function escolherBlocos(m02: readonly LinhaM02[], m04: readonly LinhaM04[], dados: Record<string, Valor>): EscolhaDosBlocos {
  const { ligadoPor, desligadoPor } = efeitosDoWizard(m04, dados);
  const ids = new Set(m02.map((l) => l.id));
  const dentro = new Set<string>();
  const excluidos: Exclusao[] = [];

  for (const linha of m02) {
    if (linha.item_modelo === SEPARADOR || linha.condicao_expr === null || linha.condicao_expr === false) continue;
    if (!verdadeiro(avaliar(linha.condicao_expr, dados))) continue;
    if (desligadoPor.has(linha.id)) {
      excluidos.push({ id: linha.id, motivo: "desligado" });
      continue;
    }
    dentro.add(linha.id);
  }
  // Filho sem o pai, em cascata na ordem do M02.
  for (const linha of m02) {
    if (!dentro.has(linha.id)) continue;
    const pai = paiDoBloco(linha.id, ids);
    if (pai !== undefined && !dentro.has(pai)) {
      dentro.delete(linha.id);
      excluidos.push({ id: linha.id, motivo: "sem_pai" });
    }
  }

  const ativos = new Set<string>();
  const opcoes = new Map<string, Set<string>>();
  for (const linha of m02) {
    if (linha.grupo_alternativa === "") continue;
    const grupo = codigoDoGrupo(linha.grupo_alternativa);
    if (linha.grupo_ativo_expr === null || verdadeiro(avaliar(linha.grupo_ativo_expr, dados))) ativos.add(grupo);
    if (linha.opcao !== "" && dentro.has(linha.id)) opcoes.set(grupo, (opcoes.get(grupo) ?? new Set()).add(linha.opcao));
  }
  const bloqueiosGrupoAlternativas = [...ativos].filter((g) => (opcoes.get(g)?.size ?? 0) !== 1).sort();

  const blocos = m02
    .filter((l) => dentro.has(l.id))
    .map((linha) => {
      const respostas: Record<string, Valor> = {};
      for (const nome of variaveisLidas(linha.condicao_expr)) {
        if (nome !== "itens") respostas[nome] = dados[nome] ?? null;
      }
      return { linha, origem: { ligadoPor: ligadoPor.get(linha.id) ?? [], respostas } };
    });
  return { blocos, excluidos, bloqueiosGrupoAlternativas };
}
