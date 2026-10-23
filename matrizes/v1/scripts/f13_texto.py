#!/usr/bin/env python3
"""Fase 13 - montagem do texto da minuta no simulador (independente do motor), pelo M02.lacunas_mapa, pelo
M02.tabela_colunas e pelos marcadores [VAR-xxx] do M08.

Usado por f10_simulador.py. Entrada: as linhas do M02 e do M08 e os dados do caminho das expressões (globais e itens já
calculados). Saída: texto de cada bloco e cláusula, lacunas que ficaram e todo valor inserido (para o teste de "Sim" e
"Não" vindos do checklist). Valor ausente vira [[LACUNA ...]]; nada é inventado.
"""
import json
import re
from decimal import Decimal

from jlogic import avaliar, verdadeiro

UNID = ["", "um", "dois", "três", "quatro", "cinco", "seis", "sete", "oito", "nove", "dez", "onze", "doze", "treze",
        "quatorze", "quinze", "dezesseis", "dezessete", "dezoito", "dezenove"]
DEZ = ["", "", "vinte", "trinta", "quarenta", "cinquenta", "sessenta", "setenta", "oitenta", "noventa"]
CEM = ["", "cento", "duzentos", "trezentos", "quatrocentos", "quinhentos", "seiscentos", "setecentos", "oitocentos",
       "novecentos"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro",
         "dezembro"]
UNIDADES = {"DIAS": ("dia", "dias"), "MESES": ("mês", "meses"), "ANOS": ("ano", "anos")}


def _ate_mil(n):
    if n == 0:
        return ""
    if n == 100:
        return "cem"
    c, r = divmod(n, 100)
    partes = [CEM[c]] if c else []
    if r:
        if r < 20:
            partes.append(UNID[r])
        else:
            d, u = divmod(r, 10)
            partes.append(DEZ[d] + (" e " + UNID[u] if u else ""))
    return " e ".join(partes)


def extenso(n):
    """inteiro não negativo por extenso (até 999.999.999): grupos separados por espaço; 'e' antes do último grupo
    quando ele é menor que cem ou centena exata (mil e quinhentos; mil duzentos e cinquenta)."""
    n = int(n)
    if n == 0:
        return "zero"
    mi, r = divmod(n, 1_000_000)
    mil, u = divmod(r, 1000)
    grupos = []
    if mi:
        grupos.append(("um milhão" if mi == 1 else _ate_mil(mi) + " milhões", mi))
    if mil:
        grupos.append(("mil" if mil == 1 else _ate_mil(mil) + " mil", mil))
    if u:
        grupos.append((_ate_mil(u), u))
    if len(grupos) == 1:
        return grupos[0][0]
    ult_txt, ult = grupos[-1]
    sep = " e " if (ult < 100 or ult % 100 == 0) else " "
    return " ".join(g for g, _ in grupos[:-1]) + sep + ult_txt


def dec(v):
    if isinstance(v, Decimal):
        return v
    if isinstance(v, bool) or v is None:
        raise ValueError(v)
    if isinstance(v, (int, float)):
        return Decimal(repr(v))
    return Decimal(str(v).replace(".", "").replace(",", ".")) if "," in str(v) else Decimal(str(v))


def num_txt(v):
    d = dec(v)
    if d == d.to_integral_value():
        return f"{int(d):,}".replace(",", ".")
    s = format(d.normalize(), "f")
    i, f = s.split(".")
    return f"{int(i):,}".replace(",", ".") + "," + f


def moeda(v):
    d = dec(v).quantize(Decimal("0.01"))
    i, c = divmod(int(d * 100), 100)
    return f"R$ {i:,}".replace(",", ".") + f",{c:02d}"


def moeda_extenso(v):
    d = dec(v).quantize(Decimal("0.01"))
    i, c = divmod(int(d * 100), 100)
    partes = []
    if i:
        de = " de" if i % 1_000_000 == 0 else ""
        partes.append(extenso(i) + de + (" real" if i == 1 else " reais"))
    if c:
        partes.append(extenso(c) + (" centavo" if c == 1 else " centavos"))
    return "(" + (" e ".join(partes) if partes else "zero real") + ")"


def pct_extenso(v):
    d = dec(v)
    if d == d.to_integral_value():
        return f"{num_txt(d)}% ({extenso(d)} por cento)"
    i, f = format(d.normalize(), "f").split(".")
    return f"{num_txt(d)}% ({extenso(int(i))} vírgula {' '.join(extenso(int(x)) for x in f)} por cento)"


def data_partes(v):
    m = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", str(v)) or re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", str(v))
    if not m:
        raise ValueError(v)
    a, b, c = m.groups()
    return (a, b, c) if len(a) == 2 else (c, b, a)


def lista_texto(xs):
    xs = [texto_valor(x) for x in xs]
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " e " + xs[-1]


def texto_valor(v):
    if isinstance(v, list):
        return "; ".join(texto_valor(x) for x in v)
    if isinstance(v, (int, float, Decimal)) and not isinstance(v, bool):
        return num_txt(v)
    if isinstance(v, dict):
        return json.dumps(v, ensure_ascii=False, default=str)
    return str(v)


def vazio(v):
    return v is None or v == "" or v == []


def pega(d, caminho):
    cur = d
    for p in caminho.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(p)
    return cur


def formatar(v, fmt, unidade=None):
    if fmt in (None, "TEXTO"):
        s = texto_valor(v)
    elif fmt == "NUMERO_EXTENSO":
        d = dec(v)
        if d != d.to_integral_value():
            raise ValueError("número não inteiro para extenso")
        s = f"{num_txt(d)} ({extenso(d)})"
    elif fmt == "NUMERO":
        s = num_txt(v)
    elif fmt == "PERCENTUAL_EXTENSO":
        s = pct_extenso(v)
    elif fmt == "PERCENTUAL_2":
        s = f"{dec(v).quantize(Decimal('0.01')):f}".replace(".", ",") + "%"
    elif fmt == "MOEDA":
        s = moeda(v)
    elif fmt == "MOEDA_POR_EXTENSO":
        s = moeda_extenso(v)
    elif fmt == "DATA":
        s = "/".join(data_partes(v))
    elif fmt == "DIA":
        s = str(int(data_partes(v)[0]))
    elif fmt == "MES_EXTENSO":
        s = MESES[int(data_partes(v)[1]) - 1]
    elif fmt == "ANO":
        s = data_partes(v)[2]
    elif fmt == "LISTA_TEXTO":
        s = lista_texto(v if isinstance(v, list) else [v])
    elif fmt == "LISTA_LINHAS":
        s = "\n".join(texto_valor(x) for x in (v if isinstance(v, list) else [v]))
    elif fmt == "MINUSCULA":
        s = texto_valor(v).lower()
    elif fmt == "INICIAL_MINUSCULA":
        s = texto_valor(v)
        s = s[:1].lower() + s[1:]
    elif fmt == "ITEM":
        s = f"item {texto_valor(v)}"
    else:
        raise ValueError(fmt)
    if unidade is not None:
        sing, plur = UNIDADES[unidade]
        s += " " + (sing if dec(v) == 1 else plur)
    return s


def ajusta_inicial(s, x):
    if x.get("inicial_minuscula"):
        return s[:1].lower() + s[1:]
    if x.get("inicial_maiuscula"):
        return s[:1].upper() + s[1:]
    return s


class Montagem:
    def __init__(self, dados):
        self.d = dados
        self.inseridos = []  # (trecho, fonte, valor)

    def valor(self, x):
        """valor bruto da fonte da entrada (com campo e índice), ou None; fontes alternativas em ordem."""
        f = x.get("fonte")
        if not f or f.startswith("itens."):
            return None
        v = self.d.get(f)
        for alt in x.get("alternativas", []):
            if not vazio(v):
                break
            v = self.d.get(alt)
        if x.get("campo"):
            v = pega(v, x["campo"]) if isinstance(v, dict) else None
        if "indice" in x:
            if not isinstance(v, list):
                v = [v] if not vazio(v) else []
            i = x["indice"]
            if x.get("juntar_restante"):
                v = v[i:] if len(v) > i else None
                v = None if not v else (v[0] if len(v) == 1 else v)
            else:
                v = v[i] if len(v) > i else None
        return None if vazio(v) else v

    def render(self, trecho, x):
        """texto da entrada PREENCHER (ou o {valor} dos modelos); None = sem valor."""
        if x.get("formato") == "NUMEROS_DOS_ITENS":
            attr = x["fonte"].split(".", 1)[1]
            nums = [it.get("numero") for it in self.d.get("itens", [])
                    if (verdadeiro(avaliar(x["filtro_item"], it)) if x.get("filtro_item") else not vazio(it.get(attr)))]
            if not nums:
                return None
            self.inseridos += [(trecho, x["fonte"], n) for n in nums]
            return lista_texto(nums)
        if x.get("formato") == "POR_ITEM":
            attr = x["fonte"].split(".", 1)[1]
            partes = [f"item {texto_valor(it.get('numero'))}: {texto_valor(it.get(attr))}"
                      for it in self.d.get("itens", []) if not vazio(it.get(attr))]
            if not partes:
                return None
            s = "; ".join(partes)
            self.inseridos += [(trecho, x["fonte"], it.get(attr)) for it in self.d.get("itens", [])
                               if not vazio(it.get(attr))]
            return s
        v = self.valor(x)
        if v is None:
            return None
        uni = None
        if x.get("unidade"):
            uni = self.d.get(x["unidade"])
            if vazio(uni):
                return None
        if isinstance(v, list) and x.get("inicial_minuscula"):
            v = [ajusta_inicial(e_, x) if isinstance(e_, str) else e_ for e_ in v]
        try:
            s = formatar(v, x.get("formato"), uni)
        except (ValueError, KeyError, ArithmeticError):
            return None
        self.inseridos.append((trecho, x["fonte"], v))
        return ajusta_inicial(s, x)

    def opcao(self, x, trecho):
        for op in x.get("opcoes", []):
            if verdadeiro(avaliar(op["quando"], self.d)):
                t = op["texto"]
                if "{valor}" in t:
                    s = self.render(trecho, x)
                    if s is None:
                        return None
                    t = t.replace("{valor}", s)
                return t
        return None

    def bloco(self, r):
        """(texto, lacunas, omitido)."""
        texto = r["texto_literal"]
        if r.get("tabela_colunas"):
            return self.tabela(r)
        mapa = json.loads(r["lacunas_mapa"]) if r.get("lacunas_mapa") else []
        if not mapa:
            return texto, [], False
        pos = []
        for x in mapa:
            ps, i = [], 0
            while True:
                p = texto.find(x["marcador"], i)
                if p < 0:
                    break
                ps.append(p)
                i = p + len(x["marcador"])
            pos.append(ps[x["ocorrencia"] - 1])
        trocas, lacunas, omitido = [], [], False
        k = 0
        while k < len(mapa):
            x, p = mapa[k], pos[k]
            fim = p + len(x["marcador"])
            acao = x.get("acao", "PREENCHER")
            if x.get("grupo"):
                j = k
                while j + 1 < len(mapa) and mapa[j + 1].get("grupo") == x["grupo"]:
                    j += 1
                ini = p - len(x.get("estende_desde", ""))
                fim = pos[j] + len(mapa[j]["marcador"]) + len(mapa[j].get("estende_ate", ""))
                t = None
                for y in mapa[k:j + 1]:
                    t = self.opcao(y, r["id"])
                    if t is not None:
                        break
                if t is None:
                    lacunas.append(f"escolha {x['grupo']} ({x['fonte']})")
                    t = f"[[LACUNA {x['fonte'] or x['grupo']}]]"
                trocas.append((ini, fim, t))
                k = j + 1
                continue
            if acao == "TABELA" or acao == "MANTER":
                pass
            elif acao == "REMOVER":
                ini = p - 1 if texto[p - 1:p] == " " else p
                trocas.append((ini, fim, ""))
            elif acao == "EQUIPE":
                lacunas.append(f"equipe: {x['marcador']}")
                trocas.append((p, fim, "[[LACUNA EQUIPE]]"))
            elif acao == "OPCIONAL":
                if verdadeiro(avaliar(x["quando"], self.d)):
                    if "texto" in x:
                        s = self.render(r["id"], dict(x, inicial_maiuscula=False)) if "{valor}" in x["texto"] else ""
                        t = ajusta_inicial(x["texto"].replace("{valor}", s), x) if s is not None else None
                    else:
                        t = x["marcador"][1:-1] if x["marcador"].startswith("[") else x["marcador"]
                    if t is None:
                        lacunas.append(x["fonte"])
                        t = f"[[LACUNA {x['fonte']}]]"
                    trocas.append((p, fim, t))
                else:
                    ra = x.get("remove_antes", "")
                    ini = p - len(ra) if ra and texto[:p].endswith(ra) else p
                    trocas.append((ini, fim, x.get("se_falso", "")))
            else:
                s = self.render(r["id"], x)
                if s is None:
                    if x.get("se_vazio") == "OMITE_BLOCO":
                        omitido = True
                    lacunas.append(x["fonte"])
                    s = f"[[LACUNA {x['fonte']}]]"
                elif "texto" in x:
                    s = x["texto"].replace("{valor}", s)
                ini = p - len(x.get("estende_desde", ""))
                trocas.append((ini, fim, s))
            k += 1
        for ini, fim, t in sorted(trocas, reverse=True):
            texto = texto[:ini] + t + texto[fim:]
        texto = re.sub(r" {2,}", " ", texto).replace(" .", ".").rstrip(" ") if trocas else texto
        if omitido:
            return texto, [], True
        return texto, lacunas, False

    # ---------------------------------------------------------------- tabelas
    def celula(self, it, col, sig):
        if col.get("sigiloso") and sig:
            return "SIGILOSO", True
        v = it.get(col["fonte"].split(".", 1)[1]) if col.get("fonte") else it.get(col.get("campo"))
        if vazio(v):
            return "[[LACUNA]]", False
        s = formatar(v, col.get("formato"))
        for c in col.get("complementos", []):
            if c.get("quando") is not None and not verdadeiro(avaliar(c["quando"], self.d)):
                continue
            cv = it.get(c["fonte"].split(".", 1)[1])
            if not vazio(cv):
                s += f"\n{c['rotulo']}: " + c.get("texto", "{valor}").replace("{valor}", texto_valor(cv))
        self.inseridos.append(("tabela", col.get("fonte") or col.get("campo"), v))
        return s, True

    def tabela(self, r):
        tc = json.loads(r["tabela_colunas"])
        cab = [c["cabecalho"] for c in tc["colunas"]]
        linhas, lac = [" | ".join(cab)], []
        if tc["linhas"] == "itens":
            sig = verdadeiro(avaliar(tc["orcamento_sigiloso"]["quando"], self.d))
            itens = sorted(self.d.get("itens", []), key=lambda i: i.get("numero") or 0)
            if not itens:
                return r["texto_literal"], ["tabela sem itens"], False
            lc = tc["linha_cota"]
            cotas = []
            for it in itens:  # itens com o próprio número (P35: sem renumerar)
                cel = []
                for col in tc["colunas"]:
                    s_, ok = self.celula(it, col, sig)
                    if not ok:
                        lac.append(f"{col['cabecalho']} do item {it.get('numero')}")
                    cel.append(s_)
                linhas.append(" | ".join(cel))
                if verdadeiro(avaliar(lc["quando"], it)):
                    cotas.append(it)
            n = max((dec(i.get("numero")) for i in itens if not vazio(i.get("numero"))), default=Decimal(0))
            for it in cotas:  # P35: cotas no fim, números seguintes ao maior número de item
                n += 1
                cel = [num_txt(n), f"Cota reservada para ME/EPP do item {texto_valor(it.get('numero'))}"]
                for cabc in cab[2:]:
                    f = lc["valores"][cabc]
                    if sig and cabc in tc["orcamento_sigiloso"]["colunas"]:
                        cel.append("SIGILOSO")
                        continue
                    v = it.get(f.split(".", 1)[1])
                    fmt = next(c.get("formato") for c in tc["colunas"] if c["cabecalho"] == cabc)
                    if vazio(v):
                        lac.append(f"{cabc} da cota do item {it.get('numero')}")
                        cel.append("[[LACUNA]]")
                    else:
                        cel.append(formatar(v, fmt))
                linhas.append(" | ".join(cel))
            return "\n".join(linhas), lac, False
        fonte = self.d.get(tc["linhas"])
        if not isinstance(fonte, list) or not fonte or not all(isinstance(x, dict) for x in fonte):
            return r["texto_literal"], [f"tabela sem linhas estruturadas ({tc['linhas']})"], False
        return "\n".join(linhas + [" | ".join(texto_valor(x.get(c.get("campo", ""), "")) for c in tc["colunas"])
                                   for x in fonte]), [], False

    # ---------------------------------------------------------------- cláusulas do M08
    def clausula(self, r):
        """Fase 14: o M08 tem lacunas_mapa no formato do M02; marcador fora do mapa fica como lacuna."""
        t, lac, _ = self.bloco({"id": r["id"], "texto_literal": r["texto_proposto"],
                                "lacunas_mapa": r.get("lacunas_mapa", "")})
        if not r.get("lacunas_mapa") and "[" in t:
            lac = lac + ["trecho entre colchetes sem mapa"]
        return t, lac


def pontuar_series(textos, m02):
    """séries de blocos-lista (lista_blocos): último presente termina em '.', o anterior em '; e', os demais em ';'."""
    series = set()
    for r in m02:
        for x in json.loads(r.get("lacunas_mapa") or "[]"):
            if x.get("lista_blocos"):
                series.add(tuple(x["lista_blocos"]))
    for s in series:
        pres = [b for b in s if b in textos]
        for i, b in enumerate(pres):
            fim = "." if i == len(pres) - 1 else "; e" if i == len(pres) - 2 else ";"
            textos[b] = re.sub(r"(;\s*e|;|\.)\s*$", "", textos[b].rstrip()) + fim


def montar_minuta(m02, m08, blocos, clausulas, dados):
    """{id: texto}, {id: [lacunas]}, inseridos; blocos omitidos (série sem elemento) saem da minuta."""
    mt = Montagem(dados)
    por_id = {r["id"]: r for r in m02}
    textos, lac = {}, {}
    for b in blocos:
        t, l_, omit = mt.bloco(por_id[b])
        if omit:
            continue
        textos[b], lac[b] = t, l_
    pontuar_series(textos, m02)
    s8 = {r["id"]: r for r in m08}
    for c in clausulas:
        if s8[c]["documento"] not in ("TR", "AMBOS") or s8[c].get("nivel") == "PREENCHE_BLOCO":
            continue  # PREENCHE_BLOCO não entra como texto: preenche as lacunas do bloco (lacunas_mapa)
        textos[c], lac[c] = mt.clausula(s8[c])
    return textos, lac, mt.inseridos
