/**
 * Lê o checklist salvo pelo LibreOffice no formato dele (.odt) e devolve os mesmos blocos da leitura do Word,
 * com as mesmas bibliotecas (jszip e fast-xml-parser; decisões 0011 e 0017). Parágrafos e títulos viram
 * parágrafos; tabelas, linhas de células. Lista numerada do LibreOffice perde o número no texto, como no Word:
 * a leitura reconhece a pergunta pelo enunciado.
 */
import { XMLParser } from "fast-xml-parser";
import JSZip from "jszip";
import { ArquivoInvalido, type Bloco } from "./docx.ts";

type No = Record<string, unknown>;

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

/** O que não é texto do documento: comentário, nota de rodapé, desenho e o registro de alterações. */
const FORA = new Set(["office:annotation", "office:annotation-end", "text:note", "text:tracked-changes", "draw:frame", "draw:custom-shape", "text:soft-page-break"]);

function textoDe(no: No): string {
  let s = "";
  for (const f of filhos(no)) {
    const n = nome(f);
    if (n === "#text") s += String(f["#text"]);
    else if (n === "text:s") s += " ".repeat(Number(atributo(f, "text:c") ?? 1));
    else if (n === "text:tab") s += "\t";
    else if (n === "text:line-break") s += "\n";
    else if (!FORA.has(n)) s += textoDe(f);
  }
  return s;
}

function paragrafosDaCelula(celula: No): string[] {
  const paragrafos: string[] = [];
  for (const b of blocosDe(filhos(celula))) {
    if (b.tipo === "p") paragrafos.push(b.texto);
    else for (const linha of b.linhas) paragrafos.push(linha.map((c) => c.join(" ").trim()).filter(Boolean).join(" | "));
  }
  return paragrafos;
}

/** Linhas da tabela, atravessando cabeçalho repetido e grupos de linhas. */
function linhasDe(no: No): No[] {
  return filhos(no).flatMap((f) => (nome(f) === "table:table-row" ? [f] : ["table:table-header-rows", "table:table-rows", "table:table-row-group"].includes(nome(f)) ? linhasDe(f) : []));
}

function blocosDe(corpo: No[]): Bloco[] {
  const blocos: Bloco[] = [];
  for (const no of corpo) {
    const n = nome(no);
    if (n === "text:p" || n === "text:h") blocos.push({ tipo: "p", texto: textoDe(no) });
    else if (n === "table:table") {
      const linhas = linhasDe(no).map((tr) => filhos(tr).filter((c) => nome(c) === "table:table-cell").map(paragrafosDaCelula));
      blocos.push({ tipo: "tbl", linhas });
    } else if (["text:list", "text:list-item", "text:list-header", "text:section", "text:index-body"].includes(n)) {
      blocos.push(...blocosDe(filhos(no)));
    }
  }
  return blocos;
}

/** O arquivo é um documento do LibreOffice (.odt): zip com o tipo gravado logo no começo. */
export function eOdt(arquivo: Uint8Array): boolean {
  const inicio = new TextDecoder("latin1").decode(arquivo.subarray(0, 100));
  return inicio.startsWith("PK") && inicio.includes("mimetypeapplication/vnd.oasis.opendocument.text");
}

/** Blocos do corpo do documento, na ordem. */
export async function lerOdt(arquivo: Uint8Array): Promise<Bloco[]> {
  let xml: string | undefined;
  try {
    xml = await (await JSZip.loadAsync(arquivo)).file("content.xml")?.async("string");
  } catch {
    throw new ArquivoInvalido("O arquivo não é um documento do LibreOffice (.odt) legível.");
  }
  if (!xml) throw new ArquivoInvalido("O arquivo não é um documento do LibreOffice (.odt) legível.");
  const arvore = new XMLParser({ preserveOrder: true, ignoreAttributes: false, trimValues: false, processEntities: true }).parse(xml) as No[];
  const documento = arvore.find((n) => nome(n) === "office:document-content");
  const corpo = documento && filhos(documento).find((n) => nome(n) === "office:body");
  const texto = corpo && filhos(corpo).find((n) => nome(n) === "office:text");
  if (!texto) throw new ArquivoInvalido("O documento do LibreOffice não tem texto legível.");
  return blocosDe(filhos(texto));
}
