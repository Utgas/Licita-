/**
 * Abre o .docx (jszip) e lê o corpo do documento (fast-xml-parser) na ordem em que está: parágrafos e tabelas
 * (decisão 0011). Não converte para HTML nem interpreta nada: só devolve o texto de cada parágrafo e de cada
 * célula. Marcas de caixa de seleção feitas com símbolo (Wingdings), com controle de conteúdo ou com campo de
 * formulário antigo viram ☐ ou ☒.
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

/** Invólucros sem conteúdo próprio (marcação de XML, revisão, controle): o que vale é o que está dentro. */
const INVOLUCROS = new Set(["w:customXml", "w:smartTag", "w:ins", "w:moveTo", "w:sdtContent"]);

/** Caixa de seleção de formulário antigo do Word (FORMCHECKBOX): w:checked vale; sem ele, o padrão (w:default). */
function caixaDeFormulario(fldChar: No): string {
  const dados = filhos(fldChar).find((f) => nome(f) === "w:ffData");
  const caixa = dados && filhos(dados).find((f) => nome(f) === "w:checkBox");
  if (!caixa) return "";
  const marcado = filhos(caixa).find((f) => nome(f) === "w:checked");
  const padrao = filhos(caixa).find((f) => nome(f) === "w:default");
  const valor = marcado ? (atributo(marcado, "w:val") ?? "1") : (padrao && atributo(padrao, "w:val")) ?? "0";
  return valor === "1" || valor === "true" ? "☒" : "☐";
}

/**
 * Texto de um trecho: w:t, tabulação, quebra, símbolo, caixa de seleção (controle de conteúdo ou formulário
 * antigo). Texto apagado com revisão ligada (w:delText, w:moveFrom) não entra; de um conteúdo alternativo
 * (mc:AlternateContent, caixa de texto) entra só a primeira versão, para não repetir o texto.
 */
function textoDe(no: No): string {
  let s = "";
  for (const f of filhos(no)) {
    const n = nome(f);
    if (n === "#text") s += String(f["#text"]);
    else if (n === "w:t") s += filhos(f).map((x) => String(x["#text"] ?? "")).join("");
    else if (n === "w:tab") s += "\t";
    else if (n === "w:br" || n === "w:cr") s += "\n";
    else if (n === "w:sym") s += SIMBOLOS[(atributo(f, "w:char") ?? "").toUpperCase()] ?? "";
    else if (n === "w:fldChar") s += caixaDeFormulario(f);
    else if (n === "w:sdt") s += textoDoControle(f);
    else if (n === "w:p") s += `${textoDe(f)}\n`;
    else if (n === "mc:AlternateContent") s += textoDe(filhos(f).find((x) => nome(x) === "mc:Choice") ?? {});
    else if (n !== "w:instrText" && n !== "w:delText" && n !== "w:sdtPr" && n !== "w:moveFrom" && n !== "w:del") s += textoDe(f);
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

/** Filhos com o nome dado, atravessando controles de conteúdo e outros invólucros (linha ou célula dentro de w:sdt). */
function filhosChamados(no: No, alvo: string): No[] {
  const achados: No[] = [];
  for (const f of filhos(no)) {
    const n = nome(f);
    if (n === alvo) achados.push(f);
    else if (n === "w:sdt" || INVOLUCROS.has(n)) achados.push(...filhosChamados(f, alvo));
  }
  return achados;
}

/** Parágrafos de uma célula, inclusive os de tabela colada dentro dela (uma linha da tabela interna por parágrafo). */
function paragrafosDaCelula(tc: No): string[] {
  const paragrafos: string[] = [];
  for (const f of filhos(tc)) {
    const n = nome(f);
    if (n === "w:p") paragrafos.push(textoDe(f));
    else if (n === "w:tbl") for (const linha of linhasDaTabela(f)) paragrafos.push(linha.map((c) => c.join(" ").trim()).filter(Boolean).join(" | "));
    else if (n === "w:sdt") {
      const conteudo = filhos(f).find((x) => nome(x) === "w:sdtContent");
      paragrafos.push(...(conteudo ? paragrafosDaCelula(conteudo) : [textoDoControle(f)]));
    } else if (INVOLUCROS.has(n)) paragrafos.push(...paragrafosDaCelula(f));
  }
  return paragrafos;
}

function linhasDaTabela(tbl: No): string[][][] {
  return filhosChamados(tbl, "w:tr").map((tr) => filhosChamados(tr, "w:tc").map(paragrafosDaCelula));
}

function blocosDe(corpo: No[]): Bloco[] {
  const blocos: Bloco[] = [];
  for (const no of corpo) {
    const n = nome(no);
    if (n === "w:p") blocos.push({ tipo: "p", texto: textoDe(no) });
    else if (n === "w:tbl") blocos.push({ tipo: "tbl", linhas: linhasDaTabela(no) });
    else if (n === "w:sdt" || INVOLUCROS.has(n)) {
      const conteudo = n === "w:sdt" ? filhos(no).find((f) => nome(f) === "w:sdtContent") : no;
      if (conteudo) blocos.push(...blocosDe(filhos(conteudo)));
    }
  }
  return blocos;
}

/** Blocos do corpo do documento, na ordem. Arquivo que não é .docx é erro claro. */
export async function lerDocx(arquivo: Uint8Array): Promise<Bloco[]> {
  // Word 97-2003 (.doc) começa com a assinatura D0 CF 11 E0: formato antigo, sem XML para ler.
  if (arquivo[0] === 0xd0 && arquivo[1] === 0xcf && arquivo[2] === 0x11 && arquivo[3] === 0xe0) {
    throw new ArquivoInvalido("Arquivo do Word antigo (.doc). Abra no Word e salve como .docx ou como PDF, e envie de novo.");
  }
  let xml: string | undefined;
  try {
    xml = await (await JSZip.loadAsync(arquivo)).file("word/document.xml")?.async("string");
  } catch {
    throw new ArquivoInvalido("O arquivo não é um documento do Word (.docx) nem um PDF.");
  }
  if (!xml) throw new ArquivoInvalido("O arquivo não é um documento do Word (.docx).");
  const arvore = new XMLParser({ preserveOrder: true, ignoreAttributes: false, trimValues: false, processEntities: true }).parse(xml) as No[];
  const documento = arvore.find((n) => nome(n) === "w:document");
  const corpo = documento && filhos(documento).find((n) => nome(n) === "w:body");
  if (!corpo) throw new ArquivoInvalido("O documento do Word não tem corpo legível.");
  return blocosDe(filhos(corpo));
}
