"use server";
/**
 * Ações da tela do ETP (Marco 3, passo 8): dado do ETP informado pela equipe (mesma tabela das respostas do wizard)
 * e marca de campo copiado para o ETP Digital (exportacao, com secao = ID do campo; decisão 0015).
 */
import { revalidatePath } from "next/cache";
import type { Resultado } from "@/auth/acoes.ts";
import { EntradaRecusada, gravarNoProcesso, mensagemDeErro } from "@/dados/acesso-processo.ts";
import { exportacao } from "@/dados/esquema.ts";
import { camposParaInformar, documentosDoProcesso, gravarVariavel } from "@/dados/etp.ts";
import { carregarPacote } from "@/dados/pacote.ts";
import { valorDoCampo } from "@/dados/wizard.ts";
import { camposParaCopiar, etpLiberado, hashDoEtp } from "@/exportacao/etp.ts";

export async function salvarCampoDoEtp(id: string, _anterior: Resultado, dados: FormData): Promise<Resultado> {
  const variavel = String(dados.get("campo") ?? "");
  try {
    return await gravarNoProcesso<Resultado>(id, "RESPOSTA_WIZARD", async (tx, p) => {
      const { pacote } = carregarPacote(p.processo.pacote, p.processo.pacoteHash);
      const campo = camposParaInformar(pacote, documentosDoProcesso(p), p).find((c) => c.id === variavel);
      if (!campo) throw new EntradaRecusada("Campo não encontrado.");
      const lido = valorDoCampo(campo, dados);
      if ("erro" in lido) throw new EntradaRecusada(lido.erro);
      await gravarVariavel(tx, id, variavel, lido.valor);
      const apagada = lido.valor === null;
      return { resultado: { aviso: `${variavel} ${apagada ? "apagada" : "salva"}.` }, detalhes: { pergunta: variavel, apagada, documento: "ETP" } };
    }).finally(() => revalidatePath(`/processos/${id}`, "layout"));
  } catch (e) {
    return { erro: mensagemDeErro(e) };
  }
}

export async function registrarCopiaDoEtp(id: string, campo: string): Promise<Resultado> {
  try {
    return await gravarNoProcesso<Resultado>(
      id,
      "ETP_CAMPO_COPIADO",
      async (tx, p, usuario) => {
        const { minuta, etp } = documentosDoProcesso(p);
        if (!etpLiberado(minuta)) throw new EntradaRecusada("Há dúvidas da leitura do checklist sem resposta: resolva-as antes de copiar o ETP.");
        if (!camposParaCopiar(etp).some((c) => c.id === campo)) throw new EntradaRecusada("Campo não encontrado.");
        await tx.insert(exportacao).values({ processoId: id, tipo: "COPIA_SECAO", secao: campo, feitoPor: usuario.id });
        return { resultado: { aviso: "Copiado." }, detalhes: { campo, hashEtp: hashDoEtp(etp) } };
      },
      { permitirConcluido: true },
    ).finally(() => revalidatePath(`/processos/${id}/etp`));
  } catch (e) {
    return { erro: mensagemDeErro(e) };
  }
}
