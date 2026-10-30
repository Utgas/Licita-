/**
 * Checklist preenchido fictício, montado por código a partir do checklist em branco de referencias/ (passo 6): marca
 * opções e escreve nas caixas como alguém faria no Word. Só dados fictícios.
 */
import { readFileSync } from "node:fs";
import path from "node:path";
import JSZip from "jszip";

const DIR = path.resolve(import.meta.dirname, "../../referencias/checklists");
export const EM_BRANCO = {
  CONSUMO: path.join(DIR, "checklist-tecnico-consumo-saude-revisao.docx"),
  PERMANENTES: path.join(DIR, "checklist-tecnico-permanentes-saude.docx"),
} as const;

const escapar = (s: string) => s.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
const paragrafo = (texto: string) =>
  `<w:p><w:r><w:t xml:space="preserve">${texto.split("\n").map(escapar).join('</w:t><w:br/><w:t xml:space="preserve">')}</w:t></w:r></w:p>`;

export class ChecklistFicticio {
  private readonly zip: JSZip;
  private xml: string;

  private constructor(zip: JSZip, xml: string) {
    this.zip = zip;
    this.xml = xml;
  }

  static async de(checklist: keyof typeof EM_BRANCO): Promise<ChecklistFicticio> {
    const zip = await JSZip.loadAsync(readFileSync(EM_BRANCO[checklist]));
    return new ChecklistFicticio(zip, (await zip.file("word/document.xml")?.async("string")) as string);
  }

  /** Início da pergunta (ou da seção sem número, como "22."). */
  private inicio(numero: string): number {
    const i = this.xml.indexOf(`>${numero}. `);
    if (i < 0) throw new Error(`pergunta ${numero} não achada no checklist em branco`);
    return i;
  }

  /** Troca o ☐ da opção pela marca dada (☒ por padrão; "X" imita quem digita um X no lugar). */
  marcar(numero: string, opcao: string, marca = "☒"): this {
    const de = this.inicio(numero);
    const alvo = `☐ ${escapar(opcao)}`;
    const i = this.xml.indexOf(alvo, de);
    if (i < 0) throw new Error(`opção ${opcao} da ${numero} não achada`);
    this.xml = this.xml.slice(0, i) + marca + this.xml.slice(i + 1);
    return this;
  }

  /** Troca o "☐ opção" inteiro por outro texto (ex.: "☐ XNão", com o X colado no rótulo). */
  trocarOpcao(numero: string, opcao: string, novo: string): this {
    const alvo = `☐ ${escapar(opcao)}`;
    const i = this.xml.indexOf(alvo, this.inicio(numero));
    if (i < 0) throw new Error(`opção ${opcao} da ${numero} não achada`);
    this.xml = this.xml.slice(0, i) + escapar(novo) + this.xml.slice(i + alvo.length);
    return this;
  }

  /** Escreve logo depois do texto da opção (ex.: "Outro: 18 meses"). */
  escreverNaOpcao(numero: string, opcao: string, texto: string): this {
    const i = this.xml.indexOf(escapar(opcao), this.inicio(numero)) + escapar(opcao).length;
    this.xml = this.xml.slice(0, i) + escapar(texto) + this.xml.slice(i);
    return this;
  }

  /** Escreve na caixa "Resposta:" da pergunta. */
  responder(numero: string, texto: string): this {
    const caixa = this.xml.indexOf("Resposta:", this.inicio(numero));
    return this.escreverNaCelula(this.xml.indexOf("<w:tc>", caixa), texto);
  }

  /** Escreve na célula de rótulo dado, depois da pergunta (ou no cabeçalho, sem pergunta). */
  preencherCampo(rotulo: string, texto: string, numero?: string): this {
    const de = numero ? this.inicio(numero) : 0;
    return this.escreverNaCelula(this.xml.lastIndexOf("<w:tc>", this.xml.indexOf(`>${escapar(rotulo)}<`, de)), texto);
  }

  /** Troca o enunciado de uma pergunta (para simular outra versão do checklist). */
  trocarEnunciado(numero: string, novo: string): this {
    const i = this.inicio(numero) + 1;
    const fim = this.xml.indexOf("<", i);
    this.xml = `${this.xml.slice(0, i)}${numero}. ${escapar(novo)}${this.xml.slice(fim)}`;
    return this;
  }

  /** Mexe direto no XML do Word, para imitar o que o Word ou quem preenche faz com o arquivo. */
  alterarXml(alterar: (xml: string) => string): this {
    const novo = alterar(this.xml);
    if (novo === this.xml) throw new Error("a alteração não mudou nada no checklist");
    this.xml = novo;
    return this;
  }

  private escreverNaCelula(inicioDaCelula: number, texto: string): this {
    const fim = this.xml.indexOf("</w:tc>", inicioDaCelula);
    this.xml = this.xml.slice(0, fim) + paragrafo(texto) + this.xml.slice(fim);
    return this;
  }

  async gerar(): Promise<Uint8Array> {
    this.zip.file("word/document.xml", this.xml);
    return this.zip.generateAsync({ type: "uint8array", compression: "DEFLATE" });
  }
}
