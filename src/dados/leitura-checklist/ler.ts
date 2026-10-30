/**
 * Leitura determinística do checklist preenchido (passo 6; decisões 0009, 0011 e 0017), sem IA. Aceita o Word
 * (.docx), o LibreOffice (.odt) e o PDF salvo a partir deles; todos viram os mesmos blocos e seguem a mesma leitura.
 *
 * - Reconhece a versão pelos enunciados: todas as perguntas numeradas do M11 têm de estar no arquivo, na ordem,
 *   com o mesmo enunciado (sem contar maiúsculas, acentos, aspas e espaços). Pergunta que falta ou mudou é erro,
 *   nunca leitura parcial. O número pode faltar (lista numerada automática do Word ou do LibreOffice), e texto a
 *   mais com cara de pergunta ("4.5. ver anexo") é tratado como resposta escrita fora da caixa.
 * - Texto escrito fora da caixa (depois de "Resposta:" na mesma linha, ou num parágrafo solto) entra como resposta;
 *   o que é do próprio modelo (orientação e opções do M11) não.
 * - Marcas: ☒, ☑, ✓, ✔, ✗, ✘, ■, [X], (X) ou um X no lugar do ☐ ou colado nele ("☐X", "X☐", "☐ XNão").
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
import { eOdt, lerOdt } from "./odt.ts";
import { ePdf, lerPdf } from "./pdf.ts";

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
/** Chave de comparação de enunciado: também iguala aspas e travessões e tira o espaço antes da pontuação. */
const chaveDoEnunciado = (s: string) =>
  chave(s)
    .replace(/[“”«»"]/g, '"')
    .replace(/[‘’`´]/g, "'")
    .replace(/[–—]/g, "-")
    .replace(/\s+([?:;,.!])/g, "$1");

/** Lista de enunciados numerados do M11 de um checklist, na ordem: a identidade da versão. */
export function enunciadosDoM11(m11: readonly LinhaM11[], checklist: Checklist): string[] {
  return m11.filter((l) => l.id.startsWith(PREFIXO[checklist]) && /^\d+\.\d+$/.test(l.numero)).map((l) => `${l.numero}|${normal(l.pergunta)}`);
}

const hashDe = (linhas: string[]) => createHash("sha256").update(linhas.join("\n")).digest("hex");

type Segmento = { marcada: boolean; rotulo: string };

/** Opções de uma linha: cada marca e o texto até a próxima. */
function segmentos(linha: string): Segmento[] {
  const texto = linha
    .replace(/☐\s*[xX](?=\s|$|[A-ZÁÉÍÓÚÂÊÔÃÕÇ])/g, "☒ ")
    .replace(/(?<=^|\s)[xX]\s*☐/g, "☒");
  const marcas = [...texto.matchAll(MARCA)];
  return marcas.map((m, i) => ({
    marcada: m[0] !== VAZIA,
    rotulo: normal(texto.slice((m.index ?? 0) + m[0].length, i + 1 < marcas.length ? marcas[i + 1].index : texto.length)),
  }));
}

const temMarca = (linha: string) => /☐|☒|☑|✓|✔|✗|✘|■|▣/.test(linha) || /\[\s*[xX]\s*\]|\(\s*[xX]\s*\)/.test(linha);

/** Texto que é do próprio modelo naquela pergunta: a orientação ou uma opção (inteira ou o pedaço que quebrou de linha). */
function doModelo(texto: string, linha: LinhaM11): boolean {
  const k = chaveDoEnunciado(texto);
  return chaveDoEnunciado(linha.orientacao).includes(k) || chaveDoEnunciado(linha.opcoes).includes(k);
}

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

/** Conteúdo de uma pergunta no arquivo: linhas de opção, caixa de resposta, campos rotulados e texto solto. */
type Trecho = { linhasDeOpcao: string[]; caixa: string | null; campos: Record<string, string>; soltos: string[] };

const novoTrecho = (): Trecho => ({ linhasDeOpcao: [], caixa: null, campos: {}, soltos: [] });

/** Perguntas numeradas do M11 de um checklist, na ordem, com a chave do enunciado. */
function perguntasDoM11(m11: readonly LinhaM11[], checklist: Checklist): { linha: LinhaM11; chave: string }[] {
  return m11.filter((l) => l.id.startsWith(PREFIXO[checklist]) && /^\d+\.\d+$/.test(l.numero)).map((l) => ({ linha: l, chave: chaveDoEnunciado(l.pergunta) }));
}

/** Índice da pergunta do M11 que o parágrafo é ("1.1. Qual..." ou só "Qual...", da lista numerada), ou -1. */
function perguntaDoParagrafo(t: string, perguntas: { linha: LinhaM11; chave: string }[], aPartirDe: number): number {
  const p = PERGUNTA.exec(t);
  const k = chaveDoEnunciado(p ? p[2] : t);
  for (let i = aPartirDe; i < perguntas.length; i++) {
    if (perguntas[i].chave !== k) continue;
    if (!p || p[1] === perguntas[i].linha.numero) return i;
  }
  return -1;
}

/**
 * Valor de um campo de tabela (1.4): a célula com o rótulo exato, ou a célula em que o valor foi escrito colado
 * ao rótulo ("NomeFulano", "Posto/graduação Cap").
 */
function valorDoCampo(campos: Record<string, string>, campo: string): string {
  if (campos[campo]) return campos[campo];
  const rotulo = Object.keys(campos).find((k) => chave(k).startsWith(chave(campo)) && chave(k) !== chave(campo));
  return rotulo ? normal([rotulo.slice(campo.length).replace(/^[:\s]+/, ""), campos[rotulo]].join(" ")) : "";
}

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

/**
 * Enunciado partido em parágrafos (o Word, ao abrir um PDF, quebra o texto onde a linha quebrava): toda pergunta do
 * checklist termina em "?" ou ":", então o parágrafo seguinte é juntado até chegar lá (no máximo três).
 */
function juntarEnunciadosQuebrados(blocos: Bloco[]): Bloco[] {
  const saida: Bloco[] = [];
  let juntados = 0;
  for (const b of blocos) {
    const anterior = saida.at(-1);
    const t = b.tipo === "p" ? normal(b.texto) : "";
    const continua =
      anterior?.tipo === "p" && PERGUNTA.test(normal(anterior.texto)) && !/[?:]$/.test(normal(anterior.texto)) && juntados < 3 &&
      t !== "" && !PERGUNTA.test(t) && !SECAO.test(t) && !temMarca(t) && !/^Resposta:?/i.test(t);
    if (continua && anterior?.tipo === "p") {
      anterior.texto = `${normal(anterior.texto)} ${t}`;
      juntados++;
    } else {
      saida.push(b.tipo === "p" ? { ...b } : b);
      juntados = 0;
    }
  }
  return saida;
}

export async function lerChecklist(arquivo: Uint8Array, pacote: Pacote): Promise<Leitura> {
  const hashArquivo = createHash("sha256").update(arquivo).digest("hex");
  const blocos = juntarEnunciadosQuebrados(ePdf(arquivo) ? await lerPdf(arquivo) : eOdt(arquivo) ? await lerOdt(arquivo) : await lerDocx(arquivo));
  const m11 = pacote.matrizes.M11;
  const paragrafos = blocos.flatMap((b) => (b.tipo === "p" && normal(b.texto) ? [normal(b.texto)] : []));

  // 0. Qual checklist: o que tem mais perguntas do M11 reconhecidas no arquivo, na ordem.
  const reconhecidas = (c: Checklist) => {
    const perguntas = perguntasDoM11(m11, c);
    let proxima = 0;
    const achadas: number[] = [];
    for (const t of paragrafos) {
      const i = perguntaDoParagrafo(t, perguntas, proxima);
      if (i >= 0) {
        achadas.push(i);
        proxima = i + 1;
      }
    }
    return { perguntas, achadas };
  };
  const candidatos = (["CONSUMO", "PERMANENTES"] as const).map((c) => ({ c, ...reconhecidas(c) }));
  const melhor = candidatos.reduce((a, b) => (b.achadas.length > a.achadas.length ? b : a));
  if (melhor.achadas.length === 0) {
    throw new VersaoDesconhecida("O arquivo não tem as perguntas do checklist técnico. Envie o checklist de consumo ou de permanentes preenchido.");
  }
  if (melhor.achadas.length < melhor.perguntas.length) {
    const faltam = melhor.perguntas.filter((_, i) => !melhor.achadas.includes(i)).map((x) => x.linha);
    const lista = faltam.slice(0, 3).map((l) => `${l.numero} ("${normal(l.pergunta)}")`).join("; ");
    throw new VersaoDesconhecida(
      `Este arquivo não é a versão distribuída do checklist de ${melhor.c === "CONSUMO" ? "consumo" : "permanentes"}: ${faltam.length === 1 ? "a pergunta" : `${faltam.length} perguntas faltam ou foram alteradas, a começar por`} ${lista}${faltam.length === 1 ? " falta ou foi alterada" : ""}. Use o checklist distribuído, sem mudar o texto das perguntas, ou digite as respostas na tela.`,
    );
  }
  const checklist: Checklist = melhor.c;
  const perguntas = melhor.perguntas;

  // 1. Estrutura: cabeçalho, perguntas numeradas e seções sem número (22, 23), com o que vem até a próxima.
  const cabecalho: string[] = [];
  const trechos = new Map<string, Trecho>();
  let atual: Trecho | null = null;
  // Pergunta numerada em que se está (para separar o texto do modelo do texto escrito por quem preencheu).
  let daPergunta: LinhaM11 | null = null;
  let esperandoCaixa = false;
  let secao = "0";
  let proxima = 0;
  for (const b of blocos) {
    if (b.tipo === "p") {
      const t = normal(b.texto);
      if (!t) continue;
      const s = SECAO.exec(t);
      if (s && t === t.toUpperCase() && Number(s[1]) >= Number(secao)) {
        secao = s[1];
        atual = novoTrecho();
        daPergunta = null;
        trechos.set(secao, atual);
        esperandoCaixa = false;
        continue;
      }
      const i = perguntaDoParagrafo(t, perguntas, proxima);
      if (i >= 0) {
        proxima = i + 1;
        daPergunta = perguntas[i].linha;
        atual = novoTrecho();
        trechos.set(daPergunta.numero, atual);
        esperandoCaixa = false;
        continue;
      }
      if (!atual) continue;
      const resposta = /^Resposta:?\s*(.*)$/i.exec(t);
      if (resposta) {
        esperandoCaixa = true;
        if (resposta[1] && daPergunta) atual.soltos.push(resposta[1]);
      } else if (temMarca(b.texto)) {
        for (const linha of b.texto.split("\n")) atual.linhasDeOpcao.push(linha);
      } else if (daPergunta && !doModelo(t, daPergunta)) {
        atual.soltos.push(t);
      }
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

  // 2. Versão: a lista de enunciados do M11 que foi reconhecida inteira (passo 0).
  const hashEnunciados = hashDe(enunciadosDoM11(m11, checklist));

  // 3. Respostas, pergunta a pergunta, pela coluna leitura do M11.
  const respostas: RespostaLida[] = [];
  const marcasMultiplas: string[] = [];
  const respostaUnica: string[] = [];
  const pendencias: string[] = [];
  const semResposta: string[] = [];
  const divergencias: string[] = [];
  const linhas = m11.filter((l) => l.id.startsWith(PREFIXO[checklist]));
  const valores = new Map<string, RespostaLida>();
  // Uma resposta por pergunta e conjunto de itens (é a chave da tabela resposta_checklist): o mesmo item citado
  // duas vezes na mesma resposta junta os dois textos, em vez de quebrar a gravação.
  const guardar = (r: RespostaLida) => {
    const igual = respostas.find((x) => x.pergunta === r.pergunta && x.itens.join(",") === r.itens.join(","));
    if (igual) {
      igual.valor = typeof igual.valor === "string" && typeof r.valor === "string" ? `${igual.valor}; ${r.valor}` : igual.valor;
      igual.texto = [igual.texto, r.texto].filter(Boolean).join("\n") || null;
      return;
    }
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
    // Texto escrito fora da caixa vale como escrito nela.
    if (trecho.soltos.length) trecho.caixa = [trecho.caixa, ...trecho.soltos].filter(Boolean).join("\n");
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
      const entrada = Object.fromEntries(campos.map((c) => [c, valorDoCampo(trecho.campos, c)]).filter(([, v]) => v));
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
