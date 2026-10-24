"use server";
/**
 * Ações da tela do checklist (passo 7). O Word é lido em memória e descartado; fica o hash na auditoria (decisão
 * 0009). Correção na tela grava com origem OPERADOR e tira a pergunta das listas da leitura.
 */
import { and, eq, like } from "drizzle-orm";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import type { Resultado } from "@/auth/acoes.ts";
import { avancarEtapa, gravarNoProcesso, mensagemDeErro } from "@/dados/acesso-processo.ts";
import { complementoOperador, processo, respostaChecklist, revisaoConfirmada } from "@/dados/esquema.ts";
import { ArquivoInvalido } from "@/dados/leitura-checklist/docx.ts";
import { VersaoDesconhecida, itensCitados, lerChecklist } from "@/dados/leitura-checklist/ler.ts";
import { carregarPacote } from "@/dados/pacote.ts";
import { type LeiturasGravadas, semPerguntaNaLeitura } from "@/dados/processos.ts";
import type { Valor } from "@/motor/pacote/avaliador.ts";
import type { LinhaM11 } from "@/motor/pacote/esquema.ts";

const TAMANHO_MAXIMO = 4 * 1024 * 1024;
const PREFIXO = { CONSUMO: "CK-C-", PERMANENTES: "CK-P-" } as const;

export async function enviarWord(id: string, _anterior: Resultado, dados: FormData): Promise<Resultado> {
  const arquivo = dados.get("arquivo");
  if (!(arquivo instanceof File) || arquivo.size === 0) return { erro: "Escolha o arquivo .docx do checklist preenchido." };
  if (arquivo.size > TAMANHO_MAXIMO) return { erro: "Arquivo maior que 4 MB. Tire imagens coladas no Word e envie de novo." };
  try {
    return await gravarNoProcesso<Resultado>(id, "CHECKLIST_LIDO", async (tx, p) => {
      const { pacote } = carregarPacote(p.processo.pacote);
      const leitura = await lerChecklist(new Uint8Array(await arquivo.arrayBuffer()), pacote);
      if (!p.processo.checklists.includes(leitura.checklist)) {
        throw new VersaoDesconhecida(`Este é o checklist de ${leitura.checklist === "CONSUMO" ? "consumo" : "permanentes"}, que não foi marcado para este processo.`);
      }
      const prefixo = PREFIXO[leitura.checklist];
      // Novo envio substitui as respostas e as confirmações daquele checklist.
      await tx.delete(respostaChecklist).where(and(eq(respostaChecklist.processoId, id), like(respostaChecklist.pergunta, `${prefixo}%`)));
      await tx.delete(revisaoConfirmada).where(and(eq(revisaoConfirmada.processoId, id), like(revisaoConfirmada.pergunta, `${prefixo}%`)));
      if (leitura.respostas.length) {
        await tx.insert(respostaChecklist).values(
          leitura.respostas.map((r) => ({ processoId: id, pergunta: r.pergunta, valor: r.valor, texto: r.texto, numero: r.numero === null ? null : String(r.numero), itens: r.itens, origem: "LEITURA_WORD" as const })),
        );
      }
      const gravadas = { ...(p.processo.leituraChecklist as LeiturasGravadas), [leitura.checklist]: leitura.metadados };
      await tx.update(processo).set({ leituraChecklist: gravadas }).where(eq(processo.id, id));
      const m = leitura.metadados;
      return {
        resultado: {
          aviso: `Checklist de ${leitura.checklist === "CONSUMO" ? "consumo" : "permanentes"} lido: ${leitura.respostas.length} resposta(s), ${m.sem_resposta?.length ?? 0} sem resposta, ${m.marcas_multiplas?.length ?? 0} com mais de uma marca. O arquivo foi descartado; ficou só o hash.`,
        },
        hashArquivo: leitura.hashArquivo,
        detalhes: { checklist: leitura.checklist, respostas: leitura.respostas.length, versao: leitura.hashEnunciados.slice(0, 16) },
      };
    }).finally(() => revalidatePath(`/processos/${id}`, "layout"));
  } catch (e) {
    if (e instanceof VersaoDesconhecida || e instanceof ArquivoInvalido) return { erro: e.message };
    return { erro: mensagemDeErro(e) };
  }
}

/** Linha do M11 de um checklist em uso no processo (ou complemento). */
function linhaDaPergunta(m11: readonly LinhaM11[], pergunta: string, checklists: string[]): LinhaM11 | null {
  const linha = m11.find((l) => l.id === pergunta);
  if (!linha) return null;
  return linha.checklist === "COMPLEMENTO" || checklists.includes(linha.checklist) ? linha : null;
}

/** Valor do formulário conforme o tipo da pergunta; null quando vazio. */
function valorDoFormulario(linha: LinhaM11, dados: FormData): Valor {
  if (linha.tipo_resposta === "MULTIPLA") {
    const marcadas = dados.getAll("valor").map(String).filter(Boolean);
    return marcadas.length ? marcadas : null;
  }
  if (linha.tipo_resposta === "TABELA") {
    const campos = /campos:\s*(.+)$/.exec(linha.opcoes)?.[1].split(/;\s*/) ?? [];
    const entrada = Object.fromEntries(campos.map((c) => [c, String(dados.get(`campo:${c}`) ?? "").trim()]).filter(([, v]) => v));
    return Object.keys(entrada).length ? [entrada] : null;
  }
  const v = String(dados.get("valor") ?? "").trim();
  if (linha.tipo_resposta === "NUMERO" && /^\d+([.,]\d+)?$/.test(v)) return Number(v.replace(",", "."));
  return v || null;
}

export async function salvarResposta(id: string, _anterior: Resultado, dados: FormData): Promise<Resultado> {
  const pergunta = String(dados.get("pergunta") ?? "");
  const linhaId = Number(dados.get("linha") ?? 0) || null;
  const confirmar = String(dados.get("confirmarMotivo") ?? "");
  try {
    return await gravarNoProcesso<Resultado>(id, "RESPOSTA_CHECKLIST", async (tx, p, usuario) => {
      const { pacote } = carregarPacote(p.processo.pacote);
      const linha = linhaDaPergunta(pacote.matrizes.M11, pergunta, p.processo.checklists);
      if (!linha || linha.checklist === "COMPLEMENTO") return { resultado: { erro: "Pergunta não encontrada." } };
      const valor = valorDoFormulario(linha, dados);
      const texto = String(dados.get("texto") ?? "").trim() || null;
      const numeroDigitado = String(dados.get("numero") ?? "").trim();
      const numero = numeroDigitado ? Number(numeroDigitado.replace(",", ".")) : null;
      if (numero !== null && !Number.isFinite(numero)) return { resultado: { erro: "O número precisa ser só algarismos." } };
      const itens = linha.por_item === "S" ? itensCitados(`itens ${String(dados.get("itens") ?? "")}`) : [];
      const campos = { valor, texto, numero: numero === null ? null : String(numero), itens, origem: "OPERADOR" as const };
      if (linhaId) {
        await tx.update(respostaChecklist).set(campos).where(and(eq(respostaChecklist.id, linhaId), eq(respostaChecklist.processoId, id), eq(respostaChecklist.pergunta, pergunta)));
      } else {
        await tx
          .insert(respostaChecklist)
          .values({ processoId: id, pergunta, ...campos })
          .onConflictDoUpdate({ target: [respostaChecklist.processoId, respostaChecklist.pergunta, respostaChecklist.itens], set: campos });
      }
      await tx.update(processo).set({ leituraChecklist: semPerguntaNaLeitura(p.processo.leituraChecklist as LeiturasGravadas, pergunta) }).where(eq(processo.id, id));
      if (confirmar) {
        await tx
          .insert(revisaoConfirmada)
          .values({ processoId: id, pergunta, motivo: confirmar, resposta: JSON.stringify(valor), confirmadoPor: usuario.id })
          .onConflictDoUpdate({ target: [revisaoConfirmada.processoId, revisaoConfirmada.pergunta, revisaoConfirmada.motivo], set: { resposta: JSON.stringify(valor), confirmadoPor: usuario.id } });
      }
      return { resultado: { aviso: `Resposta da ${pergunta} salva.` }, detalhes: { pergunta, itens: itens.join(",") || null } };
    }).finally(() => revalidatePath(`/processos/${id}`, "layout"));
  } catch (e) {
    return { erro: mensagemDeErro(e) };
  }
}

export async function apagarResposta(id: string, _anterior: Resultado, dados: FormData): Promise<Resultado> {
  const linhaId = Number(dados.get("linha") ?? 0);
  try {
    return await gravarNoProcesso<Resultado>(id, "RESPOSTA_CHECKLIST", async (tx) => {
      const [apagada] = await tx.delete(respostaChecklist).where(and(eq(respostaChecklist.id, linhaId), eq(respostaChecklist.processoId, id))).returning({ pergunta: respostaChecklist.pergunta });
      return { resultado: { aviso: apagada ? `Resposta da ${apagada.pergunta} apagada.` : "Nada a apagar." }, detalhes: { pergunta: apagada?.pergunta ?? null, apagada: true } };
    }).finally(() => revalidatePath(`/processos/${id}`, "layout"));
  } catch (e) {
    return { erro: mensagemDeErro(e) };
  }
}

/** Trava conferida: o operador confirma a resposta como está (revisao_confirmada). */
export async function confirmarRevisao(id: string, _anterior: Resultado, dados: FormData): Promise<Resultado> {
  const pergunta = String(dados.get("pergunta") ?? "");
  const motivo = String(dados.get("motivo") ?? "");
  const resposta = String(dados.get("resposta") ?? "").trim() || "Confirmada como está";
  try {
    return await gravarNoProcesso<Resultado>(id, "REVISAO_CONFIRMADA", async (tx, p, usuario) => {
      const { pacote } = carregarPacote(p.processo.pacote);
      if (!linhaDaPergunta(pacote.matrizes.M11, pergunta, p.processo.checklists)) return { resultado: { erro: "Pergunta não encontrada." } };
      await tx
        .insert(revisaoConfirmada)
        .values({ processoId: id, pergunta, motivo, resposta, confirmadoPor: usuario.id })
        .onConflictDoUpdate({ target: [revisaoConfirmada.processoId, revisaoConfirmada.pergunta, revisaoConfirmada.motivo], set: { resposta, confirmadoPor: usuario.id } });
      return { resultado: { aviso: `Revisão da ${pergunta} confirmada.` }, detalhes: { pergunta, motivo } };
    }).finally(() => revalidatePath(`/processos/${id}`, "layout"));
  } catch (e) {
    return { erro: mensagemDeErro(e) };
  }
}

export async function salvarComplemento(id: string, _anterior: Resultado, dados: FormData): Promise<Resultado> {
  const pergunta = String(dados.get("pergunta") ?? "");
  try {
    return await gravarNoProcesso<Resultado>(id, "COMPLEMENTO_OPERADOR", async (tx, p) => {
      const { pacote } = carregarPacote(p.processo.pacote);
      const linha = linhaDaPergunta(pacote.matrizes.M11, pergunta, p.processo.checklists);
      if (!linha || linha.checklist !== "COMPLEMENTO") return { resultado: { erro: "Complemento não encontrado." } };
      const ler = (campo: string): Valor => {
        const bruto = String(dados.get(campo) ?? "").trim();
        if (!bruto) return null;
        if (linha.tipo_resposta === "NUMERO") return Number(bruto.replace(",", "."));
        if (linha.tipo_resposta === "MULTIPLA") return itensCitados(`itens ${bruto}`);
        return bruto;
      };
      let valor: Valor;
      if (linha.por_item === "S") {
        const porItem: Record<string, Valor> = {};
        for (const item of p.itens) {
          const v = ler(`item:${item.numero}`);
          if (v !== null) porItem[String(item.numero)] = v;
        }
        valor = Object.keys(porItem).length ? porItem : null;
      } else {
        valor = ler("valor");
      }
      if (typeof valor === "number" && !Number.isFinite(valor)) return { resultado: { erro: "O número precisa ser só algarismos." } };
      if (valor === null || (Array.isArray(valor) && valor.length === 0)) {
        await tx.delete(complementoOperador).where(and(eq(complementoOperador.processoId, id), eq(complementoOperador.pergunta, pergunta)));
      } else {
        await tx
          .insert(complementoOperador)
          .values({ processoId: id, pergunta, valor })
          .onConflictDoUpdate({ target: [complementoOperador.processoId, complementoOperador.pergunta], set: { valor } });
      }
      return { resultado: { aviso: `Complemento ${pergunta} salvo.` }, detalhes: { pergunta } };
    }).finally(() => revalidatePath(`/processos/${id}`, "layout"));
  } catch (e) {
    return { erro: mensagemDeErro(e) };
  }
}

export async function irParaItens(id: string): Promise<void> {
  await gravarNoProcesso(id, "PROCESSO_ALTERADO", async (tx, p) => {
    await avancarEtapa(tx, p, "ITENS");
    return { resultado: null, detalhes: { etapa: "ITENS" } };
  });
  redirect(`/processos/${id}/itens`);
}
