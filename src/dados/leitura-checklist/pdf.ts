/**
 * Lê o checklist em PDF (pdfjs-dist; decisão 0017) e devolve os mesmos blocos da leitura do Word, para a leitura
 * do checklist (ler.ts) seguir igual. O PDF não tem parágrafos nem tabelas: só texto com posição. Por isso:
 *
 * - as linhas são remontadas pela posição (mesma altura na página, da esquerda para a direita), porque o PDF
 *   gravado pelo Word ou pelo LibreOffice escreve a caixa ☐ fora da ordem do texto;
 * - cabeçalho e rodapé que se repetem em todas as páginas saem;
 * - o que vem depois de "Resposta:", até a próxima pergunta, é a caixa de resposta;
 * - linhas com caixa de seleção seguidas viram um parágrafo só (opção que quebra de linha), e o enunciado que
 *   quebra de linha é juntado até o "?" ou ":" final;
 * - as demais linhas viram uma linha de tabela, com uma célula por trecho separado por espaço largo (é assim que
 *   ficam o cabeçalho e a tabela da 1.4).
 *
 * PDF escaneado (só imagem) não tem texto: é erro claro, sem leitura parcial.
 */
import { ArquivoInvalido, type Bloco } from "./docx.ts";

type Trecho = { x: number; fim: number; texto: string };
type Linha = { pagina: number; y: number; altura: number; trechos: Trecho[] };

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

type ItemDeTexto = { str: string; width: number; transform: number[] };

async function linhasDoPdf(arquivo: Uint8Array): Promise<Linha[]> {
  const pdfjs = await import("pdfjs-dist/legacy/build/pdf.mjs");
  const tarefa = pdfjs.getDocument({ data: arquivo.slice(), useSystemFonts: false, verbosity: 0 });
  let documento;
  try {
    documento = await tarefa.promise;
  } catch {
    throw new ArquivoInvalido("O arquivo não é um PDF legível.");
  }
  const linhas: Linha[] = [];
  for (let n = 1; n <= documento.numPages; n++) {
    const pagina = await documento.getPage(n);
    const conteudo = await pagina.getTextContent();
    const altura = pagina.getViewport({ scale: 1 }).height;
    const daPagina: Linha[] = [];
    for (const item of conteudo.items as ItemDeTexto[]) {
      if (typeof item.str !== "string" || item.str === "") continue;
      const x = item.transform[4];
      const y = item.transform[5];
      let linha = daPagina.find((l) => Math.abs(l.y - y) <= TOLERANCIA_Y);
      if (!linha) daPagina.push((linha = { pagina: n, y, altura, trechos: [] }));
      linha.trechos.push({ x, fim: x + item.width, texto: item.str });
    }
    for (const l of daPagina) l.trechos.sort((a, b) => a.x - b.x);
    daPagina.sort((a, b) => b.y - a.y);
    linhas.push(...daPagina);
  }
  await tarefa.destroy();
  return linhas;
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

/** Blocos do PDF, na ordem, no mesmo formato da leitura do Word. */
export async function lerPdf(arquivo: Uint8Array): Promise<Bloco[]> {
  const todas = await linhasDoPdf(arquivo);
  const fora = repetidas(todas);
  const linhas = todas.filter((l) => !fora.has(chaveDeRepeticao(l))).map((l) => ({ ...l, celulas: celulas(l) })).filter((l) => l.celulas.length > 0);
  if (linhas.length === 0) throw new ArquivoInvalido("O PDF não tem texto (parece escaneado). Envie o PDF gerado pelo Word ou o próprio .docx.");

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

/** O arquivo começa com %PDF. */
export const ePdf = (arquivo: Uint8Array) => arquivo.length > 4 && String.fromCharCode(...arquivo.subarray(0, 4)) === "%PDF";
