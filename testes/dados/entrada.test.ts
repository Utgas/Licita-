/**
 * Ida e volta pelo banco: cada cenário (C1 a C8, R1 e R2) vira linhas das tabelas do processo, volta para a entrada
 * do motor (entradaDoProcesso) e tem de gerar a mesma minuta que a entrada original. Prova que o banco guarda tudo
 * o que o motor lê, inclusive respostas por item diferentes em itens diferentes. Não precisa de banco.
 */
import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import type { ProcessoCompleto } from "../../src/dados/processos.ts";
import { ATRIBUTOS_DO_ITEM, entradaDoProcesso } from "../../src/dados/processos.ts";
import { carregarPacote } from "../../src/dados/pacote.ts";
import type { EntradaProcesso } from "../../src/motor/entrada.ts";
import { gerarMinuta } from "../../src/motor/minuta.ts";
import type { Valor } from "../../src/motor/pacote/avaliador.ts";
import { variavelDoId } from "../../src/motor/pacote/nomes.ts";

const { pacote, hash } = carregarPacote();
const DIR = path.resolve(import.meta.dirname, "../../matrizes/v1/cenarios");
const idDaVariavel = new Map([...pacote.matrizes.M04, ...pacote.matrizes.M05, ...pacote.matrizes.M11].map((l) => [variavelDoId(l.id), l.id]));
const colunaDoAtributo = new Map<string, string>(Object.entries(ATRIBUTOS_DO_ITEM).map(([coluna, atributo]) => [atributo, coluna]));

type Linha = ProcessoCompleto["respostasChecklist"][number];

/** Linhas do banco a partir da entrada de um cenário (o caminho que as telas fazem ao salvar). */
function linhasDoCenario(entrada: Omit<EntradaProcesso, "pacote" | "hashDoPacote">): ProcessoCompleto {
  const respostas = new Map<string, Linha>();
  const linha = (pergunta: string, itens: number[]): Linha => {
    const chave = `${pergunta}|${itens.join(",")}`;
    if (!respostas.has(chave)) {
      respostas.set(chave, { id: respostas.size + 1, processoId: "p", pergunta, valor: null, texto: null, numero: null, itens, origem: "OPERADOR", atualizadoEm: "" });
    }
    return respostas.get(chave) as Linha;
  };
  const guardar = (chave: string, valor: Valor, itens: number[]) => {
    const [, base, sufixo] = /^(.*?)(_texto|_numero)?$/.exec(chave) as RegExpExecArray;
    const pergunta = idDaVariavel.get(base) as string;
    expect(pergunta, chave).toBeDefined();
    const l = linha(pergunta, itens);
    if (sufixo === "_texto") l.texto = valor as string;
    else if (sufixo === "_numero") l.numero = String(valor);
    else l.valor = valor;
  };
  const complementos: ProcessoCompleto["complementos"] = [];
  for (const [chave, valor] of Object.entries(entrada.checklist)) {
    if (chave.startsWith("CK_X_")) complementos.push({ processoId: "p", pergunta: idDaVariavel.get(chave) as string, valor, atualizadoEm: "" });
    else guardar(chave, valor, []);
  }
  // Por item: itens com a mesma resposta ficam numa linha só.
  const porResposta = new Map<string, number[]>();
  for (const item of entrada.itens) {
    for (const [chave, valor] of Object.entries(item.respostas_por_item ?? {})) {
      const k = JSON.stringify([chave, valor]);
      porResposta.set(k, [...(porResposta.get(k) ?? []), item.numero]);
    }
  }
  for (const [k, itens] of porResposta) {
    const [chave, valor] = JSON.parse(k) as [string, Valor];
    guardar(chave, valor, itens);
  }
  const itens = entrada.itens.map((i) => {
    const l: Record<string, unknown> = { processoId: "p", numero: i.numero, atualizadoEm: "" };
    for (const coluna of Object.keys(ATRIBUTOS_DO_ITEM)) l[coluna] = null;
    for (const [atributo, v] of Object.entries(i)) {
      if (atributo === "numero" || atributo === "respostas_por_item") continue;
      const coluna = colunaDoAtributo.get(atributo);
      expect(coluna, `atributo de item sem coluna: ${atributo}`).toBeDefined();
      l[coluna as string] = typeof v === "number" && (atributo === "quantidade" || atributo === "valor_unitario") ? String(v) : v;
    }
    return l as ProcessoCompleto["itens"][number];
  });
  const respostasWizard = [...Object.entries(entrada.wizard), ...Object.entries(entrada.variaveis)].map(([chave, valor]) => ({
    processoId: "p",
    pergunta: idDaVariavel.get(chave) as string,
    valor,
    justificativa: null,
    origem: "EQUIPE" as const,
    atualizadoEm: "",
  }));
  const temC = Object.keys(entrada.checklist).some((k) => k.startsWith("CK_C_"));
  const temP = Object.keys(entrada.checklist).some((k) => k.startsWith("CK_P_"));
  return {
    processo: {
      id: "p",
      omId: "om",
      numero: "00000.000000/0000-00",
      objeto: "Objeto fictício",
      modalidade: "PREGAO",
      registroPrecos: false,
      checklists: [...(temC || !temP ? (["CONSUMO"] as const) : []), ...(temP ? (["PERMANENTES"] as const) : [])],
      etapa: "MINUTA",
      situacao: "RASCUNHO",
      concluidoEm: null,
      pacote: pacote.pacote,
      pacoteHash: hash,
      leituraChecklist: {},
      criadoPor: "u",
      criadoEm: "",
      atualizadoEm: "",
    },
    om: { id: "om", uasg: "999999", nome: "OM Fictícia", cabecalho: [], dados: {}, criadoEm: "" },
    respostasChecklist: [...respostas.values()],
    revisoes: [],
    complementos,
    itens,
    respostasWizard,
    exportacoes: [],
  };
}

describe.each(["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "R1", "R2"])("cenário %s pelo banco", (id) => {
  it("gera a mesma minuta que a entrada original", () => {
    const { entrada } = JSON.parse(readFileSync(path.join(DIR, `${id}.json`), "utf8"));
    const linhas = linhasDoCenario(structuredClone(entrada));
    const pelaBase = entradaDoProcesso(linhas);
    // Os metadados do processo vêm do banco (checklists marcados e textos livres digitados); a entrada original
    // recebe os mesmos, para comparar só o caminho pelo banco.
    const original: EntradaProcesso = { ...structuredClone(entrada), pacote, hashDoPacote: hash, metadados: pelaBase.metadados, om: pelaBase.om };
    const a = gerarMinuta(original);
    const b = gerarMinuta(pelaBase);
    expect(b.blocos).toEqual(a.blocos);
    expect(b.clausulasSetoriais).toEqual(a.clausulasSetoriais);
    expect(b.validacoes.disparadas.map((v) => v.id)).toEqual(a.validacoes.disparadas.map((v) => v.id));
    expect(b.trechos.map((t) => t.texto)).toEqual(a.trechos.map((t) => t.texto));
    expect(b.bloqueada).toBe(a.bloqueada);
  });
});
