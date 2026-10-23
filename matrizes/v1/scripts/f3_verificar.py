#!/usr/bin/env python3
"""Fim da Fase 3 - Conferencias das matrizes M00 a M05 (parte dos testes de aceite da Fase 9 que ja podem rodar).

Uso: python3 -I f3_verificar.py <pasta_Matrizes_v1> <f1_modelo.json> <saida.txt>

Confere: formato dos CSV (BOM, virgula, texto entre aspas); IDs unicos e no padrao; referencias cruzadas;
cobertura dos paragrafos nao vazios do modelo pelo M02 (teste 1); 102 notas ligadas a bloco existente (teste 2);
fonte e status preenchidos e status no dominio (teste 5); incisos obrigatorios no M01 (teste 6);
travessao (U+2014) fora das colunas que copiam texto literal; dominios das colunas do M04 e do M05.
"""
import csv
import io
import json
import re
import sys
from collections import Counter
from pathlib import Path

PADRAO = {
    "M01": r"ETP-\d{2}\.\d{2}",
    "M02": r"TR-[A-Za-z0-9.\-]+",
    "M03": r"NE-\d{3}",
    "M04": r"WZ-\d{2}",
    "M05": r"VAR-\d{3}",
}
LITERAIS = {"texto_literal", "texto_integral", "trecho_ancorado", "lacunas", "citacoes", "normas", "objeto_resumo"}
STATUS = {"EXTRAIDO", "INFERIDO", "A_VERIFICAR"}


def ler(p):
    return list(csv.DictReader(open(p, encoding="utf-8-sig")))


def formato_csv(p):
    bruto = p.read_bytes()
    erros = []
    if not bruto.startswith(b"\xef\xbb\xbf"):
        erros.append("sem BOM")
    if not bruto.decode("utf-8-sig").startswith('"'):
        erros.append("cabeçalho sem aspas")
    return erros


def ids_em(texto):
    out = []
    for m in re.finditer(r"\b(?:TR-[A-Za-z0-9.\-]+|ETP-\d{2}\.\d{2}|WZ-\d{2}|NE-\d{3}|VAR-\d{3})", texto):
        out.append(m.group(0).rstrip(".-"))
    return out


def main():
    pasta = Path(sys.argv[1])
    modelo = json.load(open(sys.argv[2], encoding="utf-8"))
    out = []
    falhas = 0

    def reg(ok, msg):
        nonlocal falhas
        out.append(("OK    " if ok else "FALHA ") + msg)
        falhas += 0 if ok else 1

    arqs = {"M00": "M00_inventario.csv", "M01": "M01_etp_campos.csv", "M02": "M02_tr_blocos.csv",
            "M03": "M03_notas_explicativas.csv", "M04": "M04_wizard.csv", "M05": "M05_variaveis.csv"}
    M = {k: ler(pasta / v) for k, v in arqs.items()}
    # formato
    for k, v in arqs.items():
        e = formato_csv(pasta / v)
        reg(not e, f"{v}: UTF-8 com BOM, vírgula e aspas {'(' + ', '.join(e) + ')' if e else ''}".rstrip())
    # todos os campos entre aspas: reescreve com QUOTE_ALL e compara
    for k, v in arqs.items():
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=list(M[k][0].keys()), quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(M[k])
        igual = buf.getvalue() == open(pasta / v, encoding="utf-8-sig", newline="").read()
        reg(igual, f"{v}: todos os campos entre aspas (regravação com QUOTE_ALL idêntica)")
    # IDs
    for k in ("M01", "M02", "M03", "M04", "M05"):
        ids = [r["id"] for r in M[k]]
        rep = [i for i, c in Counter(ids).items() if c > 1]
        fora = [i for i in ids if not re.fullmatch(PADRAO[k], i)]
        reg(not rep and not fora, f"{k}: {len(ids)} IDs únicos e no padrão" + (f" | repetidos {rep} | fora do padrão {fora}" if rep or fora else ""))
    todos = {r["id"] for k in ("M01", "M02", "M03", "M04", "M05") for r in M[k]}
    lista02 = [r["id"] for r in M["M02"]]
    ordem02 = {k: i for i, k in enumerate(lista02)}
    # referências cruzadas em todas as colunas não literais
    quebradas = []
    for k in ("M01", "M02", "M03", "M04", "M05"):
        for r in M[k]:
            for col, val in r.items():
                if col in LITERAIS or col in ("id", "fonte"):
                    continue
                for ref in ids_em(val):
                    for x in (ref.split("..") if ".." in ref else [ref]):
                        if x not in todos:
                            quebradas.append(f"{r['id']}.{col} -> {x}")
                    if ".." in ref:
                        a, b = ref.split("..")
                        if a in ordem02 and b in ordem02 and ordem02[a] > ordem02[b]:
                            quebradas.append(f"{r['id']}.{col} -> faixa invertida {ref}")
    reg(not quebradas, f"referências cruzadas entre M01 e M05: {len(quebradas)} quebradas" + (f": {quebradas[:20]}" if quebradas else ""))
    # teste 1: cobertura
    nao_vazios = [i for i, p in enumerate(modelo["paragrafos"]) if p["texto"].strip()]
    vazios_modelo = {p["n"] for p in modelo["paragrafos"] if not p["texto"].strip()}
    cobertos = Counter()
    for r in M["M02"]:
        m = re.search(r"parágrafos? (\d+)(?: a (\d+))?", r["fonte"])
        if not m:
            continue
        a = int(m.group(1))
        b = int(m.group(2) or a)
        for i in range(a, b + 1):
            if i not in vazios_modelo:
                cobertos[i] += 1
    nv = {modelo["paragrafos"][i]["n"] for i in nao_vazios}  # numeração 1-based usada na fonte do M02
    faltam = sorted(nv - set(cobertos))
    duplos = sorted(i for i in nv if cobertos[i] > 1)
    pct = 100 * (len(nv) - len(faltam)) / len(nv)
    reg(not faltam and not duplos, f"teste 1: {len(nv) - len(faltam)} de {len(nv)} parágrafos não vazios do modelo em exatamente um bloco do M02 "
                                   f"({pct:.2f}%)" + (f" | faltam {faltam[:20]} | em mais de um {duplos[:20]}" if faltam or duplos else ""))
    # teste 2: notas
    ne = [r for r in M["M03"]]
    sem_bloco = [r["id"] for r in ne if r["bloco_ancora"] not in ordem02]
    ids_ne = sorted(r["id"] for r in ne)
    esperado = [f"NE-{k:03d}" for k in range(1, 103)]
    reg(ids_ne == esperado and not sem_bloco, f"teste 2: {len(ne)} notas, NE-001 a NE-102, todas ligadas a bloco existente do M02"
                                                + (f" | sem bloco {sem_bloco}" if sem_bloco else ""))
    # notas citadas no M02 x âncoras do M03
    citadas = Counter()
    for r in M["M02"]:
        for n in re.findall(r"NE-\d{3}", r["notas"]):
            citadas[n] += 1
    nao_citadas = [n for n in esperado if n not in citadas]
    reg(not nao_citadas, f"M02.notas cita {len(citadas)} das 102 notas" + (f" | não citadas {nao_citadas}" if nao_citadas else ""))
    # teste 5: fonte e status
    vazios = []
    fora_dom = []
    for k in M:
        for r in M[k]:
            if not r.get("fonte", "").strip() or not r.get("status", "").strip():
                vazios.append(f"{k}:{r.get('id', r.get('arquivo'))}")
            if r.get("status") not in STATUS:
                fora_dom.append(f"{k}:{r.get('id', r.get('arquivo'))}={r.get('status')}")
    reg(not vazios and not fora_dom, f"teste 5: fonte e status preenchidos e no domínio em M00 a M05 "
                                     f"({sum(len(v) for v in M.values())} linhas)" + (f" | vazios {vazios[:10]} | fora {fora_dom[:10]}" if vazios or fora_dom else ""))
    # teste 6
    obrig = sorted({r["inciso_art18"] for r in M["M01"] if r["obrigatorio_par2"] == "S" and r["inciso_art18"]})
    nao = sorted({r["inciso_art18"] for r in M["M01"] if r["obrigatorio_par2"] == "N" and r["inciso_art18"]})
    ok6 = obrig == sorted(["I", "IV", "VI", "VIII", "XIII"]) and not set(obrig) & set(nao)
    incisos = sorted({r["inciso_art18"] for r in M["M01"] if r["inciso_art18"]}, key=lambda x: ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII"].index(x))
    reg(ok6, f"teste 6: incisos obrigatórios no M01 = {obrig}; demais incisos presentes = {[i for i in incisos if i not in obrig]}")
    reg(len(incisos) == 13, f"M01 cobre {len(incisos)} dos 13 incisos do art. 18, § 1º")
    # domínios M04 e M05
    d4 = {"documento": {"ETP", "TR", "AMBOS"}, "tipo_resposta": {"SIM_NAO", "UNICA", "MULTIPLA", "NUMERO", "DATA", "TEXTO"}}
    d5 = {"tipo_dado": {"TEXTO", "NUMERO", "MOEDA", "DATA", "LISTA", "TABELA"}, "obrigatoria": {"S", "N", "CONDICIONAL"},
          "origem": {"DFD", "WIZARD", "SISTEMA", "PESQUISA_PRECOS"}}
    for k, dom in (("M04", d4), ("M05", d5)):
        ruins = [f"{r['id']}.{c}={r[c]}" for r in M[k] for c, vals in dom.items() if r[c] not in vals]
        reg(not ruins, f"{k}: colunas de domínio fechado dentro do domínio" + (f" | {ruins}" if ruins else ""))
    ruins = [r["id"] for r in M["M04"] if not re.match(r"^[SN]\b", r["exige_justificativa"])]
    reg(not ruins, "M04.exige_justificativa começa com S ou N" + (f" | {ruins}" if ruins else ""))
    # travessão em texto produzido por mim
    trav = []
    for k in M:
        for r in M[k]:
            for col, val in r.items():
                if col not in LITERAIS and "—" in val:
                    trav.append(f"{k}:{r.get('id', r.get('arquivo'))}.{col}")
    reg(not trav, f"travessão (U+2014) fora das colunas literais: {len(trav)}" + (f" | {trav[:10]}" if trav else ""))
    # status por matriz
    for k in M:
        out.append(f"INFO  {k}: {len(M[k])} linhas | status {dict(Counter(r['status'] for r in M[k]))}")
    out.append(f"FALHAS: {falhas}")
    Path(sys.argv[3]).write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
