#!/usr/bin/env python3
"""Fase 1 - Quebra o modelo AGU de TR em blocos com ID estavel (base automatica do M02).

Uso: python3 -I f1_blocos.py <f1_modelo.json> <saida_blocos.json>

Regras de ID (registradas no README):
  - paragrafo numerado pelo Word: TR-<numeracao do modelo> (ex.: TR-1.1, TR-4.3.1.1);
  - lista em letras ou romanos: TR-<item pai>.<rotulo> (ex.: TR-7.1.a, TR-2.2.I);
  - tabela: TR-<item numerado anterior>.TAB<k>;
  - paragrafo 'OU' entre alternativas: TR-<bloco anterior>.OU;
  - subtitulo sem numero: TR-<secao>.H<nn>;
  - cabecalho do TR: TR-CAB.<nn>; local, data e assinatura: TR-ASSIN.<nn>;
  - Anexo I: prefixo TR-AI- (numeracao propria reinicia em 1) e cabecalho TR-AI.CAB.<nn>;
  - Anexo II: TR-AII.<nn>.
Cada bloco guarda: paragrafos de origem, texto literal, formatacao calculada pelos runs, lacunas,
notas (comentarios) cujo trecho ancorado toca o bloco e normas citadas no texto.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # pasta dos scripts (codigo proprio)
from citacoes import extrair as extrair_citacoes  # noqa: E402

LACUNA_RX = re.compile(
    r"\[[^\[\]]{0,160}\]"                      # [INSERIR OBJETO], [...], [ANO], [normal]
    r"|R\$ ?\.{2,}[^\s,;.]*"                   # R$ ....
    r"|\.{4,}\s*(?:\([^)]{0,80}\))?"           # ........ (com instrucao entre parenteses, se houver)
    r"|\.{2,3}\s?%"                           # ...% (percentual a preencher)
    r"|\((?:\.{2,}|…)\)"                       # (...) (....)
    r"|_{2,}(?:/_{2,})*(?:\s*\(_{2,}\))?"      # __/__/__ , ___ (____)
    r"|\bx{5}\.x{6}/x{4}-x{2}\b"               # xxxxx.xxxxxx/xxxx-xx
    r"|\bX{2,}(?:,X{2,})?%?(?:\s*\(x{3,}[^)]*\))?"  # XX% (xxxxx por cento), XXXX
    r"|\((?:especificar|indicar|escrever|identificar|incluir|valor|por extenso|parcial/total|recibo|dias ou|metade|máximo|data da|Nome e Cargo)[^)]{0,120}\)",
    flags=re.I)

NORMA_RX = re.compile(
    r"(?:(?:inciso|incisos|alínea|§)\s+[\w.º°,§ \-–“”\"]{1,40}?\s+d[oa]s?\s+)?"
    r"(?:(?:art\.|arts\.|artigo|artigos)\s+[\w.º°,§ \-–e]{1,60}?\s+d[aoe]s?\s+)?"
    r"(?:Lei Complementar|Lei|Decreto-Lei|Decreto|Instrução Normativa|IN|Portaria(?: Conjunta)?|Resolução|"
    r"Orientação Normativa|Circular|Medida Provisória|Constituição Federal)"
    r"(?:\s+[A-Za-zÀ-ú/\-]+){0,3}?\s*(?:n\.?[º°o]?\.?\s*|nº\s*)?\d[\d.]*(?:/\d{2,4})?"
    r"(?:,\s*de\s+(?:\d{1,2}º?\s+de\s+[a-zç]+\s+(?:de\s+)?)?\d{4})?",
    flags=re.I)


def classe(t):
    c = "P" if t["cor"] == "preto" else ("V" if t["cor"] == "vermelho" else "O")
    return c + ("i" if t["i"] else "")


def contagem_formatacao(pars):
    cont = {}
    realce = {}
    for p in pars:
        for t in p["trechos"]:
            k = len(re.sub(r"\s", "", t["t"]))
            if not k:
                continue
            c = classe(t)
            cont[c] = cont.get(c, 0) + k
            if t.get("realce"):
                realce[t["realce"]] = realce.get(t["realce"], 0) + k
    return cont, realce


def formatacao(cont):
    total = sum(cont.values())
    if not total:
        return "PRETO"
    if cont.get("P", 0) == total:
        return "PRETO"
    if cont.get("Vi", 0) == total:
        return "VERMELHO_ITALICO"
    return "MISTO"


def lacunas(texto, pars=None, misto=False):
    """Marcadores de preenchimento do texto; nos blocos MISTO, tambem os trechos em vermelho."""
    vistos = []
    for m in LACUNA_RX.finditer(texto):
        s = m.group(0).strip()
        if s:
            vistos.append(s)
    if misto and pars:
        for p in pars:
            atual = ""
            for t in p["trechos"] + [{"t": "", "cor": "fim", "i": False}]:
                if t["cor"] == "vermelho":
                    atual += t["t"]
                    continue
                seg = re.sub(r"\s+", " ", atual).strip(" ,;.")
                curto = len(seg.split()) <= 2 and not re.search(r"[\[\].…_]|X{2}", seg)
                if len(re.sub(r"\W", "", seg)) >= 2 and not curto and not any(seg in v or v in seg for v in vistos):
                    vistos.append(seg)
                atual = ""
    return vistos


CODIGO_RX = re.compile(r"(?:(?:art\.|artigo|artigos|arts\.)\s+[\w.º°,§ \-–e]{1,30}?\s+d[oa]\s+)?(?:Código Civil|Código de Defesa do Consumidor|Código Tributário Nacional|Consolidação das Leis do Trabalho)")


def normas(texto):
    return extrair_citacoes(texto)


def normas_antigo(texto):
    achados = []
    for m in CODIGO_RX.finditer(texto):
        s = re.sub(r"\s+", " ", m.group(0)).strip(" ,;.")
        if s not in achados:
            achados.append(s)
    for m in NORMA_RX.finditer(texto):
        s = re.sub(r"\s+", " ", m.group(0)).strip(" ,;.")
        # descarta falsos positivos como "IN 1" sem contexto ou incisos romanos
        if re.fullmatch(r"(?i)IN\s*\d{1,2}", s):
            continue
        if s not in achados:
            achados.append(s)
    return achados


def main():
    d = json.load(open(sys.argv[1], encoding="utf-8"))
    P = d["paragrafos"]
    tabelas = {t["tabela"]: t for t in d["tabelas"]}
    ne = {c["id_word"]: f"NE-{c['ordem']:03d}" for c in d["comentarios"]}
    # paragrafos cobertos por cada nota
    cobre = {}
    for c in d["comentarios"]:
        for n in range(c["par_inicio"], c["par_fim"] + 1):
            cobre.setdefault(n, []).append(ne[c["id_word"]])

    blocos = []
    usados = set()
    regiao = "CORPO"
    secao = None          # rotulo da secao (nivel 0) corrente
    ultimo_num = None     # nucleo do ultimo ID numerado
    ultimo_bloco = None
    cont_h = {}
    cont_tab = {}
    cont_cab = {"CORPO": 0, "AI": 0, "AII": 0, "ASSIN": 0}
    tab_vista = set()

    def novo_id(base):
        i, k = base, 2
        while i in usados:
            i = f"{base}-{k}"
            k += 1
        usados.add(i)
        return i

    def prefixo():
        return {"CORPO": "TR-", "AI": "TR-AI-", "AII": "TR-AII-"}[regiao]

    for p in P:
        txt = p["texto"]
        if p["tabela"]:
            if p["tabela"] in tab_vista:
                continue
            tab_vista.add(p["tabela"])
            t = tabelas[p["tabela"]]
            pars = P[t["par_inicio"] - 1:t["par_fim"]]
            base = ultimo_num or "CAB"
            cont_tab[base] = cont_tab.get(base, 0) + 1
            bid = novo_id(f"{prefixo()}{base}.TAB{cont_tab[base]}")
            linhas = [" | ".join(c.replace("\n", " / ") for c in r) for r in t["grade"]]
            texto = "\n".join(linhas)
            cont, realce = contagem_formatacao(pars)
            notas = sorted({x for q in pars for x in cobre.get(q["n"], [])})
            blocos.append({"id": bid, "regiao": regiao, "secao": secao, "item_modelo": f"tabela {p['tabela']}",
                           "paragrafos": [q["n"] for q in pars], "nao_vazios": [q["n"] for q in pars if q["texto"].strip()],
                           "estilo": "tabela", "texto": texto, "contagem": cont, "realce": realce,
                           "formatacao": formatacao(cont), "lacunas": lacunas(texto), "notas": notas,
                           "normas": normas(texto), "eh_tabela": True})
            ultimo_bloco = bid
            continue
        if not txt.strip():
            continue
        # mudanca de regiao: anexos
        if p["estilo"] == "Normal" and txt.strip() == "ANEXO I":
            regiao, secao, ultimo_num = "AI", None, None
        elif p["estilo"] == "Normal" and txt.strip() == "ANEXO II":
            regiao, secao, ultimo_num = "AII", None, None
        rot = (p["rotulo"] or "").strip()
        if rot:
            nucleo = rot.rstrip(".)")
            if re.fullmatch(r"[a-z]|[IVXL]+", nucleo):  # lista em letras/romanos: pendura no item pai
                pai = ultimo_num.split(".§")[0] if ultimo_num else "X"
                pai = re.sub(r"\.(?:[a-z]|[IVXL]+)$", "", pai)
                nucleo = f"{pai}.{nucleo}"
            else:
                if p["nivel"] == 0:
                    secao = nucleo
            bid = novo_id(prefixo() + nucleo)
            ultimo_num = nucleo
            item = rot
        elif p["estilo"] == "ou" or (txt.strip() == "OU" and len(txt.strip()) <= 3):
            base = (ultimo_bloco or "TR-CAB").replace("TR-AI-", "").replace("TR-AII-", "").replace("TR-", "")
            bid = novo_id(f"{prefixo()}{base}.OU" if not base.startswith("AI.") else f"TR-{base}.OU")
            item = "OU"
        elif regiao == "CORPO" and secao is None:
            cont_cab["CORPO"] += 1
            bid = novo_id(f"TR-CAB.{cont_cab['CORPO']:02d}")
            item = "cabeçalho"
        elif regiao == "CORPO" and secao == "12" and p["estilo"] in ("Normal", "Nvel2-Opcional") and not rot:
            cont_cab["ASSIN"] += 1
            bid = novo_id(f"TR-ASSIN.{cont_cab['ASSIN']:02d}")
            item = "fecho"
        elif regiao == "AI" and secao is None:
            cont_cab["AI"] += 1
            bid = novo_id(f"TR-AI.CAB.{cont_cab['AI']:02d}")
            item = "cabeçalho do Anexo I"
        elif regiao == "AII":
            cont_cab["AII"] += 1
            bid = novo_id(f"TR-AII.{cont_cab['AII']:02d}")
            item = "Anexo II"
        else:
            chave = (regiao, secao)
            cont_h[chave] = cont_h.get(chave, 0) + 1
            bid = novo_id(f"{prefixo()}{secao}.H{cont_h[chave]:02d}")
            item = "subtítulo"
        cont, realce = contagem_formatacao([p])
        blocos.append({"id": bid, "regiao": regiao, "secao": secao, "item_modelo": item,
                       "paragrafos": [p["n"]], "nao_vazios": [p["n"]], "estilo": p["estilo"], "texto": txt,
                       "contagem": cont, "realce": realce, "formatacao": formatacao(cont),
                       "lacunas": lacunas(txt, [p], formatacao(cont) == "MISTO" and cont.get("P", 0) >= 0.1 * sum(cont.values())),
                       "notas": sorted(set(cobre.get(p["n"], []))), "normas": normas(txt), "eh_tabela": False})
        ultimo_bloco = bid
    json.dump(blocos, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    cobertos = [n for b in blocos for n in b["nao_vazios"]]
    nao_vazios = [p["n"] for p in P if p["texto"].strip()]
    print(f"blocos: {len(blocos)}; parágrafos não vazios: {len(nao_vazios)}; cobertos: {len(set(cobertos))}; "
          f"repetidos: {len(cobertos) - len(set(cobertos))}; fora: {sorted(set(nao_vazios) - set(cobertos))[:10]}")


if __name__ == "__main__":
    main()
