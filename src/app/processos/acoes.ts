"use server";
/** Novo processo (passo 5). As escolhas do formulário já respondem as perguntas do wizard que elas decidem. */
import { redirect } from "next/navigation";
import { z } from "zod";
import type { Resultado } from "@/auth/acoes.ts";
import { exigirUsuario } from "@/auth/sessao.ts";
import { registrar } from "@/auditoria/registrar.ts";
import { bancoDaAplicacao, comoUsuario } from "@/dados/conexao.ts";
import { processo, respostaWizard } from "@/dados/esquema.ts";
import { PACOTE_ATUAL, carregarPacote } from "@/dados/pacote.ts";

const novo = z.object({
  numero: z.string().trim().min(5, "Informe o número do processo.").max(60, "Número do processo longo demais."),
  objeto: z.string().trim().min(5, "Descreva o objeto em poucas palavras.").max(500, "Resuma o objeto em até 500 caracteres."),
  modalidade: z.enum(["PREGAO", "CONCORRENCIA", "CONTRATACAO_DIRETA"], { message: "Escolha a modalidade." }),
  registroPrecos: z.enum(["SIM", "NAO"], { message: "Diga se é registro de preços." }),
  checklists: z.array(z.enum(["CONSUMO", "PERMANENTES"])).min(1, "Marque ao menos um checklist."),
});

export async function criarProcesso(_anterior: Resultado, dados: FormData): Promise<Resultado> {
  const usuario = await exigirUsuario("OPERADOR");
  const lido = novo.safeParse({
    numero: dados.get("numero"),
    objeto: dados.get("objeto"),
    modalidade: dados.get("modalidade"),
    registroPrecos: dados.get("registroPrecos"),
    checklists: dados.getAll("checklists"),
  });
  if (!lido.success) return { erro: lido.error.issues[0].message };
  const d = lido.data;
  const { pacote, hash } = carregarPacote(PACOTE_ATUAL);
  let id: string;
  try {
    id = await comoUsuario(bancoDaAplicacao(), usuario.id, async (tx) => {
      const [linha] = await tx
        .insert(processo)
        .values({ omId: usuario.omId, numero: d.numero, objeto: d.objeto, modalidade: d.modalidade, registroPrecos: d.registroPrecos === "SIM", checklists: d.checklists, pacote: pacote.pacote, pacoteHash: hash, criadoPor: usuario.id })
        .returning({ id: processo.id });
      const licitacao = d.modalidade !== "CONTRATACAO_DIRETA";
      const respostas = [
        { pergunta: "WZ-01", valor: licitacao ? "LICITACAO" : "CONTRATACAO_DIRETA" },
        ...(licitacao ? [{ pergunta: "WZ-02", valor: d.modalidade }] : []),
        { pergunta: "WZ-10", valor: d.registroPrecos },
      ];
      await tx.insert(respostaWizard).values(respostas.map((r) => ({ ...r, processoId: linha.id, origem: "EQUIPE" as const })));
      await registrar(tx, { usuarioId: usuario.id, omId: usuario.omId, processoId: linha.id, acao: "PROCESSO_CRIADO", hashPacote: hash, detalhes: { pacote: pacote.pacote } });
      return linha.id;
    });
  } catch (e) {
    const unico = String((e as { cause?: { code?: string } }).cause?.code) === "23505";
    return { erro: unico ? "Já existe um processo com esse número." : "Não foi possível criar o processo." };
  }
  redirect(`/processos/${id}/checklist`);
}
