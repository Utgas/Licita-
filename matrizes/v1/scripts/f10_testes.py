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
        base = re.sub(r"_texto$", "", nome)
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
            if re.search(r"\d", e) and e not in opcoes and not re.fullmatch(r"(TR|SET|ETP)-[A-Za-z0-9.\-]+", e):
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
    # --------------------------------------------------------- correções de 23/10/2026 (revisão da Fase 10)
    from jlogic import avaliar
    v29 = json.loads(next(r for r in M["M10"] if r["id"] == "VAL-029")["condicao_expr"])
    casos = [(["atestado pelo período mínimo de 12 meses"], True), (["Período mínimo de execução"], True),
             (["contratos dos últimos 3 anos"], True), (["Últimos exercícios"], True),
             (["fornecimento e instalação de equipamento compatível"], False), ([], False), (None, False)]
    erros29 = [str(x) for x, esp in casos if bool(avaliar(v29, {"VAR_085": x} if x is not None else {})) != esp]
    reg("some" in json.dumps(v29) and not erros29, "VAL-029: some sobre a VAR_085 (lista) acha 'período mínimo' e "
        "'últimos', com e sem inicial maiúscula, em cada item; 7 casos" + (f" | erra em {erros29}" if erros29 else ""))
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
        for campo, ids in (("blocos", ids02), ("clausulas_m08", ids08), ("validacoes_m10", ids10),
                           ("perguntas_sem_resposta", ids04)):
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
        return any(sim.comparar(d["esperado"], sim.caminho_expr(mm, d["entrada"])[0]) for d in docs)
    det = [detecta("M04", "WZ-11", "depende_de_expr", '"SIM"', '"NAO"'),
           detecta("M05", "VAR-113", "calculo_expr", '"COTA"', '"AMPLA"'),
           detecta("M11", "CK-C-12.3", "preenche_expr", "REMESSA_UNICA", "PARCELADA"),
           detecta("M04", "WZ-09", "calculo_expr", '"SIM","NAO"', '"NAO","SIM"')]
    reg(all(det), f"controle negativo das colunas novas: 4 erros injetados (depende_de_expr, M05.calculo_expr, "
        f"preenche_expr, M04.calculo_expr), detectados {sum(det)}")
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
