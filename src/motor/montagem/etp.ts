/**
 * ETP montado campo a campo (Marco 3, passo 3; decisão 0015). O ETP Digital é um formulário: cada campo do M01
 * recebe o que as respostas do processo dizem sobre ele, na ordem do M01, com a origem de cada parte.
 *
 * Ligações (todas IDs lidos do pacote, nenhuma regra escrita aqui):
 * - dado: as VAR cujo M05.usada_em cita o campo e, quando informadas, as que o M06 diz que o TR repete do campo
 *   (linha do M06 ligada só a ele);
 * - checklist: as perguntas do M11 cujo destinos cita o campo e que não preenchem uma VAR do próprio campo
 *   (JUSTIFICA, SUGERE, ALERTA), respondidas e com a condicional verdadeira;
 * - justificativa: as WZ cujo M04.exige_justificativa cita o campo, quando a equipe escreveu a justificativa;
 * - tabela: campo do tipo TB monta a tabela do bloco do M01.destino_tr que tem tabela_colunas.
 *
 * O texto de cada parte é a resposta como veio; o rótulo é a descrição do M05 ou a pergunta do M11 e do M04. Valor
 * que falta numa VAR obrigatória (M05.obrigatoria = S) vira lacuna marcada, [[LACUNA VAR-xxx]]; resposta de opção
 * do checklist nunca entra solta ("Sim"), sempre com a pergunta.
 */
import type { EntradaProcesso } from "../entrada.ts";
import type { Minuta } from "../minuta.ts";
import { type Valor, avaliar, verdadeiro } from "../pacote/avaliador.ts";
import type { LinhaM01, LinhaM04, LinhaM05, LinhaM11, Pacote } from "../pacote/esquema.ts";
import { variavelDoId } from "../pacote/nomes.ts";
import { vazia } from "../wizard/checklist.ts";
import { FormatoInvalido, formatar, textoDoValor } from "./formatos.ts";
import { MARCA_DE_TABELA, Montagem } from "./lacunas.ts";

const CAMPO_DO_ETP = /ETP-\d{2}\.\d{2}/g;
const PREFIXO_DE_ATRIBUTO = "tabela_itens.";
const PREFIXO_DA_DESCRICAO_DE_ATRIBUTO = /^Coluna da VAR-\d{3}:\s*/;
const MARCA_DE_LACUNA = "[[LACUNA";

export type OrigemDaParte =
  /** Preenchido pelas perguntas do checklist indicadas. */
  | { de: "checklist"; perguntas: string[] }
  /** Informado pela equipe (wizard ou campo da minuta). */
  | { de: "equipe" }
  /** Calculado pelo M05 a partir de outros dados. */
  | { de: "calculo" }
  /** Veio pronto na entrada (dado do sistema ou da planilha de itens). */
  | { de: "entrada" };

export type ParteDoCampo =
  | {
      tipo: "dado";
      /** VAR do M05. */
      regra: string;
      rotulo: string;
      /** Texto do valor; null quando a VAR não tem valor. */
      texto: string | null;
      obrigatoria: LinhaM05["obrigatoria"];
      origem: OrigemDaParte | null;
      /**
       * M05: a VAR cita o campo em usada_em. M06: decisão que o bloco do TR repete do campo (M06 ligado só a este
       * campo); entra só quando informada, porque a falta já aparece como lacuna no TR.
       */
      ligacao: "M05" | "M06";
    }
  | { tipo: "checklist"; regra: string; rotulo: string; texto: string }
  | { tipo: "justificativa"; regra: string; rotulo: string; texto: string; resposta: Valor }
  | { tipo: "tabela"; regra: string; texto: string; lacunas: number };

export type SituacaoDoCampo =
  /** Tem conteúdo e nenhuma lacuna. */
  | "preenchido"
  /** Tem conteúdo e alguma lacuna de dado obrigatório. */
  | "incompleto"
  /** Ligado a dados, mas nenhum veio. */
  | "vazio"
  /** Texto que o próprio ETP Digital imprime (tipo TF sem dado ligado): não se copia. */
  | "texto_do_etp_digital"
  /** O pacote não liga nenhum dado a este campo: a orientação do M01 diz o que fazer. */
  | "sem_ligacao";

export type CampoDoEtp = {
  id: string;
  secao: { numero: string; nome: string };
  campo: string;
  inciso: string;
  /** Elemento obrigatório do ETP (art. 18, § 2º; M01.obrigatorio_par2). */
  obrigatorio: boolean;
  tipo: string;
  situacao: SituacaoDoCampo;
  partes: ParteDoCampo[];
  /** Texto para colar no ETP Digital: as partes com conteúdo, separadas por linha em branco, com as lacunas marcadas. */
  texto: string;
  /** VAR obrigatórias sem valor (marcadas no texto). */
  lacunas: string[];
  orientacao: { preenchimento: string; antiAlucinacao: string; quandoNaoSeAplica: string };
  /** Blocos do TR que repetem o campo (M01.destino_tr). */
  destinoTr: string[];
  /** Validações do M10 disparadas que citam o campo ou um dado dele (coluna afeta). */
  validacoes: string[];
};

export type Etp = {
  pacote: Minuta["pacote"];
  campos: CampoDoEtp[];
  /** Justificativas do wizard que o M04 manda para o ETP sem dizer o campo (texto escrito pela equipe). */
  justificativasSemCampo: { regra: string; rotulo: string; texto: string }[];
  /** Campos obrigatórios (art. 18, § 2º) vazios ou com lacuna. */
  pendencias: string[];
};

/** IDs de campo do ETP citados num texto, sem repetir, na ordem. */
function camposCitados(texto: string): string[] {
  return [...new Set(texto.match(CAMPO_DO_ETP) ?? [])];
}

/** Rótulo de uma VAR: para atributo de item, o cabeçalho ou o rótulo da tabela de itens do M02; senão, a descrição. */
type RotuloDoAtributo = { rotulo: string; textos?: Record<string, string>; modelo?: string };

function rotulosDosAtributos(pacote: Pacote): Map<string, RotuloDoAtributo> {
  type Coluna = { cabecalho: string; fonte?: string; textos?: Record<string, string>; complementos?: { fonte: string; rotulo: string; texto?: string }[] };
  const rotulos = new Map<string, RotuloDoAtributo>();
  for (const linha of pacote.matrizes.M02) {
    const tabela = linha.tabela_colunas as { linhas?: string; colunas?: Coluna[] } | null;
    if (tabela?.linhas !== "itens") continue;
    for (const coluna of tabela.colunas ?? []) {
      if (coluna.fonte?.startsWith("itens.") && !rotulos.has(coluna.fonte)) rotulos.set(coluna.fonte, { rotulo: coluna.cabecalho, textos: coluna.textos });
      for (const c of coluna.complementos ?? []) if (!rotulos.has(c.fonte)) rotulos.set(c.fonte, { rotulo: c.rotulo, modelo: c.texto });
    }
  }
  return rotulos;
}

function inicialMaiuscula(s: string): string {
  return s.slice(0, 1).toUpperCase() + s.slice(1);
}

/** Fim certo do rótulo: parêntese, ponto e vírgula ou dois-pontos. */
const FIM_DO_ROTULO = /\s\(|;\s|:\s/;
/** Remissão a regra interna no rótulo ("da VAR-034"): é nota para quem mantém as matrizes, não para o ETP. */
const REMISSAO_INTERNA = /\s+(?:(?:d[aeo]s?|na|no|pela|pelo)\s+)?(?:VAR|WZ|CK|TR|ETP|SET|VAL)-[\w.-]+/g;
/** Palavras depois das quais a maiúscula é nome próprio ("do Plano"), e não começo de frase. */
const ANTES_DE_NOME = new Set(["a", "o", "as", "os", "de", "do", "da", "dos", "das", "no", "na", "nos", "nas", "em", "e", "ou", "com", "para", "pelo", "pela", "por", "ao", "à"]);

/** Posição onde começa a segunda frase da descrição, quando a matriz não pôs ponto ("unidade A unidade fica"). */
function inicioDeFrase(texto: string): number {
  for (const m of texto.matchAll(/(?<=^|\s)(\S+)(?=\s[A-ZÀ-Ú](?:[a-zà-ú]|\s))/g)) {
    const anterior = m[1];
    if (/^[a-zà-ú]{3,}$/.test(anterior) && !ANTES_DE_NOME.has(anterior)) return (m.index ?? 0) + anterior.length;
  }
  return -1;
}

/**
 * Rótulo de uma VAR a partir da descrição do M05: sem o "Coluna da VAR-011:" dos atributos de item e só até a
 * primeira explicação (a descrição mistura o nome do dado com notas de quem mantém as matrizes).
 */
export function rotuloDaDescricao(linha: LinhaM05): string {
  let texto = linha.descricao.replace(PREFIXO_DA_DESCRICAO_DE_ATRIBUTO, "").trim();
  const fim = texto.search(FIM_DO_ROTULO);
  if (fim > 0) texto = texto.slice(0, fim);
  // Ponto que fecha frase: depois de palavra com quatro letras ou mais (não corta "art. 10").
  const ponto = texto.search(/[a-zà-ú]{4}\.(\s|$)/);
  if (ponto >= 0) texto = texto.slice(0, ponto + 4);
  const frase = inicioDeFrase(texto);
  if (frase > 0) texto = texto.slice(0, frase);
  const curto = texto.replace(REMISSAO_INTERNA, "").trim();
  return inicialMaiuscula(curto || linha.nome);
}

/** Valor estruturado em texto: lista de objetos vira uma linha por elemento; objeto vira "a: x; b: y". */
function textoEstruturado(v: Valor): string {
  if (Array.isArray(v)) {
    const linhas = v.filter((x) => !vazia(x)).map(textoEstruturado);
    return v.some((x) => x !== null && typeof x === "object") ? linhas.join("\n") : linhas.join("; ");
  }
  if (v !== null && typeof v === "object") {
    return Object.entries(v)
      .filter(([, x]) => !vazia(x))
      .map(([k, x]) => `${k}: ${textoEstruturado(x)}`)
      .join("; ");
  }
  return textoDoValor(v);
}

/** Validação do M05 que pede ano ("AAAA"): o número sai sem separador de milhar. */
const VALIDACAO_DE_ANO = /^AAAA\b/;

/** Valor de uma VAR no formato do tipo do M05; valor fora do formato sai como veio (o dado nunca some). */
function textoDoTipo(v: Valor, linha: LinhaM05): string {
  const tipo = linha.tipo_dado;
  try {
    if (tipo === "MOEDA") return formatar(v, "MOEDA");
    if (tipo === "NUMERO" && typeof v === "number") return VALIDACAO_DE_ANO.test(linha.validacao) ? String(v) : formatar(v, "NUMERO");
    if (tipo === "DATA") return formatar(v, "DATA");
  } catch (e) {
    if (!(e instanceof FormatoInvalido)) throw e;
  }
  if (tipo === "TEXTO" && Array.isArray(v)) return v.filter((x) => !vazia(x)).map(textoEstruturado).join("\n");
  return textoEstruturado(v);
}

type Contexto = {
  pacote: Pacote;
  minuta: Minuta;
  entrada: EntradaProcesso;
  m05: Map<string, LinhaM05>;
  rotulos: ReturnType<typeof rotulosDosAtributos>;
  calculados: Set<string>;
};

function origemDaVariavel(ctx: Contexto, variavel: string): OrigemDaParte | null {
  const origem = ctx.minuta.processo.origens[variavel];
  if (origem?.origem === "CHECKLIST") return { de: "checklist", perguntas: origem.perguntas };
  if (origem?.origem === "EQUIPE") return { de: "equipe" };
  if (ctx.calculados.has(variavel)) return { de: "calculo" };
  if (Object.hasOwn(ctx.entrada.variaveis, variavel)) return { de: "equipe" };
  return origem ? { de: "entrada" } : null;
}

/** Parte de uma VAR global. */
function parteDeVariavel(ctx: Contexto, linha: LinhaM05, ligacao: "M05" | "M06"): ParteDoCampo {
  const variavel = variavelDoId(linha.id);
  const valor = ctx.minuta.processo.globais[variavel];
  return {
    tipo: "dado",
    regra: linha.id,
    rotulo: rotuloDaDescricao(linha),
    texto: vazia(valor) ? null : textoDoTipo(valor as Valor, linha),
    obrigatoria: linha.obrigatoria,
    origem: vazia(valor) ? null : origemDaVariavel(ctx, variavel),
    ligacao,
  };
}

/** Parte de um atributo de item: "item 1: valor; item 3: valor", com o código traduzido pela tabela do M02. */
function parteDeAtributo(ctx: Contexto, linha: LinhaM05, ligacao: "M05" | "M06"): ParteDoCampo {
  const atributo = linha.nome.slice(PREFIXO_DE_ATRIBUTO.length);
  const rotulo = ctx.rotulos.get(`itens.${atributo}`);
  const textos: string[] = [];
  const perguntas = new Set<string>();
  let algum = false;
  let calculado = false;
  for (const item of ctx.minuta.processo.itens) {
    const valor = item[atributo] as Valor | undefined;
    if (vazia(valor)) {
      if (linha.obrigatoria === "S") textos.push(`item ${item.numero}: [[LACUNA ${linha.id}]]`);
      continue;
    }
    algum = true;
    const bruto = textoDoTipo(valor as Valor, linha);
    const texto = rotulo?.textos?.[bruto] ?? (rotulo?.modelo?.includes("{valor}") ? rotulo.modelo.replace("{valor}", bruto) : bruto);
    textos.push(`item ${item.numero}: ${texto}`);
    const pergunta = ctx.minuta.processo.origensDeItem[`${item.numero}.${atributo}`];
    if (pergunta) perguntas.add(pergunta);
    if (ctx.minuta.processo.calculados.some((c) => c.destino === atributo && c.item === item.numero)) calculado = true;
  }
  const origem: OrigemDaParte | null = !algum ? null : perguntas.size ? { de: "checklist", perguntas: [...perguntas] } : calculado ? { de: "calculo" } : { de: "entrada" };
  return {
    tipo: "dado",
    regra: linha.id,
    rotulo: rotulo?.rotulo ?? rotuloDaDescricao(linha),
    texto: algum ? textos.join("; ") : null,
    obrigatoria: linha.obrigatoria,
    origem,
    ligacao,
  };
}

/** Destinos (VAR-xxx ou atributo) que uma pergunta do M11 preenche. */
function destinosPreenchidos(linha: LinhaM11, m05PorNome: Map<string, string>): Set<string> {
  const saida = new Set<string>();
  for (const destino of Object.keys(linha.preenche_expr ?? {})) {
    if (destino.startsWith("VAR_")) saida.add(destino.replace("_", "-"));
    else if (destino.startsWith("itens.")) {
      const id = m05PorNome.get(`${PREFIXO_DE_ATRIBUTO}${destino.slice("itens.".length)}`);
      if (id) saida.add(id);
    }
  }
  return saida;
}

/** Resposta do checklist em texto: a caixa de resposta entra sozinha; a opção marcada entra com a pergunta. */
function textoDaResposta(linha: LinhaM11, valor: Valor | undefined, texto: Valor | undefined): string | null {
  const caixa = vazia(texto) ? "" : textoDoValor(texto as Valor).trim();
  if (vazia(valor)) return caixa || null;
  if (linha.tipo_resposta === "TEXTO") return [textoDoValor(valor as Valor).trim(), caixa].filter(Boolean).join("\n");
  if (linha.tipo_resposta === "TABELA") return [textoEstruturado(valor as Valor), caixa].filter(Boolean).join("\n");
  const opcao = Array.isArray(valor) ? valor.map(textoDoValor).join("; ") : textoDoValor(valor as Valor);
  const pergunta = linha.pergunta.trim();
  const fecho = /[.!?]$/.test(opcao) ? "" : ".";
  return `${pergunta} ${opcao}${fecho}${caixa ? ` ${caixa}` : ""}`;
}

function parteDoChecklist(ctx: Contexto, linha: LinhaM11): ParteDoCampo | null {
  const dados = ctx.minuta.processo.dados;
  if (linha.condicional_expr !== null && !verdadeiro(avaliar(linha.condicional_expr, dados))) return null;
  const variavel = variavelDoId(linha.id);
  if (linha.por_item === "N" || !ctx.minuta.processo.porItem.has(variavel)) {
    const texto = textoDaResposta(linha, dados[variavel], dados[`${variavel}_texto`]);
    return texto ? { tipo: "checklist", regra: linha.id, rotulo: linha.pergunta, texto } : null;
  }
  // Pergunta por item: a resposta de cada item indicado.
  const textos: string[] = [];
  for (const item of ctx.minuta.processo.itens) {
    const respostas = item.respostas_por_item ?? {};
    const texto = textoDaResposta(linha, respostas[variavel], respostas[`${variavel}_texto`]);
    if (texto) textos.push(`item ${item.numero}: ${texto}`);
  }
  return textos.length ? { tipo: "checklist", regra: linha.id, rotulo: linha.pergunta, texto: textos.join("\n") } : null;
}

function parteDaJustificativa(ctx: Contexto, linha: LinhaM04): ParteDoCampo | null {
  const variavel = variavelDoId(linha.id);
  const texto = ctx.entrada.justificativas?.[variavel]?.trim();
  if (!texto) return null;
  return { tipo: "justificativa", regra: linha.id, rotulo: linha.pergunta, texto, resposta: ctx.minuta.processo.globais[variavel] ?? null };
}

/** Texto até este tamanho, numa linha só e sem ponto final, é dado curto: leva o rótulo para não ficar solto. */
const TAMANHO_DE_DADO_CURTO = 200;

function textoDaParte(parte: ParteDoCampo): string | null {
  if (parte.tipo !== "dado") return parte.texto;
  if (parte.texto === null) return parte.obrigatoria === "S" ? `${parte.rotulo}: [[LACUNA ${parte.regra}]]` : null;
  // Texto corrido (parágrafo escrito pela equipe ou pelo requisitante) entra sozinho; dado curto leva o rótulo.
  const corrido = parte.texto.includes("\n") || parte.texto.length >= TAMANHO_DE_DADO_CURTO || /[.!?]$/.test(parte.texto);
  return corrido ? parte.texto : `${parte.rotulo}: ${parte.texto}`;
}

export function gerarEtp(entrada: EntradaProcesso, minuta: Minuta): Etp {
  const { pacote } = entrada;
  const { M01, M02, M04, M05, M06, M10, M11 } = pacote.matrizes;
  const m05 = new Map(M05.map((l) => [l.id, l]));
  const m05PorNome = new Map(M05.map((l) => [l.nome, l.id]));
  const ctx: Contexto = {
    pacote,
    minuta,
    entrada,
    m05,
    rotulos: rotulosDosAtributos(pacote),
    calculados: new Set(minuta.processo.calculados.filter((c) => c.item === undefined).map((c) => c.destino)),
  };
  const disparadas = new Set(minuta.validacoes.disparadas.map((v) => v.id));
  const m02 = new Map(M02.map((l) => [l.id, l]));
  const montagem = new Montagem(minuta.processo.dados, (v) => M05.find((l) => variavelDoId(l.id) === v)?.id ?? v);

  const decisoesDoM06 = new Map<string, string[]>();
  for (const linha of M06) {
    const campos = camposCitados(linha.campos_etp);
    if (campos.length !== 1) continue;
    const lista = decisoesDoM06.get(campos[0]) ?? [];
    for (const id of linha.variaveis.match(/VAR-\d{3}/g) ?? []) if (!lista.includes(id)) lista.push(id);
    decisoesDoM06.set(campos[0], lista);
  }
  const justificativasComCampo = new Set<string>();
  const campos: CampoDoEtp[] = M01.map((campo: LinhaM01) => {
    const variaveis = M05.filter((l) => camposCitados(l.usada_em).includes(campo.id));
    const doCampo = new Set(variaveis.map((l) => l.id));
    const partes: ParteDoCampo[] = [];

    // Tabela: campo TB com bloco do TR que monta tabela de itens.
    let tabela = false;
    if (campo.tipo.split("+").includes("TB")) {
      for (const bloco of campo.destino_tr.split(";").map((s) => s.trim())) {
        const linha = m02.get(bloco);
        if (!linha?.tabela_colunas) continue;
        const montado = montagem.bloco(linha, linha.texto_literal);
        partes.push({ tipo: "tabela", regra: linha.id, texto: montado.texto, lacunas: montado.lacunas.length });
        tabela = true;
        break;
      }
    }
    const naTabela = (l: LinhaM05) => tabela && (l.tipo_dado === "TABELA" || (l.nome.startsWith(PREFIXO_DE_ATRIBUTO) && ctx.rotulos.has(`itens.${l.nome.slice(PREFIXO_DE_ATRIBUTO.length)}`)));

    const parteDaVar = (linha: LinhaM05, ligacao: "M05" | "M06") =>
      linha.nome.startsWith(PREFIXO_DE_ATRIBUTO) ? parteDeAtributo(ctx, linha, ligacao) : parteDeVariavel(ctx, linha, ligacao);
    for (const linha of variaveis) if (!naTabela(linha)) partes.push(parteDaVar(linha, "M05"));
    const ligadoPorDado = variaveis.length > 0 || tabela;
    // Decisões que o TR repete deste campo (M06 com só este campo): entram quando informadas.
    if (ligadoPorDado) {
      for (const id of decisoesDoM06.get(campo.id) ?? []) {
        const linha = m05.get(id);
        if (!linha || doCampo.has(id) || naTabela(linha)) continue;
        const parte = parteDaVar(linha, "M06");
        if (parte.tipo === "dado" && parte.texto !== null && !parte.texto.includes(MARCA_DE_LACUNA)) {
          partes.push(parte);
          doCampo.add(id);
        }
      }
    }
    for (const linha of M11) {
      if (linha.efeito === "SO_CONTROLE" || !camposCitados(linha.destinos).includes(campo.id)) continue;
      if ([...destinosPreenchidos(linha, m05PorNome)].some((d) => doCampo.has(d))) continue;
      const parte = parteDoChecklist(ctx, linha);
      if (parte) partes.push(parte);
    }
    for (const linha of M04) {
      if (!camposCitados(linha.exige_justificativa).includes(campo.id)) continue;
      justificativasComCampo.add(linha.id);
      const parte = parteDaJustificativa(ctx, linha);
      if (parte) partes.push(parte);
    }

    const textos = partes.map(textoDaParte).filter((t): t is string => t !== null);
    const lacunas = partes.flatMap((p) =>
      (p.tipo === "dado" && p.obrigatoria === "S" && (p.texto === null || p.texto.includes(MARCA_DE_LACUNA))) || (p.tipo === "tabela" && p.lacunas > 0) ? [p.regra] : [],
    );
    const comConteudo = partes.some((p) => (p.tipo === "dado" ? p.texto !== null : p.tipo === "tabela" ? !p.texto.includes(MARCA_DE_TABELA) : true));
    const ligado = ligadoPorDado || M11.some((l) => camposCitados(l.destinos).includes(campo.id)) || M04.some((l) => camposCitados(l.exige_justificativa).includes(campo.id));
    const situacao: SituacaoDoCampo = !ligado
      ? campo.tipo.split("+").includes("TF")
        ? "texto_do_etp_digital"
        : "sem_ligacao"
      : !comConteudo
        ? "vazio"
        : lacunas.length
          ? "incompleto"
          : "preenchido";

    const afetados = new Set([campo.id, ...variaveis.map((l) => l.id)]);
    const validacoes = M10.filter((l) => disparadas.has(l.id) && [...(l.afeta.match(/(ETP-\d{2}\.\d{2}|VAR-\d{3})/g) ?? [])].some((x) => afetados.has(x))).map((l) => l.id);

    return {
      id: campo.id,
      secao: { numero: campo.secao_numero, nome: campo.secao_nome },
      campo: campo.campo,
      inciso: campo.inciso_art18,
      obrigatorio: campo.obrigatorio_par2 === "S",
      tipo: campo.tipo,
      situacao,
      partes,
      texto: situacao === "texto_do_etp_digital" || situacao === "sem_ligacao" ? "" : textos.join("\n\n"),
      lacunas,
      orientacao: { preenchimento: campo.regra_preenchimento, antiAlucinacao: campo.regra_anti_alucinacao, quandoNaoSeAplica: campo.quando_nao_se_aplica },
      destinoTr: campo.destino_tr
        .split(";")
        .map((s) => s.trim())
        .filter(Boolean),
      validacoes,
    };
  });

  // Justificativa pedida "no ETP" sem dizer o campo: fica à vista, para a equipe pôr no campo certo.
  const justificativasSemCampo: Etp["justificativasSemCampo"] = [];
  for (const linha of M04) {
    if (justificativasComCampo.has(linha.id) || !/\bETP\b/.test(linha.exige_justificativa)) continue;
    const parte = parteDaJustificativa(ctx, linha);
    if (parte && parte.tipo === "justificativa") justificativasSemCampo.push({ regra: parte.regra, rotulo: parte.rotulo, texto: parte.texto });
  }

  return {
    pacote: minuta.pacote,
    campos,
    justificativasSemCampo,
    pendencias: campos.filter((c) => c.obrigatorio && (c.situacao === "vazio" || c.situacao === "incompleto")).map((c) => c.id),
  };
}

/** VAR ligadas a um campo do ETP (M05.usada_em), para a derivação e para a tela. */
export function variaveisDoCampo(pacote: Pacote, campo: string): string[] {
  return pacote.matrizes.M05.filter((l) => camposCitados(l.usada_em).includes(campo)).map((l) => l.id);
}

export { camposCitados };
