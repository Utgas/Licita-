/**
 * Planilha de itens (passo 8, ExcelJS): colunas fixas, modelo para baixar e importação. A importação confere tudo
 * antes de gravar; com qualquer erro, nada entra e a tela lista as linhas a corrigir. Valores e quantidades vêm da
 * planilha como estão: nada é calculado nem arredondado aqui.
 */
import ExcelJS from "exceljs";
import type { item } from "./esquema.ts";

type ColunaDoItem = Exclude<keyof typeof item.$inferInsert, "processoId" | "atualizadoEm">;

type Coluna = { titulo: string; coluna: ColunaDoItem; tipo: "inteiro" | "numero" | "texto" | "SN" | "categoria"; obrigatoria?: boolean; largura: number; exemplo: string | number };

export const COLUNAS: Coluna[] = [
  { titulo: "Item", coluna: "numero", tipo: "inteiro", obrigatoria: true, largura: 6, exemplo: 1 },
  { titulo: "Especificação", coluna: "especificacao", tipo: "texto", obrigatoria: true, largura: 50, exemplo: "Item fictício de exemplo" },
  { titulo: "CATMAT", coluna: "catmat", tipo: "texto", largura: 10, exemplo: "000000" },
  { titulo: "Unidade de medida", coluna: "unidadeMedida", tipo: "texto", obrigatoria: true, largura: 14, exemplo: "unidade" },
  { titulo: "Quantidade", coluna: "quantidade", tipo: "numero", obrigatoria: true, largura: 11, exemplo: 100 },
  { titulo: "Valor unitário (R$)", coluna: "valorUnitario", tipo: "numero", largura: 14, exemplo: 10.5 },
  { titulo: "Grupo", coluna: "grupo", tipo: "texto", largura: 8, exemplo: "" },
  { titulo: "Categoria (CONSUMO ou PERMANENTE)", coluna: "categoria", tipo: "categoria", largura: 14, exemplo: "CONSUMO" },
  { titulo: "Classe PDM", coluna: "classePdm", tipo: "texto", largura: 12, exemplo: "" },
  { titulo: "Exige amostra (S ou N)", coluna: "exigeAmostra", tipo: "SN", largura: 10, exemplo: "N" },
  { titulo: "Marca ou modelo de referência", coluna: "marcaIndicada", tipo: "texto", largura: 20, exemplo: "" },
  { titulo: "Validade mínima", coluna: "validadeMinima", tipo: "texto", largura: 14, exemplo: "" },
  { titulo: "Compatibilidade", coluna: "compatibilidade", tipo: "texto", largura: 20, exemplo: "" },
  { titulo: "Faixa de temperatura", coluna: "faixaTemperatura", tipo: "texto", largura: 14, exemplo: "" },
  { titulo: "Controle especial (S ou N)", coluna: "controleEspecial", tipo: "SN", largura: 10, exemplo: "N" },
  { titulo: "Garantia mínima (meses)", coluna: "garantiaMinimaMeses", tipo: "inteiro", largura: 10, exemplo: "" },
  { titulo: "Justificativa de exceção ME/EPP", coluna: "justificativaExcecaoMeEpp", tipo: "texto", largura: 30, exemplo: "" },
];

/** Item lido: coluna da tabela item -> valor (numero sempre presente). */
export type ItemLido = Partial<Record<ColunaDoItem, string | number | null>>;

/** Modelo para baixar: cabeçalho fixo e uma linha de exemplo fictícia. */
export async function modeloDaPlanilha(): Promise<Uint8Array> {
  const livro = new ExcelJS.Workbook();
  const aba = livro.addWorksheet("Itens");
  aba.columns = COLUNAS.map((c) => ({ header: c.titulo, key: c.coluna, width: c.largura }));
  aba.getRow(1).font = { bold: true };
  aba.addRow(Object.fromEntries(COLUNAS.map((c) => [c.coluna, c.exemplo])));
  return new Uint8Array(await livro.xlsx.writeBuffer());
}

function textoDaCelula(valor: ExcelJS.CellValue): string {
  if (valor === null || valor === undefined) return "";
  if (typeof valor === "object") {
    if ("richText" in valor) return valor.richText.map((r) => r.text).join("");
    if ("result" in valor) return textoDaCelula(valor.result as ExcelJS.CellValue);
    if ("text" in valor) return String(valor.text);
    if (valor instanceof Date) return valor.toISOString().slice(0, 10);
    return "";
  }
  return String(valor).trim();
}

/** Número como está na planilha: 1234.5, "1.234,50" ou "R$ 10,00". Texto que não é número é erro, não zero. */
export function numeroDaCelula(valor: ExcelJS.CellValue): number | null {
  if (typeof valor === "number") return valor;
  if (valor && typeof valor === "object" && "result" in valor && typeof valor.result === "number") return valor.result;
  const t = textoDaCelula(valor).replace(/^R\$\s*/i, "").replace(/\s/g, "");
  if (!t) return null;
  const normal = /,\d+$/.test(t) || /^\d{1,3}(\.\d{3})+$/.test(t) ? t.replaceAll(".", "").replace(",", ".") : t;
  return /^-?\d+(\.\d+)?$/.test(normal) ? Number(normal) : Number.NaN;
}

export type ResultadoDaImportacao = { itens: ItemLido[]; erros: string[] };

export async function lerPlanilha(arquivo: Uint8Array): Promise<ResultadoDaImportacao> {
  const livro = new ExcelJS.Workbook();
  try {
    await livro.xlsx.load(arquivo as unknown as ArrayBuffer);
  } catch {
    return { itens: [], erros: ["O arquivo não é uma planilha .xlsx. Baixe o modelo e preencha nele."] };
  }
  const aba = livro.worksheets[0];
  if (!aba) return { itens: [], erros: ["A planilha está vazia."] };
  const cabecalho = COLUNAS.map((_, i) => textoDaCelula(aba.getRow(1).getCell(i + 1).value));
  const fora = COLUNAS.filter((c, i) => cabecalho[i].toLowerCase() !== c.titulo.toLowerCase());
  if (fora.length) return { itens: [], erros: [`As colunas não são as do modelo (primeira diferente: "${fora[0].titulo}"). Baixe o modelo e copie os dados para ele.`] };

  const itens: ItemLido[] = [];
  const erros: string[] = [];
  const numeros = new Set<number>();
  aba.eachRow((linha, n) => {
    if (n === 1) return;
    const celulas = COLUNAS.map((_, i) => linha.getCell(i + 1).value);
    if (celulas.every((v) => textoDaCelula(v) === "")) return;
    const lido: ItemLido = {};
    COLUNAS.forEach((c, i) => {
      const v = celulas[i];
      const t = textoDaCelula(v);
      if (!t) {
        if (c.obrigatoria) erros.push(`Linha ${n}: falta ${c.titulo}.`);
        lido[c.coluna] = null;
        return;
      }
      if (c.tipo === "texto") lido[c.coluna] = t;
      else if (c.tipo === "SN" || c.tipo === "categoria") {
        const u = t.toUpperCase().replace("PERMANENTES", "PERMANENTE").replace("SIM", "S").replace("NÃO", "N").replace("NAO", "N");
        const validos = c.tipo === "SN" ? ["S", "N"] : ["CONSUMO", "PERMANENTE"];
        if (validos.includes(u)) lido[c.coluna] = u;
        else erros.push(`Linha ${n}: ${c.titulo} deve ser ${validos.join(" ou ")}.`);
      } else {
        const x = numeroDaCelula(v);
        if (x === null || Number.isNaN(x)) erros.push(`Linha ${n}: ${c.titulo} não é número ("${t}").`);
        else if (x <= 0) erros.push(`Linha ${n}: ${c.titulo} precisa ser maior que zero.`);
        else if (c.tipo === "inteiro" && !Number.isInteger(x)) erros.push(`Linha ${n}: ${c.titulo} precisa ser número inteiro.`);
        else lido[c.coluna] = x;
      }
    });
    if (typeof lido.numero === "number") {
      if (numeros.has(lido.numero)) erros.push(`Linha ${n}: o item ${lido.numero} aparece mais de uma vez.`);
      numeros.add(lido.numero);
      itens.push(lido);
    }
  });
  if (!itens.length && !erros.length) erros.push("A planilha não tem itens.");
  return { itens, erros };
}
