/**
 * Texto dos blocos (M02) e das cláusulas setoriais (M08) pelo lacunas_mapa, e tabelas pelo tabela_colunas
 * (Fases 13 a 15 das matrizes; README, "Texto da minuta"). A semântica segue a montagem do simulador das
 * matrizes (scripts/f13_texto.py), com duas diferenças deliberadas pedidas na tarefa:
 * - lacuna marcada com o ID da regra: [[LACUNA VAR-034]] (o simulador usa o nome da variável);
 * - opção com "padrao": true sai marcada, [[PADRÃO: texto]], para o operador ver que o valor não foi informado.
 * Valor ausente sempre vira lacuna; nada é inventado.
 */
import { type Valor, avaliar, verdadeiro } from "../pacote/avaliador.ts";
import type { LinhaM02, LinhaM08 } from "../pacote/esquema.ts";
import { vazia } from "../wizard/checklist.ts";
import { FormatoInvalido, formatar, listaEmTexto, textoDoNumero, textoDoValor } from "./formatos.ts";

export type MotivoDeLacuna =
  /** o mapa diz de onde vem o dado, e ele não veio */
  | "sem_valor"
  /** o mapa diz que a equipe preenche à mão (fonte nula, ação EQUIPE) */
  | "equipe"
  /** bloco com marcadores e sem mapa: não se sabe o que preenche */
  | "sem_mapa"
  /** tabela sem as linhas de que precisa (sem itens, ou VAR da tabela sem linhas estruturadas) */
  | "tabela_nao_montada";

export type LacunaDoTexto = {
  /** Bloco do M02 ou cláusula do M08. */
  trecho: string;
  /** Marcador do modelo, ou a célula da tabela ("ESPECIFICAÇÃO do item 1"). */
  marcador: string;
  /** Regra de onde viria o dado (VAR-034, WZ-15...), quando o mapa diz. */
  fonte: string | null;
  motivo: MotivoDeLacuna;
};

export type ValorPadrao = { trecho: string; marcador: string; texto: string };

export type TextoMontado = {
  texto: string;
  lacunas: LacunaDoTexto[];
  padroes: ValorPadrao[];
  /** Bloco de série (lista_blocos) sem elemento: sai da minuta. */
  omitido: boolean;
};

type EntradaDoMapa = {
  marcador: string;
  ocorrencia: number;
  fonte: string | null;
  acao?: string;
  campo?: string;
  indice?: number;
  juntar_restante?: boolean;
  formato?: string;
  unidade?: string;
  texto?: string;
  opcoes?: { quando: unknown; texto: string; padrao?: boolean }[];
  grupo?: string;
  quando?: unknown;
  remove_antes?: string;
  se_falso?: string;
  estende_desde?: string;
  estende_ate?: string;
  se_vazio?: string;
  alternativas?: string[];
  inicial_minuscula?: boolean;
  inicial_maiuscula?: boolean;
  filtro_item?: unknown;
  /** Fase 15: singular ou plural pelo número de itens do valor; o trecho fixo vizinho entra na troca. */
  concordancia?: { singular: string; plural: string };
  /** Fase 15: modelo de cada grupo do POR_ITEM_AGRUPADO. */
  modelo_por_item?: { singular: string; plural: string };
};

type Coluna = {
  cabecalho: string;
  fonte?: string;
  campo?: string;
  formato?: string;
  sigiloso?: string;
  /** Fase 15: a coluna só entra quando a condição é verdadeira. */
  quando?: unknown;
  /** Fase 15: código do M05 para o texto da célula; código fora da lista vira lacuna. */
  textos?: Record<string, string>;
  complementos?: { fonte: string; rotulo: string; texto?: string; quando?: unknown }[];
};

type TabelaColunas = {
  linhas: string;
  colunas: Coluna[];
  orcamento_sigiloso?: { quando: unknown; colunas: string[]; texto: string };
  /** Valor da cota: fonte itens.<atributo> ou texto fixo (Fase 15). */
  linha_cota?: { quando: unknown; valores: Record<string, string | { texto: string }> };
};

const MARCA_DE_TABELA = "[[TABELA NÃO MONTADA]]";

/** [[LACUNA ...]] com o ID da regra; sem fonte, [[LACUNA]]. */
export type NomeDaRegra = (variavel: string) => string;

function ajustarInicial(s: string, x: EntradaDoMapa): string {
  if (x.inicial_minuscula) return s.slice(0, 1).toLowerCase() + s.slice(1);
  if (x.inicial_maiuscula) return s.slice(0, 1).toUpperCase() + s.slice(1);
  return s;
}

function caminho(valor: Valor, campo: string): Valor {
  let atual: Valor | undefined = valor;
  for (const parte of campo.split(".")) {
    if (atual === null || typeof atual !== "object" || Array.isArray(atual)) return null;
    atual = atual[parte];
  }
  return atual ?? null;
}

function atributo(fonte: string): string {
  return fonte.slice("itens.".length);
}

/** Posições das ocorrências do marcador, sem sobreposição, da esquerda para a direita. */
function posicoes(texto: string, marcador: string): number[] {
  const achadas: number[] = [];
  for (let i = texto.indexOf(marcador); i >= 0; i = texto.indexOf(marcador, i + marcador.length)) achadas.push(i);
  return achadas;
}

export class Montagem {
  readonly padroes: ValorPadrao[] = [];
  private readonly dados: Record<string, Valor>;
  private readonly nomeDaRegra: NomeDaRegra;

  constructor(dados: Record<string, Valor>, nomeDaRegra: NomeDaRegra) {
    this.dados = dados;
    this.nomeDaRegra = nomeDaRegra;
  }

  private marca(fonte: string | null | undefined): string {
    return fonte ? `[[LACUNA ${this.nomeDaRegra(fonte)}]]` : "[[LACUNA]]";
  }

  private itens(): Record<string, Valor>[] {
    const itens = this.dados.itens;
    return Array.isArray(itens) ? (itens.filter((i) => i !== null && typeof i === "object" && !Array.isArray(i)) as Record<string, Valor>[]) : [];
  }

  /** Valor bruto da fonte (com alternativas, campo e índice), ou null. */
  private valor(x: EntradaDoMapa): Valor {
    if (!x.fonte || x.fonte.startsWith("itens.")) return null;
    let v: Valor = this.dados[x.fonte] ?? null;
    for (const alternativa of x.alternativas ?? []) {
      if (!vazia(v)) break;
      v = this.dados[alternativa] ?? null;
    }
    if (x.campo) v = v !== null && typeof v === "object" && !Array.isArray(v) ? caminho(v, x.campo) : null;
    if (x.indice !== undefined) {
      const lista: Valor[] = Array.isArray(v) ? v : vazia(v) ? [] : [v];
      if (x.juntar_restante) {
        const resto = lista.slice(x.indice);
        v = resto.length === 0 ? null : resto.length === 1 ? resto[0] : resto;
      } else {
        v = lista[x.indice] ?? null;
      }
    }
    return vazia(v) ? null : v;
  }

  /** Texto do valor já formatado; null quando falta dado ou o formato não cabe. */
  private render(x: EntradaDoMapa): string | null {
    if (x.formato === "NUMEROS_DOS_ITENS" && x.fonte) {
      const nome = atributo(x.fonte);
      const numeros = this.itens()
        .filter((item) => (x.filtro_item !== undefined ? verdadeiro(avaliar(x.filtro_item, item)) : !vazia(item[nome])))
        .map((item) => item.numero ?? null);
      return numeros.length ? listaEmTexto(numeros) : null;
    }
    if (x.formato === "POR_ITEM_AGRUPADO" && x.fonte && x.modelo_por_item) {
      // Fase 15: itens com o mesmo valor juntos, na ordem em que aparecem: "de 2 a 8 °C para os itens 1 e 3".
      const nome = atributo(x.fonte);
      const grupos = new Map<string, Valor[]>();
      for (const item of this.itens()) {
        if (vazia(item[nome])) continue;
        const chave = textoDoValor(item[nome]);
        grupos.set(chave, [...(grupos.get(chave) ?? []), item.numero ?? null]);
      }
      const modelo = x.modelo_por_item;
      const partes = [...grupos].map(([v, numeros]) =>
        (numeros.length === 1 ? modelo.singular : modelo.plural).replace("{valor}", v).replace("{itens}", listaEmTexto(numeros)),
      );
      return partes.length ? partes.join("; ") : null;
    }
    if (x.formato === "POR_ITEM" && x.fonte) {
      const nome = atributo(x.fonte);
      const textos = this.itens()
        .filter((item) => !vazia(item[nome]))
        .map((item) => `item ${textoDoValor(item.numero ?? null)}: ${textoDoValor(item[nome])}`);
      return textos.length ? textos.join("; ") : null;
    }
    let v = this.valor(x);
    if (v === null) return null;
    let unidade: Valor | undefined;
    if (x.unidade) {
      unidade = this.dados[x.unidade] ?? null;
      if (vazia(unidade)) return null;
    }
    if (Array.isArray(v) && x.inicial_minuscula) v = v.map((e) => (typeof e === "string" ? ajustarInicial(e, x) : e));
    try {
      return ajustarInicial(formatar(v, x.formato, unidade), x);
    } catch (e) {
      if (e instanceof FormatoInvalido) return null;
      throw e;
    }
  }

  /** Quantos itens o valor cita: itens filtrados, elementos da lista ou números escritos no texto (mínimo 1). */
  private contagem(x: EntradaDoMapa): number {
    if (x.formato === "NUMEROS_DOS_ITENS" && x.fonte) {
      const nome = atributo(x.fonte);
      return this.itens().filter((item) => (x.filtro_item !== undefined ? verdadeiro(avaliar(x.filtro_item, item)) : !vazia(item[nome]))).length;
    }
    const v = this.valor(x);
    if (Array.isArray(v)) return v.length;
    return v === null ? 0 : Math.max(1, (textoDoValor(v).match(/\d+/g) ?? []).length);
  }

  /** Primeira opção verdadeira; com {valor}, o valor da fonte; opção padrão sai marcada. */
  private opcao(x: EntradaDoMapa, trecho: string): string | null {
    for (const opcao of x.opcoes ?? []) {
      if (!verdadeiro(avaliar(opcao.quando, this.dados))) continue;
      let texto = opcao.texto;
      if (texto.includes("{valor}")) {
        const s = this.render(x);
        if (s === null) return null;
        texto = texto.replace("{valor}", s);
      }
      if (opcao.padrao) {
        this.padroes.push({ trecho, marcador: x.marcador, texto });
        return `[[PADRÃO: ${texto}]]`;
      }
      return texto;
    }
    return null;
  }

  /** Texto de um bloco ou cláusula pelo mapa. */
  texto(trecho: string, textoDoModelo: string, mapaBruto: readonly unknown[] | null, marcadoresDoModelo = ""): TextoMontado {
    const mapa = (mapaBruto ?? []) as EntradaDoMapa[];
    if (mapa.length === 0) {
      const lacunas: LacunaDoTexto[] = marcadoresDoModelo.trim()
        ? marcadoresDoModelo.split(" | ").map((marcador) => ({ trecho, marcador, fonte: null, motivo: "sem_mapa" as const }))
        : [];
      return { texto: textoDoModelo, lacunas, padroes: [], omitido: false };
    }
    const pos = mapa.map((x) => posicoes(textoDoModelo, x.marcador)[x.ocorrencia - 1] ?? -1);
    const trocas: [number, number, string][] = [];
    const lacunas: LacunaDoTexto[] = [];
    const padroesAntes = this.padroes.length;
    let omitido = false;
    const lacuna = (marcador: string, fonte: string | null, motivo: MotivoDeLacuna) =>
      lacunas.push({ trecho, marcador, fonte: fonte ? this.nomeDaRegra(fonte) : null, motivo });

    for (let k = 0; k < mapa.length; ) {
      const x = mapa[k];
      const p = pos[k];
      if (p < 0) {
        // Marcador que não está no texto: o compilador confere; aqui só não troca nada.
        k++;
        continue;
      }
      let fim = p + x.marcador.length;
      const acao = x.acao ?? "PREENCHER";
      if (x.grupo) {
        let j = k;
        while (j + 1 < mapa.length && mapa[j + 1].grupo === x.grupo) j++;
        const inicio = p - (x.estende_desde ?? "").length;
        fim = pos[j] + mapa[j].marcador.length + (mapa[j].estende_ate ?? "").length;
        let escolhido: string | null = null;
        for (const y of mapa.slice(k, j + 1)) {
          escolhido = this.opcao(y, trecho);
          if (escolhido !== null) break;
        }
        if (escolhido === null) {
          lacuna(x.marcador, x.fonte, "sem_valor");
          escolhido = x.fonte ? this.marca(x.fonte) : `[[LACUNA ${x.grupo}]]`;
        }
        trocas.push([inicio, fim, escolhido]);
        k = j + 1;
        continue;
      }
      if (acao === "REMOVER") {
        trocas.push([textoDoModelo.slice(p - 1, p) === " " ? p - 1 : p, fim, ""]);
      } else if (acao === "EQUIPE") {
        lacuna(x.marcador, null, "equipe");
        trocas.push([p, fim, "[[LACUNA EQUIPE]]"]);
      } else if (acao === "OPCIONAL") {
        if (verdadeiro(avaliar(x.quando, this.dados))) {
          let t: string | null;
          if (x.texto !== undefined) {
            const s = x.texto.includes("{valor}") ? this.render({ ...x, inicial_maiuscula: false }) : "";
            t = s === null ? null : ajustarInicial(x.texto.replace("{valor}", s), x);
          } else {
            t = x.marcador.startsWith("[") ? x.marcador.slice(1, -1) : x.marcador;
          }
          if (t === null) {
            lacuna(x.marcador, x.fonte, "sem_valor");
            t = this.marca(x.fonte);
          }
          trocas.push([p, fim, t]);
        } else {
          const antes = x.remove_antes ?? "";
          const inicio = antes && textoDoModelo.slice(0, p).endsWith(antes) ? p - antes.length : p;
          trocas.push([inicio, fim, x.se_falso ?? ""]);
        }
      } else if (acao !== "TABELA" && acao !== "MANTER") {
        let s = this.render(x);
        if (s === null) {
          if (x.se_vazio === "OMITE_BLOCO") omitido = true;
          lacuna(x.marcador, x.fonte, "sem_valor");
          s = this.marca(x.fonte);
          // Sem valor, o trecho fixo do modelo fica como está; a lacuna toma só o lugar do marcador.
          trocas.push(x.concordancia ? [p, fim, s] : [p - (x.estende_desde ?? "").length, fim + (x.estende_ate ?? "").length, s]);
        } else {
          if (x.concordancia) s = (this.contagem(x) === 1 ? x.concordancia.singular : x.concordancia.plural).replace("{valor}", s);
          else if (x.texto !== undefined) s = x.texto.replace("{valor}", s);
          trocas.push([p - (x.estende_desde ?? "").length, fim + (x.estende_ate ?? "").length, s]);
        }
      }
      k++;
    }

    let texto = textoDoModelo;
    for (const [inicio, fimDaTroca, por] of [...trocas].sort((a, b) => b[0] - a[0] || b[1] - a[1])) {
      texto = texto.slice(0, inicio) + por + texto.slice(fimDaTroca);
    }
    if (trocas.length) texto = texto.replace(/ {2,}/g, " ").replaceAll(" .", ".").replace(/ +$/, "");
    if (omitido) {
      this.padroes.length = padroesAntes;
      return { texto, lacunas: [], padroes: [], omitido: true };
    }
    return { texto, lacunas, padroes: this.padroes.slice(padroesAntes), omitido: false };
  }

  private celula(item: Record<string, Valor>, coluna: Coluna, sigiloso: boolean): string | null {
    if (coluna.sigiloso && sigiloso) return coluna.sigiloso;
    const v = coluna.fonte ? (item[atributo(coluna.fonte)] ?? null) : (item[coluna.campo ?? ""] ?? null);
    if (vazia(v)) return null;
    if (coluna.textos) return typeof v === "string" && Object.hasOwn(coluna.textos, v) ? coluna.textos[v] : null;
    let s: string;
    try {
      s = formatar(v, coluna.formato);
    } catch (e) {
      if (e instanceof FormatoInvalido) return null;
      throw e;
    }
    for (const c of coluna.complementos ?? []) {
      if (c.quando !== undefined && !verdadeiro(avaliar(c.quando, this.dados))) continue;
      const cv = item[atributo(c.fonte)] ?? null;
      if (!vazia(cv)) s += `\n${c.rotulo}: ${(c.texto ?? "{valor}").replace("{valor}", textoDoValor(cv))}`;
    }
    return s;
  }

  /** Tabela pelo tabela_colunas: itens com o próprio número e as cotas no fim (P35), ou as linhas de uma VAR. */
  tabela(trecho: string, textoDoModelo: string, bruto: unknown): TextoMontado {
    const original = bruto as TabelaColunas;
    // Fase 15: coluna com "quando" só entra quando a condição é verdadeira (PARTICIPAÇÃO, só em licitação).
    const tabela = { ...original, colunas: original.colunas.filter((c) => c.quando === undefined || verdadeiro(avaliar(c.quando, this.dados))) };
    const cabecalhos = tabela.colunas.map((c) => c.cabecalho);
    const linhas = [cabecalhos.join(" | ")];
    const lacunas: LacunaDoTexto[] = [];
    const naoMontada = (motivo: string): TextoMontado => ({
      texto: `${MARCA_DE_TABELA}\n${textoDoModelo}`,
      lacunas: [{ trecho, marcador: motivo, fonte: tabela.linhas === "itens" ? null : this.nomeDaRegra(tabela.linhas), motivo: "tabela_nao_montada" }],
      padroes: [],
      omitido: false,
    });

    if (tabela.linhas !== "itens") {
      const fonte = this.dados[tabela.linhas];
      if (!Array.isArray(fonte) || fonte.length === 0 || !fonte.every((x) => x !== null && typeof x === "object" && !Array.isArray(x))) {
        return naoMontada("tabela sem linhas estruturadas");
      }
      for (const linha of fonte as Record<string, Valor>[]) {
        linhas.push(tabela.colunas.map((c) => textoDoValor(linha[c.campo ?? ""] ?? "")).join(" | "));
      }
      return { texto: linhas.join("\n"), lacunas, padroes: [], omitido: false };
    }

    const itens = [...this.itens()].sort((a, b) => Number(a.numero ?? 0) - Number(b.numero ?? 0));
    if (itens.length === 0) return naoMontada("tabela sem itens");
    const sigiloso = tabela.orcamento_sigiloso !== undefined && verdadeiro(avaliar(tabela.orcamento_sigiloso.quando, this.dados));
    const comCota: Record<string, Valor>[] = [];
    for (const item of itens) {
      linhas.push(
        tabela.colunas
          .map((coluna) => {
            const s = this.celula(item, coluna, sigiloso);
            if (s !== null) return s;
            lacunas.push({ trecho, marcador: `${coluna.cabecalho} do item ${textoDoValor(item.numero ?? null)}`, fonte: coluna.fonte ?? null, motivo: "sem_valor" });
            return "[[LACUNA]]";
          })
          .join(" | "),
      );
      if (tabela.linha_cota && verdadeiro(avaliar(tabela.linha_cota.quando, item))) comCota.push(item);
    }
    // P35: cotas no fim, com os números seguintes ao maior número de item; os itens não são renumerados.
    let numero = Math.max(0, ...itens.map((i) => (typeof i.numero === "number" ? i.numero : 0)));
    const cota = tabela.linha_cota;
    for (const item of comCota) {
      numero++;
      const especificacao = cota?.valores[cabecalhos[1]];
      const celulas = [textoDoNumero(numero), (typeof especificacao === "string" ? especificacao : "").replace(/\{[^}]*\}/, textoDoValor(item.numero ?? null))];
      for (const cabecalho of cabecalhos.slice(2)) {
        if (sigiloso && tabela.orcamento_sigiloso?.colunas.includes(cabecalho)) {
          celulas.push(tabela.orcamento_sigiloso.texto);
          continue;
        }
        const valorDaCota = cota?.valores[cabecalho] ?? "";
        if (typeof valorDaCota === "object") {
          celulas.push(valorDaCota.texto);
          continue;
        }
        const fonte = valorDaCota;
        const coluna = tabela.colunas.find((c) => c.cabecalho === cabecalho);
        const v = fonte.startsWith("itens.") ? (item[atributo(fonte)] ?? null) : null;
        let s: string | null = null;
        if (!vazia(v)) {
          try {
            s = formatar(v, coluna?.formato);
          } catch (e) {
            if (!(e instanceof FormatoInvalido)) throw e;
          }
        }
        if (s === null) {
          lacunas.push({ trecho, marcador: `${cabecalho} da cota do item ${textoDoValor(item.numero ?? null)}`, fonte: fonte || null, motivo: "sem_valor" });
          s = "[[LACUNA]]";
        }
        celulas.push(s);
      }
      linhas.push(celulas.join(" | "));
    }
    return { texto: linhas.join("\n"), lacunas, padroes: [], omitido: false };
  }

  bloco(linha: LinhaM02, texto: string): TextoMontado {
    if (linha.tabela_colunas) return this.tabela(linha.id, texto, linha.tabela_colunas);
    return this.texto(linha.id, texto, linha.lacunas_mapa, linha.lacunas);
  }

  clausula(linha: LinhaM08): TextoMontado {
    const montado = this.texto(linha.id, linha.texto_proposto, linha.lacunas_mapa);
    if (!linha.lacunas_mapa && montado.texto.includes("[")) {
      montado.lacunas.push({ trecho: linha.id, marcador: "trecho entre colchetes sem mapa", fonte: null, motivo: "sem_mapa" });
    }
    return montado;
  }
}

/**
 * Séries de blocos-lista (lista_blocos, como TR-4.1.1 a TR-4.1.3): o último presente termina em ".", o anterior
 * em "; e", os demais em ";".
 */
export function pontuarSeries(textos: Map<string, string>, m02: readonly LinhaM02[]): void {
  const series = new Map<string, string[]>();
  for (const linha of m02) {
    for (const x of (linha.lacunas_mapa ?? []) as { lista_blocos?: string[] }[]) {
      const lista = x.lista_blocos;
      if (lista) series.set(lista.join("|"), lista);
    }
  }
  for (const serie of series.values()) {
    const presentes = serie.filter((b) => textos.has(b));
    presentes.forEach((b, i) => {
      const final = i === presentes.length - 1 ? "." : i === presentes.length - 2 ? "; e" : ";";
      textos.set(b, (textos.get(b) as string).trimEnd().replace(/(;\s*e|;|\.)\s*$/, "") + final);
    });
  }
}
