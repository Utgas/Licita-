/**
 * Processo no banco <-> entrada do motor. O banco guarda respostas, itens e confirmações; a minuta é sempre
 * remontada pelo motor a partir deles e do pacote com que o processo nasceu (arquitetura, "Modelo de dados").
 */
import { asc, eq } from "drizzle-orm";
import type { EntradaProcesso, ItemDeEntrada, LeituraDoChecklist } from "../motor/entrada.ts";
import { type Minuta, gerarMinuta } from "../motor/minuta.ts";
import type { Valor } from "../motor/pacote/avaliador.ts";
import { variavelDoId } from "../motor/pacote/nomes.ts";
import type { Transacao } from "./conexao.ts";
import * as t from "./esquema.ts";
import { carregarPacote } from "./pacote.ts";

export type ProcessoCompleto = {
  processo: typeof t.processo.$inferSelect;
  om: typeof t.om.$inferSelect;
  respostasChecklist: (typeof t.respostaChecklist.$inferSelect)[];
  revisoes: (typeof t.revisaoConfirmada.$inferSelect)[];
  complementos: (typeof t.complementoOperador.$inferSelect)[];
  itens: (typeof t.item.$inferSelect)[];
  respostasWizard: (typeof t.respostaWizard.$inferSelect)[];
  exportacoes: (typeof t.exportacao.$inferSelect)[];
};

/** Tudo do processo, lido com o RLS de quem pede; null quando não existe ou é de outra OM. */
export async function carregarProcesso(tx: Transacao, id: string): Promise<ProcessoCompleto | null> {
  if (!/^[0-9a-f-]{36}$/.test(id)) return null;
  const [processo] = await tx.select().from(t.processo).where(eq(t.processo.id, id));
  if (!processo) return null;
  const [om] = await tx.select().from(t.om).where(eq(t.om.id, processo.omId));
  return {
    processo,
    om,
    respostasChecklist: await tx.select().from(t.respostaChecklist).where(eq(t.respostaChecklist.processoId, id)).orderBy(asc(t.respostaChecklist.pergunta)),
    revisoes: await tx.select().from(t.revisaoConfirmada).where(eq(t.revisaoConfirmada.processoId, id)),
    complementos: await tx.select().from(t.complementoOperador).where(eq(t.complementoOperador.processoId, id)),
    itens: await tx.select().from(t.item).where(eq(t.item.processoId, id)).orderBy(asc(t.item.numero)),
    respostasWizard: await tx.select().from(t.respostaWizard).where(eq(t.respostaWizard.processoId, id)),
    exportacoes: await tx.select().from(t.exportacao).where(eq(t.exportacao.processoId, id)).orderBy(asc(t.exportacao.id)),
  };
}

/** Colunas da tabela item -> atributo do M05 (tabela_itens.*). */
export const ATRIBUTOS_DO_ITEM = {
  especificacao: "especificacao",
  catmat: "catmat",
  unidadeMedida: "unidade_medida",
  quantidade: "quantidade",
  valorUnitario: "valor_unitario",
  classePdm: "classe_pdm",
  grupo: "grupo",
  categoria: "categoria",
  exigeAmostra: "exige_amostra",
  marcaIndicada: "marca_indicada",
  validadeMinima: "validade_minima",
  compatibilidade: "compatibilidade",
  faixaTemperatura: "faixa_temperatura",
  controleEspecial: "controle_especial",
  garantiaMinimaMeses: "garantia_minima_meses",
  justificativaExcecaoMeEpp: "justificativa_excecao_me_epp",
} as const satisfies Partial<Record<keyof typeof t.item.$inferSelect, string>>;

const NUMERICOS = new Set(["quantidade", "valor_unitario"]);

/** Entrada do motor a partir do que está no banco. Nada é inventado: o que falta fica ausente. */
export function entradaDoProcesso(p: ProcessoCompleto): EntradaProcesso {
  const { pacote, hash } = carregarPacote(p.processo.pacote);
  if (hash !== p.processo.pacoteHash) throw new Error("o pacote de regras do processo mudou desde a criação");
  const porItem = new Set(pacote.matrizes.M11.filter((l) => l.por_item === "S").map((l) => l.id));

  const itens: ItemDeEntrada[] = p.itens.map((linha) => {
    const item: ItemDeEntrada = { numero: linha.numero };
    for (const [coluna, atributo] of Object.entries(ATRIBUTOS_DO_ITEM)) {
      const v = linha[coluna as keyof typeof ATRIBUTOS_DO_ITEM];
      if (v === null || v === "") continue;
      item[atributo] = NUMERICOS.has(atributo) ? Number(v) : v;
    }
    return item;
  });
  const porNumero = new Map(itens.map((i) => [i.numero, i]));

  const checklist: Record<string, Valor> = {};
  for (const r of p.respostasChecklist) {
    const nome = variavelDoId(r.pergunta);
    const valores: Record<string, Valor> = {};
    if (r.valor !== null) valores[nome] = r.valor as Valor;
    if (r.texto) valores[`${nome}_texto`] = r.texto;
    if (r.numero !== null) valores[`${nome}_numero`] = Number(r.numero);
    if (porItem.has(r.pergunta) && r.itens.length > 0) {
      for (const n of r.itens) {
        const item = porNumero.get(n);
        if (item) item.respostas_por_item = { ...item.respostas_por_item, ...valores };
      }
    } else {
      Object.assign(checklist, valores);
    }
  }
  const complementoPorItem = new Set(pacote.matrizes.M11.filter((l) => l.checklist === "COMPLEMENTO" && l.por_item === "S").map((l) => l.id));
  for (const c of p.complementos) {
    const nome = variavelDoId(c.pergunta);
    if (!complementoPorItem.has(c.pergunta)) {
      checklist[nome] = c.valor as Valor;
      continue;
    }
    // Complemento por item: { "1": valor, "3": valor }.
    for (const [n, v] of Object.entries((c.valor ?? {}) as Record<string, Valor>)) {
      const item = porNumero.get(Number(n));
      if (item && v !== null && v !== "") item.respostas_por_item = { ...item.respostas_por_item, [nome]: v };
    }
  }

  const wizard: Record<string, Valor> = {};
  const variaveis: Record<string, Valor> = {};
  const justificativas: Record<string, string> = {};
  for (const r of p.respostasWizard) {
    if (r.pergunta.startsWith("WZ-") && r.justificativa?.trim()) justificativas[variavelDoId(r.pergunta)] = r.justificativa;
    if (r.valor === null) continue;
    (r.pergunta.startsWith("WZ-") ? wizard : variaveis)[variavelDoId(r.pergunta)] = r.valor as Valor;
  }

  // Texto livre que o processo tem (caixas de resposta, complementos, justificativas e campos de texto): as
  // validações do M10 procuram nele citação de norma revogada e justificativa genérica.
  const textosLivres = [
    ...p.respostasChecklist.map((r) => r.texto),
    ...p.complementos.map((c) => c.valor),
    ...p.respostasWizard.flatMap((r) => [r.justificativa, r.valor]),
  ].filter((x): x is string => typeof x === "string" && x.trim() !== "");

  const leitura = juntarLeituras(p.processo.leituraChecklist as LeiturasGravadas);
  return {
    pacote,
    hashDoPacote: hash,
    checklist,
    wizard,
    justificativas,
    itens,
    variaveis,
    metadados: {
      ...(textosLivres.length > 0 ? { textos_livres: textosLivres.join("\n") } : {}),
      checklist: {
        consumo: p.processo.checklists.includes("CONSUMO"),
        permanentes: p.processo.checklists.includes("PERMANENTES"),
        ...leitura,
      },
    },
    revisoes_confirmadas: [...new Set(p.revisoes.map((r) => r.pergunta))],
    om: { uasg: p.om.uasg, nome: p.om.nome, cabecalho: p.om.cabecalho, ...(p.om.dados as Record<string, Valor>) },
  };
}

/** Metadados da leitura do Word, guardados por checklist: cada envio substitui só os do seu checklist. */
export type LeiturasGravadas = Partial<Record<"CONSUMO" | "PERMANENTES", LeituraDoChecklist>>;

const LISTAS_DA_LEITURA = ["marcas_multiplas", "resposta_unica_por_item", "divergencias_leitura", "leitura_pendencias", "sem_resposta"] as const;

export function juntarLeituras(gravadas: LeiturasGravadas): LeituraDoChecklist {
  const junta: LeituraDoChecklist = {};
  for (const leitura of Object.values(gravadas)) {
    if (!leitura) continue;
    for (const lista of LISTAS_DA_LEITURA) junta[lista] = [...(junta[lista] ?? []), ...(leitura[lista] ?? [])];
    // VAL-036 compara o modelo com o M11: basta um checklist fora da versão para acusar.
    if (leitura.sha256_modelo && (!junta.sha256_modelo || leitura.sha256_modelo !== leitura.sha256_m11)) {
      junta.sha256_modelo = leitura.sha256_modelo;
      junta.sha256_m11 = leitura.sha256_m11;
    }
  }
  return junta;
}

/** Tira uma pergunta das listas da leitura (o operador corrigiu ou confirmou a resposta na tela). */
export function semPerguntaNaLeitura(gravadas: LeiturasGravadas, pergunta: string): LeiturasGravadas {
  const novas: LeiturasGravadas = {};
  for (const [c, leitura] of Object.entries(gravadas) as [keyof LeiturasGravadas, LeituraDoChecklist][]) {
    const copia: LeituraDoChecklist = { ...leitura };
    for (const lista of LISTAS_DA_LEITURA) if (copia[lista]) copia[lista] = copia[lista].filter((x) => x !== pergunta);
    novas[c] = copia;
  }
  return novas;
}

export function minutaDoProcesso(p: ProcessoCompleto): Minuta {
  return gerarMinuta(entradaDoProcesso(p));
}

/** Data em que o expurgo apaga o processo concluído (30 dias depois; arquitetura, "Segurança e retenção"). */
export const DIAS_ATE_O_EXPURGO = 30;
export function dataDoExpurgo(concluidoEm: string | null): Date | null {
  if (!concluidoEm) return null;
  return new Date(new Date(concluidoEm).getTime() + DIAS_ATE_O_EXPURGO * 24 * 60 * 60 * 1000);
}

export type Pendencias = { travas: number; perguntas: number; bloqueios: number; lacunas: number; bloqueada: boolean };

/** Resumo do que falta, para o painel e o cabeçalho do processo. */
export function pendenciasDaMinuta(m: Minuta): Pendencias {
  return {
    travas: m.revisao.perguntasAoOperador.length,
    perguntas: m.perguntasSemResposta.length,
    bloqueios: m.validacoes.disparadas.filter((v) => v.tipo === "BLOQUEIO").length + m.bloqueiosGrupoAlternativas.length,
    lacunas: m.lacunasNoTexto.length,
    bloqueada: m.bloqueada,
  };
}
