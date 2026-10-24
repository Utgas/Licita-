/**
 * Word fictício do teste de tela: o checklist de consumo em branco com todas as perguntas respondidas (a primeira
 * opção, ou "Não" quando houver; texto e número fictícios), a partir do M11. Os anexos obrigatórios (3.1 e 4.8)
 * ficam "Sim". Duas marcas na 3.3 provocam uma trava, que o teste resolve na tela.
 */
import { carregarPacote } from "../../src/dados/pacote.ts";
import { ChecklistFicticio } from "../dados/checklist-ficticio.ts";

const SIM = new Set(["3.1", "4.8"]);

export async function wordFicticioCompleto(numeroDoProcesso: string): Promise<Buffer> {
  const { pacote } = carregarPacote();
  const word = await ChecklistFicticio.de("CONSUMO");
  for (const l of pacote.matrizes.M11.filter((x) => x.checklist === "CONSUMO")) {
    const opcoes = l.opcoes
      .split(/;\s*/)
      .map((o) => o.trim())
      .filter((o) => o && !o.startsWith("campos:"));
    const campos = /campos:\s*(.+)$/.exec(l.opcoes)?.[1].split(/;\s*/) ?? [];
    if (l.numero.startsWith("CAB")) {
      word.preencherCampo(l.pergunta, l.numero === "CAB.01" ? numeroDoProcesso : "Texto fictício");
      continue;
    }
    if (["UNICA", "SIM_NAO", "MULTIPLA"].includes(l.tipo_resposta) && opcoes.length) {
      word.marcar(l.numero, SIM.has(l.numero) ? "Sim" : opcoes.includes("Não") ? "Não" : opcoes[0]);
    }
    for (const c of campos) word.preencherCampo(c, "Texto fictício", l.numero);
    if (l.tipo_resposta === "TEXTO" || l.tipo_resposta === "NUMERO") word.responder(l.numero, l.tipo_resposta === "NUMERO" ? "10" : "Texto fictício");
  }
  word.marcar("3.3", "Sim");
  return Buffer.from(await word.gerar());
}
