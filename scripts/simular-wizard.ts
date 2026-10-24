/**
 * Simulação legível: monta a minuta de um cenário e imprime em texto corrido, para conferência sem ler código.
 *
 * Uso: npm run simular -- C1        (C1 a C8, R1 ou R2, de matrizes/v1/cenarios/)
 *      npm run simular -- C1 --etp  (o ETP do mesmo cenário, campo a campo, com a derivação para o TR)
 *
 * O script lê o pacote gravado em regras/ (o motor nunca lê arquivo) e passa ao motor a entrada do cenário,
 * que é fictícia. Lacuna aparece no texto como [[LACUNA VAR-xxx]]; tabela ainda não montada, como
 * [[TABELA NÃO MONTADA]].
 */
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { type Derivacao, derivarEtpParaTr } from "../src/motor/derivacao/derivacao.ts";
import { type Minuta, gerarMinuta } from "../src/motor/minuta.ts";
import { type Etp, type SituacaoDoCampo, gerarEtp } from "../src/motor/montagem/etp.ts";
import type { MotivoDeLacuna } from "../src/motor/montagem/lacunas.ts";
import { esquemaDoPacote } from "../src/motor/pacote/esquema.ts";
import { DIR_PACOTE } from "./compilar-regras.ts";

const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const DIR_CENARIOS = path.join(RAIZ, "matrizes", "v1", "cenarios");

/** Rótulo de cada motivo de lacuna, na ordem da contagem. */
const MOTIVOS_DE_LACUNA: Record<MotivoDeLacuna, string> = {
  sem_valor: "falta de dado",
  sem_mapa: "ligação ambígua do marcador",
  tabela_nao_montada: "tabela não montada",
  equipe: "preenchimento da equipe",
};

function lerPacote() {
  const json = readFileSync(path.join(DIR_PACOTE, "pacote.json"), "utf8");
  const hash = readFileSync(path.join(DIR_PACOTE, "pacote.sha256"), "utf8").split(/\s+/)[0];
  return { pacote: esquemaDoPacote.parse(JSON.parse(json)), hash };
}

function lista(titulo: string, linhas: string[], saida: string[]): void {
  saida.push("", `${titulo}: ${linhas.length}`);
  for (const linha of linhas) saida.push(`  - ${linha}`);
}

export function textoDaSimulacao(id: string, descricao: string, minuta: Minuta): string {
  const saida: string[] = [];
  saida.push(`SIMULAÇÃO ${id}: ${descricao}`);
  saida.push(`Pacote ${minuta.pacote.pacote}, SHA-256 ${minuta.pacote.hash.slice(0, 12)}...`);
  saida.push(`Dados fictícios. Minuta ${minuta.bloqueada ? "BLOQUEADA (veja as pendências no fim)" : "sem bloqueio"}.`);
  saida.push("", "=".repeat(78), "");

  for (const trecho of minuta.trechos) {
    if (trecho.tipo === "clausula_setorial") {
      saida.push(`${trecho.numero ? `${trecho.numero} ` : ""}${trecho.texto}`, `    [cláusula setorial ${trecho.id}, ${trecho.tema}]`, "");
      continue;
    }
    const numero = trecho.numero ? `${trecho.numero} ` : "";
    const [primeira, ...resto] = trecho.texto.split("\n");
    saida.push(`${numero}${primeira}`);
    for (const linha of resto) saida.push(`    ${linha}`);
    saida.push("");
  }

  saida.push("=".repeat(78));
  lista(
    "Perguntas do wizard sem resposta",
    minuta.perguntasSemResposta.map((p) => `${p.id}${p.decisaoJuridica ? " (decisão jurídica da equipe)" : ""}`),
    saida,
  );
  lista(
    "Validações disparadas (M10)",
    minuta.validacoes.disparadas.map((v) => `${v.id} ${v.tipo}: ${v.mensagem}`),
    saida,
  );
  lista("Conferência manual (regras do M10 sem expressão)", minuta.validacoes.conferenciaManual.map((v) => `${v.id}: ${v.regra}`), saida);
  lista("Grupos de alternativas sem exatamente uma opção (bloqueio)", minuta.bloqueiosGrupoAlternativas, saida);
  lista("Perguntas ao operador sobre o checklist (bloqueiam até confirmar)", minuta.revisao.perguntasAoOperador.map((p) => `${p.pergunta} (${p.motivo}): ${p.texto}`), saida);
  lista("Respostas do checklist destacadas para revisão (sem bloquear)", minuta.revisao.destaques.filter((d) => d.motivos.every((m) => !m.bloqueia)).map((d) => `${d.pergunta}: ${d.motivos.map((m) => m.motivo).join(", ")}`), saida);
  lista("Valores padrão, que entraram sem ter sido informados ([[PADRÃO: ...]])", minuta.valoresPadrao.map((p) => `${p.trecho}: ${p.texto}`), saida);
  lista("Sugestões do checklist (a equipe decide)", minuta.sugestoes.map((s) => `${s.destino}${s.item === undefined ? "" : ` (item ${s.item})`} = ${JSON.stringify(s.valor)}, pela ${s.pergunta}`), saida);
  lista("Avisos do motor", minuta.avisos.map((a) => `${a.codigo}: ${a.mensagem}`), saida);

  const contagem: Record<MotivoDeLacuna, number> = { sem_valor: 0, sem_mapa: 0, tabela_nao_montada: 0, equipe: 0 };
  for (const lacuna of minuta.lacunasNoTexto) contagem[lacuna.motivo]++;
  contagem.sem_valor += minuta.lacunasDeDados.length;
  const total = Object.values(contagem).reduce((a, b) => a + b, 0);
  saida.push("", `Lacunas por motivo (total ${total}):`);
  for (const [motivo, rotulo] of Object.entries(MOTIVOS_DE_LACUNA)) {
    saida.push(`  ${rotulo.padEnd(30)} ${contagem[motivo as MotivoDeLacuna]}`);
  }
  return saida.join("\n");
}

/** Rótulo de cada situação de campo do ETP. */
const SITUACOES_DO_CAMPO: Record<SituacaoDoCampo, string> = {
  preenchido: "preenchido",
  incompleto: "com lacuna",
  vazio: "vazio",
  texto_do_etp_digital: "texto do próprio ETP Digital (não se copia)",
  sem_ligacao: "sem dado ligado no pacote (veja a orientação do M01)",
};

export function textoDoEtp(id: string, descricao: string, etp: Etp, derivacao: Derivacao): string {
  const saida: string[] = [];
  saida.push(`ETP ${id}: ${descricao}`);
  saida.push(`Pacote ${etp.pacote.pacote}, SHA-256 ${etp.pacote.hash.slice(0, 12)}...`);
  saida.push("Dados fictícios. Campo a campo, na ordem do ETP Digital (M01).", "", "=".repeat(78));
  let secao = "";
  for (const campo of etp.campos) {
    if (campo.secao.numero !== secao) {
      secao = campo.secao.numero;
      saida.push("", `${campo.secao.numero}. ${campo.secao.nome.toUpperCase()}`);
    }
    const marca = campo.obrigatorio ? " [obrigatório]" : "";
    saida.push("", `${campo.id} ${campo.campo}${marca}: ${SITUACOES_DO_CAMPO[campo.situacao]}`);
    if (campo.texto) for (const linha of campo.texto.split("\n")) saida.push(`    ${linha}`);
    else if (campo.situacao !== "texto_do_etp_digital") saida.push(`    Orientação: ${campo.orientacao.preenchimento}`);
    const blocos = derivacao.porCampo[campo.id] ?? [];
    if (blocos.length) saida.push(`    -> no TR: ${blocos.map((b) => (b.numero ? `${b.numero} (${b.bloco})` : b.bloco)).join(", ")}`);
    if (campo.validacoes.length) saida.push(`    validações: ${campo.validacoes.join(", ")}`);
  }
  saida.push("", "=".repeat(78));
  lista("Campos obrigatórios vazios ou com lacuna (art. 18, § 2º)", etp.pendencias, saida);
  lista("Justificativas que o M04 pede no ETP sem dizer o campo", etp.justificativasSemCampo.map((j) => `${j.regra}: ${j.texto}`), saida);
  lista(
    "Blocos do TR que repetem campo vazio do ETP (rever o ETP antes)",
    derivacao.blocos.filter((b) => b.situacao === "campo_vazio").map((b) => `${b.bloco}: ${b.camposVazios.join(", ")}`),
    saida,
  );
  return saida.join("\n");
}

function principal(): void {
  const id = process.argv[2];
  const etp = process.argv.includes("--etp");
  if (!id) {
    console.error("Uso: npm run simular -- C1 [--etp]   (C1 a C8, R1 ou R2)");
    process.exitCode = 1;
    return;
  }
  let caso: { descricao: string; entrada: Omit<Parameters<typeof gerarMinuta>[0], "pacote" | "hashDoPacote"> };
  try {
    caso = JSON.parse(readFileSync(path.join(DIR_CENARIOS, `${id}.json`), "utf8"));
  } catch {
    console.error(`Cenário ${id} não encontrado em matrizes/v1/cenarios/.`);
    process.exitCode = 1;
    return;
  }
  const { pacote, hash } = lerPacote();
  const entrada = { pacote, hashDoPacote: hash, ...caso.entrada };
  const minuta = gerarMinuta(entrada);
  if (!etp) {
    console.log(textoDaSimulacao(id, caso.descricao, minuta));
    return;
  }
  const documento = gerarEtp(entrada, minuta);
  console.log(textoDoEtp(id, caso.descricao, documento, derivarEtpParaTr(pacote, minuta, documento)));
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) principal();
