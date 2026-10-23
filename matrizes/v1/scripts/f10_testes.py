#!/usr/bin/env python3
"""Testes da Fase 10 (chamados pelo f9_testes.py): JSON Logic de todas as colunas *_expr, M12, cenários de ouro e casos
de reprodução, números de processo e correções do compilador.

testes(pasta, M) devolve uma lista de (ok, mensagem). M é o dicionário de matrizes lido pelo f9_testes.py.
"""
import copy
import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f10_simulador as sim  # noqa: E402

PERMITIDOS = {"var", "==", "!=", "!", "!!", "and", "or", "if", "in", "merge", "some", "none", "<=", ">"}
P31 = {"reduce", "+", "*", "-", "/", "%"}  # registrados na P31; só em M04.calculo_expr e M05.calculo_expr
ONDE_P31 = {("M04", "calculo_expr"), ("M05", "calculo_expr")}
METADADOS = ("textos_livres", "importacao.", "checklist.")
NUP = re.compile(r"\b\d{5}\.\d{6}/\d{4}-\d{2}\b|\b\d{17}\b")
NUP_FICTICIO = "00000.000000/0000-00"


def _ck(rid):
    return "CK_" + rid[3:].replace("-", "_").replace(".", "_")


def testes(pasta, M):
    out = []
    reg = lambda ok, msg: out.append((ok, msg))  # noqa: E731
    m12 = M["M12"]
    nomes_par = {r["nome"] for r in m12}
    attr_item = {r["nome"].split(".", 1)[1] for r in M["M05"] if r["nome"].startswith("tabela_itens.")}
    globais = ({r["id"].replace("-", "_") for r in M["M04"]} | {r["id"].replace("-", "_") for r in M["M05"]}
               | {_ck(r["id"]) for r in M["M11"]})
    opcoes = set()
    for r in M["M04"]:
        opcoes |= {o.strip() for o in r["opcoes"].split(";")}
    for r in M["M11"]:
        opcoes |= {o.strip() for o in r["opcoes"].split("campos:")[0].split(";")}
    erros, fora_p31, literais = [], [], []
    n_expr = 0

    def var_ok(nome, ctx):
        nome = str(nome)
        if nome.startswith("parametros."):
            return nome[11:] in nomes_par
        if nome.startswith(METADADOS) or nome in ("itens",):
            return True
        if ctx == "reduce":
            return nome == "accumulator" or (nome.startswith("current.") and nome[8:] in attr_item)
        base = re.sub(r"_(?:texto|numero)$", "", nome)
        if base in globais:
            return True
        if ctx == "item":
            # {"var": ""} dentro de some/none é o próprio elemento (lista de textos, ex.: VAR_085 na VAL-029)
            return nome in attr_item or nome in ("itens_do_grupo", "")
        return False

    def visita(e, onde, mat, col, ctx):
        nonlocal literais
        if isinstance(e, list):
            for x in e:
                visita(x, onde, mat, col, ctx)
            return
        if isinstance(e, bool) or e is None:
            return
        if isinstance(e, (int, float)):
            if e not in (0, 1):
                literais.append(f"{onde}: número {e}")
            return
        if isinstance(e, str):
            if re.search(r"\d", e) and e not in opcoes and not re.fullmatch(r"(TR|SET|ETP)-[A-Za-z0-9.\-]+", e) and \
                    not re.fullmatch(r"CK-[CPX]-(?:CAB\.\d{2}|\d{1,2}(?:\.\d{1,2})?)", e):
                literais.append(f"{onde}: texto '{e}'")
            return
        if not isinstance(e, dict) or len(e) != 1:
            erros.append(f"{onde}: objeto inválido")
            return
        op, a = next(iter(e.items()))
        if op not in PERMITIDOS:
            if op in P31 and (mat, col) in ONDE_P31:
                fora_p31.append(op)
            else:
                erros.append(f"{onde}: operador {op}")
        if op == "var":
            nome = a[0] if isinstance(a, list) else a
            if not var_ok(nome, ctx):
                erros.append(f"{onde}: variável {nome}")
            if isinstance(a, list) and len(a) > 1:
                visita(a[1], onde, mat, col, ctx)
            return
        if op in ("some", "none", "all"):
            visita(a[0], onde, mat, col, ctx)
            visita(a[1], onde, mat, col, "item")
            return
        if op == "reduce":
            visita(a[0], onde, mat, col, ctx)
            visita(a[1], onde, mat, col, "reduce")
            visita(a[2:], onde, mat, col, ctx)
            return
        visita(a, onde, mat, col, ctx)

    def literal_de_opcao(rid, ex, mat):
        """M11: número só como tradução de opção da própria pergunta ('36 meses' -> 36)."""
        if mat != "M11":
            return
        ops = [o.strip() for o in next(r for r in M["M11"] if r["id"] == rid)["opcoes"].split(";")]
        txt = json.dumps(ex)
        for n in re.findall(r"(?<![\w.\"])(\d+)(?![\w.\"])", txt):
            if int(n) in (0, 1):
                continue
            if not any(o.startswith(n + " ") for o in ops):
                literais.append(f"M11:{rid}: número {n} sem opção correspondente")

    cols = {}
    for k, rows in M.items():
        if rows:
            cols[k] = [c for c in rows[0] if c.endswith("_expr")]
    for k, cs in cols.items():
        for r in M[k]:
            rid = r.get("id") or r.get("bloco_tr")
            for c in cs:
                if not r[c]:
                    continue
                n_expr += 1
                try:
                    ex = json.loads(r[c])
                except json.JSONDecodeError as exc:
                    erros.append(f"{k}:{rid}.{c}: JSON inválido ({exc})")
                    continue
                onde = f"{k}:{rid}.{c}"
                if k == "M11" and c in ("preenche_expr", "sugere_expr"):
                    if not isinstance(ex, dict) or not ex:
                        erros.append(f"{onde}: não é objeto destino -> expressão")
                        continue
                    lit_antes = len(literais)
                    for dest, sub in ex.items():
                        ok_dest = (re.fullmatch(r"WZ_\d{2}", dest) and dest in globais) or \
                                  (re.fullmatch(r"VAR_\d{3}", dest) and dest in globais) or \
                                  (dest.startswith("itens.") and dest[6:] in attr_item)
                        if not ok_dest:
                            erros.append(f"{onde}: destino {dest}")
                        visita(sub, f"{onde}[{dest}]", k, c, "item" if dest.startswith("itens.") else "global")
                    # números que traduzem opção da própria pergunta são permitidos
                    novos = literais[lit_antes:]
                    del literais[lit_antes:]
                    literais += [x for x in novos if not x.split(": número ")[-1].isdigit()]
                    literal_de_opcao(rid, ex, k)
                    continue
                ctx = "item" if (k == "M05" and r["nome"].startswith("tabela_itens.")) else "global"
                visita(ex, onde, k, c, ctx)
    # o "0" da WZ-12 (número de participantes) é resposta, não valor de norma
    literais = [x for x in literais if "texto '0'" not in x]
    reg(not erros, f"JSON Logic: {n_expr} expressões em todas as colunas *_expr, JSON válido, só operadores permitidos e "
        f"variáveis conhecidas (parametros.* no M12)" + (f" | {erros[:8]}" if erros else ""))
    reg(set(fora_p31) <= P31, f"operadores fora da lista só em M04.calculo_expr e M05.calculo_expr e registrados na P31: "
        f"{sorted(set(fora_p31))}")
    reg(not literais, "nenhum número de lei ou valor monetário dentro de expressão (números só 0 e 1 de contagem e "
        "opção literal do checklist; textos com dígito só se forem opção)" + (f" | {literais[:8]}" if literais else ""))
    # --------------------------------------------------------- colunas novas: cobertura e coerência
    sem_dep = [r["id"] for r in M["M04"] if bool(r["depende_de_expr"]) != bool(
        [p for p in r["depende_de"].split(";") if p.strip() and not p.strip().startswith("VAR-")])]
    reg(not sem_dep, "M04: depende_de_expr preenchida exatamente nas perguntas com condição em depende_de"
        + (f" | {sem_dep}" if sem_dep else ""))
    calc4 = sorted(r["id"] for r in M["M04"] if r["calculo_expr"])
    reg(calc4 == ["WZ-09", "WZ-13", "WZ-18", "WZ-20", "WZ-24", "WZ-50"], f"M04: calculo_expr nas 6 derivadas: {calc4}")
    ef = [r["id"] for r in M["M11"] if (r["preenche_expr"] and r["efeito"] != "PREENCHE")
          or (r["sugere_expr"] and r["efeito"] != "SUGERE")]
    cond = [r["id"] for r in M["M11"] if bool(r["condicional"]) != bool(r["condicional_expr"])]
    reg(not ef and not cond, "M11: preenche_expr só em PREENCHE, sugere_expr só em SUGERE, condicional_expr em toda "
        f"condicional ({sum(1 for r in M['M11'] if r['condicional_expr'])})" + (f" | {ef} {cond}" if ef or cond else ""))
    calc5 = [r for r in M["M05"] if r["calculo_expr"]]
    ordens = [int(r["calculo_ordem"]) for r in calc5]
    calculados = {r["nome"].split(".", 1)[1]: int(r["calculo_ordem"]) for r in calc5 if r["nome"].startswith("tabela_itens.")}
    fora_ordem = []
    for r in calc5:
        for a, o in calculados.items():
            if re.search(r'"(?:current\.)?' + a + r'"', r["calculo_expr"]) and o >= int(r["calculo_ordem"]) and \
                    r["nome"] != "tabela_itens." + a:
                fora_ordem.append(f"{r['id']} lê {a}")
    reg(len(set(ordens)) == len(ordens) and not fora_ordem and not [r["id"] for r in M["M05"] if r["calculo_ordem"]
                                                                   and not r["calculo_expr"]],
        f"M05: calculo_expr em {len(calc5)} variáveis, ordem única e cada cálculo só lê atributo já calculado"
        + (f" | {fora_ordem}" if fora_ordem else ""))
    faltam = [a for a in ("catmat", "quantidade", "valor_unitario", "numero") if a not in attr_item]
    reg(not faltam, "M05: atributos de item catmat, quantidade, valor_unitario e numero presentes (achado do compilador)")
    # --------------------------------------------------------- M12
    ruins = [r["id"] for r in m12 if not (r["fonte"] and r["status"] in ("EXTRAIDO", "INFERIDO", "A_VERIFICAR")
                                          and re.fullmatch(r"PAR-\d{2}", r["id"]))]
    sem_uso = [r["nome"] for r in m12 if not r["usado_em"]]
    reg(not ruins and not sem_uso, f"M12: {len(m12)} parâmetros com fonte e status, todos usados por alguma regra"
        + (f" | {ruins} {sem_uso}" if ruins or sem_uso else ""))
    # --------------------------------------------------------- Fase 11
    from jlogic import avaliar as _av
    from parametros import VALORES
    import f11_checklist as f11

    def com_globais(d):
        d = dict(d, parametros=VALORES)
        d["itens"] = [dict({k: v for k, v in d.items() if k != "itens"}, **i) for i in d.get("itens", [])]
        return d
    cs11 = f11.casos(M["M11"])
    ruins11, n11 = [], 0
    for r in M["M11"]:
        if not r["revisao_expr"]:
            continue
        ex = json.loads(r["revisao_expr"])
        lst = cs11.get(r["id"], [])
        if not any(v for _, v in lst) or not any(v is False for _, v in lst):
            ruins11.append(f"{r['id']}: sem caso que dispara e caso que não dispara")
        for dados, esp in lst:
            n11 += 1
            if bool(_av(ex, com_globais(dados))) != esp:
                ruins11.append(f"{r['id']}: {dados} deveria {'disparar' if esp else 'não disparar'}")
    reg(not ruins11, f"M11.revisao_expr: {sum(1 for r in M['M11'] if r['revisao_expr'])} expressões, {n11} casos (cada uma "
        f"dispara e não dispara)" + (f" | {ruins11[:6]}" if ruins11 else ""))
    gerais = [r["id"] for r in M["M11"] if r["revisao_expr"] and re.search(r'"(reduce|\+|\*|-|/|%)":', r["revisao_expr"])]
    reg(not gerais, "M11.revisao_expr só com operadores gerais (sem os de cálculo)")
    compl = [r for r in M["M11"] if r["checklist"] == "COMPLEMENTO"]
    ok_c = len(compl) == 9 and all(re.fullmatch(r"CK-X-\d{2}", r["id"]) and (r["preenche_expr"] or r["sugere_expr"])
                                   and r["condicional_expr"] for r in compl)
    reg(ok_c, f"M11: {len(compl)} complementos do operador (CK-X-01 a CK-X-09, checklist COMPLEMENTO), com condição e "
        f"expressão")
    com = [r["id"] for r in M["M11"] if r["id"] in [f"CK-C-10.{n}" for n in range(1, 12)]
           and (r["efeito"] != "SO_CONTROLE" or r["destinos"] or r["preenche_expr"] or r["sugere_expr"])]
    wz56 = next(r for r in M["M04"] if r["id"] == "WZ-56")["depende_de_expr"]
    s01 = next(r for r in M["M08"] if r["id"] == "SET-01")["condicao_expr"]
    v27 = next(r for r in M["M10"] if r["id"] == "VAL-027")["condicao_expr"]
    reg(not com and wz56 == s01 == v27 == "false", "comodato fora do sistema: CK-C-10.1 a 10.11 só controle; WZ-56, SET-01 e "
        "VAL-027 com expressão false e o motivo no texto" + (f" | {com}" if com else ""))
    # cota zero: VAR-160 e VAL-051
    v51 = json.loads(next(r for r in M["M10"] if r["id"] == "VAL-051")["condicao_expr"])
    m5 = {r["id"]: r for r in M["M05"]}
    item = {"quantidade": 3, "valor_unitario": 40000, "WZ_01": "LICITACAO", "VAR_057": 25, "parametros": VALORES}
    ctx = dict(item)
    for vid in ("VAR-119", "VAR-160", "VAR-113", "VAR-118"):
        ctx["itens_do_grupo"] = [dict(ctx)]
        ctx[m5[vid]["nome"].split(".", 1)[1]] = _av(json.loads(m5[vid]["calculo_expr"]), ctx)
    ctx2 = dict(item, quantidade=9, valor_unitario=15000)
    for vid in ("VAR-119", "VAR-160", "VAR-113", "VAR-118"):
        ctx2["itens_do_grupo"] = [dict(ctx2)]
        ctx2[m5[vid]["nome"].split(".", 1)[1]] = _av(json.loads(m5[vid]["calculo_expr"]), ctx2)
    ok_cz = (ctx["cota_calculada"] == 0 and ctx["tratamento_me_epp"] == "AMPLA" and ctx["quantidade_cota"] is None
             and _av(v51, {"itens": [ctx]}) and ctx2["tratamento_me_epp"] == "COTA" and ctx2["quantidade_cota"] == 2
             and not _av(v51, {"itens": [ctx2]}))
    reg(ok_cz, f"cota zero: 3 x 25% dá cota 0, item em AMPLA e VAL-051 dispara; 9 x 25% dá cota 2, COTA e VAL-051 não "
        f"dispara ({ctx['tratamento_me_epp']}, {ctx2['tratamento_me_epp']})")
    sem_valor = dict(item, valor_unitario=None)
    for vid in ("VAR-119", "VAR-160", "VAR-113"):
        sem_valor["itens_do_grupo"] = [dict(sem_valor)]
        sem_valor[m5[vid]["nome"].split(".", 1)[1]] = _av(json.loads(m5[vid]["calculo_expr"]), sem_valor)
    reg(sem_valor["valor_unidade_disputa"] is None and sem_valor["tratamento_me_epp"] is None,
        "valor ausente: item sem valor_unitario fica sem valor da unidade e sem tratamento ME/EPP (não vira EXCLUSIVO)")
    # limite exato em decimal: soma igual ao limite é EXCLUSIVO; um centavo acima, não
    lim = dict(item, quantidade=3, valor_unitario=26666.67)  # 80000.01
    lim2 = dict(item, quantidade=4, valor_unitario=20000.00)  # 80000.00
    res = []
    for x in (lim2, lim):
        for vid in ("VAR-119", "VAR-160", "VAR-113"):
            x["itens_do_grupo"] = [dict(x)]
            x[m5[vid]["nome"].split(".", 1)[1]] = _av(json.loads(m5[vid]["calculo_expr"]), x)
        res.append(x["tratamento_me_epp"])
    reg(res == ["EXCLUSIVO", "AMPLA"], f"conta exata no limite: 4 x 20.000,00 = limite dá EXCLUSIVO; 3 x 26.666,67 "
        f"(80.000,01) não ({res})")
    tipos = {r["nome"]: r["tipo"] for r in m12}
    reg(all(t in ("numero", "lista", "texto") for t in tipos.values()) and tipos.get("prazo_entrega_referencia") == "numero",
        f"M12: coluna tipo em todas as linhas ({sorted(set(tipos.values()))})")
    ids05 = {r["id"] for r in M["M05"]}
    citados = {v for r in m12 for v in re.findall(r"VAR-\d{3}", r["fonte"] + r["base"])}
    reg(citados <= ids05, f"M12: toda VAR citada na fonte e na base existe no M05 ({sorted(citados)})")
    # --------------------------------------------------------- correções de 23/10/2026 (revisão da Fase 10)
    from jlogic import avaliar
    v29 = json.loads(next(r for r in M["M10"] if r["id"] == "VAL-029")["condicao_expr"])
    casos = [(["atestado pelo período mínimo de 12 meses"], True), (["Período mínimo de execução"], True),
             (["contratos dos últimos 3 anos"], True), (["Últimos exercícios"], True),
             (["fornecimento e instalação de equipamento compatível"], False), ([], False), (None, False),
             (["garantia técnica prestada pelo período mínimo de 12 meses"], False),
             (["Garantia mínima de 12 meses prestada ao equipamento"], False),
             (["garantia prestada nos últimos 2 anos"], True)]
    erros29 = [str(x) for x, esp in casos if bool(avaliar(v29, {"VAR_085": x} if x is not None else {})) != esp]
    reg("some" in json.dumps(v29) and not erros29, "VAL-029: some sobre a VAR_085 (lista) acha 'período mínimo' e "
        "'últimos', com e sem inicial maiúscula, em cada item, sem barrar a duração da garantia já prestada (P25); 10 casos" + (f" | erra em {erros29}" if erros29 else ""))
    p05 = next(r for r in m12 if r["id"] == "PAR-05")
    reg(re.fullmatch(r"\d+", p05["valor"]) and p05["unidade"] == "dias corridos",
        f"PAR-05: valor numérico ({p05['valor']}) com unidade '{p05['unidade']}'")
    # --------------------------------------------------------- cenários
    pc = pasta / "cenarios"
    arqs = {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in sorted(pc.glob("*.json"))}
    cs = [k for k in arqs if k.startswith("C")]
    rs = [k for k in arqs if k.startswith("R")]
    estrutura = []
    ids02, ids08, ids10, ids04 = ({r["id"] for r in M[k]} for k in ("M02", "M08", "M10", "M04"))
    ids09 = {r["id"] for r in M["M09"]}
    for k, d in arqs.items():
        e = d.get("esperado", {})
        if set(d.get("entrada", {})) != {"wizard", "checklist", "itens", "variaveis", "metadados"}:
            estrutura.append(f"{k}: entrada")
        ids_ga = {r["grupo_alternativa"].split(" ")[0] for r in M["M02"] if r["grupo_alternativa"]}
        for campo, ids in (("blocos", ids02), ("clausulas_m08", ids08), ("validacoes_m10", ids10),
                           ("perguntas_sem_resposta", ids04), ("bloqueios_grupo_alternativas", ids_ga)):
            if campo not in e or [x for x in e[campo] if x not in ids]:
                estrutura.append(f"{k}: esperado.{campo}")
        if k.startswith("R") and ([x["dv"] for x in d.get("divergencias_conhecidas", []) if x["dv"] not in ids09]
                                  or not d.get("divergencias_conhecidas")):
            estrutura.append(f"{k}: divergencias_conhecidas")
    reg(len(cs) == 8 and len(rs) == 2 and not estrutura,
        f"cenarios/: {len(cs)} cenários de ouro e {len(rs)} casos de reprodução com entrada e esperado completos, IDs "
        f"existentes e DV-xx do M09" + (f" | {estrutura}" if estrutura else ""))
    rep = sim.reproduzir(str(pasta))
    falhou = {k: v for k, v in rep.items() if v}
    reg(len(rep) == 8 and not falhou, f"simulador pelas colunas novas reproduz os {len(rep)} cenários (blocos, M08, M10 e "
        f"perguntas sem resposta)" + (f" | {falhou}" if falhou else ""))
    # controle negativo: um erro em cada coluna nova tem de mudar o resultado de algum cenário
    m = sim.carregar(str(pasta))
    docs = [d for k, d in arqs.items() if k.startswith("C")]

    def detecta(mat, rid, col, de, para):
        mm = copy.deepcopy(m)
        for r in mm[mat]:
            if r["id"] == rid:
                r[col] = r[col].replace(de, para, 1)
        return any(sim.comparar(d["esperado"], sim.simular(mm, d["entrada"])) for d in docs)
    det = [detecta("M04", "WZ-11", "depende_de_expr", '"SIM"', '"NAO"'),
           detecta("M05", "VAR-113", "calculo_expr", '"COTA"', '"AMPLA"'),
           detecta("M11", "CK-C-12.3", "preenche_expr", "REMESSA_UNICA", "PARCELADA"),
           detecta("M04", "WZ-09", "calculo_expr", '"SIM","NAO"', '"NAO","SIM"')]
    reg(all(det), f"controle negativo das colunas novas: 4 erros injetados (depende_de_expr, M05.calculo_expr, "
        f"preenche_expr, M04.calculo_expr), detectados {sum(det)}")
    # regras do motor que nenhum cenário de ouro aciona: filho sem pai e grupo de alternativas
    c1 = next(d for d in docs if d["id"] == "C1")
    base_blocos = sim.caminho_expr(m, c1["entrada"])[0]["blocos"]
    paiz = next(b for b in base_blocos if any(x.startswith(b + ".") for x in base_blocos) and
                next(r for r in m["M02"] if r["id"] == b)["grupo_alternativa"] == "")
    ids02_ = {r["id"] for r in m["M02"]}
    filhos = [x for x in base_blocos if sim.pai(x, ids02_) == paiz]
    mm = copy.deepcopy(m)
    for r in mm["M02"]:
        if r["id"] == paiz:
            r["condicao_expr"] = "false"
    sem_pai = sim.caminho_expr(mm, c1["entrada"])[0]["blocos"]
    ok_pai = not [x for x in filhos if x in sem_pai]
    mm = copy.deepcopy(m)
    alt = next(r for r in mm["M02"] if r["grupo_alternativa"].startswith("GA-01") and r["opcao"] and r["id"] not in base_blocos)
    alt["condicao_expr"] = "true"
    bl = sim.caminho_expr(mm, c1["entrada"])[0]["bloqueios_grupo_alternativas"]
    reg(ok_pai and bl == ["GA-01"], f"regras de montagem no simulador: com {paiz} desligado, {len(filhos)} filhos saem; com "
        f"duas opções no GA-01 ({alt['id']} ligado à força), bloqueio {bl}")
    # --------------------------------------------------------- dados reais
    achados = []
    for k, d in arqs.items():
        t = json.dumps(d.get("entrada", {}), ensure_ascii=False)
        if [n for n in NUP.findall(t) if n != NUP_FICTICIO] or re.search(r"UASG|\b16\d{4}\b", t):
            achados.append(k)
    for nome in ("M00_inventario.csv", "perguntas_abertas.md", "scripts/f0_gerar_M00.py", "scripts/f9_testes.py"):
        f = pasta / nome
        if f.exists() and [n for n in NUP.findall(f.read_text(encoding="utf-8-sig")) if n != NUP_FICTICIO]:
            achados.append(nome)
    reg(not achados, "números de processo trocados por PROC-xx no M00, no perguntas_abertas.md e nos scripts; entradas "
        "dos cenários sem número de processo nem UASG" + (f" | {achados}" if achados else ""))
    # --------------------------------------------------------- correções do compilador
    v33 = next(r for r in M["M10"] if r["id"] == "VAL-033")
    reg("ETP-SS.CC" not in v33["mensagem"], "VAL-033: mensagem ao usuário sem 'ETP-SS.CC'")
    readme = (pasta / "README.md").read_text(encoding="utf-8")
    lin = [l for l in readme.splitlines() if l.startswith("- Operadores permitidos:")]
    lidos = set(re.findall(r"`([^`]+)`", lin[0])) if lin else set()
    reg(lidos == PERMITIDOS, f"README: lista de operadores igual à da Fase 10 ({len(lidos)} operadores)")
    return out


if __name__ == "__main__":
    pasta = Path(sys.argv[1])
    arqs = {"M00": "M00_inventario.csv", "M02": "M02_tr_blocos.csv", "M04": "M04_wizard.csv", "M05": "M05_variaveis.csv",
            "M08": "M08_clausulas_setoriais.csv", "M09": "M09_desvios.csv", "M10": "M10_validacoes.csv",
            "M11": "M11_checklist.csv", "M12": "M12_parametros.csv"}
    M = {k: list(csv.DictReader(open(pasta / v, encoding="utf-8-sig"))) for k, v in arqs.items()}
    for ok, msg in testes(pasta, M):
        print(("OK    " if ok else "FALHA ") + msg)
