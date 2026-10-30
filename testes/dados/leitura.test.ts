/**
 * Leitura do checklist em Word (passo 6), com Words preenchidos fictícios montados por código a partir dos em
 * branco. Cobre cada motivo de revisão: sem resposta, duas marcas, "Outro" ilegível, nome de pessoa e resposta
 * única para vários itens, passando a leitura pelo motor (revisão do M11). Não precisa de banco.
 */
import { describe, expect, it } from "vitest";
import { carregarPacote } from "../../src/dados/pacote.ts";
import { ArquivoInvalido } from "../../src/dados/leitura-checklist/docx.ts";
import { type Leitura, VersaoDesconhecida, itensCitados, lerChecklist } from "../../src/dados/leitura-checklist/ler.ts";
import { gerarMinuta } from "../../src/motor/minuta.ts";
import type { Valor } from "../../src/motor/pacote/avaliador.ts";
import { variavelDoId } from "../../src/motor/pacote/nomes.ts";
import { ChecklistFicticio } from "./checklist-ficticio.ts";

const { pacote, hash } = carregarPacote();
const resposta = (l: Leitura, pergunta: string) => l.respostas.filter((r) => r.pergunta === pergunta);

/** Revisão do motor sobre o que a leitura produziu (o mesmo caminho do banco: respostas globais e por item). */
function revisao(l: Leitura, itens = [1, 2, 3]) {
  const checklist: Record<string, Valor> = {};
  const porItem: Record<number, Record<string, Valor>> = {};
  for (const r of l.respostas) {
    const nome = variavelDoId(r.pergunta);
    const valores: Record<string, Valor> = { [nome]: r.valor, ...(r.texto ? { [`${nome}_texto`]: r.texto } : {}), ...(r.numero !== null ? { [`${nome}_numero`]: r.numero } : {}) };
    if (r.itens.length) for (const n of r.itens) porItem[n] = { ...porItem[n], ...valores };
    else Object.assign(checklist, valores);
  }
  const minuta = gerarMinuta({
    pacote,
    hashDoPacote: hash,
    checklist,
    wizard: {},
    variaveis: {},
    itens: itens.map((numero) => ({ numero, respostas_por_item: porItem[numero] })),
    metadados: { checklist: l.metadados },
  });
  const motivos = new Map<string, string[]>();
  for (const d of minuta.revisao.destaques) motivos.set(d.pergunta, d.motivos.map((m) => m.motivo));
  return { motivos, perguntas: minuta.revisao.perguntasAoOperador.map((p) => `${p.pergunta}:${p.motivo}`) };
}

describe("checklist em branco", () => {
  it.each(["CONSUMO", "PERMANENTES"] as const)("%s: versão reconhecida, nenhuma resposta, nada pendente", async (c) => {
    const l = await lerChecklist(await (await ChecklistFicticio.de(c)).gerar(), pacote);
    expect(l.checklist).toBe(c);
    expect(l.respostas).toEqual([]);
    expect(l.metadados.leitura_pendencias).toEqual([]);
    expect(l.metadados.sem_resposta?.length).toBe(pacote.matrizes.M11.filter((x) => x.id.startsWith(c === "CONSUMO" ? "CK-C-" : "CK-P-")).length);
    expect(l.metadados.sha256_modelo).toBe(c === "CONSUMO" ? "6294e718c983" : "7c6d3cc9bf16");
  });
});

describe("checklist de consumo preenchido", async () => {
  const doc = (await ChecklistFicticio.de("CONSUMO"))
    .preencherCampo("Nº do processo", "00000.000000/2026-00")
    .preencherCampo("Responsável técnico", "Responsável Fictício A")
    .responder("1.1", "Hospital Fictício")
    .preencherCampo("Nome", "Responsável Fictício B", "1.4")
    .preencherCampo("Posto/graduação", "Cargo Fictício", "1.4")
    .marcar("1.5", "Medicamentos")
    .marcar("1.5", "Materiais de enfermagem", "X")
    .marcar("2.5", "Sim")
    .responder("2.5", "Cerca de 40 pacientes")
    .marcar("3.2", "Sim")
    .marcar("3.2", "Não")
    .marcar("9.1", "Sim")
    .responder("9.7", "Fulano Fictício de Tal")
    .marcar("12.1", "Outro")
    .preencherCampo("Prazo solicitado", "45 dias", "12.1")
    .marcar("16.3", "Outro")
    .preencherCampo("Prazo escolhido / justificativa, se necessário", "uma semana", "16.3")
    .responder("14.1", "Itens 1 e 2: 24 meses; item 3: 36 meses")
    .marcar("14.2", "12 meses", "☑");
  const l = await lerChecklist(await doc.gerar(), pacote);
  const r = revisao(l);

  it("cabeçalho, caixa de texto, tabela e várias marcas (inclusive X no lugar do ☐)", () => {
    expect(resposta(l, "CK-C-CAB.01")[0].valor).toBe("00000.000000/2026-00");
    expect(resposta(l, "CK-C-1.1")[0].valor).toBe("Hospital Fictício");
    expect(resposta(l, "CK-C-1.4")[0].valor).toEqual([{ Nome: "Responsável Fictício B", "Posto/graduação": "Cargo Fictício" }]);
    expect(resposta(l, "CK-C-1.5")[0].valor).toEqual(["Medicamentos", "Materiais de enfermagem"]);
    expect(resposta(l, "CK-C-2.5")[0]).toMatchObject({ valor: "Sim", texto: "Cerca de 40 pacientes" });
  });

  it("sem resposta: pergunta não preenchida fica destacada", () => {
    expect(l.metadados.sem_resposta).toContain("CK-C-2.1");
    expect(r.motivos.get("CK-C-2.1")).toContain("SEM_RESPOSTA");
  });

  it("duas marcas: resposta vazia, ID em marcas_multiplas e pergunta ao operador", () => {
    expect(resposta(l, "CK-C-3.2")[0].valor).toBeNull();
    expect(l.metadados.marcas_multiplas).toContain("CK-C-3.2");
    expect(r.motivos.get("CK-C-3.2")).toContain("MARCAS_MULTIPLAS");
  });

  it("'Outro' com número e unidade vira _numero; 'Outro' ilegível fica sem número e vira pergunta", () => {
    expect(resposta(l, "CK-C-12.1")[0]).toMatchObject({ valor: "Outro", numero: 45, texto: "45 dias" });
    expect(resposta(l, "CK-C-16.3")[0]).toMatchObject({ valor: "Outro", numero: null, texto: "uma semana" });
    expect(r.motivos.get("CK-C-16.3")).toContain("OUTRO_ILEGIVEL");
    expect(r.perguntas).toContain("CK-C-16.3:OUTRO_ILEGIVEL");
  });

  it("nome de pessoa: resposta à 'Quem...' fica destacada", () => {
    expect(r.motivos.get("CK-C-9.7")).toContain("NOME_DE_PESSOA");
  });

  it("por item: texto ligado aos itens citados; resposta sem item citado é única para vários itens", () => {
    expect(resposta(l, "CK-C-14.1").map((x) => [x.itens, x.valor])).toEqual([
      [[1, 2], "24 meses"],
      [[3], "36 meses"],
    ]);
    expect(resposta(l, "CK-C-14.2")[0]).toMatchObject({ valor: "12 meses", itens: [] });
    expect(l.metadados.resposta_unica_por_item).toEqual(["CK-C-14.2"]);
    expect(r.motivos.get("CK-C-14.2")).toContain("RESPOSTA_UNICA_POR_ITEM");
  });

  it("nome do responsável diferente entre o cabeçalho e a 1.4: divergência de leitura", () => {
    expect(l.metadados.divergencias_leitura).toEqual(["CK-C-CAB.04", "CK-C-1.4"]);
  });

  it("guarda só o hash do arquivo", () => {
    expect(l.hashArquivo).toMatch(/^[0-9a-f]{64}$/);
  });
});

describe("checklist de permanentes preenchido", () => {
  it("cabeçalho em outra disposição e 'Outro' escrito na própria linha", async () => {
    const doc = (await ChecklistFicticio.de("PERMANENTES")).preencherCampo("OMS requisitante", "Hospital Fictício").marcar("13.1", "Outro").escreverNaOpcao("13.1", "Outro: ", "18");
    const l = await lerChecklist(await doc.gerar(), pacote);
    expect(resposta(l, "CK-P-CAB.02")[0].valor).toBe("Hospital Fictício");
    expect(resposta(l, "CK-P-13.1")[0]).toMatchObject({ valor: "Outro: ______ meses", numero: 18 });
  });
});

describe("o que acontece com o Word de verdade", () => {
  const permanentes = () => ChecklistFicticio.de("PERMANENTES");
  const ler = async (doc: ChecklistFicticio) => lerChecklist(await doc.gerar(), pacote);

  it("resposta escrita na mesma linha de 'Resposta:'", async () => {
    const l = await ler((await permanentes()).alterarXml((x) => x.replace(/>Resposta:</, ">Resposta: Hospital Fictício<")));
    expect(resposta(l, "CK-P-1.1")[0].valor).toBe("Hospital Fictício");
  });

  it("resposta escrita num parágrafo fora da caixa, mesmo começando com número", async () => {
    const solto = '<w:p><w:r><w:t xml:space="preserve">4.5. ver memória de cálculo anexa</w:t></w:r></w:p>';
    const l = await ler((await permanentes()).alterarXml((x) => x.replace(/(<w:p\b(?:(?!<w:p\b)[\s\S])*?>4\.6\. )/, `${solto}$1`)));
    expect(resposta(l, "CK-P-4.5")[0].valor).toBe("4.5. ver memória de cálculo anexa");
  });

  it("orientação e opções do modelo não viram resposta", async () => {
    const l = await ler(await permanentes());
    expect(l.respostas).toEqual([]);
  });

  it("pergunta com numeração automática (o número sai do texto)", async () => {
    const l = await ler((await permanentes()).responder("1.1", "Hospital Fictício").alterarXml((x) => x.replace(/>1\.1\. Qual/, ">Qual")));
    expect(resposta(l, "CK-P-1.1")[0].valor).toBe("Hospital Fictício");
  });

  it("enunciado com espaço a mais ou aspas trocadas continua reconhecido", async () => {
    const l = await ler((await permanentes()).alterarXml((x) => x.replace(/>1\.2\. Qual setor/, ">1.2. Qual  setor").replace(/>1\.3\. Qual é o nome/, ">1.3. Qual é o </w:t></w:r><w:r><w:rPr><w:b/></w:rPr><w:t xml:space=\"preserve\">nome")));
    expect(l.checklist).toBe("PERMANENTES");
  });

  it("enunciado partido em dois parágrafos (Word abrindo um PDF)", async () => {
    const l = await ler(
      (await permanentes()).responder("2.1", "Necessidade fictícia").alterarXml((x) => x.replace(/>2\.1\. Qual necessidade assistencial, /, '>2.1. Qual necessidade assistencial,</w:t></w:r></w:p><w:p><w:r><w:t xml:space="preserve">')),
    );
    expect(resposta(l, "CK-P-2.1")[0].valor).toBe("Necessidade fictícia");
  });

  it("caixa de seleção de formulário antigo do Word (FORMCHECKBOX)", async () => {
    const caixa = '</w:t></w:r><w:r><w:fldChar w:fldCharType="begin"><w:ffData><w:checkBox><w:default w:val="0"/><w:checked/></w:checkBox></w:ffData></w:fldChar></w:r><w:r><w:t xml:space="preserve"> ';
    const l = await ler((await permanentes()).alterarXml((x) => x.replace(/(>2\.4\. [\s\S]*?)☐ Sim/, `$1${caixa}Sim`)));
    expect(resposta(l, "CK-P-2.4")[0].valor).toBe("Sim");
  });

  it("pergunta dentro de marcação customXml continua lida", async () => {
    const l = await ler(
      (await permanentes()).alterarXml((x) => x.replace(/(<w:p\b(?:(?!<w:p\b)[\s\S])*?>1\.1\. [^<]*<\/w:t><\/w:r><\/w:p>)/, '<w:customXml w:element="x">$1</w:customXml>')).responder("1.1", "Hospital Fictício"),
    );
    expect(resposta(l, "CK-P-1.1")[0].valor).toBe("Hospital Fictício");
  });

  it("o mesmo item citado duas vezes numa resposta por item junta os textos (a gravação não quebra)", async () => {
    const doc = (await ChecklistFicticio.de("CONSUMO")).responder("14.1", "Item 1: 24 meses; item 1: contados da entrega");
    const l = await lerChecklist(await doc.gerar(), pacote);
    expect(resposta(l, "CK-C-14.1").map((x) => [x.itens, x.valor])).toEqual([[[1], "24 meses; contados da entrega"]]);
  });

  it("pergunta apagada: erro que diz qual pergunta falta", async () => {
    const doc = (await permanentes()).alterarXml((x) => x.replace(/>6\.3\. [^<]*</, "><"));
    await expect(ler(doc)).rejects.toThrow(/pergunta 6\.3 \("Quais itens seriam exclusivos\?"\) falta ou foi alterada/);
  });
});

describe("arquivo que não serve", () => {
  it("versão desconhecida é erro claro, nunca leitura parcial", async () => {
    const doc = (await ChecklistFicticio.de("CONSUMO")).trocarEnunciado("2.1", "Pergunta de outra versão?");
    await expect(lerChecklist(await doc.gerar(), pacote)).rejects.toThrow(VersaoDesconhecida);
    await expect(lerChecklist(await doc.gerar(), pacote)).rejects.toThrow(/pergunta 2\.1 /);
  });

  it("arquivo que não é Word", async () => {
    await expect(lerChecklist(new TextEncoder().encode("não sou um docx"), pacote)).rejects.toThrow(ArquivoInvalido);
  });
});

describe("itens citados", () => {
  it.each([
    ["item 2", [2]],
    ["itens 1, 3 e 5", [1, 3, 5]],
    ["Itens 1 a 4: x", [1, 2, 3, 4]],
    ["sem item", []],
  ])("%s", (texto, esperado) => {
    expect(itensCitados(texto)).toEqual(esperado);
  });
});
