#!/usr/bin/env python3
"""Fase 10 - regras em JSON Logic para o motor: M04.depende_de_expr e M04.calculo_expr, M05.calculo_expr (com
M05.calculo_ordem e as linhas novas de atributo de item) e M11.condicional_expr, M11.preenche_expr e M11.sugere_expr.

Uso: python3 -I f10_gerar_expr.py <pasta_Matrizes_v1> <saida_log.txt>

Roda depois do f6_gerar_expr.py. O texto livre das colunas existentes não muda: as colunas novas entram ao lado da
coluna de origem. Convenções (contexto de item, ordem de avaliação, contribuições de várias perguntas para o mesmo
destino) no README e em jlogic.py; operadores e variáveis fora da lista da Fase 10, na P31.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import gravar_csv, ler_csv  # noqa: E402
from f10_m11_regras import regras_m11  # noqa: E402
from jlogic import dumps, e, eq, inn, ne, nao, ou, tem, var, vazio  # noqa: E402

P = "parametros."


def par(nome):
    return var(P + nome)


def se(cond, a, b=None):
    return {"if": [cond, a, b]}


def algum(lista, cond):
    return {"some": [var(lista), cond]}


def nenhum(lista, cond):
    return {"none": [var(lista), cond]}


def reduz(lista, passo, inicial):
    return {"reduce": [lista if isinstance(lista, dict) else var(lista), passo, inicial]}


def cur(a):
    return var("current." + a)


ACC = var("accumulator")


# --------------------------------------------------------------------------- M04
def wz(t):
    return t.strip().replace("-", "_")


def cond_simples(t):
    t = t.strip()
    m = re.fullmatch(r"(WZ-\d{2}) respondida", t)
    if m:
        return tem(wz(m.group(1)))
    m = re.fullmatch(r"(WZ-\d{2}) contém ([A-Z0-9_]+)", t)
    if m:
        return inn(m.group(2), var(wz(m.group(1)), []))
    m = re.fullmatch(r"(WZ-\d{2}) diferente de ([A-Z0-9_]+)", t)
    if m:
        return ne(wz(m.group(1)), m.group(2))
    m = re.fullmatch(r"(WZ-\d{2}) em ([A-Z0-9_]+(?: ou [A-Z0-9_]+)+)", t)
    if m:
        return inn(var(wz(m.group(1))), m.group(2).split(" ou "))
    m = re.fullmatch(r"(WZ-\d{2})=([A-Z0-9_]+)", t)
    if m:
        return eq(wz(m.group(1)), m.group(2))
    m = re.fullmatch(r"CK-([CP])-([\d.]+)=(.+)", t)
    if m:
        return eq(f"CK_{m.group(1)}_{m.group(2).replace('.', '_')}", m.group(3))
    raise SystemExit(f"depende_de sem tradução: '{t}'")


def depende_expr(texto):
    """'A e B', 'A ou B', 'X em P ou Q'; trechos 'VAR-xxx (...)' são dependência de dado, não condição."""
    partes = [p.strip() for p in texto.split(";")]
    conds = [p for p in partes if p and not p.startswith("VAR-")]
    if texto.startswith("DESLIGADA"):
        return False  # pergunta fora do sistema; o motivo está no próprio texto de depende_de
    if not conds:
        return None
    if len(conds) > 1:
        raise SystemExit(f"depende_de com duas condições separadas por ';': {texto}")
    c = conds[0]
    if " e " in c:
        return e(*(cond_simples(x) for x in c.split(" e ")))
    if re.search(r"\bem\b", c):
        return cond_simples(c)
    if " ou " in c:
        return ou(*(cond_simples(x) for x in c.split(" ou ")))
    return cond_simples(c)


def dep13():
    return e(eq("WZ_10", "SIM"), inn(var("WZ_03"), ["MENOR_PRECO", "MAIOR_DESCONTO"]))


def contagem_grupos():
    """número de rótulos de grupo distintos (0 e 1 só como valor inicial e passo de contagem)."""
    rotulos = reduz("itens", se(e(tem(cur("grupo")), nao(inn(cur("grupo"), ACC))), {"merge": [ACC, [cur("grupo")]]}, ACC), [])
    return reduz(rotulos, {"+": [ACC, 1]}, 0)


def contagem_isolados():
    return reduz("itens", se(tem(cur("grupo")), ACC, {"+": [ACC, 1]}), 0)


CALC_M04 = {
    "WZ-09": se(algum("itens", eq("perecivel", "S")), "SIM", "NAO"),
    "WZ-13": se(dep13(), se(algum("itens", tem("grupo")), "SIM", "NAO"), None),
    "WZ-18": se(algum("itens", tem("marca_indicada")), "SIM", "NAO"),
    "WZ-20": se(ou(eq("WZ_01", "LICITACAO"), eq("WZ_05", "SIM")), se(algum("itens", eq("exige_amostra", "S")), "SIM", "NAO"),
                None),
    "WZ-24": se(eq("WZ_01", "LICITACAO"), se(algum("itens", eq("tratamento_me_epp", "COTA")), "SIM", "NAO"), None),
    "WZ-50": {"if": [{"==": [{"+": [contagem_grupos(), contagem_isolados()]}, 1]}, "NAO_PARCELADO",
                     {"and": [{">": [contagem_grupos(), 0]}, {">": [contagem_isolados(), 0]}]}, "POR_ITEM_E_GRUPO",
                     {">": [contagem_grupos(), 0]}, "POR_GRUPO",
                     "POR_ITEM"]},
}


# --------------------------------------------------------------------------- M05
def piso_percentual(qtd, pct):
    """parte inteira de qtd x pct / divisor: (x - x % divisor) / divisor."""
    x = {"*": [qtd, pct]}
    return {"/": [{"-": [x, {"%": [x, par("divisor_percentual")]}]}, par("divisor_percentual")]}


VALOR_UNIDADE = reduz("itens_do_grupo", {"+": [ACC, {"*": [cur("quantidade"), cur("valor_unitario")]}]}, 0)
# cota só quando todo item da unidade de disputa tem cota calculada maior que zero; cota zero fica em ampla com alerta
# (VAL-051, decisão 0008 de 23/10/2026). Valor ausente não vira zero: sem valor da unidade, o tratamento fica vazio.
COTA_POSSIVEL = e(tem("VAR_057"), nenhum("itens_do_grupo", nao({">": [var("cota_calculada"), 0]})))
TRATAMENTO = se(eq("WZ_01", "LICITACAO"),
                {"if": [algum("itens_do_grupo", tem("justificativa_excecao_me_epp")), "EXCECAO_JUSTIFICADA",
                        vazio("valor_unidade_disputa"), None,
                        {"<=": [var("valor_unidade_disputa"), par("limite_exclusivo_me_epp")]}, "EXCLUSIVO",
                        COTA_POSSIVEL, "COTA",
                        "AMPLA"]},
                None)
VALIDADE_COMUM = se(eq(reduz("itens", se(ne(cur("perecivel"), "S"), ACC,
                                         se(eq(ACC, None), cur("validade_minima"),
                                            se(eq(ACC, cur("validade_minima")), ACC, ""))), None), ""),
                    None,
                    reduz("itens", se(ne(cur("perecivel"), "S"), ACC,
                                      se(eq(ACC, None), cur("validade_minima"),
                                         se(eq(ACC, cur("validade_minima")), ACC, ""))), None))

# id: (ordem, expressão, nota para o log)
CALC_M05 = {
    "VAR-116": (1, se(eq("categoria", "PERMANENTE"), "N", se(ou(tem("validade_minima"), tem("CK_C_14_1")), "S", "N")),
                "por item; S quando o checklist de consumo informa prazo de validade (CK-C-14.1) ou validade mínima "
                "(CK-C-14.2) para o item; N em permanente"),
    "VAR-154": (2, se(inn(var("classe_pdm"), par("classes_tic")), "S", "N"), "por item; lista de classes do M12"),
    "VAR-119": (3, VALOR_UNIDADE, "por item; soma de quantidade x valor_unitario em itens_do_grupo"),
    "VAR-160": (4, piso_percentual(var("quantidade"), var("VAR_057")),
                "por item; parte inteira de quantidade x VAR-057 / 100 para todo item (vazia sem VAR-057 ou sem quantidade)"),
    "VAR-113": (5, TRATAMENTO, "por item; exceção > sem valor (vazio) > limite exclusivo > cota calculada maior que zero em "
                               "todos os itens da unidade > ampla"),
    "VAR-118": (6, se(eq("tratamento_me_epp", "COTA"), var("cota_calculada"), None),
                "por item; parte inteira de quantidade x VAR-057 / 100, só com COTA"),
    "VAR-111": (7, {"if": [eq("WZ_14", "CONTINUO"), "CONTINUADO", eq("WZ_26", "REMESSA_UNICA"), "INTEGRAL",
                           eq("WZ_26", "PARCELADA"), "PARCELADO", None]}, "global"),
    "VAR-031": (8, CALC_M04["WZ-13"], "global; mesmo cálculo da WZ-13"),
    "VAR-049": (9, reduz("itens", se(eq(cur("exige_amostra"), "S"), {"merge": [ACC, [cur("numero")]]}, ACC), []),
                "global; números dos itens com exige_amostra = S"),
    "VAR-065": (10, VALIDADE_COMUM, "global; validade comum aos perecíveis, vazia se os critérios forem diferentes"),
}

NOVAS_M05 = [
    {"id": "VAR-156", "nome": "tabela_itens.numero", "descricao": "Coluna da VAR-011: número do item na tabela",
     "tipo_dado": "NUMERO", "validacao": "inteiro maior que zero, único na tabela", "obrigatoria": "S", "origem": "DFD",
     "usada_em": "TR-1.1.TAB1; VAR-049"},
    {"id": "VAR-157", "nome": "tabela_itens.catmat",
     "descricao": "Coluna da VAR-011: código CATMAT do item, quando houver",
     "tipo_dado": "TEXTO", "validacao": "numérico quando informado; o DFD do Compras.gov traz classe e PDM, sem o código (DV-27)",
     "obrigatoria": "N", "origem": "DFD", "usada_em": "TR-1.1.TAB1; M10"},
    {"id": "VAR-158", "nome": "tabela_itens.quantidade",
     "descricao": "Coluna da VAR-011: quantidade do item (no registro de preços, a soma dos órgãos)",
     "tipo_dado": "NUMERO", "validacao": "inteira maior que zero; como informada, nunca calculada pelo sistema",
     "obrigatoria": "S", "origem": "DFD", "usada_em": "TR-1.1.TAB1; ETP-07.02; VAR-118; VAR-119; M10"},
    {"id": "VAR-159", "nome": "tabela_itens.valor_unitario",
     "descricao": "Coluna da VAR-011: valor unitário de referência do item, da pesquisa de preços",
     "tipo_dado": "MOEDA", "validacao": "maior que zero; vem da pesquisa de preços, nunca calculado pelo sistema",
     "obrigatoria": "S", "origem": "PESQUISA_PRECOS", "usada_em": "TR-1.1.TAB1; VAR-119"},
    {"id": "VAR-161", "nome": "garantia_atestado_meses",
     "descricao": "Prazo mínimo, em meses, da garantia técnica já prestada que os atestados devem comprovar (WZ-60)",
     "tipo_dado": "NUMERO", "validacao": "inteiro de 12 ou mais (PAR-13, resposta da P25); obrigatório com WZ-60 = SIM",
     "obrigatoria": "CONDICIONAL", "origem": "WIZARD", "usada_em": "SET-23; VAL-052"},
    {"id": "VAR-162", "nome": "justificativa_garantia_atestado",
     "descricao": "Justificativa técnica, no ETP, da exigência de garantia já prestada nos atestados (WZ-60)",
     "tipo_dado": "TEXTO", "validacao": "obrigatória com WZ-60 = SIM; fatos técnicos, sem texto padrão",
     "obrigatoria": "CONDICIONAL", "origem": "WIZARD", "usada_em": "ETP-04.01; SET-23; VAL-053"},
    {"id": "VAR-160", "nome": "tabela_itens.cota_calculada",
     "descricao": "Coluna da VAR-011: parte inteira de quantidade x VAR-057 / 100, calculada para todo item quando há "
                  "percentual de cota; decide se a unidade de disputa pode ter cota (VAR-113), dá a quantidade reservada "
                  "(VAR-118) e dispara o alerta de cota zero (VAL-051)",
     "tipo_dado": "NUMERO", "validacao": "inteiro maior ou igual a zero; vazia sem VAR-057 ou sem quantidade",
     "obrigatoria": "N", "origem": "SISTEMA", "usada_em": "VAR-113; VAR-118; VAL-051"},
]
FONTE_NOVA = ("Linha criada na Fase 10 (23/10/2026): atributo de item já usado nas expressões do M10 (achado do compilador "
              "do Marco 0) ou no calculo_expr do M05; descrição a partir da VAR-011.")


NOTA = (" Fase 10 (23/10/2026): {cols} em JSON Logic, tradução do texto da própria linha feita pelo f10_gerar_expr.py; "
        "convenções no README e na P31.")


def anota(r, cols):
    cols = [c for c in cols if r.get(c)]
    if cols and "Fase 10 (23/10/2026)" not in r["fonte"]:
        r["fonte"] = r["fonte"].rstrip() + NOTA.format(cols=", ".join(cols))


# grupo de alternativas ativo: exatamente uma opção tem de entrar (regra do motor); fora disso o grupo não se aplica
GRUPO_ATIVO = {"GA-03": eq("WZ_49", "SIM"), "GA-11": ne("WZ_43", "CONTRATO"), "GA-12": ne("WZ_43", "CONTRATO"),
               "GA-13": ne("WZ_43", "CONTRATO")}


def main():
    pasta = Path(sys.argv[1])
    log = []
    # M02: grupo_ativo_expr
    m02 = ler_csv(pasta / "M02_tr_blocos.csv")
    cols2 = [c for c in m02[0] if c != "grupo_ativo_expr"]
    k2 = cols2.index("opcao") + 1
    cols2 = cols2[:k2] + ["grupo_ativo_expr"] + cols2[k2:]
    for r in m02:
        g = r["grupo_alternativa"].split(" ")[0] if r["grupo_alternativa"] else ""
        r["grupo_ativo_expr"] = dumps(GRUPO_ATIVO.get(g, True)) if g else ""
        anota(r, ("grupo_ativo_expr",))
    gravar_csv(pasta / "M02_tr_blocos.csv", cols2, m02, preservar=())
    log.append(f"M02: grupo_ativo_expr em {sum(1 for r in m02 if r['grupo_ativo_expr'])} blocos de "
               f"{len({r['grupo_alternativa'].split(' ')[0] for r in m02 if r['grupo_alternativa']})} grupos")
    # M04
    m04 = ler_csv(pasta / "M04_wizard.csv")
    cols4 = [c for c in m04[0] if c not in ("depende_de_expr", "calculo_expr")]
    i = cols4.index("depende_de") + 1
    cols4 = cols4[:i] + ["depende_de_expr"] + cols4[i:]
    j = cols4.index("pre_preenchida_por") + 1
    cols4 = cols4[:j] + ["calculo_expr"] + cols4[j:]
    for r in m04:
        ex = depende_expr(r["depende_de"])
        r["depende_de_expr"] = dumps(ex) if ex is not None else ""
        if r["depende_de"] and ex is None:
            log.append(f"M04 {r['id']}: depende_de só cita dado ({r['depende_de']}); pergunta derivada, sem condição")
        r["calculo_expr"] = dumps(CALC_M04[r["id"]]) if r["id"] in CALC_M04 else ""
        anota(r, ("depende_de_expr", "calculo_expr"))
    faltam = [k for k in CALC_M04 if k not in {r["id"] for r in m04}]
    if faltam:
        raise SystemExit(f"M04 sem as derivadas {faltam}")
    gravar_csv(pasta / "M04_wizard.csv", cols4, m04)
    log.append(f"M04: depende_de_expr em {sum(1 for r in m04 if r['depende_de_expr'])} de {len(m04)}; calculo_expr em "
               f"{sum(1 for r in m04 if r['calculo_expr'])}")
    # M05
    m05 = ler_csv(pasta / "M05_variaveis.csv")
    ids5 = {r["id"] for r in m05}
    for n in sorted(NOVAS_M05, key=lambda x: x["id"]):
        if n["id"] in ids5:
            raise SystemExit(f"M05: {n['id']} já existe")
        m05.append(dict(n, fonte=FONTE_NOVA, status="INFERIDO"))
    cols5 = [c for c in m05[0] if c not in ("calculo_expr", "calculo_ordem")]
    k = cols5.index("validacao") + 1
    cols5 = cols5[:k] + ["calculo_expr", "calculo_ordem"] + cols5[k:]
    for r in m05:
        if r["id"] in CALC_M05:
            ordem, ex, nota = CALC_M05[r["id"]]
            r["calculo_expr"], r["calculo_ordem"] = dumps(ex), str(ordem)
            anota(r, ("calculo_expr",))
            log.append(f"M05 {r['id']} ({r['nome']}): ordem {ordem}; {nota}")
        else:
            r["calculo_expr"], r["calculo_ordem"] = "", ""
    sist = [r["id"] for r in m05 if r["origem"] == "SISTEMA" and not r["calculo_expr"]]
    log.append(f"M05: SISTEMA sem calculo_expr (dado do cadastro da OM, data ou texto montado, não cálculo): {sist}")
    gravar_csv(pasta / "M05_variaveis.csv", cols5, m05, preservar=())
    # M11
    m11 = ler_csv(pasta / "M11_checklist.csv")
    regras, log11 = regras_m11(m11)
    log += log11
    cols11 = [c for c in m11[0] if c not in ("condicional_expr", "preenche_expr", "sugere_expr")]
    a = cols11.index("condicional") + 1
    cols11 = cols11[:a] + ["condicional_expr"] + cols11[a:]
    b = cols11.index("regra") + 1
    cols11 = cols11[:b] + ["preenche_expr", "sugere_expr"] + cols11[b:]
    for r in m11:
        cond, pre, sug = regras.get(r["id"], (None, None, None))
        r["condicional_expr"] = dumps(cond) if cond is not None else ""
        r["preenche_expr"] = dumps(pre) if pre else ""
        r["sugere_expr"] = dumps(sug) if sug else ""
        anota(r, ("condicional_expr", "preenche_expr", "sugere_expr"))
    gravar_csv(pasta / "M11_checklist.csv", cols11, m11, preservar=())
    log.append(f"M11: condicional_expr {sum(1 for r in m11 if r['condicional_expr'])} de "
               f"{sum(1 for r in m11 if r['condicional'])} condicionais; preenche_expr {sum(1 for r in m11 if r['preenche_expr'])} "
               f"de {sum(1 for r in m11 if r['efeito'] == 'PREENCHE')} PREENCHE; sugere_expr "
               f"{sum(1 for r in m11 if r['sugere_expr'])} de {sum(1 for r in m11 if r['efeito'] == 'SUGERE')} SUGERE")
    Path(sys.argv[2]).write_text("\n".join(log) + "\n", encoding="utf-8")
    print("\n".join(l for l in log if l.startswith(("M04:", "M05:", "M11:"))))


if __name__ == "__main__":
    main()
