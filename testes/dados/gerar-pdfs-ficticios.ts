/**
 * Gera os checklists fictícios em PDF e em .odt usados por leitura-pdf.test.ts, convertendo o Word fictício pelo
 * LibreOffice, como faz quem preenche no Word e "salva como PDF" ou salva no formato do LibreOffice. As marcas imitam o que chega das OMs: X colado no ☐ ("☐X",
 * "X☐", "☐ XNão"), valor escrito embaixo do rótulo ou colado nele. Só dados fictícios.
 *
 * Rodar só quando o checklist ficticio mudar (exige LibreOffice): node testes/dados/gerar-pdfs-ficticios.ts
 * O teste usa os arquivos já gerados e não precisa do LibreOffice.
 */
import { execFileSync } from "node:child_process";
import { mkdtempSync, renameSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { ChecklistFicticio } from "./checklist-ficticio.ts";

export const FIXTURES = path.resolve(import.meta.dirname, "fixtures");

/** Permanentes preenchido como os PDFs que chegam das OMs. */
export async function permanentesPreenchido(): Promise<ChecklistFicticio> {
  return (await ChecklistFicticio.de("PERMANENTES"))
    .preencherCampo("OMS requisitante", "Hospital Fictício")
    .preencherCampo("Setor requisitante", "Setor Fictício")
    .responder("1.1", "Hospital Fictício")
    .responder("1.3", "Equipamento fictício")
    .escreverNaOpcao("1.4", "Nome", "Responsável Fictício")
    .preencherCampo("Posto/graduação", "Cargo Fictício", "1.4")
    .marcar("1.5", "Equipamentos médico-hospitalares", "☐X")
    .marcar("1.5", "Equipamentos de diagnóstico ou terapia", "☐X")
    .marcar("2.3", "Substituir equipamento existente", "X☐")
    .marcar("2.4", "Sim", "☐x")
    .responder("2.4", "Equipamento fictício antigo, com mais de cinco anos de uso.\nSegunda linha da resposta.")
    .trocarOpcao("3.1", "Não", "☐ XNão")
    .marcar("3.6", "Não", "☐ X")
    .marcar("12.6", "Antes da utilização", "☐x")
    .trocarOpcao("12.6", "Antes do recebimento definitivo", "☐ xAntes do recebimento definitivo");
}

function converter(docx: Uint8Array, nome: string, formato: "pdf" | "odt") {
  const dir = mkdtempSync(path.join(tmpdir(), "checklist-"));
  try {
    writeFileSync(path.join(dir, `${nome}.docx`), docx);
    execFileSync("soffice", ["--headless", "--convert-to", formato, "--outdir", dir, path.join(dir, `${nome}.docx`)], { stdio: "ignore" });
    renameSync(path.join(dir, `${nome}.${formato}`), path.join(FIXTURES, `${nome}.${formato}`));
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

if (import.meta.main) {
  converter(await (await permanentesPreenchido()).gerar(), "permanentes-ficticio", "pdf");
  converter(await (await permanentesPreenchido()).gerar(), "permanentes-ficticio", "odt");
  converter(await (await ChecklistFicticio.de("CONSUMO")).gerar(), "consumo-em-branco", "pdf");
  console.log(`Arquivos gravados em ${FIXTURES}`);
}
