/**
 * Lacunas do texto do bloco (coluna lacunas do M02) e das cláusulas setoriais (marcadores [VAR-xxx] do M08).
 *
 * O M02 lista os marcadores do texto (separados por " | "), mas não diz qual variável preenche cada um. A ligação
 * vem do M05 (usada_em). O motor só preenche quando ela é certa: o bloco tem um marcador só e uma variável só o
 * cita. Nos demais casos o marcador fica como lacuna, com as variáveis candidatas, e nada é adivinhado.
 * Valor ausente também fica marcado: [[LACUNA VAR-xxx]].
 */
import { type Valor } from "../pacote/avaliador.ts";
import type { LinhaM02, LinhaM05 } from "../pacote/esquema.ts";
import { variavelDoId } from "../pacote/nomes.ts";
import { vazia } from "../wizard/checklist.ts";

const CITACAO_DE_BLOCO = /TR-[A-Za-z0-9]+(?:[.-][A-Za-z0-9]+)*/g;
const MARCADOR_DO_M08 = /\[(VAR-\d{3})(?:[^\][]*)\]/g;

export type LacunaDoTexto = {
  /** Bloco do M02 ou cláusula do M08. */
  trecho: string;
  /** Marcador como está no texto do modelo. */
  marcador: string;
  /** Variáveis que podem preencher o marcador (vazia quando o M05 não liga nenhuma ao bloco). */
  candidatas: string[];
  motivo: "sem_valor" | "sem_ligacao_unica";
};

/** Variáveis do M05 que citam cada bloco na coluna usada_em. */
export function variaveisPorBloco(m05: readonly LinhaM05[]): Map<string, string[]> {
  const mapa = new Map<string, string[]>();
  for (const linha of m05) {
    for (const [bloco] of linha.usada_em.matchAll(CITACAO_DE_BLOCO)) {
      const lista = mapa.get(bloco) ?? [];
      if (!lista.includes(linha.id)) mapa.set(bloco, [...lista, linha.id]);
    }
  }
  return mapa;
}

/** Valor como aparece no texto: número com vírgula decimal, lista separada por "; ". */
export function textoDoValor(valor: Valor): string {
  if (Array.isArray(valor)) return valor.map(textoDoValor).join("; ");
  if (typeof valor === "number") return String(valor).replace(".", ",");
  if (valor !== null && typeof valor === "object") return JSON.stringify(valor);
  return String(valor);
}

function marca(candidatas: string[]): string {
  return candidatas.length > 0 ? `[[LACUNA ${candidatas.join(", ")}]]` : "[[LACUNA]]";
}

/** Substitui a próxima ocorrência do marcador a partir de `inicio`; devolve o texto e onde continuar. */
function substituir(texto: string, marcador: string, por: string, inicio: number): [string, number] {
  const posicao = texto.indexOf(marcador, inicio);
  if (posicao < 0) return [texto, inicio];
  return [texto.slice(0, posicao) + por + texto.slice(posicao + marcador.length), posicao + por.length];
}

export function preencherBloco(
  linha: LinhaM02,
  texto: string,
  candidatasDoBloco: string[],
  globais: Record<string, Valor>,
): { texto: string; lacunas: LacunaDoTexto[]; preenchidas: string[] } {
  if (linha.lacunas.trim() === "") return { texto, lacunas: [], preenchidas: [] };
  const marcadores = linha.lacunas.split(" | ").filter((m) => m !== "");
  const ligacaoUnica = marcadores.length === 1 && candidatasDoBloco.length === 1;
  const lacunas: LacunaDoTexto[] = [];
  const preenchidas: string[] = [];
  let saida = texto;
  let cursor = 0;
  for (const marcador of marcadores) {
    if (ligacaoUnica) {
      const variavel = candidatasDoBloco[0];
      const valor = globais[variavelDoId(variavel)];
      if (!vazia(valor)) {
        [saida, cursor] = substituir(saida, marcador, textoDoValor(valor as Valor), cursor);
        preenchidas.push(variavel);
        continue;
      }
      lacunas.push({ trecho: linha.id, marcador, candidatas: [variavel], motivo: "sem_valor" });
      [saida, cursor] = substituir(saida, marcador, marca([variavel]), cursor);
      continue;
    }
    lacunas.push({ trecho: linha.id, marcador, candidatas: candidatasDoBloco, motivo: "sem_ligacao_unica" });
    [saida, cursor] = substituir(saida, marcador, marca(candidatasDoBloco), cursor);
  }
  return { texto: saida, lacunas, preenchidas };
}

/** Cláusula do M08: cada marcador [VAR-xxx: ...] com uma variável só é preenchido; o resto fica marcado. */
export function preencherClausula(
  id: string,
  texto: string,
  globais: Record<string, Valor>,
): { texto: string; lacunas: LacunaDoTexto[]; preenchidas: string[] } {
  const lacunas: LacunaDoTexto[] = [];
  const preenchidas: string[] = [];
  const saida = texto.replace(MARCADOR_DO_M08, (marcador: string, variavel: string) => {
    const outras = [...marcador.matchAll(/VAR-\d{3}/g)].map((m) => m[0]);
    if (outras.length > 1) {
      lacunas.push({ trecho: id, marcador, candidatas: outras, motivo: "sem_ligacao_unica" });
      return marca(outras);
    }
    const valor = globais[variavelDoId(variavel)];
    if (vazia(valor)) {
      lacunas.push({ trecho: id, marcador, candidatas: [variavel], motivo: "sem_valor" });
      return marca([variavel]);
    }
    preenchidas.push(variavel);
    return textoDoValor(valor as Valor);
  });
  return { texto: saida, lacunas, preenchidas };
}
