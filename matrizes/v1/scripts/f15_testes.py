#!/usr/bin/env python3
"""Testes da Fase 15 (chamados pelo f9_testes.py): redação das cláusulas setoriais (concordância, lista por item, sem ID
interno) e complementos do operador CK-X-10 a CK-X-19 (P38). A coluna PARTICIPAÇÃO está no f13_testes.py.

testes(pasta, M) devolve uma lista de (ok, mensagem).
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f10_simulador as sim  # noqa: E402
from f11_checklist import COMPL_M08  # noqa: E402
from f13_lacunas import marcadores_m08  # noqa: E402
from f13_texto import Montagem  # noqa: E402
from jlogic import avaliar  # noqa: E402

ID_INTERNO = re.compile(r"\b(?:TR|SET|VAR|WZ|CK)-[A-Za-z0-9]")
LACUNA = re.compile(r"\[\[LACUNA[^\]]*\]\]")
ITENS_UM = re.compile(r"\bitens (\d+)\b(?!\s*(?:,|e)\s*\d)")


def _ck(rid):
    return "CK_" + rid[3:].replace("-", "_").replace(".", "_")


def testes(pasta, M):
    out = []
    reg = lambda ok, msg: out.append((ok, msg))  # noqa: E731
    m08 = {r["id"]: r for r in M["M08"]}
    # ------------------------------------------------ 1. texto_proposto sem ID interno fora dos marcadores
    com_id = []
    for r in M["M08"]:
        t = r["texto_proposto"]
        for mk in marcadores_m08(t):
            t = t.replace(mk, "", 1)
        if ID_INTERNO.search(t):
            com_id.append(r["id"])
    reg(not com_id, "M08.texto_proposto: nenhum ID interno (TR-, SET-, VAR-, WZ-, CK-) fora dos marcadores; a "
        "referência fica nas colunas de controle" + (f" | {com_id}" if com_id else ""))
    # ------------------------------------------------ 2. montagem: concordância e lista por item (casos fixos)
    def cl(sid, dados):
        return Montagem(dict(dados, parametros=sim.VALORES)).clausula(m08[sid])

    um = [{"numero": 1, "faixa_temperatura": "2 a 8 °C"}, {"numero": 2}]
    dois = [{"numero": 1, "faixa_temperatura": "2 a 8 °C"}, {"numero": 2, "faixa_temperatura": "15 a 30 °C"},
            {"numero": 3, "faixa_temperatura": "2 a 8 °C"}]
    casos = [
        ("SET-02", {"itens": um}, "O item 1 será transportado, armazenado até a entrega e entregue nas condições de "
                                  "conservação indicadas pelo fabricante, observada a faixa de temperatura de 2 a 8 °C "
                                  "para o item 1."),
        ("SET-02", {"itens": dois}, "Os itens 1, 2 e 3 serão transportados, armazenados até a entrega e entregues nas "
                                    "condições de conservação indicadas pelo fabricante, observada a faixa de temperatura "
                                    "de 2 a 8 °C para os itens 1 e 3; de 15 a 30 °C para o item 2."),
        ("SET-07", {"CK_X_11": [2], "CK_X_12": "na entrega", "VAR_135": "esterilidade"},
         "O item 2 deverá atender aos seguintes requisitos, comprovados na entrega: esterilidade."),
        ("SET-11", {"CK_X_18": [1, 2], "CK_P_11_3": ["Instalação"], "CK_P_11_4": "laudo", "CK_P_11_5": "teste"},
         "O Contratado executará, nos itens 1 e 2, as atividades instalação"),
        ("SET-10", {"CK_X_17": [4], "VAR_132": "24 horas"}, "Para o item 4, em situação de urgência"),
        ("SET-03", {"CK_X_10": [1, 5], "VAR_130": "laudo do lote"}, "A entrega dos itens 1 e 5 será acompanhada de laudo do "
                                                                     "lote"),
        ("SET-09", {"CK_X_15": "almoxarifado", "CK_X_16": "48 horas", "VAR_131": "entrada pela doca"},
         "A entrega será previamente agendada com almoxarifado, com antecedência mínima de 48 horas, observadas as "
         "seguintes restrições: entrada pela doca."),
        ("SET-08", {"CK_X_13": "Distribuição de medicamentos", "CK_X_14": "Anvisa"},
         "Atividade distribuição de medicamentos, órgão expedidor Anvisa"),
        ("SET-18", {"CK_X_19": "autoclave antiga, sala 3", "VAR_144": "descontaminação"},
         "a retirada de autoclave antiga, sala 3, com os procedimentos descontaminação"),
    ]
    falhas = []
    for sid, dados, trecho in casos:
        t, lac = cl(sid, dados)
        if trecho not in t or lac:
            falhas.append(f"{sid}: {t[:180]} | {lac}")
    reg(not falhas, f"cláusulas do M08: {len(casos)} casos fixos (singular com um item, plural com mais de um, faixa "
        f"de temperatura agrupada por item, complementos CK-X-10 a CK-X-19 no lugar das partes da equipe)"
        + (f" | {falhas[:3]}" if falhas else ""))
    # ------------------------------------------------ 3. cenários C1 a C8: sem ID interno e sem 'itens <um número>'
    m = sim.carregar(str(pasta))
    docs = [json.loads(f.read_text(encoding="utf-8")) for f in sorted((pasta / "cenarios").glob("C*.json"))]
    achados = []
    for doc in docs:
        obt, extra = sim.caminho_expr(m, doc["entrada"])
        textos, _, _ = sim.com_texto(m, obt, extra)
        for k, t in textos.items():
            limpo = LACUNA.sub("", t)
            if ID_INTERNO.search(limpo):
                achados.append(f"{doc['id']} {k}: ID {ID_INTERNO.search(limpo).group(0)}")
            if ITENS_UM.search(limpo):
                achados.append(f"{doc['id']} {k}: '{ITENS_UM.search(limpo).group(0)}'")
    reg(len(docs) == 8 and not achados, "cenários C1 a C8: nenhum texto montado com ID interno fora das marcas de lacuna "
        "nem 'itens' seguido de um número só" + (f" | {achados[:6]}" if achados else ""))
    # ------------------------------------------------ 4. complementos do operador CK-X-10 a CK-X-19 (P38)
    m11 = {r["id"]: r for r in M["M11"]}
    ruins = []
    for cid, sid, vid, *_ in COMPL_M08:
        r = m11.get(cid)
        if not r or r["checklist"] != "COMPLEMENTO" or r["condicional_expr"] != m08[sid]["condicao_expr"] \
                or sid not in r["destinos"] or vid not in r["destinos"]:
            ruins.append(cid)
    usados = set()
    for r in M["M08"]:
        for x in json.loads(r["lacunas_mapa"] or "[]"):
            if x.get("acao") == "EQUIPE":
                ruins.append(f"{r['id']}: parte ainda com a equipe ({x['marcador'][:30]})")
            f = x.get("fonte") or ""
            if f.startswith("CK_X_"):
                cid = "CK-X-" + f[5:]
                usados.add(cid)
                if cid not in m11 or r["id"] not in m11[cid]["destinos"]:
                    ruins.append(f"{r['id']}: {f} sem complemento ligado à cláusula")
    faltam = {c for c, *_ in COMPL_M08} - usados
    reg(not ruins and not faltam and len(COMPL_M08) == 10,
        f"M11: complementos CK-X-10 a CK-X-19 (checklist = COMPLEMENTO), com a condição da cláusula, ligados à VAR e à "
        f"cláusula; toda parte do M08 que era da equipe aponta para um deles" + (f" | {ruins + sorted(faltam)}" if ruins
                                                                               or faltam else ""))
    # só aparecem quando a cláusula entra
    fora = []
    for doc in docs:
        obt, extra = sim.caminho_expr(m, doc["entrada"])
        d = extra["dados"]
        for cid, sid, *_ in COMPL_M08:
            aparece = bool(avaliar(json.loads(m11[cid]["condicional_expr"]), d))
            if aparece != (sid in obt["clausulas_m08"]):
                fora.append(f"{doc['id']} {cid}")
    reg(not fora, "complementos do M08 aparecem exatamente quando a cláusula entra, nos 8 cenários"
        + (f" | {fora[:6]}" if fora else ""))
    return out
