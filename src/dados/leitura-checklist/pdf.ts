/**
 * Lê o checklist em PDF (pdfjs-dist; decisão 0017) e devolve os mesmos blocos da leitura do Word, para a leitura
 * do checklist (ler.ts) seguir igual. O PDF não tem parágrafos nem tabelas: só texto com posição, que linhas.ts
 * remonta. PDF escaneado (só imagem) não tem texto: é erro claro, sem leitura parcial.
 */
import { ArquivoInvalido, type Bloco } from "./docx.ts";
import { type Linha, blocosDeLinhas, linhasDaPagina } from "./linhas.ts";

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
    const itens = (conteudo.items as ItemDeTexto[])
      .filter((i) => typeof i.str === "string")
      .map((i) => ({ x: i.transform[4], y: i.transform[5], largura: i.width, texto: i.str }));
    linhas.push(...linhasDaPagina(n, altura, itens));
  }
  await tarefa.destroy();
  return linhas;
}

/** Blocos do PDF, na ordem, no mesmo formato da leitura do Word. */
export async function lerPdf(arquivo: Uint8Array): Promise<Bloco[]> {
  const blocos = blocosDeLinhas(await linhasDoPdf(arquivo));
  if (blocos.length === 0) throw new ArquivoInvalido("O PDF não tem texto (parece escaneado). Envie o PDF gerado pelo Word ou o próprio .docx.");
  return blocos;
}

/** O arquivo começa com %PDF. */
export const ePdf = (arquivo: Uint8Array) => arquivo.length > 4 && String.fromCharCode(...arquivo.subarray(0, 4)) === "%PDF";
