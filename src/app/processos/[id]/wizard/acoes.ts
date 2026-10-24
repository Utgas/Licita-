"use server";
/** Ações do wizard (passo 9): resposta da equipe, sugestão aceita e campos extras (VAR) que a minuta pede. */
import { and, eq } from "drizzle-orm";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import type { Resultado } from "@/auth/acoes.ts";
import { avancarEtapa, gravarNoProcesso, mensagemDeErro } from "@/dados/acesso-processo.ts";
import { respostaWizard } from "@/dados/esquema.ts";
import { carregarPacote } from "@/dados/pacote.ts";
import { numeroDaCelula } from "@/dados/planilha-itens.ts";
import type { Valor } from "@/motor/pacote/avaliador.ts";
import { justificativaObrigatoria, opcoesDaPergunta } from "./regras.ts";

export async function responderPergunta(id: string, _anterior: Resultado, dados: FormData): Promise<Resultado> {
  const pergunta = String(dados.get("pergunta") ?? "");
  const proxima = String(dados.get("proxima") ?? "");
  const origem = dados.get("origem") === "SUGESTAO_ACEITA" ? "SUGESTAO_ACEITA" : "EQUIPE";
  let resultado: Resultado;
  try {
    resultado = await gravarNoProcesso<Resultado>(id, "RESPOSTA_WIZARD", async (tx, p) => {
      const { pacote } = carregarPacote(p.processo.pacote);
      const linha = pacote.matrizes.M04.find((l) => l.id === pergunta);
      if (!linha || linha.calculo_expr !== null || linha.depende_de_expr === false) return { resultado: { erro: "Pergunta não encontrada ou calculada pelo sistema." } };
      const opcoes = opcoesDaPergunta(linha.tipo_resposta, linha.opcoes);
      let valor: Valor;
      if (linha.tipo_resposta === "MULTIPLA") {
        const marcadas = dados.getAll("valor").map(String).filter((v) => opcoes.includes(v));
        valor = marcadas.length ? marcadas : null;
      } else {
        const bruto = String(dados.get("valor") ?? "").trim();
        if (opcoes.length && bruto && !opcoes.includes(bruto)) return { resultado: { erro: "Opção inválida." } };
        const n = linha.tipo_resposta === "NUMERO" ? numeroDaCelula(bruto) : null;
        valor = bruto ? (n !== null && !Number.isNaN(n) ? n : bruto) : null;
      }
      const justificativa = String(dados.get("justificativa") ?? "").trim() || null;
      if (valor !== null && !justificativa && justificativaObrigatoria(linha.exige_justificativa, valor)) {
        return { resultado: { erro: `Esta resposta exige justificativa: ${linha.exige_justificativa}` } };
      }
      if (valor === null) await tx.delete(respostaWizard).where(and(eq(respostaWizard.processoId, id), eq(respostaWizard.pergunta, pergunta)));
      else {
        const campos = { valor, justificativa, origem: origem as "EQUIPE" | "SUGESTAO_ACEITA" };
        await tx.insert(respostaWizard).values({ processoId: id, pergunta, ...campos }).onConflictDoUpdate({ target: [respostaWizard.processoId, respostaWizard.pergunta], set: campos });
      }
      return { resultado: { aviso: `${pergunta} salva.` }, detalhes: { pergunta, origem } };
    }).finally(() => revalidatePath(`/processos/${id}`, "layout"));
  } catch (e) {
    return { erro: mensagemDeErro(e) };
  }
  if (resultado?.erro || !proxima) return resultado;
  redirect(`/processos/${id}/wizard?q=${encodeURIComponent(proxima)}`);
}

/** Campo extra: variável do M05 que a minuta acusa como faltando (lacuna com fonte VAR-xxx). */
export async function salvarVariavel(id: string, _anterior: Resultado, dados: FormData): Promise<Resultado> {
  const variavel = String(dados.get("variavel") ?? "");
  try {
    return await gravarNoProcesso<Resultado>(id, "RESPOSTA_WIZARD", async (tx, p) => {
      const { pacote } = carregarPacote(p.processo.pacote);
      const linha = pacote.matrizes.M05.find((l) => l.id === variavel);
      if (!linha || linha.nome.startsWith("tabela_itens") || linha.calculo_expr !== null) return { resultado: { erro: "Campo não encontrado." } };
      const bruto = String(dados.get("valor") ?? "").trim();
      let valor: Valor = bruto || null;
      if (bruto && (linha.tipo_dado === "NUMERO" || linha.tipo_dado === "MOEDA")) {
        const n = numeroDaCelula(bruto);
        if (n === null || Number.isNaN(n)) return { resultado: { erro: "Informe só o número (ex.: 12 ou 1.234,56)." } };
        valor = n;
      } else if (bruto && linha.tipo_dado === "LISTA") valor = bruto.toUpperCase();
      else if (bruto && linha.tipo_dado === "TABELA") valor = bruto.split("\n").map((s) => s.trim()).filter(Boolean);
      if (valor === null) await tx.delete(respostaWizard).where(and(eq(respostaWizard.processoId, id), eq(respostaWizard.pergunta, variavel)));
      else await tx.insert(respostaWizard).values({ processoId: id, pergunta: variavel, valor, origem: "EQUIPE" }).onConflictDoUpdate({ target: [respostaWizard.processoId, respostaWizard.pergunta], set: { valor, origem: "EQUIPE" } });
      return { resultado: { aviso: `${variavel} salva.` }, detalhes: { pergunta: variavel } };
    }).finally(() => revalidatePath(`/processos/${id}`, "layout"));
  } catch (e) {
    return { erro: mensagemDeErro(e) };
  }
}

export async function irParaMinuta(id: string): Promise<void> {
  await gravarNoProcesso(id, "PROCESSO_ALTERADO", async (tx, p) => {
    await avancarEtapa(tx, p, "MINUTA");
    return { resultado: null, detalhes: { etapa: "MINUTA" } };
  });
  redirect(`/processos/${id}/revisao`);
}
