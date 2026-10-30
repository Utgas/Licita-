/**
 * Monta parágrafos e tabelas a partir de texto solto com posição na página (decisão 0017). Serve ao PDF e ao Word
 * que saiu de um conversor de PDF, em que cada pedaço de texto é uma caixa de texto posicionada:
 *
 * - as linhas são remontadas pela posição (mesma altura na página, da esquerda para a direita), porque a caixa ☐
 *   costuma vir fora da ordem do texto;
 * - cabeçalho e rodapé que se repetem em todas as páginas saem;
 * - o que vem depois de "Resposta:", até a próxima pergunta, é a caixa de resposta;
 * - linhas com caixa de seleção seguidas viram um parágrafo só (opção que quebra de linha), e o enunciado que
 *   quebra de linha é juntado até o "?" ou ":" final;
 * - no cabeçalho e nas linhas com mais de um trecho separado por espaço largo (a tabela da 1.4), cada trecho é uma
 *   célula; as demais linhas são parágrafos.
 *
 * Posição em pontos, com y crescendo para cima (como no PDF).
 */
import type { Bloco } from "./docx.ts";

export type Trecho = { x: number; fim: number; texto: string };
export type Linha = { pagina: number; y: number; altura: number; trechos: Trecho[] };

/** Espaço maior que isto (em pontos) separa células; menor, só palavras. */
const SEPARADOR = 15;
const TOLERANCIA_Y = 2;
/** Distância máxima entre duas linhas do mesmo parágrafo; mais que isso é outra linha da tabela. */
const ENTRELINHA = 9;
/** Rótulo de célula é curto ("Nome", "OMS requisitante"); linha mais larga que isto é texto corrido que quebrou. */
const ROTULO = 150;

const SECAO = /^\d{1,2}\.\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ]/;
const PERGUNTA = /^\d{1,2}\.\d{1,2}\.\s/;
const CAIXA = /☐|☒|☑|✓|✔|✗|✘|■|▣|\[\s*[xX]\s*\]|\(\s*[xX]\s*\)/;

/** Pedaços de texto de uma página agrupados em linhas (mesma altura), de cima para baixo e da esquerda para a direita. */
export function linhasDaPagina(pagina: number, altura: number, itens: { x: number; y: number; largura: number; texto: string }[]): Linha[] {
  const linhas: Linha[] = [];
  for (const item of itens) {
    if (item.texto === "") continue;
    let linha = linhas.find((l) => Math.abs(l.y - item.y) <= TOLERANCIA_Y);
    if (!linha) linhas.push((linha = { pagina, y: item.y, altura, trechos: [] }));
    linha.trechos.push({ x: item.x, fim: item.x + item.largura, texto: item.texto });
  }
  for (const l of linhas) l.trechos.sort((a, b) => a.x - b.x);
  return linhas.sort((a, b) => b.y - a.y);
}

type Celula = { x: number; fim: number; texto: string };

/** Células de uma linha: o texto é juntado em ordem e um espaço largo (ou um item só de espaço largo) separa células. */
function celulas(linha: Linha): Celula[] {
  const saida: Celula[] = [];
  let atual: Celula | null = null;
  let fim = -Infinity;
  for (const t of linha.trechos) {
    const vazio = t.texto.trim() === "";
    if (vazio && t.fim - t.x > SEPARADOR) {
      if (atual) saida.push(atual);
      atual = null;
      fim = t.fim;
      continue;
    }
    if (atual && t.x - fim > SEPARADOR) {
      saida.push(atual);
      atual = null;
    } else if (atual && t.x - fim > 1 && !/\s$/.test(atual.texto) && !/^\s/.test(t.texto)) {
      atual.texto += " ";
    }
    if (!atual) atual = { x: t.x, fim: t.fim, texto: "" };
    atual.texto += t.texto;
    fim = Math.max(fim, t.fim);
    atual.fim = fim;
  }
  if (atual) saida.push(atual);
  return saida.map((c) => ({ ...c, texto: c.texto.replace(/\s+/g, " ").trim() })).filter((c) => c.texto);
}

const textoDaLinha = (l: Linha) => celulas(l).map((c) => c.texto).join(" ");

/**
 * Cabeçalho e rodapé: texto na margem de cima ou de baixo (5% da página) que se repete na mesma altura em pelo
 * menos metade das páginas, com os números trocados (o "Página 2").
 */
function repetidas(linhas: Linha[]): Set<string> {
  const paginas = new Set(linhas.map((l) => l.pagina)).size;
  if (paginas < 2) return new Set();
  const contagem = new Map<string, Set<number>>();
  for (const l of linhas) {
    if (l.y < l.altura * 0.95 && l.y > l.altura * 0.05) continue;
    const k = chaveDeRepeticao(l);
    contagem.set(k, (contagem.get(k) ?? new Set()).add(l.pagina));
  }
  return new Set([...contagem].filter(([, p]) => p.size >= Math.max(2, paginas / 2)).map(([k]) => k));
}

const chaveDeRepeticao = (l: Linha) => `${Math.round(l.y)}|${textoDaLinha(l).replace(/\d+/g, "#")}`;

type LinhaDeRotulos = { linha: string[][]; xs: number[]; pagina: number; y: number };

/** Coluna de cada célula da linha embaixo dos rótulos, ou null se ela não é continuação deles (longe ou fora das colunas). */
function colunasDosRotulos(rotulos: LinhaDeRotulos, l: Linha & { celulas: Celula[] }): number[] | null {
  if (rotulos.pagina !== l.pagina || rotulos.y - l.y > ENTRELINHA) return null;
  const colunas = l.celulas.map((c) => rotulos.xs.findIndex((x) => Math.abs(x - c.x) <= 3));
  return colunas.every((i) => i >= 0) ? colunas : null;
}

/** Blocos das linhas de todas as páginas, na ordem, no mesmo formato da leitura do Word. Sem texto: lista vazia. */
export function blocosDeLinhas(todas: Linha[]): Bloco[] {
  const fora = repetidas(todas);
  const linhas = todas.filter((l) => !fora.has(chaveDeRepeticao(l))).map((l) => ({ ...l, celulas: celulas(l) })).filter((l) => l.celulas.length > 0);

  const blocos: Bloco[] = [];
  // Caixa de resposta aberta: o texto e a margem do "Resposta:" (o que começa mais à direita é conteúdo da caixa).
  let caixa: { textos: string[]; margem: number } | null = null;
  // Linha de rótulos anterior, para juntar o valor escrito embaixo do rótulo na mesma célula.
  let tabela = null as LinhaDeRotulos | null;
  let dentroDoCorpo = false;
  const fecharCaixa = () => {
    if (caixa) blocos.push({ tipo: "tbl", linhas: [[[caixa.textos.join("\n")]]] });
    caixa = null;
  };
  for (const l of linhas) {
    const texto = l.celulas.map((c) => c.texto).join(" ");
    const x = l.celulas[0].x;
    const anterior = blocos.at(-1);
    const estrutura = SECAO.test(texto) || PERGUNTA.test(texto);
    const colunas = tabela ? colunasDosRotulos(tabela, l) : null;
    const rotulosAcima = tabela;
    tabela = null;
    if (estrutura && (!caixa || x <= caixa.margem + 2)) {
      dentroDoCorpo = true;
      fecharCaixa();
      blocos.push({ tipo: "p", texto });
    } else if (caixa) {
      caixa.textos.push(texto);
    } else if (anterior?.tipo === "p" && PERGUNTA.test(anterior.texto) && !/[?:]$/.test(anterior.texto) && !CAIXA.test(texto)) {
      // Enunciado que quebrou de linha: toda pergunta do checklist termina em "?" ou ":".
      anterior.texto += ` ${texto}`;
    } else if (/^Resposta:?$/i.test(texto)) {
      blocos.push({ tipo: "p", texto });
      caixa = { textos: [], margem: x };
    } else if (CAIXA.test(texto)) {
      if (anterior?.tipo === "p" && CAIXA.test(anterior.texto)) anterior.texto += ` ${texto}`;
      else blocos.push({ tipo: "p", texto });
    } else if (colunas && rotulosAcima) {
      // Valor escrito na linha de baixo do rótulo, na mesma coluna: outro parágrafo da mesma célula.
      l.celulas.forEach((c, i) => rotulosAcima.linha[colunas[i]].push(c.texto));
      tabela = { ...rotulosAcima, y: l.y };
    } else if (dentroDoCorpo && l.celulas.length === 1) {
      // Orientação ou texto escrito fora da caixa: parágrafo, como no Word.
      blocos.push({ tipo: "p", texto });
    } else {
      const linha = l.celulas.map((c) => [c.texto]);
      blocos.push({ tipo: "tbl", linhas: [linha] });
      // Só é linha de rótulos a do cabeçalho ou a com duas células ou mais (a 1.4); orientação de uma linha só não.
      const rotulos = (!dentroDoCorpo || l.celulas.length > 1) && l.celulas.every((c) => c.fim - c.x <= ROTULO);
      if (rotulos) tabela = { linha, xs: l.celulas.map((c) => c.x), pagina: l.pagina, y: l.y };
    }
  }
  fecharCaixa();
  return blocos;
}

