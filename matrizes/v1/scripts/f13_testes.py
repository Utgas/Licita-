#!/usr/bin/env python3
"""Testes da Fase 13 (chamados pelo f9_testes.py): lacunas_mapa, tabela_colunas, inserção do M08, Sim/Não do M11,
revisão que destaca x pergunta que bloqueia, VAR-160 e montagem do texto nos cenários.

testes(pasta, M) devolve uma lista de (ok, mensagem).
"""
import copy
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f10_simulador as sim  # noqa: E402
from f11_checklist import casos_pergunta  # noqa: E402
from f13_texto import Montagem, montar_minuta  # noqa: E402
from jlogic import avaliar  # noqa: E402

GERAIS = {"var", "==", "!=", "!", "!!", "and", "or", "if", "in", "merge", "some", "none", "<=", ">"}
ACOES = {"PREENCHER", "ESCOLHA", "OPCIONAL", "TABELA", "REMOVER", "MANTER", "EQUIPE"}
FORMATOS = {"TEXTO", "NUMERO_EXTENSO", "PERCENTUAL_EXTENSO", "PERCENTUAL_2", "MOEDA", "MOEDA_POR_EXTENSO", "DATA", "DIA",
            "MES_EXTENSO", "ANO", "LISTA_TEXTO", "LISTA_LINHAS", "MINUSCULA", "INICIAL_MINUSCULA", "ITEM", "POR_ITEM"}


def _ck(rid):
    return "CK_" + rid[3:].replace("-", "_").replace(".", "_")


def operadores(x, out):
    if isinstance(x, dict):
        for k, v in x.items():
            out.add(k)
            operadores(v, out)
    elif isinstance(x, list):
        for v in x:
            operadores(v, out)
    return out


def posicoes(texto, m):
    out, i = [], 0
    while True:
        p = texto.find(m, i)
        if p < 0:
            return out
        out.append(p)
        i = p + len(m)


def testes(pasta, M):
    out = []
    reg = lambda ok, msg: out.append((ok, msg))  # noqa: E731
    m02 = M["M02"]
    ids02 = {r["id"] for r in m02}
    vars5 = {r["id"].replace("-", "_") for r in M["M05"]}
    wz = {r["id"].replace("-", "_") for r in M["M04"]}
    cks = {_ck(r["id"]) for r in M["M11"]}
    attr = {r["nome"].split(".", 1)[1] for r in M["M05"] if r["nome"].startswith("tabela_itens.")}

    def fonte_ok(f):
        if f is None:
            return True
        if f.startswith("itens."):
            return f[6:] in attr
        return f in vars5 or f in wz or f in cks

    # ------------------------------------------------ 1. lacunas_mapa: todo marcador, na ordem e na quantidade do texto
    sem_mapa, ordem, fontes, acoes, equipe_sem_motivo, ops_ruins, formatos = [], [], [], [], [], [], []
    n_marc = 0
    for r in m02:
        marc = [x for x in r["lacunas"].split(" | ") if x] if r["lacunas"].strip() else []
        if not marc:
            if r["lacunas_mapa"]:
                sem_mapa.append(f"{r['id']} (mapa sem marcador)")
            continue
        if not r["lacunas_mapa"]:
            sem_mapa.append(r["id"])
            continue
        mapa = json.loads(r["lacunas_mapa"])
        n_marc += len(mapa)
        if sorted(x["marcador"] for x in mapa) != sorted(marc):
            ordem.append(f"{r['id']}: quantidade")
            continue
        t, ult = r["texto_literal"], -1
        for x in mapa:
            ps = posicoes(t, x["marcador"])
            if not isinstance(x.get("ocorrencia"), int) or x["ocorrencia"] > len(ps) or ps[x["ocorrencia"] - 1] <= ult:
                ordem.append(f"{r['id']}: {x['marcador']}")
                break
            ult = ps[x["ocorrencia"] - 1]
        for x in mapa:
            if not fonte_ok(x.get("fonte")) or (x.get("unidade") and x["unidade"] not in vars5):
                fontes.append(f"{r['id']}: {x.get('fonte')}")
            if x.get("acao", "PREENCHER") not in ACOES or (x.get("fonte") is None and x.get("acao", "PREENCHER")
                                                            == "PREENCHER"):
                acoes.append(f"{r['id']}: {x.get('acao')}")
            if x.get("acao") == "EQUIPE" and (x.get("fonte") is not None or not x.get("comentario")):
                equipe_sem_motivo.append(r["id"])
            if x.get("formato", "TEXTO") not in FORMATOS:
                formatos.append(f"{r['id']}: {x.get('formato')}")
            for ex in [x.get("quando")] + [o["quando"] for o in x.get("opcoes", [])]:
                if isinstance(ex, (dict, list)) and operadores(ex, set()) - GERAIS:
                    ops_ruins.append(r["id"])
    reg(not sem_mapa, f"M02.lacunas_mapa em todos os {sum(1 for r in m02 if r['lacunas'].strip())} blocos com marcador "
        f"({n_marc} marcadores)" + (f" | {sem_mapa}" if sem_mapa else ""))
    reg(not ordem, "M02.lacunas_mapa: todo marcador do texto_literal (coluna lacunas) aparece no mapa, na mesma ordem do "
        "texto e na mesma quantidade (ocorrência sem sobreposição)" + (f" | {ordem[:6]}" if ordem else ""))
    reg(not fontes and not acoes and not equipe_sem_motivo and not formatos and not ops_ruins,
        "M02.lacunas_mapa: fonte existe (VAR, WZ, CK ou atributo de item), ação e formato conhecidos, fonte null só com "
        "ação e EQUIPE sempre com motivo, condições só com operadores gerais"
        + (f" | {(fontes + acoes + equipe_sem_motivo + formatos + ops_ruins)[:8]}" if fontes or acoes or equipe_sem_motivo
           or formatos or ops_ruins else ""))
    # ------------------------------------------------ 2. tabela_colunas
    tabs = {r["id"]: json.loads(r["tabela_colunas"]) for r in m02 if r["tabela_colunas"]}
    esperadas = {"TR-1.1.TAB1", "TR-1.1.1.TAB1", "TR-1.1.1.TAB2", "TR-1.1.1.TAB3", "TR-5.2.TAB1"}
    ruins = []
    for b, tc in tabs.items():
        cab = [c["cabecalho"] for c in tc["colunas"]]
        texto = next(r["texto_literal"] for r in m02 if r["id"] == b)
        prim = [c.strip() for c in texto.splitlines()[1 if texto.splitlines()[0].endswith(":") else 0].split("|")]
        if cab != prim:
            ruins.append(f"{b}: cabeçalhos {cab} x modelo {prim}")
        for c in tc["colunas"]:
            if c.get("fonte") and not fonte_ok(c["fonte"]):
                ruins.append(f"{b}: {c['fonte']}")
            for k in c.get("complementos", []):
                if not fonte_ok(k["fonte"]):
                    ruins.append(f"{b}: {k['fonte']}")
    t1 = tabs.get("TR-1.1.TAB1", {})
    cota = t1.get("linha_cota", {})
    reg(set(tabs) == esperadas and not ruins and cota.get("quando") and set(cota.get("valores", {})) ==
        {c["cabecalho"] for c in t1.get("colunas", [])} and t1.get("orcamento_sigiloso", {}).get("quando"),
        f"M02.tabela_colunas nas {len(tabs)} tabelas que vêm dos itens ou de tabelas do wizard, com os cabeçalhos do "
        f"modelo na ordem, fontes existentes, orçamento sigiloso (NE-004) e a linha de cota reservada com valor para "
        f"cada coluna" + (f" | {ruins}" if ruins else ""))
    # ------------------------------------------------ 3. M08: inserir_apos e nivel
    ruins8 = []
    for r in M["M08"]:
        if r["documento"] not in ("TR", "AMBOS"):
            continue
        if r["inserir_apos"] not in ids02 or r["nivel"] not in ("MESMO_NIVEL", "SUBITEM", "PREENCHE_BLOCO"):
            ruins8.append(r["id"])
        for parte in [p.strip() for p in r["inserir_apos_alternativo"].split(";") if p.strip()]:
            mm = re.fullmatch(r"(TR-[\w.\-]+) \((MESMO_NIVEL|SUBITEM)\)", parte)
            if not mm or mm.group(1) not in ids02:
                ruins8.append(f"{r['id']}: {parte}")
        ref = next(x for x in m02 if x["id"] == r["inserir_apos"]) if r["inserir_apos"] in ids02 else None
        if ref and not r["inserir_apos_alternativo"] and r["nivel"] != "PREENCHE_BLOCO" and ref["condicao_expr"] != "true":
            ruins8.append(f"{r['id']}: bloco pode faltar sem alternativo")
        if r["inserir_apos"] in ("TR-5.12", "TR-5.13"):
            ruins8.append(f"{r['id']}: entre o TR-5.12 e o TR-5.14 ('subitem anterior')")
    reg(not ruins8, "M08: inserir_apos é bloco do M02, nivel MESMO_NIVEL, SUBITEM ou PREENCHE_BLOCO, alternativo quando o "
        "bloco pode faltar, nada entre o TR-5.12 e o TR-5.14" + (f" | {ruins8}" if ruins8 else ""))
    # ------------------------------------------------ 4. M11: Sim/Não em variável que não é Sim/Não
    m05t = {r["id"].replace("-", "_"): r["tipo_dado"] for r in M["M05"]}
    copia = []
    for r in M["M11"]:
        o = [x.strip() for x in r["opcoes"].split("campos:")[0].split(";") if x.strip()]
        if not ("Sim" in o and any(x.startswith("Não") for x in o)) or not r["preenche_expr"]:
            continue
        for d, ex in json.loads(r["preenche_expr"]).items():
            if ex == {"var": _ck(r["id"])} and d in m05t:
                copia.append(f"{r['id']} -> {d} ({m05t[d]})")
    reg(not copia, "M11: nenhuma pergunta Sim/Não copia a opção para variável de texto, tabela, lista ou número "
        "(critério da Fase 13; antes, 65)" + (f" | {copia[:6]}" if copia else ""))
    # ------------------------------------------------ 5. revisão: falta de resposta destaca, não pergunta nem bloqueia
    ruins11, n = [], 0
    for cid, lst in casos_pergunta(M["M11"]).items():
        r = next(x for x in M["M11"] if x["id"] == cid)
        ex = json.loads(r["revisao_pergunta_expr"])
        for dados, dispara in lst:
            n += 1
            d = dict(dados, parametros=sim.VALORES)
            d.setdefault("itens", [])
            if bool(avaliar(ex, d)) != dispara:
                ruins11.append(f"{cid}: {dados} -> {not dispara}")
    sem_perg = [r["id"] for r in M["M11"] if bool(r["revisao_pergunta"]) != bool(r["revisao_pergunta_expr"])]
    destaca = sum(1 for r in M["M11"] if r["revisao_expr"])
    reg(not ruins11 and not sem_perg, f"M11.revisao_pergunta_expr: {sum(1 for r in M['M11'] if r['revisao_pergunta_expr'])} "
        f"perguntas que bloqueiam, {n} casos (pergunta sem resposta nunca bloqueia; duas marcas e dúvidas específicas "
        f"bloqueiam); revisao_expr continua destacando em {destaca}" + (f" | {(ruins11 + sem_perg)[:6]}" if ruins11 or
                                                                        sem_perg else ""))
    # ------------------------------------------------ 6. VAR-160 só com percentual de cota
    v160 = json.loads(next(r for r in M["M05"] if r["id"] == "VAR-160")["calculo_expr"])
    sem = avaliar(v160, {"quantidade": 10, "parametros": sim.VALORES})
    com = avaliar(v160, {"quantidade": 10, "VAR_057": 25, "parametros": sim.VALORES})
    reg(sem is None and com == 2, f"VAR-160: sem VAR-057 fica vazia ({sem}); com 25% de 10 dá {com}")
    # ------------------------------------------------ 7. montagem do texto: casos fixos (dados fictícios)
    por_id = {r["id"]: r for r in m02}

    def bloco(b, dados):
        return Montagem(dict(dados, parametros=sim.VALORES)).bloco(por_id[b])

    casos = [
        ("TR-9.1", {"WZ_02": "PREGAO", "WZ_03": "MENOR_PRECO"},
         "na modalidade PREGÃO, sob a forma ELETRÔNICA, com adoção do critério de julgamento pelo MENOR PREÇO."),
        ("TR-1.5", {"VAR_034": 12, "VAR_163": "MESES", "VAR_035": "assinatura do contrato"},
         "é de 12 (doze) meses contados do(a) assinatura do contrato, na forma"),
        ("TR-12.1", {"WZ_40": "NAO"}, "não são classificadas como sigilosas."),
        ("TR-12.1", {"WZ_40": "SIM"}, "sigilosas exceto o custo estimado da contratação, que possui caráter sigiloso até o "
                                      "julgamento das propostas."),
        ("TR-1.1", {"VAR_008": "material de teste", "WZ_08": "NAO"}, "Aquisição de material de teste, nos termos"),
        ("TR-1.1", {"VAR_008": "equipamento de teste", "WZ_08": "SIM", "VAR_009": ["instalação", "treinamento"]},
         "Aquisição de equipamento de teste, incluindo instalação e treinamento, nos termos"),
        ("TR-5.4.1", {"VAR_065": "12 meses"}, "não poderá ser inferior a 12 meses."),
        ("TR-5.4.1", {"VAR_065": "Dois terços do prazo total"},
         "não poderá ser inferior a dois terços do prazo total recomendado pelo fabricante."),
        ("TR-5.4.1", {"VAR_065": "75% do prazo total"},
         "não poderá ser inferior a 75% do prazo total recomendado pelo fabricante."),
        ("TR-4.25", {"VAR_055": 5, "VAR_056": "ANUAL"}, "correspondente a 5% (cinco por cento) do valor anual da"),
        ("TR-10.1", {"VAR_014": 1234.56, "VAR_089": "ITEM_1.1"},
         "é de R$ 1.234,56 (mil duzentos e trinta e quatro reais e cinquenta e seis centavos), conforme custos unitários "
         "apostos na tabela contida no item 1.1 acima."),
        ("TR-9.3", {"VAR_111": "INTEGRAL"}, "O fornecimento do objeto será integral."),
        ("TR-8.41", {"VAR_078": "IPCA"}, "do índice IPCA, exclusivamente"),
        ("TR-ASSIN.01", {"VAR_005": "Cidade-UF", "VAR_097": "23/10/2026"}, "Cidade-UF, 23 de outubro de 2026."),
        ("TR-AI-3.1.8.1", {}, "A Administração terá o prazo de 1 (um) mês, a contar"),
        ("TR-9.4.1", {"VAR_032": "ITEM_DO_TR"}, "Valores unitários: conforme tabela constante no item 1.1 deste Termo"),
        ("TR-11.2.II", {"VAR_091": {"fonte_recursos": "0100"}}, "Fonte de recursos: 0100;"),
        ("TR-7.2.4.7", {"VAR_071": {"a": {"minimo": 1, "maximo": 5}}, "WZ_33": "NAO"},
         "de 1% (um por cento) a 5% (cinco por cento) do valor da contratação."),
        ("TR-AI-4.1.1", {"WZ_43": "SUBSTITUTIVO_ENTREGA_IMEDIATA"}, "com uma versão em português;"),
    ]
    falhas = []
    for b, dados, trecho in casos:
        t, lac, _ = bloco(b, dados)
        if trecho not in t or lac:
            falhas.append(f"{b}: {t[:160]} | lacunas {lac}")
    t, lac, _ = bloco("TR-1.5", {"VAR_034": 12})
    if "[[LACUNA" not in t:
        falhas.append("TR-1.5 sem unidade deveria ficar com lacuna")
    # tabela do item 1.1 com cota e com orçamento sigiloso
    itens = [{"numero": 1, "especificacao": "Item A", "unidade_medida": "unidade", "catmat": "000000",
              "quantidade_principal": 75, "valor_unitario": 10, "valor_total": 750, "tratamento_me_epp": "COTA",
              "quantidade_cota": 25, "valor_total_cota": 250}]
    t, lac, _ = bloco("TR-1.1.TAB1", {"itens": itens, "VAR_057": 25, "WZ_40": "NAO"})
    if ("1 | Item A | 000000 | unidade | 75 | R$ 10,00 | R$ 750,00" not in t or
            "2 | Idem ao Item 1 – Cota reservada para ME/EPP em 25,00% | 000000 | unidade | 25 | R$ 10,00 | R$ 250,00"
            not in t or lac):
        falhas.append(f"TR-1.1.TAB1 com cota: {t} | {lac}")
    t, lac, _ = bloco("TR-1.1.TAB1", {"itens": itens, "VAR_057": 25, "WZ_40": "SIM"})
    if t.count("SIGILOSO") != 4:
        falhas.append(f"TR-1.1.TAB1 sigiloso: {t}")
    # série de lista: dois elementos em três blocos
    tx, lc, _ = montar_minuta(m02, M["M08"], ["TR-4.1.1", "TR-4.1.2", "TR-4.1.3"], [],
                              {"VAR_044": ["critério A", "critério B"], "parametros": sim.VALORES})
    if tx != {"TR-4.1.1": "critério A; e", "TR-4.1.2": "critério B."}:
        falhas.append(f"série TR-4.1.x: {tx}")
    reg(not falhas, f"montagem do texto: {len(casos) + 4} casos fixos (escolha, opcional, extenso, moeda, data, série de "
        f"lista com pontuação, tabela com cota e com sigilo, lacuna sem unidade)" + (f" | {falhas[:4]}" if falhas else ""))
    # ------------------------------------------------ 8. cenários: Sim/Não do checklist e texto_sem_lacuna
    m = sim.carregar(str(pasta))
    docs = [json.loads(f.read_text(encoding="utf-8")) for f in sorted((pasta / "cenarios").glob("C*.json"))]
    achados, sem_campo = [], []
    for doc in docs:
        if "texto_sem_lacuna" not in doc["esperado"]:
            sem_campo.append(doc["id"])
        obt, extra = sim.caminho_expr(m, doc["entrada"])
        textos, lac, ins = sim.com_texto(m, obt, extra)
        for trecho, fonte, v in ins:
            for x in (v if isinstance(v, list) else [v]):
                if str(x).strip().upper() in ("SIM", "NÃO", "NAO"):
                    achados.append(f"{doc['id']} {trecho} {fonte}")
    reg(len(docs) == 8 and not sem_campo and not achados,
        f"cenários C1 a C8: esperado.texto_sem_lacuna em todos e nenhum texto da minuta com 'Sim' ou 'Não' vindo de "
        f"resposta do checklist" + (f" | {sem_campo or achados[:6]}" if sem_campo or achados else ""))
    # controle negativo: a regra antiga (resposta copiada) põe "Sim" no texto de algum cenário
    mm = copy.deepcopy(m)
    for r in mm["M11"]:
        if r["id"] == "CK-P-16.6":
            r["preenche_expr"] = json.dumps({"VAR_150": {"var": "CK_P_16_6"}})
    pega = False
    for doc in docs:
        obt, extra = sim.caminho_expr(mm, doc["entrada"])
        _, _, ins = sim.com_texto(mm, obt, extra)
        pega |= any(str(v) == "Sim" for _, _, v in ins)
    reg(pega, "controle negativo: com a cópia antiga da CK-P-16.6 para a VAR-150, o teste de Sim/Não acusa o 'acompanhado "
        "de Sim' da SET-19 em algum cenário")
    return out
