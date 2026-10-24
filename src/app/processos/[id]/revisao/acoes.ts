"use server";
/** Ação da tela da minuta (passo 10): a minuta conferida segue para a exportação, com o hash dela na auditoria. */
import { redirect } from "next/navigation";
import { avancarEtapa, gravarNoProcesso } from "@/dados/acesso-processo.ts";
import { minutaDoProcesso } from "@/dados/processos.ts";
import { hashDaMinuta } from "@/exportacao/secoes.ts";

export async function irParaExportar(id: string): Promise<void> {
  await gravarNoProcesso(id, "MINUTA_GERADA", async (tx, p) => {
    const minuta = minutaDoProcesso(p);
    await avancarEtapa(tx, p, "EXPORTACAO");
    return {
      resultado: null,
      detalhes: { hashMinuta: hashDaMinuta(minuta), bloqueada: minuta.bloqueada, lacunas: minuta.lacunasNoTexto.length, trechos: minuta.trechos.length },
    };
  });
  redirect(`/processos/${id}/exportar`);
}
