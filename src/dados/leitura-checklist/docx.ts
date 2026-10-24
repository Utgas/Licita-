/**
 * Abre o .docx (jszip) e lê o corpo do documento (fast-xml-parser) na ordem em que está: parágrafos e tabelas
 * (decisão 0011). Não converte para HTML nem interpreta nada: só devolve o texto de cada parágrafo e de cada
 * célula. Marcas de caixa de seleção feitas com símbolo (Wingdings) ou com controle de conteúdo viram ☐ ou ☒.
 */
import { XMLParser } from "fast-xml-parser";
import JSZip from "jszip";

export type Bloco = { tipo: "p"; texto: string } | { tipo: "tbl"; linhas: string[][][] };

export class ArquivoInvalido extends Error {}

type No = Record<string, unknown>;

/** Símbolos de fonte que o Word usa para caixas marcadas e vazias. */
const SIMBOLOS: Record<string, string> = {
  F0FE: "☒", F0FD: "☒", F078: "☒", F0FB: "☒", F0FC: "☒", "00FE": "☒", "00FD": "☒",
  F0A8: "☐", F06F: "☐", F071: "☐", "00A8": "☐",
  F054: "☒", F053: "☒", F051: "☒", F052: "☒", F0A3: "☐", F0A2: "☐",
};

function filhos(no: No): No[] {
  for (const [chave, valor] of Object.entries(no)) if (chave !== ":@" && Array.isArray(valor)) return valor as No[];
  return [];
}

function nome(no: No): string {
  return Object.keys(no).find((k) => k !== ":@") ?? "";
}

function atributo(no: No, chave: string): string | undefined {
  const a = no[":@"] as Record<string, string> | undefined;
  return a?.[`@_${chave}`];
}

/** Texto de um trecho: w:t, tabulação, quebra, símbolo e caixa de seleção de controle de conteúdo. */
function textoDe(no: No): string {
  let s = "";
  for (const f of filhos(no)) {
    const n = nome(f);
    if (n === "#text") s += String(f["#text"]);
    else if (n === "w:t") s += filhos(f).map((x) => String(x["#text"] ?? "")).join("");
    else if (n === "w:tab") s += "\t";
    else if (n === "w:br" || n === "w:cr") s += "\n";
    else if (n === "w:sym") s += SIMBOLOS[(atributo(f, "w:char") ?? "").toUpperCase()] ?? "";
    else if (n === "w:sdt") s += textoDoControle(f);
    else if (n === "w:p") s += `${textoDe(f)}\n`;
    else if (n !== "w:instrText" && n !== "w:delText" && n !== "w:sdtPr") s += textoDe(f);
  }
  return s;
}

/** Controle de conteúdo: caixa de seleção vira ☐ ou ☒; os demais, o texto que mostram. */
function textoDoControle(sdt: No): string {
  const propriedades = filhos(sdt).find((f) => nome(f) === "w:sdtPr");
  const caixa = propriedades && filhos(propriedades).find((f) => nome(f) === "w14:checkbox");
  if (caixa) {
    const marcado = filhos(caixa).find((f) => nome(f) === "w14:checked");
    const v = marcado && atributo(marcado, "w14:val");
    return v === "1" || v === "true" ? "☒" : "☐";
  }
  const conteudo = filhos(sdt).find((f) => nome(f) === "w:sdtContent");
  return conteudo ? textoDe(conteudo) : "";
}

function paragrafosDaCelula(tc: No): string[] {
  const paragrafos: string[] = [];
  for (const f of filhos(tc)) {
    if (nome(f) === "w:p") paragrafos.push(textoDe(f));
    else if (nome(f) === "w:sdt") paragrafos.push(textoDoControle(f));
  }
  return paragrafos;
}

function blocosDe(corpo: No[]): Bloco[] {
  const blocos: Bloco[] = [];
  for (const no of corpo) {
    const n = nome(no);
    if (n === "w:p") blocos.push({ tipo: "p", texto: textoDe(no) });
    else if (n === "w:tbl") {
      const linhas = filhos(no)
        .filter((f) => nome(f) === "w:tr")
        .map((tr) => filhos(tr).filter((f) => nome(f) === "w:tc").map(paragrafosDaCelula));
      blocos.push({ tipo: "tbl", linhas });
    } else if (n === "w:sdt") {
      const conteudo = filhos(no).find((f) => nome(f) === "w:sdtContent");
      if (conteudo) blocos.push(...blocosDe(filhos(conteudo)));
    }
  }
  return blocos;
}

/** Blocos do corpo do documento, na ordem. Arquivo que não é .docx é erro claro. */
export async function lerDocx(arquivo: Uint8Array): Promise<Bloco[]> {
  let xml: string | undefined;
  try {
    xml = await (await JSZip.loadAsync(arquivo)).file("word/document.xml")?.async("string");
  } catch {
    throw new ArquivoInvalido("O arquivo não é um documento do Word (.docx).");
  }
  if (!xml) throw new ArquivoInvalido("O arquivo não é um documento do Word (.docx).");
  const arvore = new XMLParser({ preserveOrder: true, ignoreAttributes: false, trimValues: false, processEntities: true }).parse(xml) as No[];
  const documento = arvore.find((n) => nome(n) === "w:document");
  const corpo = documento && filhos(documento).find((n) => nome(n) === "w:body");
  if (!corpo) throw new ArquivoInvalido("O documento do Word não tem corpo legível.");
  return blocosDe(filhos(corpo));
}
