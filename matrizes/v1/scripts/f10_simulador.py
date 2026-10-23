#!/usr/bin/env python3
"""Fase 10 - simulador independente do motor: cenários de ouro C1 a C8 em JSON e reprodução pelas colunas novas.

Uso:
  python3 -I f10_simulador.py gerar <pasta_Matrizes_v1>      grava cenarios/C1..C8.json e imprime o resumo
  python3 -I f10_simulador.py reproduzir <pasta_Matrizes_v1> lê cenarios/*.json (C e R) e confere pelas expressões

Dois caminhos, com código separado:
  1. caminho do texto (gera `esperado`): respostas completas do cenário (as que o checklist preenche estão escritas à
     mão em `via_checklist`), derivadas e tratamento de ME/EPP calculados em Python (f3_simular_wizard.py), blocos pelo
     texto de liga_blocos/desliga_blocos do M04, perguntas aplicáveis pelo texto de depende_de; M08 e M10 só têm
     expressão, avaliada sobre os dados desse caminho;
  2. caminho das expressões (reprodução): parte de `entrada`, aplica M11.preenche_expr, M05.calculo_expr,
     M04.calculo_expr e M04.depende_de_expr, e avalia M02.condicao_expr, M08.condicao_expr e M10.condicao_expr.
Os dados dos cenários são fictícios (quantidades, preços e textos de teste; nenhum dado real de processo).
"""
import copy
from decimal import Decimal
import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from f3_simular_wizard import CENARIOS, dec, derivar, efeitos, pai  # noqa: E402
from jlogic import avaliar as jl  # noqa: E402
from parametros import VALORES  # noqa: E402
from f13_texto import montar_minuta  # noqa: E402

DERIVADAS = {"WZ-09", "WZ-13", "WZ-18", "WZ-20", "WZ-24", "WZ-50"}
ATRIB_CALC = {"perecivel", "tic", "valor_unidade_disputa", "tratamento_me_epp", "quantidade_cota"}
GLOBAIS_META = ("textos_livres", "importacao", "checklist")


def ler(pasta, nome):
    return list(csv.DictReader(open(Path(pasta) / nome, encoding="utf-8-sig")))


def carregar(pasta):
    return {k: ler(pasta, f) for k, f in (("M02", "M02_tr_blocos.csv"), ("M04", "M04_wizard.csv"),
                                           ("M05", "M05_variaveis.csv"), ("M08", "M08_clausulas_setoriais.csv"),
                                           ("M10", "M10_validacoes.csv"), ("M11", "M11_checklist.csv"))}


def vazio(v):
    return v is None or v == "" or v == []


def wzv(k):
    return k.replace("-", "_")


# =========================================================================== cenários
# via_checklist: o que o checklist da entrada deve preencher, escrito à mão a partir da coluna `regra` do M11
# (independente das expressões). wz: respostas do wizard; itens: atributos por número de item; ck: respostas globais
# acrescentadas; por_item: respostas ligadas a cada item; tirar_itens: atributos que saem da entrada (vêm do checklist).
VIA = {
    "C1": {"wz": {"WZ-26": "PARCELADA", "WZ-07": "CONSUMO"},
           "ck": {"CK_C_12_3": "Parcelada", "CK_C_1_5": ["Medicamentos"]},
           "itens": {1: {"categoria": "CONSUMO"}, 2: {"categoria": "CONSUMO"}}, "tirar_itens": ["categoria"]},
    "C2": {"wz": {"WZ-26": "REMESSA_UNICA"}, "ck": {"CK_C_12_3": "Única"}},
    "C3": {"wz": {"WZ-07": "AMBOS"}, "ck": {"CK_C_1_5": ["Medicamentos"], "CK_P_1_5": ["Equipamentos médico-hospitalares"]}},
    "C4": {"wz": {"WZ-26": "PARCELADA", "WZ-07": "PERMANENTE", "WZ-08": "SIM"},
           "ck": {"CK_P_8_3": "Em etapas previamente definidas", "CK_P_1_5": ["Equipamentos médico-hospitalares"],
                  "CK_P_11_1": "Sim"},
           "itens": {1: {"categoria": "PERMANENTE"}}, "tirar_itens": ["categoria"]},
    "C5": {"ck": {"CK_C_9_1": "Não"}, "itens": {1: {"exige_amostra": "N"}, 2: {"exige_amostra": "N"}},
           "tirar_itens": ["exige_amostra"]},
    "C6": {"ck": {"CK_C_9_1": "Sim", "CK_C_9_2": "Item 2: amostra de 2 unidades", "CK_C_13_1": "Sim",
                  "CK_C_8_2": "Sim"},
           "por_item": {2: {"CK_C_9_2": "amostra de 2 unidades"},
                        3: {"CK_C_13_1": "Sim", "CK_C_13_1_texto": "2 a 8 °C"},
                        5: {"CK_C_8_2": "Sim", "CK_C_8_2_texto": "G1"}, 6: {"CK_C_8_2": "Sim", "CK_C_8_2_texto": "G1"}},
           "itens": {1: {"exige_amostra": "N"}, 2: {"exige_amostra": "S"}, 3: {"exige_amostra": "N",
                     "faixa_temperatura": "2 a 8 °C"}, 4: {"exige_amostra": "N"}, 5: {"exige_amostra": "N", "grupo": "G1"},
                     6: {"exige_amostra": "N", "grupo": "G1"}, 7: {"exige_amostra": "N"}},
           "tirar_itens": ["exige_amostra", "faixa_temperatura", "grupo"]},
    "C7": {"wz": {"WZ-47": "SIM", "WZ-08": "SIM"},
           "por_item": {1: {"CK_P_13_1": "36 meses"}, 2: {"CK_P_13_1": "12 meses"}},
           "itens": {1: {"garantia_minima_meses": 36}, 2: {"garantia_minima_meses": 12}},
           "tirar_itens": ["garantia_minima_meses"], "tirar_wz": ["WZ-08"]},
    "C8": {"ck": {"CK_C_14_2": "12 meses", "CK_C_15_2": "Sim"},
           "por_item": {1: {"CK_C_14_2": "12 meses"}, 2: {"CK_C_14_2": "75% do prazo total", "CK_C_15_2": "Sim"}},
           "itens": {1: {"validade_minima": "12 meses"}, 2: {"validade_minima": "75% do prazo total",
                                                            "controle_especial": "S"}},
           "tirar_itens": ["validade_minima", "controle_especial"],
           "var": {"VAR_060": 45}, "tirar_var": ["VAR_060"]},
}
# por cenário, o código (C1..C8) é o prefixo do nome no f3_simular_wizard.py
CODIGOS = {nome.split(" ")[0]: nome for nome in CENARIOS}


def item_entrada(it):
    """atributos de entrada de um item do f3 (sem os calculados e sem campos vazios)."""
    out = {}
    for k, v in it.items():
        if k in ATRIB_CALC or k in ("excecao",) or vazio(v):
            continue
        if k == "tic":
            continue
        out[k] = v
    out.setdefault("classe_pdm", "")
    return out


def montar_entrada(cod):
    cen = CENARIOS[CODIGOS[cod]]
    via = VIA.get(cod, {})
    resp = dict(cen["resp"])
    for k in list(via.get("wz", {})) + via.get("tirar_wz", []):
        resp.pop(k, None)
    wizard = {wzv(k): (v.split(";") if k == "WZ-38" else v) for k, v in resp.items()}
    checklist = dict(cen.get("ck", {}))
    checklist.update(via.get("ck", {}))
    itens = []
    for it in cen["itens"]:
        x = item_entrada(it)
        for a in via.get("tirar_itens", []):
            x.pop(a, None)
        pi = via.get("por_item", {}).get(it["numero"])
        if pi:
            x["respostas_por_item"] = pi
        itens.append(x)
    variaveis = {k: v for k, v in cen.get("var", {}).items() if k not in via.get("tirar_var", [])}
    if cen.get("pct_cota") is not None:
        variaveis["VAR_057"] = cen["pct_cota"]
    variaveis.setdefault("VAR_099", "DEZ/2025")
    meta = dict(cen.get("meta", {}))
    return {"wizard": wizard, "checklist": checklist, "itens": itens, "variaveis": variaveis, "metadados": meta}


# =========================================================================== caminho do texto
def cond_texto(t, r):
    """avalia um trecho de depende_de em Python, sobre as respostas r (chaves 'WZ-xx' e 'CK_...')."""
    t = t.strip()
    m = re.fullmatch(r"(WZ-\d{2}) respondida", t)
    if m:
        return not vazio(r.get(m.group(1)))
    m = re.fullmatch(r"(WZ-\d{2}) contém ([A-Z0-9_]+)", t)
    if m:
        v = r.get(m.group(1)) or ""
        return m.group(2) in (v.split(";") if isinstance(v, str) else v)
    m = re.fullmatch(r"(WZ-\d{2}) diferente de ([A-Z0-9_]+)", t)
    if m:
        return r.get(m.group(1)) != m.group(2)
    m = re.fullmatch(r"(WZ-\d{2}) em (.+)", t)
    if m:
        return r.get(m.group(1)) in m.group(2).split(" ou ")
    m = re.fullmatch(r"(WZ-\d{2})=([A-Z0-9_]+)", t)
    if m:
        return r.get(m.group(1)) == m.group(2)
    m = re.fullmatch(r"CK-([CP])-([\d.]+)=(.+)", t)
    if m:
        return r.get(f"CK_{m.group(1)}_{m.group(2).replace('.', '_')}") == m.group(3)
    raise ValueError(t)


def aplica_texto(dep, r):
    if dep.startswith("DESLIGADA"):
        return False
    conds = [p.strip() for p in dep.split(";") if p.strip() and not p.strip().startswith("VAR-")]
    if not conds:
        return True
    c = conds[0]
    if " e " in c:
        return all(cond_texto(x, r) for x in c.split(" e "))
    if re.search(r"\bem\b", c):
        return cond_texto(c, r)
    if " ou " in c:
        return any(cond_texto(x, r) for x in c.split(" ou "))
    return cond_texto(c, r)


CHAVES_ESPERADO = ("blocos", "clausulas_m08", "validacoes_m10", "perguntas_sem_resposta", "bloqueios_grupo_alternativas",
                   "texto_sem_lacuna")


def sem_orfaos(blocos, lista):
    """Regra do motor: filho sem o pai não entra. Pai = o ID sem o último segmento (TR-4.41.1 -> TR-4.41), quando esse
    ID existe no M02; aplicada na ordem do M02, em cascata."""
    ids = set(lista)
    dentro = set(blocos)
    for i in [x for x in lista if x in dentro]:
        p = pai(i, ids)
        if p and p not in dentro:
            dentro.discard(i)
    return [x for x in lista if x in dentro]


def bloqueios_grupo(m, blocos, ativos):
    """Regra do motor: num grupo de alternativas ativo, exatamente uma opção entra; nenhuma ou mais de uma é bloqueio."""
    ops = {}
    dentro = set(blocos)
    for r in m["M02"]:
        if r["grupo_alternativa"] and r["opcao"] and r["id"] in dentro:
            ops.setdefault(r["grupo_alternativa"].split(" ")[0], set()).add(r["opcao"])
    return sorted(g for g in ativos if len(ops.get(g, set())) != 1)


def COM_MARCADOR(m):
    return {r["id"] for r in m["M02"] if r.get("lacunas_mapa") or r.get("tabela_colunas")}


def json_num(o):
    if isinstance(o, Decimal):
        return int(o) if o == o.to_integral_value() else str(o)
    raise TypeError(type(o))


def com_contexto(globais, itens):
    """cada item carrega as variáveis globais (convenção da Fase 10)."""
    return [dict(globais, **i) for i in itens]


def caminho_texto(m, cod):
    cen = CENARIOS[CODIGOS[cod]]
    via = VIA.get(cod, {})
    resp = dict(cen["resp"])
    resp.update(via.get("wz", {}))
    itens = copy.deepcopy(cen["itens"])
    for it in itens:
        for k, v in via.get("itens", {}).get(it["numero"], {}).items():
            it[k] = v
        it["perecivel"] = "S" if it["validade_minima"] and it["categoria"] != "PERMANENTE" else "N"
        it["tic"] = "N"
        it["excecao"] = it.get("justificativa_excecao_me_epp", "")
    derivadas, trat = derivar(resp, itens, cen["pct_cota"])
    todas = dict(resp, **derivadas)
    # blocos pelo texto do M04 (mesma semântica do f3_simular_wizard.py)
    lista = [r["id"] for r in m["M02"]]
    ordem = {k: i for i, k in enumerate(lista)}
    por_wz = {r["id"]: (efeitos(r["liga_blocos"], ordem, lista), efeitos(r["desliga_blocos"], ordem, lista))
              for r in m["M04"]}
    multipla = {r["id"]: r["tipo_resposta"] == "MULTIPLA" for r in m["M04"]}
    liga, desl = set(), set()
    for wz, valor in todas.items():
        li, de = por_wz[wz]
        marcadas = valor.split(";")
        for v in marcadas:
            liga |= li.get(v, set())
            desl |= de.get(v, set())
        if multipla[wz]:
            ligadas = set().union(*(li.get(v, set()) for v in marcadas))
            for v, ids_v in li.items():
                if v not in marcadas:
                    desl |= ids_v - ligadas
    blocos = []
    for r in m["M02"]:
        i = r["id"]
        if r["item_modelo"] == "OU" or i in desl or r["condicao_inclusao"].startswith(("Não entra", "Nunca")):
            continue
        if not r["condicao_inclusao"].startswith(("SE ", "Acompanha", "Opcional")) or i in liga:
            blocos.append(i)
    blocos = sem_orfaos(blocos, lista)
    # grupos de alternativas ativos (regra escrita aqui, independente da coluna grupo_ativo_expr do M02)
    ativos = {"GA-01", "GA-02", "GA-04", "GA-05", "GA-06", "GA-07", "GA-08", "GA-09", "GA-10"}
    if todas.get("WZ-49") == "SIM":
        ativos.add("GA-03")
    if todas.get("WZ-43") != "CONTRATO":
        ativos |= {"GA-11", "GA-12", "GA-13"}
    bloq = bloqueios_grupo(m, blocos, ativos)
    # dados para M08 e M10
    ent = montar_entrada(cod)
    g = {wzv(k): ([x for x in v.split(";") if x] if multipla.get(k) else v) for k, v in todas.items()}
    g.update(ent["checklist"])
    g.update(ent["variaveis"])
    g.update(via.get("var", {}))
    g.update(ent["metadados"])
    g["parametros"] = VALORES
    vud = {}
    for it in itens:
        mesmo = [x for x in itens if (x["grupo"] and x["grupo"] == it["grupo"]) or x is it]
        vud[it["numero"]] = sum(dec(x["quantidade"]) * dec(x["valor_unitario"]) for x in mesmo)
    base_itens = []
    for it in itens:
        x = {k: v for k, v in it.items() if k != "excecao"}
        x["tratamento_me_epp"] = trat.get(it["numero"])
        x["valor_unidade_disputa"] = vud[it["numero"]]
        pct = cen["pct_cota"]
        x["cota_calculada"] = int(dec(it["quantidade"]) * dec(pct) / 100) if pct is not None else None
        x["quantidade_cota"] = x["cota_calculada"] if x["tratamento_me_epp"] == "COTA" else None
        base_itens.append(x)
    g["itens"] = com_contexto({k: v for k, v in g.items() if k != "itens"}, base_itens)
    sets = [r["id"] for r in m["M08"] if r["condicao_expr"] and jl(json.loads(r["condicao_expr"]), g)]
    vals = [r["id"] for r in m["M10"] if r["condicao_expr"] and jl(json.loads(r["condicao_expr"]), g)]
    r_dep = dict(todas)
    r_dep.update(ent["checklist"])
    sem = [r["id"] for r in m["M04"] if r["id"] not in DERIVADAS and aplica_texto(r["depende_de"], r_dep)
           and vazio(todas.get(r["id"]))]
    ref = {"derivadas": {k: derivadas[k] for k in sorted(derivadas)},
           "tratamento_me_epp": {str(k): v for k, v in sorted(trat.items())},
           "via_checklist": {k: v for k, v in via.get("wz", {}).items()}}
    return {"blocos": blocos, "clausulas_m08": sets, "validacoes_m10": vals, "perguntas_sem_resposta": sem,
            "bloqueios_grupo_alternativas": bloq}, ref


# =========================================================================== caminho das expressões
def por_item_ids(m11):
    return {"CK_" + r["id"][3:].replace("-", "_").replace(".", "_") for r in m11 if r["por_item"] == "S"}


def contexto_item(g, it, todos, por_item):
    """item com as globais; respostas de pergunta por item: só a ligada ao item."""
    ctx = {k: v for k, v in g.items() if k != "itens" and not (k in por_item or k.removesuffix("_texto") in por_item)}
    ctx.update({k: v for k, v in it.items() if k != "respostas_por_item"})
    ctx.update(it.get("respostas_por_item", {}))
    return ctx


def itens_contexto(g, itens, por_item):
    return [contexto_item(g, it, itens, por_item) for it in itens]


def juntar(atual, novo, tipo):
    if vazio(atual):
        return novo
    if tipo == "TEXTO":
        return f"{atual}\n{novo}" if not isinstance(atual, list) else atual + [novo]
    if tipo in ("LISTA", "TABELA"):
        a = atual if isinstance(atual, list) else [atual]
        return a + (novo if isinstance(novo, list) else [novo])
    return atual if atual == novo else {"conflito": [atual, novo]}


def caminho_expr(m, ent):
    tipo5 = {r["id"].replace("-", "_"): r["tipo_dado"] for r in m["M05"]}
    por_item = por_item_ids(m["M11"])
    g = {}
    g.update(ent["checklist"])
    g.update(ent["variaveis"])
    g.update(ent["metadados"])
    g.update(ent["wizard"])
    g["parametros"] = VALORES
    itens = [copy.deepcopy(i) for i in ent["itens"]]
    dados_entrada = set(ent["wizard"]) | set(ent["variaveis"])
    attr_entrada = [set(i) for i in itens]
    preenchido, conflitos, sugestoes = {}, [], {}
    for r in m["M11"]:
        n = "CK_" + r["id"][3:].replace("-", "_").replace(".", "_")
        if vazio(g.get(n)):
            continue
        if r["condicional_expr"] and not jl(json.loads(r["condicional_expr"]), dict(g, itens=itens_contexto(g, itens, por_item))):
            continue
        for col, alvo in (("preenche_expr", "pre"), ("sugere_expr", "sug")):
            if not r[col]:
                continue
            for dest, ex in json.loads(r[col]).items():
                if dest.startswith("itens."):
                    a = dest[6:]
                    for k, it in enumerate(itens):
                        v = jl(ex, dict(contexto_item(g, it, itens, por_item),
                                        itens=itens_contexto(g, itens, por_item)))
                        if v is None:
                            continue
                        if alvo == "sug":
                            sugestoes.setdefault(f"item {it['numero']}.{a}", []).append((r["id"], v))
                        elif a not in attr_entrada[k]:
                            it[a] = v
                    continue
                v = jl(ex, dict(g, itens=itens_contexto(g, itens, por_item)))
                if v is None:
                    continue
                if alvo == "sug":
                    sugestoes.setdefault(dest, []).append((r["id"], v))
                    continue
                if dest in dados_entrada:
                    continue
                if dest.startswith("WZ_"):
                    if dest in preenchido and preenchido[dest] != v:
                        conflitos.append((dest, preenchido[dest], v, r["id"]))
                        continue
                    preenchido[dest] = v
                    g[dest] = v
                else:
                    g[dest] = juntar(g.get(dest), v, tipo5.get(dest, "TEXTO"))
    for dest, *_ in conflitos:
        g.pop(dest, None)
        preenchido.pop(dest, None)
    # M05: atributos de item, depois globais, na ordem de cálculo
    calc = sorted((r for r in m["M05"] if r["calculo_expr"]), key=lambda r: int(r["calculo_ordem"]))
    for r in calc:
        ex = json.loads(r["calculo_expr"])
        if r["nome"].startswith("tabela_itens."):
            a = r["nome"].split(".", 1)[1]
            novos = []
            for it in itens:
                grupo = [x for x in itens if (it.get("grupo") and x.get("grupo") == it.get("grupo")) or x is it]
                ctx = contexto_item(g, it, itens, por_item)
                ctx["itens_do_grupo"] = itens_contexto(g, grupo, por_item)
                ctx["itens"] = itens_contexto(g, itens, por_item)
                novos.append(jl(ex, ctx))
            for it, v in zip(itens, novos):
                it[a] = v
        else:
            g[r["id"].replace("-", "_")] = jl(ex, dict(g, itens=itens_contexto(g, itens, por_item)))
    # M04: derivadas
    for r in m["M04"]:
        if r["calculo_expr"]:
            g[wzv(r["id"])] = jl(json.loads(r["calculo_expr"]), dict(g, itens=itens_contexto(g, itens, por_item)))
    d = dict(g, itens=itens_contexto(g, itens, por_item))
    sem = []
    for r in m["M04"]:
        if r["id"] in DERIVADAS:
            continue
        aplica = True if not r["depende_de_expr"] else bool(jl(json.loads(r["depende_de_expr"]), d))
        if aplica and vazio(g.get(wzv(r["id"]))):
            sem.append(r["id"])
    blocos = [r["id"] for r in m["M02"] if r["item_modelo"] != "OU" and jl(json.loads(r["condicao_expr"]), d)]
    blocos = sem_orfaos(blocos, [r["id"] for r in m["M02"]])
    ativos = set()
    for r in m["M02"]:
        if r["grupo_ativo_expr"] and jl(json.loads(r["grupo_ativo_expr"]), d):
            ativos.add(r["grupo_alternativa"].split(" ")[0])
    bloq = bloqueios_grupo(m, blocos, ativos)
    sets = [r["id"] for r in m["M08"] if r["condicao_expr"] and jl(json.loads(r["condicao_expr"]), d)]
    vals = [r["id"] for r in m["M10"] if r["condicao_expr"] and jl(json.loads(r["condicao_expr"]), d)]
    extra = {"dados": d, "variaveis": {k: v for k, v in g.items() if k.startswith("VAR_")},
             "preenchido_pelo_checklist": preenchido, "conflitos": conflitos, "sugestoes": sugestoes,
             "derivadas": {k: g.get(wzv(k)) for k in sorted(DERIVADAS)},
             "itens": [{a: it.get(a) for a in ("numero", "tratamento_me_epp", "valor_unidade_disputa", "cota_calculada",
                                                 "quantidade_cota",
                                                 "perecivel", "exige_amostra", "grupo", "faixa_temperatura",
                                                 "garantia_minima_meses", "validade_minima", "controle_especial",
                                                 "categoria")} for it in itens]}
    return {"blocos": blocos, "clausulas_m08": sets, "validacoes_m10": vals, "perguntas_sem_resposta": sem,
            "bloqueios_grupo_alternativas": bloq}, extra


# =========================================================================== gravação e conferência
NOMES_CURTOS = {cod: nome.split(" ", 1)[1] for cod, nome in CODIGOS.items()}


def com_texto(m, obt, extra):
    """Fase 13: monta o texto (lacunas_mapa, tabela_colunas e marcadores do M08) e acrescenta texto_sem_lacuna: blocos
    e cláusulas da minuta, na ordem, que saem sem nenhuma lacuna com as entradas do cenário."""
    textos, lac, ins = montar_minuta(m["M02"], m["M08"], obt["blocos"], obt["clausulas_m08"], extra["dados"])
    obt["texto_sem_lacuna"] = [k for k in textos if not lac[k]]
    return textos, lac, ins


def simular(m, ent):
    """caminho das expressões com a montagem do texto (o que o motor entrega)."""
    obt, extra = caminho_expr(m, ent)
    com_texto(m, obt, extra)
    return obt


def comparar(esp, obt):
    dif = []
    for k in CHAVES_ESPERADO:
        if k not in esp:
            continue
        if esp.get(k) != obt.get(k):
            a, b = esp.get(k) or [], obt.get(k) or []
            dif.append(f"{k}: faltam {[x for x in a if x not in b][:10]}, sobram {[x for x in b if x not in a][:10]}"
                       + ("" if set(a) != set(b) else " (só a ordem)"))
    return dif


def gerar(pasta):
    m = carregar(pasta)
    saida = Path(pasta) / "cenarios"
    saida.mkdir(exist_ok=True)
    total = 0
    for cod in sorted(CODIGOS, key=lambda c: int(c[1:])):
        esp, ref = caminho_texto(m, cod)
        ent = montar_entrada(cod)
        obt, extra = caminho_expr(m, ent)
        textos, lac, ins = com_texto(m, obt, extra)
        # o caminho do texto não monta texto: texto_sem_lacuna vem do caminho das expressões com a montagem do f13
        esp["texto_sem_lacuna"] = obt["texto_sem_lacuna"]
        dif = comparar(esp, obt)
        sim_nao = [(t, f, v) for t, f, v in ins if any(str(x).strip().upper() in ("SIM", "NÃO", "NAO")
                                                      for x in (v if isinstance(v, list) else [v]))]
        if sim_nao:
            dif.append(f"Sim/Não no texto: {sim_nao[:5]}")
        pre_esp = {wzv(k): v for k, v in VIA.get(cod, {}).get("wz", {}).items()}
        if extra["preenchido_pelo_checklist"] != pre_esp:
            dif.append(f"WZ preenchidas pelo checklist: {extra['preenchido_pelo_checklist']} x esperado {pre_esp}")
        for n, attrs in VIA.get(cod, {}).get("itens", {}).items():
            it = next(i for i in extra["itens"] if i["numero"] == n)
            for a, v in attrs.items():
                if it.get(a) != v:
                    dif.append(f"item {n}.{a} = {it.get(a)}, esperado {v}")
        for k, v in VIA.get(cod, {}).get("var", {}).items():
            if extra["variaveis"].get(k) != v:
                dif.append(f"{k} = {extra['variaveis'].get(k)}, esperado {v} (preenchido pelo checklist)")
        if extra["conflitos"]:
            dif.append(f"conflitos: {extra['conflitos']}")
        total += len(dif)
        doc = {"id": cod, "descricao": NOMES_CURTOS[cod],
               "observacao": "Dados fictícios de teste. Gerado por f10_simulador.py (caminho do texto); a reprodução "
                             "pelas colunas _expr é conferida pelo f9_testes.py.",
               "entrada": ent, "esperado": esp,
               "referencia": dict(ref, preenchido_pelo_checklist=extra["preenchido_pelo_checklist"],
                                  texto_montado={k: v for k, v in textos.items()
                                                 if k.startswith("SET-") or k in COM_MARCADOR(m)},
                                  lacunas_do_texto={k: v for k, v in lac.items() if v},
                                  sugestoes={k: v for k, v in extra["sugestoes"].items()},
                                  itens_calculados=extra["itens"])}
        (saida / f"{cod}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1, default=json_num) + "\n",
                                           encoding="utf-8")
        print(f"{cod}: {len(esp['blocos'])} blocos ({len(esp['texto_sem_lacuna'])} trechos sem lacuna), "
              f"M08 {esp['clausulas_m08']}, M10 {esp['validacoes_m10']}, "
              f"sem resposta {len(esp['perguntas_sem_resposta'])}; preenchidas pelo checklist "
              f"{extra['preenchido_pelo_checklist']}" + (" | DIFERENÇAS: " + " || ".join(dif) if dif else ""))
    print(f"TOTAL DE DIFERENÇAS: {total}")
    return total


def reproduzir(pasta, prefixos=("C",)):
    m = carregar(pasta)
    res = {}
    for f in sorted((Path(pasta) / "cenarios").glob("*.json")):
        doc = json.loads(f.read_text(encoding="utf-8"))
        if not doc["id"].startswith(prefixos):
            continue
        obt, extra = caminho_expr(m, doc["entrada"])
        com_texto(m, obt, extra)
        res[doc["id"]] = comparar(doc["esperado"], obt)
    return res


if __name__ == "__main__":
    if sys.argv[1] == "gerar":
        sys.exit(1 if gerar(sys.argv[2]) else 0)
    r = reproduzir(sys.argv[2])
    for k, v in r.items():
        print(k, "OK" if not v else v)
