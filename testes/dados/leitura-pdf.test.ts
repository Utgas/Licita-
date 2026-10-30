/**
 * Leitura do checklist em PDF e em .odt (decisão 0017), com arquivos fictícios gerados do Word fictício pelo LibreOffice
 * (gerar-pdfs-ficticios.ts). Cobre o que chega das OMs: X colado no ☐, valor embaixo do rótulo ou colado nele,
 * resposta em mais de uma linha, cabeçalho e rodapé repetidos. A leitura do PDF tem de dar o mesmo que a do Word.
 * Não precisa de banco.
 */
import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { carregarPacote } from "../../src/dados/pacote.ts";
import { ArquivoInvalido } from "../../src/dados/leitura-checklist/docx.ts";
import { type Leitura, lerChecklist } from "../../src/dados/leitura-checklist/ler.ts";
import { lerPdf } from "../../src/dados/leitura-checklist/pdf.ts";
import { FIXTURES, permanentesPreenchido } from "./gerar-pdfs-ficticios.ts";

const { pacote } = carregarPacote();
const fixture = (nome: string) => new Uint8Array(readFileSync(path.join(FIXTURES, nome)));
const resposta = (l: Leitura, pergunta: string) => l.respostas.filter((r) => r.pergunta === pergunta);

describe("checklist de permanentes em PDF", async () => {
  const l = await lerChecklist(fixture("permanentes-ficticio.pdf"), pacote);

  it("reconhece a versão pelas perguntas, como no Word", () => {
    expect(l.checklist).toBe("PERMANENTES");
    expect(l.metadados.sha256_modelo).toBe("7c6d3cc9bf16");
    expect(l.metadados.leitura_pendencias).toEqual([]);
  });

  it("cabeçalho com o valor embaixo do rótulo", () => {
    expect(resposta(l, "CK-P-CAB.02")[0].valor).toBe("Hospital Fictício");
    expect(resposta(l, "CK-P-CAB.03")[0].valor).toBe("Setor Fictício");
  });

  it("tabela da 1.4 com o valor colado no rótulo e embaixo dele", () => {
    expect(resposta(l, "CK-P-1.4")[0].valor).toEqual([{ Nome: "Responsável Fictício", "Posto/graduação": "Cargo Fictício" }]);
  });

  it("X colado no ☐, antes ou depois, maiúsculo ou minúsculo", () => {
    expect(resposta(l, "CK-P-1.5")[0].valor).toEqual(["Equipamentos médico-hospitalares", "Equipamentos de diagnóstico ou terapia"]);
    expect(resposta(l, "CK-P-2.3")[0].valor).toEqual(["Substituir equipamento existente"]);
    expect(resposta(l, "CK-P-2.4")[0].valor).toBe("Sim");
    expect(resposta(l, "CK-P-3.1")[0].valor).toBe("Não");
    expect(resposta(l, "CK-P-3.6")[0].valor).toBe("Não");
  });

  it("resposta em mais de uma linha fica inteira", () => {
    expect(resposta(l, "CK-P-2.4")[0].texto).toBe("Equipamento fictício antigo, com mais de cinco anos de uso.\nSegunda linha da resposta.");
  });

  it("duas marcas numa pergunta de uma opção: resposta vazia e destacada", () => {
    expect(resposta(l, "CK-P-12.6")[0].valor).toBeNull();
    expect(l.metadados.marcas_multiplas).toEqual(["CK-P-12.6"]);
  });

  it("orientação que quebra de linha não vira resposta", () => {
    for (const p of ["CK-P-8.8", "CK-P-13.2", "CK-P-18.1"]) expect(l.metadados.sem_resposta).toContain(p);
  });

  it("dá as mesmas respostas que o Word de onde o PDF saiu", async () => {
    const doWord = await lerChecklist(await (await permanentesPreenchido()).gerar(), pacote);
    const semHash = (x: Leitura) => x.respostas.map((r) => [r.pergunta, r.valor, r.texto?.replace(/\s+/g, " ") ?? null]);
    expect(semHash(l)).toEqual(semHash(doWord));
    expect(l.metadados).toEqual(doWord.metadados);
  });
});

describe("checklist de permanentes salvo pelo LibreOffice (.odt)", () => {
  it("dá as mesmas respostas que o Word de onde saiu", async () => {
    const l = await lerChecklist(fixture("permanentes-ficticio.odt"), pacote);
    const doWord = await lerChecklist(await (await permanentesPreenchido()).gerar(), pacote);
    const semHash = (x: Leitura) => x.respostas.map((r) => [r.pergunta, r.valor, r.texto]);
    expect(l.checklist).toBe("PERMANENTES");
    expect(semHash(l)).toEqual(semHash(doWord));
    expect(l.metadados).toEqual(doWord.metadados);
  });
});

describe("checklist de consumo em PDF", () => {
  it("em branco: versão reconhecida e nenhuma resposta", async () => {
    const l = await lerChecklist(fixture("consumo-em-branco.pdf"), pacote);
    expect(l.checklist).toBe("CONSUMO");
    expect(l.respostas).toEqual([]);
  });

  it("cabeçalho e rodapé de página saem do texto", async () => {
    const blocos = await lerPdf(fixture("consumo-em-branco.pdf"));
    const textos = blocos.map((b) => (b.tipo === "p" ? b.texto : b.linhas.flat(2).join(" ")));
    expect(textos.some((t) => /\| Página \d/.test(t))).toBe(false);
  });
});

describe("PDF que não serve", () => {
  it("PDF sem texto (escaneado) é erro claro", async () => {
    const vazio = new TextEncoder().encode(
      "%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 595 842]>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF",
    );
    await expect(lerChecklist(vazio, pacote)).rejects.toThrow(/escaneado/);
  });

  it("PDF corrompido é erro claro", async () => {
    await expect(lerChecklist(new TextEncoder().encode("%PDF-1.4 lixo"), pacote)).rejects.toThrow(ArquivoInvalido);
  });

  it("Word antigo (.doc) pede para salvar como .docx ou PDF", async () => {
    await expect(lerChecklist(new Uint8Array([0xd0, 0xcf, 0x11, 0xe0, 0xa1, 0xb1, 0x1a, 0xe1]), pacote)).rejects.toThrow(/\.doc\)/);
  });
});
