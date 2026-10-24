/**
 * Leitura determinística do checklist preenchido (passo 6; decisões 0009 e 0011), sem IA.
 *
 * - Reconhece a versão pelos enunciados: as perguntas numeradas do Word têm de ser exatamente as do M11 (número e
 *   enunciado). Versão desconhecida é erro, nunca leitura parcial.
 * - Marcas: ☒, ☑, ✓, ✔, ✗, ✘, ■, [X], (X) ou um X no lugar do ☐.
 * - Resposta: a caixa de uma célula depois de "Resposta:"; tabelas com rótulo (campos) também são lidas.
 * - Produz os dados que as expressões usam (README das matrizes): CK_*, _texto, _numero e os metadados
 *   checklist.* (consumo, permanentes, marcas_multiplas, resposta_unica_por_item, divergencias_leitura,
 *   leitura_pendencias, sem_resposta, sha256_modelo e sha256_m11).
 * - O que fazer em cada pergunta vem da coluna leitura do M11; nada de regra jurídica aqui.
 */
import { createHash } from "node:crypto";
import type { LeituraDoChecklist } from "../../motor/entrada.ts";
import type { Valor } from "../../motor/pacote/avaliador.ts";
import type { LinhaM11, Pacote } from "../../motor/pacote/esquema.ts";
import { type Bloco, lerDocx } from "./docx.ts";

export type Checklist = "CONSUMO" | "PERMANENTES";

/** Uma resposta lida, já no formato da tabela resposta_checklist. itens vazio = vale para o processo. */
export type RespostaLida = { pergunta: string; valor: Valor; texto: string | null; numero: number | null; itens: number[] };

export type Leitura = {
  checklist: Checklist;
  respostas: RespostaLida[];
  metadados: LeituraDoChecklist;
  /** SHA-256 do arquivo enviado (vai para a auditoria; o arquivo é descartado). */
  hashArquivo: string;
  /** SHA-256 da lista de enunciados reconhecida (identifica a versão do checklist). */
  hashEnunciados: string;
};

export class VersaoDesconhecida extends Error {}

const PREFIXO: Record<Checklist, string> = { CONSUMO: "CK-C-", PERMANENTES: "CK-P-" };
const SECAO = /^(\d{1,2})\.\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ0-9 ,/\-–()]+)$/;
const PERGUNTA = /^(\d{1,2}\.\d{1,2})\.\s+([\s\S]+)$/;
const MARCA = /☐|☒|☑|✓|✔|✗|✘|■|▣|\[\s*[xX]\s*\]|\(\s*[xX]\s*\)|(?<=^|\s)[xX](?=\s)/g;
const VAZIA = "☐";

const normal = (s: string) => s.replace(/\s+/g, " ").trim();
const chave = (s: string) => normal(s).toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");

/** Lista de enunciados numerados do M11 de um checklist, na ordem: a identidade da versão. */
export function enunciadosDoM11(m11: readonly LinhaM11[], checklist: Checklist): string[] {
  return m11.filter((l) => l.id.startsWith(PREFIXO[checklist]) && /^\d+\.\d+$/.test(l.numero)).map((l) => `${l.numero}|${normal(l.pergunta)}`);
}

const hashDe = (linhas: string[]) => createHash("sha256").update(linhas.join("\n")).digest("hex");

type Segmento = { marcada: boolean; rotulo: string };

/** Opções de uma linha: cada marca e o texto até a próxima. */
function segmentos(linha: string): Segmento[] {
  const texto = linha.replace(/☐\s*[xX](?=\s)/g, "☒").replace(/(?<=^|\s)[xX]\s*☐/g, "☒");
  const marcas = [...texto.matchAll(MARCA)];
  return marcas.map((m, i) => ({
    marcada: m[0] !== VAZIA,
    rotulo: normal(texto.slice((m.index ?? 0) + m[0].length, i + 1 < marcas.length ? marcas[i + 1].index : texto.length)),
  }));
}

const temMarca = (linha: string) => /☐|☒|☑|✓|✔|✗|✘|■|▣/.test(linha) || /\[\s*[xX]\s*\]|\(\s*[xX]\s*\)/.test(linha);

/** Opções do M11 ("Sim; Não", sem "campos: ..."). */
function opcoesDoM11(linha: LinhaM11): string[] {
  return linha.opcoes
    .split(/;\s*/)
    .map((o) => o.trim())
    .filter((o) => o && !o.startsWith("campos:"));
}

/** Opção do M11 que o rótulo escrito no Word representa, e o texto escrito além dela (o "Outro: ..."). */
function casarOpcao(rotulo: string, opcoes: string[]): { opcao: string; resto: string } | null {
  const r = chave(rotulo);
  let melhor: { opcao: string; resto: string; tamanho: number } | null = null;
  for (const opcao of opcoes) {
    const base = chave(opcao.split(/[:_]/)[0]);
    if (!base || !r.startsWith(base)) continue;
    if (melhor && base.length <= melhor.tamanho) continue;
    const resto = normal(rotulo.slice(base.length)).replace(/^[:\s_]+/, "").replace(/_+/g, "").trim();
    melhor = { opcao, resto, tamanho: base.length };
  }
  return melhor && { opcao: melhor.opcao, resto: melhor.resto };
}

/** Conteúdo de uma pergunta no Word: linhas de opção, caixa de resposta e campos rotulados. */
type Trecho = { linhasDeOpcao: string[]; caixa: string | null; campos: Record<string, string>; linhas: number };

function textoDaCelula(paragrafos: string[]): string {
  return paragrafos.join("\n").replace(/\n+$/, "");
}

/** Itens citados num texto: "item 2", "itens 1, 3 e 5", "itens 1 a 4". */
export function itensCitados(texto: string): number[] {
  const achados = new Set<number>();
  for (const m of texto.matchAll(/\b(?:itens|item)\s+((?:\d+\s*(?:,|e|a|-|–|ao?)\s*)*\d+)/gi)) {
    const partes = m[1].split(/\s*(,|e(?!\w))\s*/).filter((p) => p && p !== "," && p !== "e");
    for (const parte of partes) {
      const faixa = /^(\d+)\s*(?:a|ao|-|–)\s*(\d+)$/.exec(parte.trim());
      if (faixa) for (let n = Number(faixa[1]); n <= Number(faixa[2]) && n - Number(faixa[1]) < 500; n++) achados.add(n);
      else for (const n of parte.match(/\d+/g) ?? []) achados.add(Number(n));
    }
  }
  return [...achados].sort((a, b) => a - b);
}

/** Texto por item: "Itens 1 e 2: 24 meses; item 3: 36 meses" -> [[1,2], "24 meses"], [[3], "36 meses"]. */
function textosPorItem(texto: string): { itens: number[]; texto: string }[] {
  return texto
    .split(/\n|;/)
    .map((s) => s.trim())
    .filter(Boolean)
    .map((s) => ({ itens: itensCitados(s), texto: s.replace(/^\s*(?:para\s+(?:o|os)\s+)?(?:itens|item)\s+[\d\s,e\-–a]+[:\-–]\s*/i, "").trim() }))
    .filter((x) => x.itens.length > 0);
}

/** Unidade do número lido do "Outro", pela coluna leitura do M11: "número seguido de 'dias úteis'". */
function unidadeDoNumero(linha: LinhaM11): string | null {
  return /número seguido de '([^']+)'/.exec(linha.leitura)?.[1] ?? null;
}

export async function lerChecklist(arquivo: Uint8Array, pacote: Pacote): Promise<Leitura> {
  const hashArquivo = createHash("sha256").update(arquivo).digest("hex");
  const blocos = await lerDocx(arquivo);
  const m11 = pacote.matrizes.M11;

  // 1. Estrutura: cabeçalho, perguntas numeradas e seções sem número (22, 23), com o que vem até a próxima.
  const cabecalho: string[] = [];
  const enunciados: string[] = [];
  const trechos = new Map<string, Trecho>();
  let atual: Trecho | null = null;
  let esperandoCaixa = false;
  let secao = "0";
  for (const b of blocos) {
    if (b.tipo === "p") {
      const t = normal(b.texto);
      if (!t) continue;
      const s = SECAO.exec(t);
      if (s && t === t.toUpperCase()) {
        secao = s[1];
        atual = { linhasDeOpcao: [], caixa: null, campos: {}, linhas: 0 };
        trechos.set(secao, atual);
        esperandoCaixa = false;
        continue;
      }
      const p = PERGUNTA.exec(t);
      if (p) {
        enunciados.push(`${p[1]}|${normal(p[2])}`);
        atual = { linhasDeOpcao: [], caixa: null, campos: {}, linhas: 0 };
        trechos.set(p[1], atual);
        esperandoCaixa = false;
        continue;
      }
      if (!atual) continue;
      if (/^Resposta:?$/i.test(t)) esperandoCaixa = true;
      else if (temMarca(b.texto)) for (const linha of b.texto.split("\n")) atual.linhasDeOpcao.push(linha);
      atual.linhas++;
      continue;
    }
    // Tabela
    if (secao === "0") {
      for (const linha of b.linhas) for (const celula of linha) cabecalho.push(textoDaCelula(celula));
      continue;
    }
    if (!atual) continue;
    const celulas = b.linhas.flat();
    if (esperandoCaixa && celulas.length === 1) {
      atual.caixa = textoDaCelula(celulas[0]).trim();
      esperandoCaixa = false;
      continue;
    }
    for (const celula of celulas) {
      const [rotulo, ...resto] = textoDaCelula(celula).split("\n");
      if (normal(rotulo)) atual.campos[normal(rotulo)] = resto.join("\n").trim();
    }
  }

  // 2. Versão: os enunciados têm de ser exatamente os de um checklist do M11.
  const hashEnunciados = hashDe(enunciados);
  const checklist = (["CONSUMO", "PERMANENTES"] as const).find((c) => hashDe(enunciadosDoM11(m11, c)) === hashEnunciados);
  if (!checklist) {
    const candidatos = (["CONSUMO", "PERMANENTES"] as const).map((c) => enunciadosDoM11(m11, c));
    const maisProximo = candidatos.reduce((a, b) => (b.filter((x) => enunciados.includes(x)).length > a.filter((x) => enunciados.includes(x)).length ? b : a));
    const diferenca = maisProximo.find((x, i) => enunciados[i] !== x);
    throw new VersaoDesconhecida(
      enunciados.length === 0
        ? "O arquivo não tem as perguntas numeradas do checklist técnico. Envie o checklist de consumo ou de permanentes preenchido."
        : `Versão do checklist desconhecida: as perguntas não são as da versão distribuída${diferenca ? ` (primeira diferença na pergunta ${diferenca.split("|")[0]})` : ""}. Use o checklist distribuído, sem alterar as perguntas, ou digite as respostas na tela.`,
    );
  }

  // 3. Respostas, pergunta a pergunta, pela coluna leitura do M11.
  const respostas: RespostaLida[] = [];
  const marcasMultiplas: string[] = [];
  const respostaUnica: string[] = [];
  const pendencias: string[] = [];
  const semResposta: string[] = [];
  const divergencias: string[] = [];
  const linhas = m11.filter((l) => l.id.startsWith(PREFIXO[checklist]));
  const valores = new Map<string, RespostaLida>();
  const guardar = (r: RespostaLida) => {
    respostas.push(r);
    if (r.itens.length === 0) valores.set(r.pergunta, r);
  };

  for (const linha of linhas) {
    if (linha.numero.startsWith("CAB.")) {
      // Célula do cabeçalho pelo rótulo (a disposição muda entre os checklists); a resposta é o que vem depois dele.
      const celula = cabecalho.find((c) => chave(c).startsWith(chave(linha.pergunta)));
      if (celula === undefined) {
        pendencias.push(linha.id);
        continue;
      }
      const texto = normal(celula.slice(celula.indexOf(linha.pergunta.trim()) + linha.pergunta.trim().length)).replace(/^[:\s]+/, "");
      if (texto) guardar({ pergunta: linha.id, valor: texto, texto: null, numero: null, itens: [] });
      else semResposta.push(linha.id);
      continue;
    }
    const trecho = trechos.get(linha.numero);
    if (!trecho) {
      pendencias.push(linha.id);
      continue;
    }
    const opcoes = opcoesDoM11(linha);
    const marcadas: { opcao: string; resto: string }[] = [];
    let marcaSemOpcao = false;
    for (const l of trecho.linhasDeOpcao) {
      for (const seg of segmentos(l)) {
        if (!seg.marcada) continue;
        const casada = casarOpcao(seg.rotulo, opcoes);
        if (casada) marcadas.push(casada);
        else marcaSemOpcao = true;
      }
    }
    if (marcaSemOpcao) pendencias.push(linha.id);
    const camposPreenchidos = Object.values(trecho.campos).filter(Boolean);
    const textoOutro = marcadas.map((m) => m.resto).filter(Boolean);
    const textoLivre = [...textoOutro, ...(linha.tipo_resposta === "TEXTO" || linha.tipo_resposta === "TABELA" ? [] : camposPreenchidos), ...(trecho.caixa && linha.tipo_resposta !== "TEXTO" ? [trecho.caixa] : [])].join("\n") || null;

    let valor: Valor = null;
    if (linha.tipo_resposta === "SIM_NAO" || linha.tipo_resposta === "UNICA") {
      if (marcadas.length === 1) valor = marcadas[0].opcao;
      else if (marcadas.length > 1) marcasMultiplas.push(linha.id);
    } else if (linha.tipo_resposta === "MULTIPLA") {
      if (marcadas.length) valor = [...new Set(marcadas.map((m) => m.opcao))];
    } else if (linha.tipo_resposta === "TABELA") {
      const campos = /campos:\s*(.+)$/.exec(linha.opcoes)?.[1].split(/;\s*/) ?? [];
      const entrada = Object.fromEntries(campos.map((c) => [c, trecho.campos[c] ?? ""]).filter(([, v]) => v));
      if (Object.keys(entrada).length) valor = [entrada];
    } else {
      valor = trecho.caixa || camposPreenchidos.join("\n") || null;
    }

    // Número do "Outro" (P32): só quando o M11 diz a unidade e o "Outro" foi a opção marcada.
    let numero: number | null = null;
    const unidade = unidadeDoNumero(linha);
    if (unidade && typeof valor === "string" && chave(valor).startsWith("outro")) {
      const fonte = textoOutro[0] ?? camposPreenchidos[0] ?? "";
      const m = new RegExp(`^\\s*(\\d+)\\s*${unidade.replace(/\s+/g, "\\s+")}\\b`, "i").exec(fonte);
      if (m) numero = Number(m[1]);
    }

    const respondida = valor !== null || marcadas.length > 0 || textoLivre;
    if (!respondida) {
      semResposta.push(linha.id);
      continue;
    }

    // Por item: liga aos itens citados; sem item citado, vale para o processo (e, quando o M11 manda, é
    // "resposta única para vários itens", destacada para o operador confirmar).
    if (linha.por_item === "S") {
      if (linha.tipo_resposta === "TEXTO" && typeof valor === "string") {
        const partes = textosPorItem(valor);
        if (partes.length > 0) {
          for (const parte of partes) guardar({ pergunta: linha.id, valor: parte.texto, texto: null, numero: null, itens: parte.itens });
          continue;
        }
      } else {
        const itens = itensCitados(textoLivre ?? "");
        if (itens.length > 0) {
          guardar({ pergunta: linha.id, valor, texto: textoLivre, numero, itens });
          continue;
        }
      }
      if (linha.leitura.includes("resposta_unica_por_item")) respostaUnica.push(linha.id);
    }
    guardar({ pergunta: linha.id, valor, texto: linha.tipo_resposta === "TEXTO" ? null : textoLivre, numero, itens: [] });
  }

  // Divergência de nome do responsável entre cabeçalho e a 1.4 (S03), pela leitura do M11.
  const p = PREFIXO[checklist];
  const nomeCab = valores.get(`${p}CAB.04`)?.valor;
  const tabela14 = valores.get(`${p}1.4`)?.valor;
  const nome14 = Array.isArray(tabela14) ? (tabela14[0] as Record<string, string> | undefined)?.Nome : undefined;
  if (typeof nomeCab === "string" && nome14 && chave(nomeCab) !== chave(nome14)) divergencias.push(`${p}CAB.04`, `${p}1.4`);

  const sha = /SHA-256 ([0-9a-f]{12})/.exec(linhas[0]?.fonte ?? "")?.[1] ?? null;
  const metadados: LeituraDoChecklist = {
    consumo: checklist === "CONSUMO",
    permanentes: checklist === "PERMANENTES",
    marcas_multiplas: marcasMultiplas,
    resposta_unica_por_item: respostaUnica,
    divergencias_leitura: divergencias,
    leitura_pendencias: pendencias,
    sem_resposta: semResposta,
    ...(sha ? { sha256_modelo: sha, sha256_m11: sha } : {}),
  };
  return { checklist, respostas, metadados, hashArquivo, hashEnunciados };
}

export type { Bloco };
