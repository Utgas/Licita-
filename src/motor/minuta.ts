/**
 * Monta a minuta do TR a partir da entrada de um processo (contrato do Marco 1).
 *
 * Ordem: prepararProcesso (checklist, itens, derivadas, wizard); blocos do M02 (condição, liga/desliga, filhos sem
 * pai, alternativas); numeração; lacunas; cláusulas do M08 no ponto de inserção; validações do M10; revisão do
 * checklist. Cada trecho guarda o ID do bloco ou da cláusula, a condição que o ligou e o pacote de onde veio.
 */
import type { AvisoDoMotor, Lacuna } from "./avisos.ts";
import type { EntradaProcesso } from "./entrada.ts";
import { type OrigemDoBloco, escolherBlocos, variaveisLidas } from "./montagem/blocos.ts";
import { type LacunaDoTexto, preencherBloco, preencherClausula, variaveisPorBloco } from "./montagem/lacunas.ts";
import { numerar, semNumeracaoDigitada } from "./montagem/numeracao.ts";
import { type Ancora, ancoraDaClausula, clausulasQueEntram } from "./montagem/setoriais.ts";
import type { Valor } from "./pacote/avaliador.ts";
import type { LinhaM02 } from "./pacote/esquema.ts";
import { type ProcessoPreparado, prepararProcesso } from "./processo.ts";
import { type ResultadoDasValidacoes, validar } from "./validacao/validacoes.ts";
import { type Revisao, type Sugestao, revisarChecklist } from "./wizard/checklist.ts";
import type { PerguntaPendente } from "./wizard/perguntas.ts";

export type OrigemDoPacote = { pacote: string; hash: string };

export type TrechoDaMinuta =
  | {
      tipo: "bloco";
      id: string;
      /** Número recalculado; null para subtítulo, tabela, cabeçalho e fecho. */
      numero: string | null;
      texto: string;
      formatacao: LinhaM02["formatacao"];
      secao: string;
      origem: OrigemDoBloco & OrigemDoPacote;
    }
  | {
      tipo: "clausula_setorial";
      id: string;
      tema: string;
      texto: string;
      pontoDeInsercao: string;
      ancora: Ancora;
      origem: { respostas: Record<string, Valor> } & OrigemDoPacote;
    };

export type Minuta = {
  pacote: OrigemDoPacote;
  trechos: TrechoDaMinuta[];
  /** IDs dos blocos do M02 que entraram, na ordem do modelo. */
  blocos: string[];
  /** IDs das cláusulas do M08 que entraram, na ordem do M08. */
  clausulasSetoriais: string[];
  /** Blocos com condição verdadeira que ficaram fora (desligados ou sem o pai). */
  blocosExcluidos: { id: string; motivo: "desligado" | "sem_pai" }[];
  bloqueiosGrupoAlternativas: string[];
  lacunasNoTexto: LacunaDoTexto[];
  /** Dados que faltaram antes da montagem (tipo incompatível vindo do checklist). */
  lacunasDeDados: Lacuna[];
  validacoes: ResultadoDasValidacoes;
  perguntasSemResposta: PerguntaPendente[];
  revisao: Revisao;
  sugestoes: Sugestao[];
  avisos: AvisoDoMotor[];
  /** Verdadeiro quando há bloqueio do M10, grupo de alternativas sem uma opção ou pergunta ao operador pendente. */
  bloqueada: boolean;
  /** Dados preparados (para conferência e para a simulação legível). */
  processo: ProcessoPreparado;
};

const PREFIXO_DO_ANEXO = "Anexo";

/** Posição (no array de trechos de blocos) depois da qual a cláusula entra. */
function posicaoDaAncora(ancora: Ancora, blocos: readonly LinhaM02[]): number {
  const ultimo = (filtro: (l: LinhaM02) => boolean) => blocos.reduce((achado, l, i) => (filtro(l) ? i : achado), -1);
  const doCorpo = (l: LinhaM02) => !l.secao.startsWith(PREFIXO_DO_ANEXO);
  if (ancora.tipo === "depois_do_bloco") {
    const inicio = blocos.findIndex((l) => l.id === ancora.bloco);
    let fim = inicio;
    while (fim + 1 < blocos.length && blocos[fim + 1].id.startsWith(`${ancora.bloco}.`)) fim++;
    return fim;
  }
  if (ancora.tipo === "fim_da_secao") {
    const posicao = ultimo((l) => doCorpo(l) && new RegExp(`^TR-${ancora.secao}(?:[.]|$)`).test(l.id));
    if (posicao >= 0) return posicao;
  }
  return ultimo(doCorpo);
}

export function gerarMinuta(entrada: EntradaProcesso): Minuta {
  const { pacote } = entrada;
  const { M02, M04, M05, M08, M10, M11 } = pacote.matrizes;
  const origemDoPacote: OrigemDoPacote = { pacote: pacote.pacote, hash: entrada.hashDoPacote };
  const processo = prepararProcesso(entrada);
  const { dados, globais } = processo;

  const escolha = escolherBlocos(M02, M04, dados);
  const linhas = escolha.blocos.map((b) => b.linha);
  const numeros = numerar(linhas);
  const candidatas = variaveisPorBloco(M05);
  const lacunasNoTexto: LacunaDoTexto[] = [];

  const trechosDeBloco: TrechoDaMinuta[] = escolha.blocos.map(({ linha, origem }) => {
    const preenchido = preencherBloco(linha, semNumeracaoDigitada(linha.texto_literal), candidatas.get(linha.id) ?? [], globais);
    lacunasNoTexto.push(...preenchido.lacunas);
    return {
      tipo: "bloco",
      id: linha.id,
      numero: numeros.get(linha.id) ?? null,
      texto: preenchido.texto,
      formatacao: linha.formatacao,
      secao: linha.secao,
      origem: { ...origem, ...origemDoPacote },
    };
  });

  const naMinuta = new Set(linhas.map((l) => l.id));
  const clausulas = clausulasQueEntram(M08, dados);
  const depoisDe = new Map<number, TrechoDaMinuta[]>();
  for (const clausula of clausulas) {
    const ancora = ancoraDaClausula(clausula, naMinuta);
    const preenchida = preencherClausula(clausula.id, clausula.texto_proposto, globais);
    lacunasNoTexto.push(...preenchida.lacunas);
    const respostas: Record<string, Valor> = {};
    for (const nome of variaveisLidas(clausula.condicao_expr)) if (nome !== "itens") respostas[nome] = dados[nome] ?? null;
    const posicao = posicaoDaAncora(ancora, linhas);
    depoisDe.set(posicao, [
      ...(depoisDe.get(posicao) ?? []),
      {
        tipo: "clausula_setorial",
        id: clausula.id,
        tema: clausula.tema,
        texto: preenchida.texto,
        pontoDeInsercao: clausula.ponto_insercao,
        ancora,
        origem: { respostas, ...origemDoPacote },
      },
    ]);
  }
  const trechos: TrechoDaMinuta[] = [...(depoisDe.get(-1) ?? [])];
  trechosDeBloco.forEach((trecho, i) => trechos.push(trecho, ...(depoisDe.get(i) ?? [])));

  const validacoes = validar(M10, dados);
  const revisao = revisarChecklist(M11, dados, entrada.revisoes_confirmadas ?? []);
  const bloqueada =
    validacoes.disparadas.some((v) => v.tipo === "BLOQUEIO") ||
    escolha.bloqueiosGrupoAlternativas.length > 0 ||
    revisao.perguntasAoOperador.length > 0;

  return {
    pacote: origemDoPacote,
    trechos,
    blocos: linhas.map((l) => l.id),
    clausulasSetoriais: clausulas.map((c) => c.id),
    blocosExcluidos: escolha.excluidos,
    bloqueiosGrupoAlternativas: escolha.bloqueiosGrupoAlternativas,
    lacunasNoTexto,
    lacunasDeDados: processo.lacunas,
    validacoes,
    perguntasSemResposta: processo.wizard.pendentes,
    revisao,
    sugestoes: processo.sugestoes,
    avisos: processo.avisos,
    bloqueada,
    processo,
  };
}
