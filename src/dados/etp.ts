/**
 * ETP do processo (Marco 3): o mesmo dado do banco monta a minuta do TR e o ETP, e a derivação liga os dois
 * (decisão 0015). Aqui também ficam os campos que a equipe informa na tela do ETP.
 */
import { and, eq } from "drizzle-orm";
import { type Derivacao, derivarEtpParaTr } from "../motor/derivacao/derivacao.ts";
import type { EntradaProcesso } from "../motor/entrada.ts";
import { type Minuta, gerarMinuta } from "../motor/minuta.ts";
import { type Etp, gerarEtp } from "../motor/montagem/etp.ts";
import type { Valor } from "../motor/pacote/avaliador.ts";
import type { Pacote } from "../motor/pacote/esquema.ts";
import type { Transacao } from "./conexao.ts";
import { respostaWizard } from "./esquema.ts";
import { type ProcessoCompleto, entradaDoProcesso } from "./processos.ts";
import { type CampoDaMinuta, campoDaVariavel } from "./wizard.ts";

export type DocumentosDoProcesso = { entrada: EntradaProcesso; minuta: Minuta; etp: Etp; derivacao: Derivacao };

export function documentosDoProcesso(p: ProcessoCompleto): DocumentosDoProcesso {
  const entrada = entradaDoProcesso(p);
  const minuta = gerarMinuta(entrada);
  const etp = gerarEtp(entrada, minuta);
  return { entrada, minuta, etp, derivacao: derivarEtpParaTr(entrada.pacote, minuta, etp) };
}

/** VAR que a equipe informa na tela do ETP: dado de um campo do ETP, nem calculado nem coluna de item. */
export type CampoDoEtpParaInformar = CampoDaMinuta & {
  /** Campos do ETP onde o dado aparece. */
  camposDoEtp: string[];
  /** Perguntas do checklist que também preenchem o dado (a resposta da equipe vale sobre elas). */
  doChecklist: string[];
  /** Valor que o processo tem hoje, venha da equipe ou do checklist. */
  valorAtual: Valor;
};

export function camposParaInformar(pacote: Pacote, documentos: DocumentosDoProcesso, p: ProcessoCompleto): CampoDoEtpParaInformar[] {
  const m05 = new Map(pacote.matrizes.M05.map((l) => [l.id, l]));
  const informadas = new Map(p.respostasWizard.filter((r) => r.pergunta.startsWith("VAR-")).map((r) => [r.pergunta, r.valor as Valor]));
  const porVariavel = new Map<string, string[]>();
  for (const campo of documentos.etp.campos) {
    for (const parte of campo.partes) {
      if (parte.tipo !== "dado") continue;
      const linha = m05.get(parte.regra);
      if (!linha || linha.calculo_expr !== null || linha.nome.startsWith("tabela_itens.")) continue;
      porVariavel.set(parte.regra, [...(porVariavel.get(parte.regra) ?? []), campo.id]);
    }
  }
  const origens = documentos.minuta.processo.origens;
  return [...porVariavel].map(([id, camposDoEtp]) => {
    const variavel = id.replace("-", "_");
    const origem = origens[variavel];
    return {
      ...campoDaVariavel(pacote, m05.get(id) as NonNullable<ReturnType<typeof m05.get>>, informadas.get(id) ?? null),
      camposDoEtp,
      doChecklist: origem?.origem === "CHECKLIST" ? origem.perguntas : [],
      valorAtual: documentos.minuta.processo.globais[variavel] ?? null,
    };
  });
}

/** Grava (ou apaga, com valor nulo) uma VAR informada pela equipe. */
export async function gravarVariavel(tx: Transacao, processoId: string, variavel: string, valor: Valor): Promise<void> {
  if (valor === null) {
    await tx.delete(respostaWizard).where(and(eq(respostaWizard.processoId, processoId), eq(respostaWizard.pergunta, variavel)));
    return;
  }
  const campos = { valor, origem: "EQUIPE" as const };
  await tx
    .insert(respostaWizard)
    .values({ processoId, pergunta: variavel, ...campos })
    .onConflictDoUpdate({ target: [respostaWizard.processoId, respostaWizard.pergunta], set: campos });
}
