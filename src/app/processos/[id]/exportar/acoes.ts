"use server";
/** Ações da exportação (passo 11): marca de seção copiada e conclusão do processo. Só sem travas. */
import { eq, sql } from "drizzle-orm";
import { revalidatePath } from "next/cache";
import type { Resultado } from "@/auth/acoes.ts";
import { EntradaRecusada, gravarNoProcesso, mensagemDeErro } from "@/dados/acesso-processo.ts";
import { exportacao, processo } from "@/dados/esquema.ts";
import { minutaDoProcesso } from "@/dados/processos.ts";
import { hashDaMinuta, secoesDaMinuta } from "@/exportacao/secoes.ts";

export async function registrarCopia(id: string, secao: string): Promise<Resultado> {
  try {
    return await gravarNoProcesso<Resultado>(
      id,
      "SECAO_COPIADA",
      async (tx, p, usuario) => {
        const minuta = minutaDoProcesso(p);
        if (minuta.bloqueada) throw new EntradaRecusada("A minuta tem travas: exportação bloqueada.");
        if (!secoesDaMinuta(minuta).some((s) => s.titulo === secao)) throw new EntradaRecusada("Seção não encontrada.");
        await tx.insert(exportacao).values({ processoId: id, tipo: "COPIA_SECAO", secao, feitoPor: usuario.id });
        return { resultado: { aviso: "Copiado." }, detalhes: { secao, hashMinuta: hashDaMinuta(minuta) } };
      },
      { permitirConcluido: true },
    ).finally(() => revalidatePath(`/processos/${id}/exportar`));
  } catch (e) {
    return { erro: mensagemDeErro(e) };
  }
}

export async function concluirProcesso(id: string, _anterior: Resultado, dados: FormData): Promise<Resultado> {
  if (dados.get("confirmo") !== "sim") return { erro: "Marque a confirmação antes de concluir." };
  try {
    return await gravarNoProcesso<Resultado>(id, "PROCESSO_CONCLUIDO", async (tx, p) => {
      const minuta = minutaDoProcesso(p);
      if (minuta.bloqueada) throw new EntradaRecusada("A minuta tem travas: resolva-as antes de concluir.");
      await tx.update(processo).set({ situacao: "CONCLUIDO", concluidoEm: sql`now()` }).where(eq(processo.id, id));
      return { resultado: { aviso: "Processo concluído." }, detalhes: { hashMinuta: hashDaMinuta(minuta) } };
    }).finally(() => revalidatePath(`/processos/${id}`, "layout"));
  } catch (e) {
    return { erro: mensagemDeErro(e) };
  }
}
