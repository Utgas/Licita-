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
import { type LacunaDoTexto, Montagem, type ValorPadrao, pontuarSeries } from "./montagem/lacunas.ts";
import { type LinhaNumeravel, numerar, semNumeracaoDigitada } from "./montagem/numeracao.ts";
import { type Insercao, clausulasQueEntram, insercaoDaClausula } from "./montagem/setoriais.ts";
import type { Valor } from "./pacote/avaliador.ts";
import type { LinhaM02, Pacote } from "./pacote/esquema.ts";
import { variavelDoId } from "./pacote/nomes.ts";
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
      /** Número no nível indicado pelo M08 (nivel); null quando a cláusula vai para o fim do corpo. */
      numero: string | null;
      pontoDeInsercao: string;
      insercao: Insercao;
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
  /** Valores que entraram pelo padrão do mapa, sem terem sido informados (marcados no texto com [[PADRÃO: ...]]). */
  valoresPadrao: ValorPadrao[];
  /** Blocos de série (lista_blocos) que saíram por não terem elemento. */
  blocosOmitidos: string[];
  /** Cláusulas do M08 com nivel PREENCHE_BLOCO: não entram como texto, preenchem o bloco indicado. */
  clausulasQuePreenchemBloco: { id: string; bloco: string }[];
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
const PREFIXO_DA_ASSINATURA = "TR-ASSIN";
const NUMERO_DO_ITEM = /^(\d+(?:\.\d+)*)/;

/** Nível numérico do item_modelo ("5.4." = 2); 0 quando não é item numerado. */
function nivelDoItem(itemModelo: string): number {
  const numero = NUMERO_DO_ITEM.exec(itemModelo.trim())?.[1];
  return numero ? numero.split(".").length : 0;
}

/** item_modelo de mentira, só com a quantidade de níveis, para a numeração da cláusula. */
function itemModeloDoNivel(nivel: number): string {
  if (nivel === 0) return "";
  const numero = Array.from({ length: nivel }, () => "0").join(".");
  return nivel <= 2 ? `${numero}.` : numero;
}

/** Variável da expressão -> ID da regra (VAR_034 -> VAR-034, CK_C_12_1 -> CK-C-12.1), para a marca de lacuna. */
function nomesDasRegras(pacote: Pacote): (variavel: string) => string {
  const { M04, M05, M11 } = pacote.matrizes;
  const mapa = new Map<string, string>();
  for (const { id } of [...M04, ...M05, ...M11]) mapa.set(variavelDoId(id), id);
  return (variavel) => mapa.get(variavel) ?? variavel;
}

type Posicionado = { trecho: TrechoDaMinuta; linha: LinhaNumeravel; ancora?: string };

export function gerarMinuta(entrada: EntradaProcesso): Minuta {
  const { pacote } = entrada;
  const { M02, M04, M08, M10, M11 } = pacote.matrizes;
  const origemDoPacote: OrigemDoPacote = { pacote: pacote.pacote, hash: entrada.hashDoPacote };
  const processo = prepararProcesso(entrada);
  const { dados } = processo;

  const escolha = escolherBlocos(M02, M04, dados);
  const montagem = new Montagem(dados, nomesDasRegras(pacote));
  const lacunasNoTexto: LacunaDoTexto[] = [];
  const blocosOmitidos: string[] = [];

  // Texto de cada bloco; bloco de série sem elemento sai.
  const textos = new Map<string, string>();
  const presentes: { linha: LinhaM02; origem: OrigemDoBloco }[] = [];
  for (const { linha, origem } of escolha.blocos) {
    const montado = montagem.bloco(linha, semNumeracaoDigitada(linha.texto_literal));
    if (montado.omitido) {
      blocosOmitidos.push(linha.id);
      continue;
    }
    textos.set(linha.id, montado.texto);
    lacunasNoTexto.push(...montado.lacunas);
    presentes.push({ linha, origem });
  }
  pontuarSeries(textos, M02);

  const sequencia: Posicionado[] = presentes.map(({ linha, origem }) => ({
    linha,
    trecho: {
      tipo: "bloco",
      id: linha.id,
      numero: null,
      texto: textos.get(linha.id) as string,
      formatacao: linha.formatacao,
      secao: linha.secao,
      origem: { ...origem, ...origemDoPacote },
    },
  }));

  // Cláusulas do M08 no ponto de inserção, na ordem do M08.
  const naMinuta = new Set(presentes.map((p) => p.linha.id));
  const clausulas = clausulasQueEntram(M08, dados);
  const clausulasQuePreenchemBloco: Minuta["clausulasQuePreenchemBloco"] = [];
  for (const clausula of clausulas) {
    const insercao = insercaoDaClausula(clausula, naMinuta);
    if (insercao.tipo === "preenche_bloco") {
      clausulasQuePreenchemBloco.push({ id: clausula.id, bloco: insercao.bloco });
      continue;
    }
    const montado = montagem.clausula(clausula);
    lacunasNoTexto.push(...montado.lacunas);
    const respostas: Record<string, Valor> = {};
    for (const nome of variaveisLidas(clausula.condicao_expr)) if (nome !== "itens") respostas[nome] = dados[nome] ?? null;
    const trecho: TrechoDaMinuta = {
      tipo: "clausula_setorial",
      id: clausula.id,
      tema: clausula.tema,
      texto: montado.texto,
      numero: null,
      pontoDeInsercao: clausula.ponto_insercao,
      insercao,
      origem: { respostas, ...origemDoPacote },
    };
    if (insercao.tipo === "fim_do_corpo") {
      const ultimo = sequencia.reduce((achado, p, i) => (p.trecho.tipo === "bloco" && !p.linha.secao.startsWith(PREFIXO_DO_ANEXO) && !p.linha.id.startsWith(PREFIXO_DA_ASSINATURA) ? i : achado), -1);
      sequencia.splice(ultimo + 1, 0, { trecho, linha: { id: clausula.id, item_modelo: "", secao: "" } });
      continue;
    }
    const indice = sequencia.findIndex((p) => p.linha.id === insercao.bloco);
    const ancora = sequencia[indice].linha;
    const nivel = nivelDoItem(ancora.item_modelo);
    // Depois do bloco, dos subitens dele (pelo ID ou por nível mais fundo na mesma seção) e das cláusulas já postas ali.
    let fim = indice;
    while (fim + 1 < sequencia.length) {
      const seguinte = sequencia[fim + 1];
      const subitem =
        seguinte.linha.id.startsWith(`${insercao.bloco}.`) ||
        (seguinte.linha.secao === ancora.secao && nivel > 0 && nivelDoItem(seguinte.linha.item_modelo) > nivel) ||
        seguinte.ancora === insercao.bloco;
      if (!subitem) break;
      fim++;
    }
    const nivelDaClausula = nivel === 0 ? 0 : insercao.nivel === "SUBITEM" ? nivel + 1 : nivel;
    sequencia.splice(fim + 1, 0, { trecho, ancora: insercao.bloco, linha: { id: clausula.id, item_modelo: itemModeloDoNivel(nivelDaClausula), secao: ancora.secao } });
  }

  // Numeração refeita depois das exclusões, com as cláusulas no lugar delas.
  const numeros = numerar(sequencia.map((p) => p.linha));
  const trechos = sequencia.map((p) => ({ ...p.trecho, numero: numeros.get(p.linha.id) ?? null }) as TrechoDaMinuta);

  const validacoes = validar(M10, dados);
  const revisao = revisarChecklist(M11, dados, entrada.revisoes_confirmadas ?? []);
  const bloqueada =
    validacoes.disparadas.some((v) => v.tipo === "BLOQUEIO") ||
    escolha.bloqueiosGrupoAlternativas.length > 0 ||
    revisao.perguntasAoOperador.length > 0;

  return {
    pacote: origemDoPacote,
    trechos,
    blocos: escolha.blocos.map((b) => b.linha.id),
    clausulasSetoriais: clausulas.map((c) => c.id),
    blocosExcluidos: escolha.excluidos,
    bloqueiosGrupoAlternativas: escolha.bloqueiosGrupoAlternativas,
    lacunasNoTexto,
    valoresPadrao: montagem.padroes,
    blocosOmitidos,
    clausulasQuePreenchemBloco,
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
