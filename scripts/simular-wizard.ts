/**
 * Simulação legível: monta a minuta de um cenário e imprime em texto corrido, para conferência sem ler código.
 *
 * Uso: npm run simular -- C1        (C1 a C8, R1 ou R2, de matrizes/v1/cenarios/)
 *
 * O script lê o pacote gravado em regras/ (o motor nunca lê arquivo) e passa ao motor a entrada do cenário,
 * que é fictícia. Lacuna aparece no texto como [[LACUNA VAR-xxx]]; tabela ainda não montada, como
 * [[TABELA NÃO MONTADA]].
 */
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { type Minuta, gerarMinuta } from "../src/motor/minuta.ts";
import { esquemaDoPacote } from "../src/motor/pacote/esquema.ts";
import { DIR_PACOTE } from "./compilar-regras.ts";

const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const DIR_CENARIOS = path.join(RAIZ, "matrizes", "v1", "cenarios");

const MOTIVOS_DE_LACUNA = {
  sem_valor: "falta de dado",
  sem_ligacao_unica: "ligação ambígua do marcador",
  tabela_nao_montada: "tabela não montada",
} as const;

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
      saida.push(`[Cláusula setorial ${trecho.id}, ${trecho.tema}]`, `    ${trecho.texto}`, "");
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
  lista("Perguntas ao operador sobre o checklist (bloqueiam até confirmar)", minuta.revisao.perguntasAoOperador.map((p) => `${p.pergunta}: ${p.texto}`), saida);
  lista("Sugestões do checklist (a equipe decide)", minuta.sugestoes.map((s) => `${s.destino}${s.item === undefined ? "" : ` (item ${s.item})`} = ${JSON.stringify(s.valor)}, pela ${s.pergunta}`), saida);
  lista("Avisos do motor", minuta.avisos.map((a) => `${a.codigo}: ${a.mensagem}`), saida);

  const contagem = { sem_valor: 0, sem_ligacao_unica: 0, tabela_nao_montada: 0 };
  for (const lacuna of minuta.lacunasNoTexto) contagem[lacuna.motivo]++;
  contagem.sem_valor += minuta.lacunasDeDados.length;
  const total = contagem.sem_valor + contagem.sem_ligacao_unica + contagem.tabela_nao_montada;
  saida.push("", `Lacunas por motivo (total ${total}):`);
  for (const [motivo, rotulo] of Object.entries(MOTIVOS_DE_LACUNA)) {
    saida.push(`  ${rotulo.padEnd(30)} ${contagem[motivo as keyof typeof contagem]}`);
  }
  return saida.join("\n");
}

function principal(): void {
  const id = process.argv[2];
  if (!id) {
    console.error("Uso: npm run simular -- C1   (C1 a C8, R1 ou R2)");
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
  const minuta = gerarMinuta({ pacote, hashDoPacote: hash, ...caso.entrada });
  console.log(textoDaSimulacao(id, caso.descricao, minuta));
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) principal();
