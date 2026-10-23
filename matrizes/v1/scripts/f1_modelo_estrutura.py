#!/usr/bin/env python3
"""Fase 1 - Estrutura completa do modelo AGU de TR (docx), sem perder notas nem formatacao.

Uso: python3 -I f1_modelo_estrutura.py <modelo.docx> <saida.json>

Para cada paragrafo do corpo (inclusive dentro de tabelas), na ordem do documento:
  - numero sequencial (mesma contagem da Fase 0 e das 'Linhas' da matriz 01);
  - estilo, numeracao automatica do Word calculada (numbering.xml + estilos), nivel;
  - texto e trechos com a formatacao efetiva de cada run: cor (preto, vermelho, outra),
    italico, negrito e realce, resolvendo estilo de paragrafo, estilo de caractere e
    formatacao direta;
  - comentarios (notas explicativas) que comecam, terminam ou cobrem o paragrafo.
Para cada tabela: paragrafos que a compoem e grade de celulas.
Para cada comentario: id do Word, ordem no documento, paragrafos de inicio e fim, trecho ancorado
e texto integral.
"""
import json
import re
import sys
import zipfile
from xml.etree import ElementTree as ET

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def q(t):
    return f"{{{W}}}{t}"


def val(el, tag):
    if el is None:
        return None
    x = el.find(q(tag))
    return None if x is None else x.get(q("val"), "1")


def onoff(v):
    if v is None:
        return None
    return v not in ("0", "false", "off")


# ----------------------------------------------------------------- estilos
def ler_estilos(z):
    st = ET.fromstring(z.read("word/styles.xml"))
    estilos = {}
    for s in st.findall(q("style")):
        sid = s.get(q("styleId"))
        ppr = s.find(q("pPr"))
        rpr = s.find(q("rPr"))
        num = ppr.find(q("numPr")) if ppr is not None else None
        d = {
            "tipo": s.get(q("type")),
            "nome": val(s, "name"),
            "basedOn": val(s, "basedOn"),
            "ilvl": val(num, "ilvl") if num is not None else None,
            "numId": val(num, "numId") if num is not None else None,
            "rpr": ler_rpr(rpr),
        }
        estilos[sid] = d
    dd = st.find(q("docDefaults"))
    padrao = {}
    if dd is not None:
        r = dd.find(f"{q('rPrDefault')}/{q('rPr')}")
        padrao = ler_rpr(r)
    return estilos, padrao


def ler_rpr(rpr):
    d = {}
    if rpr is None:
        return d
    c = rpr.find(q("color"))
    if c is not None:
        d["color"] = c.get(q("val"))
        if c.get(q("themeColor")):
            d["themeColor"] = c.get(q("themeColor"))
    for tag, chave in (("i", "i"), ("b", "b")):
        x = rpr.find(q(tag))
        if x is not None:
            d[chave] = onoff(x.get(q("val"), "1"))
    h = rpr.find(q("highlight"))
    if h is not None:
        d["highlight"] = h.get(q("val"))
    rs = rpr.find(q("rStyle"))
    if rs is not None:
        d["rStyle"] = rs.get(q("val"))
    return d


def cadeia(estilos, sid):
    vistos = []
    while sid and sid in estilos and sid not in vistos:
        vistos.append(sid)
        sid = estilos[sid]["basedOn"]
    return vistos  # do proprio para o mais basico


def prop_estilo(estilos, sid, chave):
    for s in cadeia(estilos, sid):
        v = estilos[s].get(chave)
        if v is not None:
            return v
    return None


def rpr_estilo(estilos, sid):
    efetivo = {}
    for s in reversed(cadeia(estilos, sid)):
        efetivo.update({k: v for k, v in estilos[s]["rpr"].items() if k != "rStyle"})
    return efetivo


# ----------------------------------------------------------------- numeracao
ROMANOS = [(1000, "m"), (900, "cm"), (500, "d"), (400, "cd"), (100, "c"), (90, "xc"), (50, "l"), (40, "xl"),
           (10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")]


def romano(n):
    s = ""
    for v, r in ROMANOS:
        while n >= v:
            s += r
            n -= v
    return s


def letra(n):
    s = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(97 + r) + s
    return s


def formata(n, fmt):
    if fmt == "lowerLetter":
        return letra(n)
    if fmt == "upperLetter":
        return letra(n).upper()
    if fmt == "lowerRoman":
        return romano(n)
    if fmt == "upperRoman":
        return romano(n).upper()
    if fmt == "bullet":
        return "•"
    if fmt == "none":
        return ""
    return str(n)


def ler_numeracao(z):
    nb = ET.fromstring(z.read("word/numbering.xml"))
    abstratos = {}
    for a in nb.findall(q("abstractNum")):
        aid = a.get(q("abstractNumId"))
        niveis = {}
        for l in a.findall(q("lvl")):
            il = int(l.get(q("ilvl")))
            niveis[il] = {
                "start": int(val(l, "start") or 1),
                "fmt": val(l, "numFmt") or "decimal",
                "texto": val(l, "lvlText") or "",
                "lgl": l.find(q("isLgl")) is not None,
            }
        abstratos[aid] = niveis
    nums = {}
    for n in nb.findall(q("num")):
        nid = n.get(q("numId"))
        ov = {}
        for o in n.findall(q("lvlOverride")):
            so = o.find(q("startOverride"))
            if so is not None:
                ov[int(o.get(q("ilvl")))] = int(so.get(q("val")))
        nums[nid] = {"abs": val(n, "abstractNumId"), "override": ov}
    return abstratos, nums


class Contador:
    def __init__(self, abstratos, nums):
        self.abstratos, self.nums = abstratos, nums
        self.cont = {}
        self.usados = set()

    def proximo(self, numId, ilvl):
        if numId in (None, "0") or numId not in self.nums:
            return None
        aid = self.nums[numId]["abs"]
        niveis = self.abstratos.get(aid, {})
        if ilvl not in niveis:
            return None
        c = self.cont.setdefault(aid, {})
        if numId not in self.usados:
            self.usados.add(numId)
            for l, s in self.nums[numId]["override"].items():
                c[l] = s - 1
                for k in list(c):
                    if k > l:
                        c.pop(k)
        c[ilvl] = (c[ilvl] + 1) if c.get(ilvl) is not None else niveis[ilvl]["start"]
        for k in list(c):
            if k > ilvl:
                c.pop(k)
        for k in range(ilvl):
            if c.get(k) is None and k in niveis:
                c[k] = niveis[k]["start"]
        txt = niveis[ilvl]["texto"]

        def sub(m):
            k = int(m.group(1)) - 1
            fmt = "decimal" if niveis[ilvl]["lgl"] else niveis.get(k, {}).get("fmt", "decimal")
            return formata(c.get(k, 1), fmt)

        return re.sub(r"%(\d)", sub, txt), aid


# ----------------------------------------------------------------- documento
def classe_cor(rp):
    cor = (rp.get("color") or "auto").upper()
    if rp.get("themeColor") in ("text1", "dark1"):
        return "preto"
    if cor in ("AUTO", "000000"):
        return "preto"
    if cor in ("FF0000",):
        return "vermelho"
    return "outra:" + cor


def main():
    z = zipfile.ZipFile(sys.argv[1])
    estilos, padrao = ler_estilos(z)
    abstratos, nums = ler_numeracao(z)
    cont = Contador(abstratos, nums)
    doc = ET.fromstring(z.read("word/document.xml"))
    body = doc.find(q("body"))

    pars, tabelas = [], []
    abertos = {}  # id -> paragrafo de inicio
    coment_ini, coment_fim, coment_ref = {}, {}, {}
    ancorado = {}
    pendentes_ini = []  # inicios fora de paragrafo: valem para o proximo paragrafo
    estado = {"par_atual": None, "tabela": None}

    def processa_marcador(el):
        tag = el.tag.split("}")[1]
        cid = el.get(q("id"))
        if tag == "commentRangeStart":
            if estado["par_atual"] is None:
                pendentes_ini.append(cid)
            else:
                coment_ini[cid] = estado["par_atual"]["n"]
            abertos[cid] = True
            ancorado.setdefault(cid, "")
        elif tag == "commentRangeEnd":
            coment_fim[cid] = estado["par_atual"]["n"] if estado["par_atual"] else (pars[-1]["n"] if pars else 0)
            abertos.pop(cid, None)

    def paragrafo(p, tabela=None, celula=None, sem_numero=False):
        n = len(pars) + 1
        ppr = p.find(q("pPr"))
        sid = val(ppr, "pStyle") if ppr is not None else None
        sid = sid or "Normal"
        dnum = ppr.find(q("numPr")) if ppr is not None else None
        ilvl = val(dnum, "ilvl") if dnum is not None else None
        numId = val(dnum, "numId") if dnum is not None else None
        if ilvl is None:
            ilvl = prop_estilo(estilos, sid, "ilvl")
        if numId is None:
            numId = prop_estilo(estilos, sid, "numId")
        ilvl = int(ilvl) if ilvl is not None else 0
        rot = None if sem_numero else cont.proximo(numId, ilvl)
        reg = {"n": n, "estilo": sid, "estilo_nome": estilos.get(sid, {}).get("nome"),
               "numId": numId, "nivel": ilvl if rot else None, "rotulo": rot[0] if rot else None,
               "abs": rot[1] if rot else None, "tabela": tabela, "celula": celula, "trechos": [],
               "comentarios_inicio": [], "comentarios_fim": [], "comentarios_ref": [], "comentarios_cobrem": []}
        estado["par_atual"] = reg
        for cid in pendentes_ini:
            coment_ini[cid] = n
        pendentes_ini.clear()
        rpr_par = dict(padrao)
        rpr_par.update(rpr_estilo(estilos, sid))
        campo = {"dentro_instr": False}

        def run(r):
            rp = dict(rpr_par)
            rr = r.find(q("rPr"))
            direto = ler_rpr(rr)
            if "rStyle" in direto:
                rp.update(rpr_estilo(estilos, direto["rStyle"]))
            rp.update({k: v for k, v in direto.items() if k != "rStyle"})
            for ch in r:
                tag = ch.tag.split("}")[1]
                if tag == "fldChar":
                    t = ch.get(q("fldCharType"))
                    if t == "begin":
                        campo["dentro_instr"] = True
                    elif t in ("separate", "end"):
                        campo["dentro_instr"] = False
                    continue
                if campo["dentro_instr"]:
                    continue
                txt = None
                if tag == "t":
                    txt = ch.text or ""
                elif tag == "tab":
                    txt = "\t"
                elif tag in ("br", "cr"):
                    txt = "\n"
                elif tag == "noBreakHyphen":
                    txt = "-"
                elif tag == "commentReference":
                    reg["comentarios_ref"].append(ch.get(q("id")))
                    coment_ref[ch.get(q("id"))] = n
                if txt:
                    reg["trechos"].append({"t": txt, "cor": classe_cor(rp), "i": bool(rp.get("i")),
                                           "b": bool(rp.get("b")), "realce": rp.get("highlight")})
                    for cid in abertos:
                        ancorado[cid] = ancorado.get(cid, "") + txt

        def percorre(el):
            for ch in el:
                tag = ch.tag.split("}")[1]
                if tag == "r":
                    run(ch)
                elif tag in ("commentRangeStart", "commentRangeEnd"):
                    processa_marcador(ch)
                elif tag in ("hyperlink", "smartTag", "fldSimple", "ins", "customXml"):
                    percorre(ch)
                elif tag == "pPr":
                    continue

        percorre(p)
        reg["texto"] = "".join(t["t"] for t in reg["trechos"])
        for cid in abertos:
            ancorado[cid] = ancorado.get(cid, "") + "\n"
        reg["comentarios_cobrem"] = sorted(abertos, key=int)
        pars.append(reg)
        estado["par_atual"] = None

    def tabela(tbl):
        ti = len(tabelas) + 1
        grade = []
        inicio = len(pars) + 1
        for el in tbl:
            if el.tag.split("}")[1] in ("commentRangeStart", "commentRangeEnd"):
                processa_marcador(el)
        for ri, tr in enumerate(tbl.findall(q("tr"))):
            linha = []
            for el in tr:
                if el.tag.split("}")[1] in ("commentRangeStart", "commentRangeEnd"):
                    processa_marcador(el)
            for ci, tc in enumerate(tr.findall(q("tc"))):
                textos = []
                tcpr = tc.find(q("tcPr"))
                vm = tcpr.find(q("vMerge")) if tcpr is not None else None
                # celula de continuacao de mescla vertical: o Word nao exibe o conteudo, entao o
                # paragrafo nao recebe numero (mesmo comportamento do LibreOffice)
                continua = vm is not None and vm.get(q("val"), "continue") != "restart"
                for ch in tc:
                    tag = ch.tag.split("}")[1]
                    if tag == "p":
                        paragrafo(ch, ti, (ri, ci), sem_numero=continua)
                        textos.append(pars[-1]["texto"])
                    elif tag == "tbl":
                        tabela(ch)
                    elif tag in ("commentRangeStart", "commentRangeEnd"):
                        processa_marcador(ch)
                linha.append("\n".join(textos))
            grade.append(linha)
        tabelas.append({"tabela": ti, "par_inicio": inicio, "par_fim": len(pars), "grade": grade})

    for ch in body:
        tag = ch.tag.split("}")[1]
        if tag == "p":
            paragrafo(ch)
        elif tag == "tbl":
            tabela(ch)
        elif tag in ("commentRangeStart", "commentRangeEnd"):
            processa_marcador(ch)
    tabelas.sort(key=lambda t: t["tabela"])

    for cid, n in coment_ini.items():
        pars[n - 1]["comentarios_inicio"].append(cid)
    for cid, n in coment_fim.items():
        if n:
            pars[n - 1]["comentarios_fim"].append(cid)

    # comentarios
    # documento sem comentarios (ex.: checklists): lista vazia
    cx = ET.fromstring(z.read("word/comments.xml")) if "word/comments.xml" in z.namelist() else ET.Element("vazio")
    comentarios = []
    ordem_doc = [m.group(1) for m in re.finditer(r'<w:commentRangeStart w:id="(\d+)"/>', z.read("word/document.xml").decode("utf-8"))]
    for c in cx.findall(q("comment")):
        cid = c.get(q("id"))
        paras = ["".join((t.text or "") for t in pp.iter(q("t"))) for pp in c.findall(q("p"))]
        comentarios.append({"id_word": cid, "ordem": ordem_doc.index(cid) + 1 if cid in ordem_doc else None,
                            "par_inicio": coment_ini.get(cid), "par_fim": coment_fim.get(cid),
                            "par_referencia": coment_ref.get(cid), "trecho_ancorado": ancorado.get(cid, ""),
                            "texto": "\n".join(paras)})
    comentarios.sort(key=lambda c: c["ordem"])

    out = {"paragrafos": pars, "tabelas": tabelas, "comentarios": comentarios,
           "resumo": {"paragrafos": len(pars), "nao_vazios": sum(1 for p in pars if p["texto"].strip()),
                      "em_tabela": sum(1 for p in pars if p["tabela"]), "tabelas": len(tabelas),
                      "numerados": sum(1 for p in pars if p["rotulo"]), "comentarios": len(comentarios)}}
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(json.dumps(out["resumo"], ensure_ascii=False))


if __name__ == "__main__":
    main()
