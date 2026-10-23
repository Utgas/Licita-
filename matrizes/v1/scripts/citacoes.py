#!/usr/bin/env python3
"""Extrator de citacoes normativas e de julgados, como escritas no texto (usado nas Fases 1, 2 e 5).

Uso como script: python3 -I citacoes.py "<texto>"
Uso como modulo: from citacoes import extrair  (o chamador acrescenta a pasta scripts ao sys.path)
Devolve a lista de trechos na ordem em que aparecem, sem repeticao. Nao interpreta nem corrige.
"""
import re
import sys

_ART = r"(?:(?:inciso|incisos|alínea|alíneas|parágrafo único|caput)\s+[\w.º°,§ \-–“”\"']{0,40}?\s+d[oa]s?\s+|§\s*[\w.º°, ]{0,12}?\s*d[oa]s?\s+)?" \
       r"(?:(?:art\.|arts\.|artigo|artigos|Art\.)\s+[\w.º°,§ \-–e]{1,60}?\s*(?:,\s*)?d[aoe]s?\s+)?"
_NUM = r"\s*(?:n\.?\s*[º°o]?\.?\s*|nº\s*|n\.º\s*|Nº\s*)?\d[\d.]*(?:/\d{2,4})?(?:,?\s*de\s+(?:\d{1,2}º?\s*(?:de\s+)?[a-zç]+\s+(?:de\s+)?)?\d{4})?"
PADROES = [
    # normas com numero
    _ART + r"(?:Lei Complementar|Decreto-Lei|Decreto|Lei|Instrução Normativa|Portaria Conjunta|Portaria|Resolução|"
           r"Circular|Medida Provisória|Comunicado)(?:\s+(?:da\s+Diretoria\s+Colegiada\s*-?\s*)?[A-Za-zÀ-ú/\-]+){0,3}?" + _NUM,
    _ART + r"IN(?:\s+[A-Za-z/]+){0,2}" + _NUM,
    r"LC\s+n[º°.o]*\s*\d+/\d{4}",
    r"RDC\s*(?:n[º°.o]*\s*)?\d+(?:/\d{4})?(?:,?\s*de\s+(?:\d{1,2}º?\s*(?:de\s+)?[a-zç]+\s+(?:de\s+)?)?\d{4})?",
    r"Lei de Usura",
    # codigos e constituicao
    _ART + r"(?:Código Civil|Código de Defesa do Consumidor|Código Tributário Nacional|Consolidação das Leis do Trabalho|Constituição Federal)",
    # orientacoes normativas
    r"(?:Orientação Normativa|ORIENTAÇÃO NORMATIVA|Orientação normativa)\s+(?:AGU\s+)?(?:n[º°.o]*\s*|Nº\s*)?\d+(?:/\d{4})?(?:,\s*(?:de|DE)\s+(?:\d{1,2}\s+(?:de|DE)\s+[a-zA-ZçÇ]+\s+(?:de|DE)\s+)?\d{4})?",
    # julgados do TCU
    r"(?:Acórdão|Ac\.)\s*(?:n[º°.o]*\s*)?[\d.]+/\d{4}(?:\s*[–-]\s*(?:TCU\s*[–-]\s*)?(?:Plenário|Primeira Câmara|Segunda Câmara))?",
    r"Decis(?:ão|ões)\s+[\d.]+/\d{4}(?:\s+e\s+[\d.]+/\d{4})?",
    r"TC-[\d.]+/\d{4}-\d",
    # pareceres, notas e despachos da AGU
    r"(?:PARECER|Parecer)\s+(?:n[º°.o]*\s*)?(?:JL\s*[–-]?\s*0?\d+(?:/\d{4})?|nº\s*JL\s*[–-]\s*\d+/\d{4}|\d+/\d{4}/[A-Z]+(?:/[A-Z]+)*)",
    r"NOTA\s+n\.\s*\d+/\d{4}/[A-Z]+(?:/[A-Z]+)*",
    r"(?:DESPACHO|Despacho)\s+(?:do\s+[A-Z][\wÀ-ú\-]+(?:\s+[\wÀ-ú\-]+){0,5}\s+)?n[º°.o]*\s*[\d.]+(?:/\d{4}/[A-Z]+(?:/[A-Z]+)*)?(?:,\s*de\s+\d{1,2},?\s+de\s+[a-zç]+\s+de\s+\d{4})?",
]
RX = re.compile("|".join(f"(?:{p})" for p in PADROES), flags=re.I)
_FALSOS = re.compile(r"(?i)^(?:in|art\.?)\s*\d{1,2}$|^IN\s+\w+$")


def extrair(texto):
    achados = []
    for m in RX.finditer(texto or ""):
        s = re.sub(r"\s+", " ", m.group(0)).strip(" ,;.:()")
        if len(s) < 6 or _FALSOS.match(s):
            continue
        if s not in achados:
            achados.append(s)
    return achados


if __name__ == "__main__":
    for c in extrair(" ".join(sys.argv[1:])):
        print(c)
