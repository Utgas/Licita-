/**
 * Wizard na tela (passo 9): o que o motor devolve, organizado para o operador. Nada de regra jurídica aqui: estado,
 * opções, justificativa e campos extras vêm do pacote (M04, M05, M02 e M08) e da minuta montada pelo motor.
 *
 * - Pergunta: as habilitadas pelo motor e as derivadas (calculadas, só leitura), na ordem do M04.
 * - Justificativa: a coluna exige_justificativa do M04. "N..." não pede; "S se X ou Y: ..." é obrigatória com a
 *   resposta X ou Y; "S..." sem "se" é obrigatória sempre.
 * - Campos extras: as variáveis (VAR) que a minuta ainda pede (lacunas do texto com fonte VAR) ou que a equipe já
 *   informou, com a forma de entrada tirada do mapa de lacunas (campo, índice, unidade) e do tabela_colunas.
 */
import type { Minuta } from "../motor/minuta.ts";
import { variaveisLidas } from "../motor/montagem/blocos.ts";
import type { Valor } from "../motor/pacote/avaliador.ts";
import type { LinhaM04, LinhaM05, Pacote } from "../motor/pacote/esquema.ts";
import { variavelDoId } from "../motor/pacote/nomes.ts";
import type { ProcessoCompleto } from "./processos.ts";

export type EstadoDaPergunta = "respondida" | "checklist" | "decisao_pendente" | "pendente" | "calculada";

export type Justificativa = { texto: string; obrigatoriaCom: "sempre" | string[] };

export type PerguntaDoWizard = {
  id: string;
  pergunta: string;
  tipo: LinhaM04["tipo_resposta"];
  /** Códigos das opções (UNICA, SIM_NAO, MULTIPLA); vazio nas perguntas de número e texto. */
  opcoes: string[];
  /** Nas perguntas de número e texto, o que a resposta deve trazer (coluna opcoes do M04). */
  orientacao: string;
  estado: EstadoDaPergunta;
  valor: Valor;
  /** Perguntas do checklist que preencheram a resposta. */
  doChecklist: string[];
  sugestoes: { valor: Valor; pergunta: string }[];
  justificativa: Justificativa | null;
  justificativaAtual: string;
  fundamento: string;
};

const TIPOS_COM_OPCOES = new Set(["UNICA", "SIM_NAO", "MULTIPLA"]);

export function opcoesDoM04(linha: LinhaM04): string[] {
  if (!TIPOS_COM_OPCOES.has(linha.tipo_resposta)) return [];
  return linha.opcoes
    .split(";")
    .map((o) => o.trim())
    .filter(Boolean);
}

export function justificativaDoM04(linha: LinhaM04): Justificativa | null {
  const texto = linha.exige_justificativa.trim();
  if (!texto.startsWith("S")) return null;
  const condicional = /^S se ([A-Z0-9_]+(?:\s+ou\s+[A-Z0-9_]+)*)/.exec(texto);
  const explicacao = texto.replace(/^S\b\s*:?\s*/, "");
  return { texto: explicacao, obrigatoriaCom: condicional ? condicional[1].split(/\s+ou\s+/) : "sempre" };
}

/** A resposta dada exige justificativa? */
export function justificativaObrigatoria(j: Justificativa | null, valor: Valor): boolean {
  if (!j) return false;
  if (j.obrigatoriaCom === "sempre") return true;
  const escolhidos = Array.isArray(valor) ? valor : [valor];
  return escolhidos.some((v) => typeof v === "string" && j.obrigatoriaCom.includes(v));
}

export function perguntasDoWizard(pacote: Pacote, minuta: Minuta, p: ProcessoCompleto): PerguntaDoWizard[] {
  const { wizard, derivadas, origens, sugestoes, globais } = minuta.processo;
  const habilitadas = new Set(wizard.habilitadas);
  const pendentes = new Map(wizard.pendentes.map((x) => [x.id, x]));
  const gravadas = new Map(p.respostasWizard.map((r) => [r.pergunta, r]));
  const lista: PerguntaDoWizard[] = [];
  for (const linha of pacote.matrizes.M04) {
    const derivada = Object.hasOwn(derivadas, linha.id);
    if (!habilitadas.has(linha.id) && !derivada) continue;
    const variavel = variavelDoId(linha.id);
    const origem = origens[variavel];
    const pendente = pendentes.get(linha.id);
    const estado: EstadoDaPergunta = derivada
      ? "calculada"
      : pendente
        ? pendente.decisaoJuridica
          ? "decisao_pendente"
          : "pendente"
        : origem?.origem === "CHECKLIST"
          ? "checklist"
          : "respondida";
    lista.push({
      id: linha.id,
      pergunta: linha.pergunta,
      tipo: linha.tipo_resposta,
      opcoes: opcoesDoM04(linha),
      orientacao: TIPOS_COM_OPCOES.has(linha.tipo_resposta) ? "" : linha.opcoes,
      estado,
      valor: derivada ? derivadas[linha.id] : (globais[variavel] ?? null),
      doChecklist: origem?.origem === "CHECKLIST" ? origem.perguntas : [],
      sugestoes: sugestoes.filter((s) => s.destino === variavel && s.item === undefined).map(({ valor, pergunta }) => ({ valor, pergunta })),
      justificativa: justificativaDoM04(linha),
      justificativaAtual: gravadas.get(linha.id)?.justificativa ?? "",
      fundamento: linha.fundamento,
    });
  }
  return lista;
}

/** Próxima pergunta a responder depois de `atual` (a primeira pendente, dando a volta na lista). */
export function proximaPendente(perguntas: PerguntaDoWizard[], atual?: string): string | null {
  const abertas = (x: PerguntaDoWizard) => x.estado === "pendente" || x.estado === "decisao_pendente";
  const k = perguntas.findIndex((x) => x.id === atual);
  const depois = [...perguntas.slice(k + 1), ...perguntas.slice(0, k + 1)];
  return depois.find((x) => abertas(x) && x.id !== atual)?.id ?? null;
}

// ---------------------------------------------------------------------------------------------------------------
// Campos extras (VAR) que a minuta pede.

const FORMATOS_NUMERICOS = new Set(["NUMERO", "NUMERO_EXTENSO", "PERCENTUAL_EXTENSO", "PERCENTUAL_2", "MOEDA", "MOEDA_POR_EXTENSO"]);

export type FormaDoCampo =
  | { tipo: "simples"; numerico: boolean; data: boolean }
  /** Uma linha por elemento. */
  | { tipo: "lista" }
  /** Um campo por parte do valor (caminho com ponto, ex.: a.minimo). */
  | { tipo: "partes"; partes: { caminho: string; numerico: boolean }[] }
  /** Uma linha por linha da tabela, com as colunas separadas por ";". */
  | { tipo: "tabela"; colunas: { campo: string; cabecalho: string }[] };

export type CampoDaMinuta = {
  id: string;
  descricao: string;
  tipoDeDado: LinhaM05["tipo_dado"];
  origem: LinhaM05["origem"];
  validacao: string;
  /** Códigos aceitos, quando a validação do M05 os lista (ex.: DIAS, MESES ou ANOS). */
  codigos: string[];
  forma: FormaDoCampo;
  /** Trechos da minuta (ou validações de bloqueio) onde o dado falta; vazio quando já foi informado. */
  trechos: string[];
  valor: Valor;
};

type EntradaDoMapa = { fonte?: string | null; alternativas?: string[]; campo?: string; indice?: number; formato?: string; unidade?: string };
type Uso = { campos: Map<string, boolean>; indice: boolean; numerico: boolean; unidades: Set<string>; tabela?: { campo: string; cabecalho: string }[] };

const usosEmCache = new WeakMap<Pacote, Map<string, Uso>>();

/** Como cada VAR é usada nos mapas do M02 e do M08 e nas tabelas do M02. */
function usosDasVariaveis(pacote: Pacote): Map<string, Uso> {
  const emCache = usosEmCache.get(pacote);
  if (emCache) return emCache;
  const usos = new Map<string, Uso>();
  usosEmCache.set(pacote, usos);
  const uso = (v: string) => {
    let u = usos.get(v);
    if (!u) usos.set(v, (u = { campos: new Map(), indice: false, numerico: false, unidades: new Set() }));
    return u;
  };
  for (const linha of [...pacote.matrizes.M02, ...pacote.matrizes.M08]) {
    for (const x of (linha.lacunas_mapa ?? []) as EntradaDoMapa[]) {
      for (const fonte of [x.fonte, ...(x.alternativas ?? [])]) {
        if (!fonte?.startsWith("VAR_")) continue;
        const u = uso(fonte);
        const numerico = FORMATOS_NUMERICOS.has(x.formato ?? "");
        if (x.campo) u.campos.set(x.campo, (u.campos.get(x.campo) ?? false) || numerico);
        else if (numerico) u.numerico = true;
        if (x.indice !== undefined) u.indice = true;
        if (x.unidade) u.unidades.add(x.unidade);
      }
    }
  }
  for (const linha of pacote.matrizes.M02) {
    const tabela = linha.tabela_colunas as { linhas?: string; colunas?: { campo?: string; cabecalho: string }[] } | null;
    if (!tabela?.linhas?.startsWith("VAR_")) continue;
    // A mesma VAR pode montar mais de uma tabela: as colunas se somam, na ordem em que aparecem.
    const u = uso(tabela.linhas);
    for (const c of tabela.colunas ?? []) {
      if (c.campo && !u.tabela?.some((x) => x.campo === c.campo)) u.tabela = [...(u.tabela ?? []), { campo: c.campo, cabecalho: c.cabecalho }];
    }
  }
  return usos;
}

/** Códigos em maiúsculas que a validação do M05 lista antes do primeiro ";" (ex.: "SIM ou NAO"). */
export function codigosDaValidacao(validacao: string): string[] {
  const inicio = validacao.split(";")[0];
  const partes = inicio.split(/,|\s+ou\s+/).map((s) => s.trim().replace(/\s*\(.*$/, ""));
  return partes.length > 1 && partes.every((s) => /^[A-Z][A-Z0-9_.]+$/.test(s)) ? partes : [];
}

function formaDoCampo(linha: LinhaM05, uso: Uso | undefined): FormaDoCampo {
  if (uso?.tabela && uso.tabela.length) return { tipo: "tabela", colunas: uso.tabela };
  if (uso && uso.campos.size) {
    const partes = [...uso.campos].map(([caminho, numerico]) => ({ caminho, numerico }));
    return { tipo: "partes", partes: partes.sort((a, b) => a.caminho.localeCompare(b.caminho)) };
  }
  if (uso?.indice || (linha.tipo_dado === "LISTA" && codigosDaValidacao(linha.validacao).length === 0)) return { tipo: "lista" };
  const numerico = linha.tipo_dado === "NUMERO" || linha.tipo_dado === "MOEDA" || Boolean(uso?.numerico);
  return { tipo: "simples", numerico, data: linha.tipo_dado === "DATA" };
}

/** Origens que a equipe informa nesta tela; as do checklist se corrigem na tela do checklist. */
const ORIGENS_DESTA_TELA = new Set<LinhaM05["origem"]>(["WIZARD", "SISTEMA", "DFD", "PESQUISA_PRECOS"]);

export type CamposDaMinuta = {
  /** Informados nesta tela. */
  campos: CampoDaMinuta[];
  /** Dados que vêm do checklist (VAR de origem CHECKLIST e complementos CK-X): corrigir na tela do checklist. */
  doChecklist: { id: string; descricao: string; trechos: string[] }[];
  /** Marcadores que a equipe completa à mão na minuta (sem dado ligado). */
  daEquipe: { trecho: string; marcador: string }[];
};

export function camposDaMinuta(pacote: Pacote, minuta: Minuta, p: ProcessoCompleto): CamposDaMinuta {
  const m05 = new Map(pacote.matrizes.M05.map((l) => [l.id, l]));
  const usos = usosDasVariaveis(pacote);
  const trechos = new Map<string, Set<string>>();
  const daEquipe: CamposDaMinuta["daEquipe"] = [];
  for (const l of minuta.lacunasNoTexto) {
    if (!l.fonte) {
      if (l.motivo === "equipe") daEquipe.push({ trecho: l.trecho, marcador: l.marcador });
      continue;
    }
    trechos.set(l.fonte, (trechos.get(l.fonte) ?? new Set()).add(l.trecho));
  }
  // Unidade ligada a um valor que falta (VAR-163 da VAR-034) entra junto.
  for (const fonte of [...trechos.keys()]) {
    for (const unidade of usos.get(variavelDoId(fonte))?.unidades ?? []) {
      const id = unidade.replace("_", "-");
      if (!trechos.has(id) && minuta.processo.globais[unidade] === undefined) trechos.set(id, new Set(trechos.get(fonte)));
    }
  }
  // Dado que uma validação de bloqueio disparada lê (VAL-005 lê a VAR-001, VAL-047 a VAR-099) também é pedido aqui.
  const m10 = new Map(pacote.matrizes.M10.map((l) => [l.id, l]));
  for (const v of minuta.validacoes.disparadas.filter((x) => x.tipo === "BLOQUEIO")) {
    for (const nome of variaveisLidas(m10.get(v.id)?.condicao_expr ?? null)) {
      if (!/^VAR_\d+$/.test(nome)) continue;
      const id = nome.replace("_", "-");
      trechos.set(id, (trechos.get(id) ?? new Set()).add(v.id));
    }
  }
  const informadas = new Map(p.respostasWizard.filter((r) => r.pergunta.startsWith("VAR-")).map((r) => [r.pergunta, r.valor as Valor]));

  const campos: CampoDaMinuta[] = [];
  const doChecklist: CamposDaMinuta["doChecklist"] = [];
  const ids = [...new Set([...trechos.keys(), ...informadas.keys()])].sort((a, b) => a.localeCompare(b, "pt-BR", { numeric: true }));
  for (const id of ids) {
    const onde = [...(trechos.get(id) ?? [])];
    if (id.startsWith("CK-")) {
      const linha = pacote.matrizes.M11.find((l) => l.id === id);
      doChecklist.push({ id, descricao: linha?.pergunta ?? id, trechos: onde });
      continue;
    }
    const linha = m05.get(id);
    if (!linha) continue;
    if (!ORIGENS_DESTA_TELA.has(linha.origem) || linha.calculo_expr !== null) {
      if (onde.length) doChecklist.push({ id, descricao: linha.descricao, trechos: onde });
      continue;
    }
    campos.push(campoDaVariavel(pacote, linha, informadas.get(id) ?? null, onde));
  }
  return { campos, doChecklist, daEquipe };
}

/** Campo de entrada de uma VAR (forma tirada dos mapas e das tabelas do M02), com o valor que a equipe informou. */
export function campoDaVariavel(pacote: Pacote, linha: LinhaM05, valor: Valor, trechos: string[] = []): CampoDaMinuta {
  return {
    id: linha.id,
    descricao: linha.descricao,
    tipoDeDado: linha.tipo_dado,
    origem: linha.origem,
    validacao: linha.validacao,
    codigos: codigosDaValidacao(linha.validacao),
    forma: formaDoCampo(linha, usosDasVariaveis(pacote).get(variavelDoId(linha.id))),
    trechos,
    valor,
  };
}

/** Número digitado com vírgula ou ponto decimal ("1.234,56", "2,5", "30"); null quando não é número. */
export function numeroDigitado(texto: string): number | null {
  const t = texto.trim().replace(/\s|%|R\$/g, "");
  if (!t) return null;
  const normal = t.includes(",") ? t.replace(/\./g, "").replace(",", ".") : t;
  return /^-?\d+(\.\d+)?$/.test(normal) ? Number(normal) : null;
}

function definir(objeto: Record<string, Valor>, caminho: string, valor: Valor) {
  const partes = caminho.split(".");
  let atual = objeto;
  for (const parte of partes.slice(0, -1)) {
    const proximo = atual[parte];
    if (proximo === null || typeof proximo !== "object" || Array.isArray(proximo)) atual[parte] = {};
    atual = atual[parte] as Record<string, Valor>;
  }
  atual[partes[partes.length - 1]] = valor;
}

/** Valor de um campo extra a partir do formulário; erro em texto quando não confere com a forma. */
export function valorDoCampo(campo: CampoDaMinuta, dados: FormData): { valor: Valor } | { erro: string } {
  const texto = (nome: string) => String(dados.get(nome) ?? "").trim();
  const forma = campo.forma;
  if (forma.tipo === "simples") {
    const t = texto("valor");
    if (!t) return { valor: null };
    if (forma.numerico) {
      const n = numeroDigitado(t);
      return n === null ? { erro: "Informe só o número (ex.: 30 ou 2,5)." } : { valor: n };
    }
    if (forma.data && !/^\d{2}\/\d{2}\/\d{4}$/.test(t)) return { erro: "Informe a data como DD/MM/AAAA." };
    if (campo.codigos.length && !campo.codigos.includes(t)) return { erro: `Use um destes códigos: ${campo.codigos.join(", ")}.` };
    return { valor: t };
  }
  if (forma.tipo === "lista") {
    const linhas = texto("valor")
      .split("\n")
      .map((l) => l.trim())
      .filter(Boolean);
    return { valor: linhas.length === 0 ? null : linhas.length === 1 && campo.tipoDeDado !== "LISTA" ? linhas[0] : linhas };
  }
  if (forma.tipo === "partes") {
    const objeto: Record<string, Valor> = {};
    for (const parte of forma.partes) {
      const t = texto(`parte:${parte.caminho}`);
      if (!t) continue;
      if (parte.numerico) {
        const n = numeroDigitado(t);
        if (n === null) return { erro: `${parte.caminho}: informe só o número.` };
        definir(objeto, parte.caminho, n);
      } else definir(objeto, parte.caminho, t);
    }
    return { valor: Object.keys(objeto).length ? objeto : null };
  }
  const linhas = texto("valor")
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);
  const tabela: Record<string, Valor>[] = [];
  for (const [k, linha] of linhas.entries()) {
    const celulas = linha.split(";").map((c) => c.trim());
    if (celulas.length !== forma.colunas.length) return { erro: `Linha ${k + 1}: são ${forma.colunas.length} colunas, separadas por ";".` };
    tabela.push(Object.fromEntries(forma.colunas.map((c, j) => [c.campo, numeroDigitado(celulas[j]) ?? celulas[j]])));
  }
  return { valor: tabela.length ? tabela : null };
}

/** Valor gravado no formato do formulário (para preencher os campos ao editar). */
export function textoDoCampo(campo: CampoDaMinuta): Record<string, string> {
  const v = campo.valor;
  const forma = campo.forma;
  const br = (x: Valor) => (typeof x === "number" ? String(x).replace(".", ",") : x === null ? "" : String(x));
  if (v === null) return {};
  if (forma.tipo === "partes") {
    const saida: Record<string, string> = {};
    for (const parte of forma.partes) {
      let atual: Valor = v;
      for (const k of parte.caminho.split(".")) atual = atual && typeof atual === "object" && !Array.isArray(atual) ? (atual[k] ?? null) : null;
      saida[`parte:${parte.caminho}`] = br(atual);
    }
    return saida;
  }
  if (forma.tipo === "tabela" && Array.isArray(v)) {
    return { valor: v.map((linha) => forma.colunas.map((c) => br(linha && typeof linha === "object" && !Array.isArray(linha) ? (linha[c.campo] ?? null) : null)).join("; ")).join("\n") };
  }
  if (Array.isArray(v)) return { valor: v.map(br).join("\n") };
  return { valor: br(v) };
}
