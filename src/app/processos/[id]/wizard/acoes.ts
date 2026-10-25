"use server";
/**
 * Ações da tela do wizard (passo 9). A resposta da equipe vale sobre o checklist (o motor avisa a divergência);
 * a sugestão aceita grava com origem SUGESTAO_ACEITA. Campos extras (VAR) gravam na mesma tabela.
 */
import { and, eq } from "drizzle-orm";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import type { Resultado } from "@/auth/acoes.ts";
import { EntradaRecusada, abrirProcesso, avancarEtapa, gravarNoProcesso, mensagemDeErro } from "@/dados/acesso-processo.ts";
import { respostaWizard } from "@/dados/esquema.ts";
import { gravarVariavel } from "@/dados/etp.ts";
import { carregarPacote } from "@/dados/pacote.ts";
import { minutaDoProcesso } from "@/dados/processos.ts";
import { camposDaMinuta, justificativaDoM04, justificativaObrigatoria, opcoesDoM04, perguntasDoWizard, proximaPendente, valorDoCampo } from "@/dados/wizard.ts";
import type { Valor } from "@/motor/pacote/avaliador.ts";

export async function responderPergunta(id: string, _anterior: Resultado, dados: FormData): Promise<Resultado> {
  const pergunta = String(dados.get("pergunta") ?? "");
  const aceitarSugestao = dados.get("origem") === "SUGESTAO_ACEITA";
  let resultado: Resultado;
  try {
    resultado = await gravarNoProcesso<Resultado>(id, "RESPOSTA_WIZARD", async (tx, p) => {
      const { pacote } = carregarPacote(p.processo.pacote, p.processo.pacoteHash);
      const linha = pacote.matrizes.M04.find((l) => l.id === pergunta);
      if (!linha || linha.calculo_expr !== null) throw new EntradaRecusada("Pergunta não encontrada.");
      const opcoes = opcoesDoM04(linha);
      let valor: Valor;
      if (linha.tipo_resposta === "MULTIPLA") {
        const marcadas = dados.getAll("valor").map(String).filter(Boolean);
        valor = marcadas.length ? marcadas : null;
      } else {
        valor = String(dados.get("valor") ?? "").trim() || null;
      }
      if (valor === null) throw new EntradaRecusada("Escolha ou escreva a resposta.");
      const fora = (Array.isArray(valor) ? valor : [valor]).filter((v) => opcoes.length && !opcoes.includes(String(v)));
      if (fora.length) throw new EntradaRecusada("Opção desconhecida.");
      const justificativa = String(dados.get("justificativa") ?? "").trim() || null;
      if (justificativaObrigatoria(justificativaDoM04(linha), valor) && !justificativa) {
        throw new EntradaRecusada("Esta resposta exige justificativa. Escreva-a antes de salvar.");
      }
      const campos = { valor, justificativa, origem: aceitarSugestao ? ("SUGESTAO_ACEITA" as const) : ("EQUIPE" as const) };
      await tx
        .insert(respostaWizard)
        .values({ processoId: id, pergunta, ...campos })
        .onConflictDoUpdate({ target: [respostaWizard.processoId, respostaWizard.pergunta], set: campos });
      return { resultado: { aviso: `Resposta da ${pergunta} salva.` }, detalhes: { pergunta, origem: campos.origem } };
    });
  } catch (e) {
    return { erro: mensagemDeErro(e) };
  } finally {
    revalidatePath(`/processos/${id}`, "layout");
  }
  if (!resultado?.aviso) return resultado;
  // A próxima pergunta sai da minuta montada de novo, já com a resposta (pode habilitar ou desligar outras).
  const proxima = await proximaDepois(id, pergunta);
  redirect(`/processos/${id}/wizard${proxima ? `?p=${proxima}` : "?p=fim"}`);
}

async function proximaDepois(id: string, pergunta: string): Promise<string | null> {
  const { p } = await abrirProcesso(id);
  const { pacote } = carregarPacote(p.processo.pacote, p.processo.pacoteHash);
  return proximaPendente(perguntasDoWizard(pacote, minutaDoProcesso(p), p), pergunta);
}

export async function limparPergunta(id: string, _anterior: Resultado, dados: FormData): Promise<Resultado> {
  const pergunta = String(dados.get("pergunta") ?? "");
  if (!/^(WZ|VAR)-\d+$/.test(pergunta)) return { erro: "Pergunta não encontrada." };
  try {
    return await gravarNoProcesso<Resultado>(id, "RESPOSTA_WIZARD", async (tx) => {
      await tx.delete(respostaWizard).where(and(eq(respostaWizard.processoId, id), eq(respostaWizard.pergunta, pergunta)));
      return { resultado: { aviso: `Resposta da ${pergunta} apagada.` }, detalhes: { pergunta, apagada: true } };
    }).finally(() => revalidatePath(`/processos/${id}`, "layout"));
  } catch (e) {
    return { erro: mensagemDeErro(e) };
  }
}

export async function salvarCampo(id: string, _anterior: Resultado, dados: FormData): Promise<Resultado> {
  const variavel = String(dados.get("campo") ?? "");
  try {
    return await gravarNoProcesso<Resultado>(id, "RESPOSTA_WIZARD", async (tx, p) => {
      const { pacote } = carregarPacote(p.processo.pacote, p.processo.pacoteHash);
      const campo = camposDaMinuta(pacote, minutaDoProcesso(p), p).campos.find((c) => c.id === variavel);
      if (!campo) throw new EntradaRecusada("Campo não encontrado.");
      const lido = valorDoCampo(campo, dados);
      if ("erro" in lido) throw new EntradaRecusada(lido.erro);
      await gravarVariavel(tx, id, variavel, lido.valor);
      const apagada = lido.valor === null;
      return { resultado: { aviso: `${variavel} ${apagada ? "apagada" : "salva"}.` }, detalhes: { pergunta: variavel, apagada } };
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
