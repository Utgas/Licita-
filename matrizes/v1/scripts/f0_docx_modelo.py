#!/usr/bin/env python3
"""Fase 0 - Conferencia estrutural do modelo AGU de TR (docx).

Uso: python3 -I f0_docx_modelo.py <modelo.docx> <saida.json>

Confere:
  - numero de comentarios em word/comments.xml;
  - para cada comentario, se existe commentRangeStart e commentRangeEnd com o mesmo id em
    word/document.xml (ancoragem) e se o trecho ancorado tem texto;
  - lista de paragrafos do corpo (inclusive dentro de tabelas), em ordem, com texto.
"""
import json
import re
import sys
import zipfile
from xml.etree import ElementTree as ET

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}


def q(tag):
    return f"{{{W}}}{tag}"


def main():
    z = zipfile.ZipFile(sys.argv[1])
    doc = ET.fromstring(z.read("word/document.xml"))
    com = ET.fromstring(z.read("word/comments.xml"))
    comentarios = {}
    for c in com.findall("w:comment", NS):
        cid = c.get(q("id"))
        texto = "\n".join("".join(t.text or "" for t in p.iter(q("t"))) for p in c.findall("w:p", NS))
        comentarios[cid] = {"autor_presente": bool(c.get(q("author"))), "texto": texto}

    body = doc.find("w:body", NS)
    # percorre o corpo na ordem do documento, acumulando texto ancorado por comentario
    abertos = set()
    ancorado = {cid: "" for cid in comentarios}
    starts, ends = set(), set()
    paragrafos = []

    def walk(el, em_tabela=False):
        for ch in el:
            tag = ch.tag.split("}")[1]
            if tag == "p":
                paragrafo(ch, em_tabela)
            elif tag == "tbl":
                for tr in ch.findall("w:tr", NS):
                    for tc in tr.findall("w:tc", NS):
                        walk(tc, True)
            elif tag in ("sdt",):
                content = ch.find("w:sdtContent", NS)
                if content is not None:
                    walk(content, em_tabela)
            elif tag == "sectPr":
                pass
            else:
                walk(ch, em_tabela)

    def paragrafo(p, em_tabela):
        txt = []
        for el in p.iter():
            tag = el.tag.split("}")[1]
            if tag == "commentRangeStart":
                cid = el.get(q("id"))
                starts.add(cid)
                abertos.add(cid)
            elif tag == "commentRangeEnd":
                cid = el.get(q("id"))
                ends.add(cid)
                abertos.discard(cid)
            elif tag == "t":
                txt.append(el.text or "")
                for cid in abertos:
                    ancorado[cid] += el.text or ""
            elif tag == "tab":
                txt.append("\t")
        for cid in abertos:
            ancorado[cid] += "\n"
        paragrafos.append({"n": len(paragrafos) + 1, "tabela": em_tabela, "texto": "".join(txt)})

    walk(body)
    sem_start = sorted(set(comentarios) - starts, key=int)
    sem_end = sorted(set(comentarios) - ends, key=int)
    vazios = sorted([cid for cid, t in ancorado.items() if not t.strip()], key=int)
    out = {
        "comentarios_total": len(comentarios),
        "comentarios_sem_commentRangeStart": sem_start,
        "comentarios_sem_commentRangeEnd": sem_end,
        "comentarios_com_trecho_ancorado_vazio": vazios,
        "paragrafos_total": len(paragrafos),
        "paragrafos_nao_vazios": sum(1 for p in paragrafos if p["texto"].strip()),
        "paragrafos_em_tabela": sum(1 for p in paragrafos if p["tabela"]),
        "paragrafos": paragrafos,
        "ancoras": {cid: ancorado[cid][:300] for cid in comentarios},
        "comentarios": comentarios,
    }
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    for k in ("comentarios_total", "comentarios_sem_commentRangeStart", "comentarios_sem_commentRangeEnd",
              "comentarios_com_trecho_ancorado_vazio", "paragrafos_total", "paragrafos_nao_vazios",
              "paragrafos_em_tabela"):
        print(k, out[k])


if __name__ == "__main__":
    main()
