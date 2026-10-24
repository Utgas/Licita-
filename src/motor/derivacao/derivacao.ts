/**
 * Derivação do ETP para o TR (M06; Marco 3, passo 4; decisão 0015).
 *
 * O ETP e o TR saem das mesmas respostas, então o TR não contradiz o ETP: a derivação é rastreabilidade. Para cada
 * bloco do TR na minuta que o M06 liga a campos do ETP, diz quais campos, VAR e WZ ele repete e se o campo do ETP
 * está com conteúdo. Bloco presente com campo vazio no ETP é aviso: o M06 manda rever o ETP antes ("se o dado mudou,
 * o ETP é revisto antes").
 */
import type { Etp, SituacaoDoCampo } from "../montagem/etp.ts";
import { camposCitados } from "../montagem/etp.ts";
import type { Minuta } from "../minuta.ts";
import type { Valor } from "../pacote/avaliador.ts";
import type { LinhaM06, Pacote } from "../pacote/esquema.ts";
import { variavelDoId } from "../pacote/nomes.ts";

/** Campo sem conteúdo próprio: o TR que o repete remete a um ETP vazio. */
const SEM_CONTEUDO = new Set<SituacaoDoCampo>(["vazio"]);

export type BlocoDerivado = {
  /** Bloco do M02 (ou cláusula, quando o M06 a citar). */
  bloco: string;
  /** Número do bloco na minuta; null em subtítulo e tabela. */
  numero: string | null;
  campos: string[];
  /** VAR que o M06 diz que o bloco repete, com o valor do processo (o mesmo no ETP e no TR). */
  variaveis: { regra: string; valor: Valor }[];
  perguntas: string[];
  classeDeOrigem: string;
  regra: string;
  situacao: "derivado" | "campo_vazio";
  /** Campos do ETP sem conteúdo que o bloco repete. */
  camposVazios: string[];
};

export type Derivacao = {
  blocos: BlocoDerivado[];
  /** Campo do ETP -> blocos do TR na minuta que o repetem, na ordem da minuta. */
  porCampo: Record<string, { bloco: string; numero: string | null }[]>;
};

function lista(texto: string, padrao: RegExp): string[] {
  return [...new Set(texto.match(padrao) ?? [])];
}

export function derivarEtpParaTr(pacote: Pacote, minuta: Minuta, etp: Etp): Derivacao {
  const m06 = new Map<string, LinhaM06>(pacote.matrizes.M06.map((l) => [l.bloco_tr, l]));
  const situacao = new Map(etp.campos.map((c) => [c.id, c.situacao]));
  const blocos: BlocoDerivado[] = [];
  const porCampo: Derivacao["porCampo"] = {};
  for (const trecho of minuta.trechos) {
    const linha = m06.get(trecho.id);
    if (!linha) continue;
    const campos = camposCitados(linha.campos_etp).filter((c) => situacao.has(c));
    if (campos.length === 0) continue;
    const camposVazios = campos.filter((c) => SEM_CONTEUDO.has(situacao.get(c) as SituacaoDoCampo));
    blocos.push({
      bloco: trecho.id,
      numero: trecho.numero,
      campos,
      variaveis: lista(linha.variaveis, /VAR-\d{3}/g).map((regra) => ({ regra, valor: minuta.processo.globais[variavelDoId(regra)] ?? null })),
      perguntas: lista(linha.perguntas_wz, /WZ-\d{2}/g),
      classeDeOrigem: linha.classe_origem,
      regra: linha.regra_derivacao,
      situacao: camposVazios.length ? "campo_vazio" : "derivado",
      camposVazios,
    });
    for (const campo of campos) (porCampo[campo] ??= []).push({ bloco: trecho.id, numero: trecho.numero });
  }
  return { blocos, porCampo };
}
