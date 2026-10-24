"use server";
/** Ações da tela dos itens (passo 8). Valores e quantidades entram como informados; o motor calcula o resto. */
import { createHash } from "node:crypto";
import { and, eq } from "drizzle-orm";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import type { Resultado } from "@/auth/acoes.ts";
import { avancarEtapa, gravarNoProcesso, mensagemDeErro } from "@/dados/acesso-processo.ts";
import { item, respostaWizard } from "@/dados/esquema.ts";
import { COLUNAS, type ItemLido, lerPlanilha, numeroDaCelula } from "@/dados/planilha-itens.ts";

const TAMANHO_MAXIMO = 4 * 1024 * 1024;
const paraBanco = (i: ItemLido) => {
  const linha: Record<string, string | number | null> = {};
  for (const c of COLUNAS) {
    const v = i[c.coluna] ?? null;
    linha[c.coluna] = v !== null && (c.coluna === "quantidade" || c.coluna === "valorUnitario") ? String(v) : v;
  }
  return linha as typeof item.$inferInsert;
};

export async function importarPlanilha(id: string, _anterior: Resultado, dados: FormData): Promise<Resultado> {
  const arquivo = dados.get("planilha");
  if (!(arquivo instanceof File) || arquivo.size === 0) return { erro: "Escolha a planilha .xlsx." };
  if (arquivo.size > TAMANHO_MAXIMO) return { erro: "Planilha maior que 4 MB." };
  const bytes = new Uint8Array(await arquivo.arrayBuffer());
  const { itens, erros } = await lerPlanilha(bytes);
  if (erros.length) return { erro: `Nada foi importado. Corrija e envie de novo: ${erros.slice(0, 15).join(" ")}${erros.length > 15 ? ` (e mais ${erros.length - 15})` : ""}` };
  try {
    return await gravarNoProcesso<Resultado>(id, "ITENS_IMPORTADOS", async (tx) => {
      await tx.delete(item).where(eq(item.processoId, id));
      await tx.insert(item).values(itens.map((i) => ({ ...paraBanco(i), processoId: id })));
      return { resultado: { aviso: `${itens.length} item(ns) importado(s). A tabela anterior foi substituída.` }, hashArquivo: createHash("sha256").update(bytes).digest("hex"), detalhes: { itens: itens.length } };
    }).finally(() => revalidatePath(`/processos/${id}`, "layout"));
  } catch (e) {
    return { erro: mensagemDeErro(e) };
  }
}

export async function salvarItem(id: string, _anterior: Resultado, dados: FormData): Promise<Resultado> {
  const original = Number(dados.get("original") ?? 0) || null;
  const lido: ItemLido = {};
  const erros: string[] = [];
  for (const c of COLUNAS) {
    const t = String(dados.get(c.coluna) ?? "").trim();
    if (!t) {
      if (c.obrigatoria) erros.push(`Falta ${c.titulo}.`);
      lido[c.coluna] = null;
    } else if (c.tipo === "texto" || c.tipo === "SN" || c.tipo === "categoria") lido[c.coluna] = t;
    else {
      const n = numeroDaCelula(t);
      if (n === null || Number.isNaN(n) || n <= 0 || (c.tipo === "inteiro" && !Number.isInteger(n))) erros.push(`${c.titulo}: informe um número ${c.tipo === "inteiro" ? "inteiro " : ""}maior que zero.`);
      else lido[c.coluna] = n;
    }
  }
  if (erros.length) return { erro: erros.join(" ") };
  try {
    return await gravarNoProcesso<Resultado>(id, "ITENS_ALTERADOS", async (tx, p) => {
      const numero = lido.numero as number;
      if (numero !== original && p.itens.some((i) => i.numero === numero)) return { resultado: { erro: `Já existe o item ${numero}.` } };
      const valores = paraBanco(lido);
      if (original) await tx.update(item).set(valores).where(and(eq(item.processoId, id), eq(item.numero, original)));
      else await tx.insert(item).values({ ...valores, processoId: id });
      return { resultado: { aviso: `Item ${numero} salvo.` }, detalhes: { item: numero } };
    }).finally(() => revalidatePath(`/processos/${id}`, "layout"));
  } catch (e) {
    return { erro: mensagemDeErro(e) };
  }
}

export async function apagarItem(id: string, _anterior: Resultado, dados: FormData): Promise<Resultado> {
  const numero = Number(dados.get("numero"));
  try {
    return await gravarNoProcesso<Resultado>(id, "ITENS_ALTERADOS", async (tx) => {
      await tx.delete(item).where(and(eq(item.processoId, id), eq(item.numero, numero)));
      return { resultado: { aviso: `Item ${numero} apagado.` }, detalhes: { item: numero, apagado: true } };
    }).finally(() => revalidatePath(`/processos/${id}`, "layout"));
  } catch (e) {
    return { erro: mensagemDeErro(e) };
  }
}

/** Resposta do wizard dada nesta tela (orçamento sigiloso, percentual da cota). */
export async function responderAqui(id: string, _anterior: Resultado, dados: FormData): Promise<Resultado> {
  const pergunta = String(dados.get("pergunta") ?? "");
  if (pergunta !== "WZ-40" && pergunta !== "VAR-057") return { erro: "Campo desconhecido." };
  const bruto = String(dados.get("valor") ?? "").trim();
  const valor = pergunta === "VAR-057" ? (bruto ? numeroDaCelula(bruto) : null) : bruto || null;
  if (typeof valor === "number" && (Number.isNaN(valor) || valor <= 0)) return { erro: "Informe um número maior que zero." };
  try {
    return await gravarNoProcesso<Resultado>(id, "RESPOSTA_WIZARD", async (tx) => {
      if (valor === null) await tx.delete(respostaWizard).where(and(eq(respostaWizard.processoId, id), eq(respostaWizard.pergunta, pergunta)));
      else await tx.insert(respostaWizard).values({ processoId: id, pergunta, valor, origem: "EQUIPE" }).onConflictDoUpdate({ target: [respostaWizard.processoId, respostaWizard.pergunta], set: { valor, origem: "EQUIPE" } });
      return { resultado: { aviso: "Salvo." }, detalhes: { pergunta } };
    }).finally(() => revalidatePath(`/processos/${id}`, "layout"));
  } catch (e) {
    return { erro: mensagemDeErro(e) };
  }
}

export async function irParaWizard(id: string): Promise<void> {
  await gravarNoProcesso(id, "PROCESSO_ALTERADO", async (tx, p) => {
    await avancarEtapa(tx, p, "WIZARD");
    return { resultado: null, detalhes: { etapa: "WIZARD" } };
  });
  redirect(`/processos/${id}/wizard`);
}
