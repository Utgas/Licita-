#!/usr/bin/env python3
"""Fase 6 - Compara os TRs 23/2026 e 58/2026 (feitos sobre o modelo DEZ/2025) com os blocos do M02.

Uso: python3 -I f6_comparar_trs.py <M02_tr_blocos.csv> <pasta_texto_TR> [<pasta_texto_TR> ...] <saida.json>

Para cada bloco do M02 (exceto separadores 'OU', tabelas e notas) procura no TR o trecho mais parecido
(difflib, texto normalizado: minúsculas, sem espaços duplicados, sem numeração). Classes:
  IGUAL      razão >= 0,95
  ALTERADO   0,60 <= razão < 0,95
  AUSENTE    razão < 0,60
Para cada parágrafo numerado do TR que não casa com nenhum bloco (razão < 0,60): NOVO.
Os rodapés de página do ETP Digital ('Termo de Referência NN/AAAA', 'N de M', cabeçalho da UASG) são removidos.
O resultado é material para a curadoria do M08 (cláusula setorial) e do M09 (desvio); não classifica sozinho.
"""
import csv
import difflib
import glob
import json
import re
import sys
from pathlib import Path


def norm(t):
    t = t.lower()
    t = re.sub(r"^\s*\d+(?:\.\d+)*\.?\s*", "", t)
    t = re.sub(r"[“”\"'´`]", "", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip(" .;:")


def texto_tr(pasta):
    paginas = []
    for f in sorted(glob.glob(str(Path(pasta) / "p0*.txt"))):
        if "fluxo" in f:
            continue
        t = open(f, encoding="utf-8").read()
        t = re.sub(r"(?m)^.*\b\d+ de \d+\s*$", "", t)
        t = re.sub(r"(?m)^\s*UASG \d+.*$", "", t)
        t = re.sub(r"(?m)^\s*Termo de Referência \d+/\d{4}\s*$", "", t)
        paginas.append((int(Path(f).stem[1:]), t))
    return paginas


def paragrafos(paginas):
    """Quebra o texto em itens numerados ('5.1.', '9.34.1.') ou alíneas; guarda a página de início."""
    pars = []
    rx = re.compile(r"(?m)^\s*(\d{1,2}(?:\.\d{1,2}){1,4})\.?\s+(?=\S)")
    for pg, t in paginas:
        t = re.sub(r"[ \t]+", " ", t)
        pos = [(m.start(), m.group(1)) for m in rx.finditer(t)]
        if not pos:
            continue
        for k, (ini, num) in enumerate(pos):
            fim = pos[k + 1][0] if k + 1 < len(pos) else len(t)
            corpo = re.sub(r"\s+", " ", t[ini:fim]).strip()
            if len(corpo) > 25:
                pars.append({"num": num, "pagina": pg, "texto": corpo})
    return pars


def main():
    m02 = list(csv.DictReader(open(sys.argv[1], encoding="utf-8-sig")))
    pastas, saida = sys.argv[2:-1], sys.argv[-1]
    blocos = [r for r in m02 if r["item_modelo"] != "OU" and ".TAB" not in r["id"] and r["formatacao"] != "NOTA_EXPLICATIVA"
              and len(norm(r["texto_literal"])) >= 25]
    res = {}
    for pasta in pastas:
        pags = texto_tr(pasta)
        pars = paragrafos(pags)
        corpo = norm(" ".join(t for _, t in pags))
        comp = []
        for b in blocos:
            alvo = norm(b["texto_literal"])
            melhor, onde = 0.0, None
            for p in pars:
                r = difflib.SequenceMatcher(None, alvo, norm(p["texto"]), autojunk=False).ratio()
                if r > melhor:
                    melhor, onde = r, p
            if alvo and alvo in corpo:
                melhor = max(melhor, 1.0)
            classe = "IGUAL" if melhor >= 0.95 else "ALTERADO" if melhor >= 0.60 else "AUSENTE"
            comp.append({"bloco": b["id"], "formatacao": b["formatacao"], "razao": round(melhor, 3), "classe": classe,
                         "tr_num": onde["num"] if onde else "", "tr_pagina": onde["pagina"] if onde else "",
                         "tr_trecho": (onde["texto"][:400] if onde and classe == "ALTERADO" else "")})
        novos = []
        alvos = [norm(b["texto_literal"]) for b in blocos]
        for p in pars:
            pn = norm(p["texto"])
            melhor = max((difflib.SequenceMatcher(None, pn, a, autojunk=False).quick_ratio() for a in alvos), default=0)
            if melhor >= 0.60:
                melhor = max(difflib.SequenceMatcher(None, pn, a, autojunk=False).ratio() for a in alvos)
            if melhor < 0.60:
                novos.append({"tr_num": p["num"], "tr_pagina": p["pagina"], "razao": round(melhor, 3), "texto": p["texto"][:500]})
        res[Path(pasta).name] = {"comparacao": comp, "novos": novos}
        from collections import Counter
        c = Counter((x["formatacao"], x["classe"]) for x in comp)
        print(Path(pasta).name, f"{len(pars)} parágrafos;", dict(sorted(c.items())), f"novos: {len(novos)}")
    json.dump(res, open(saida, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
