#!/usr/bin/env python3
"""JSON Logic: construtores e avaliador mínimo usados nas matrizes (análise, não código do sistema).

Convenções de nomes de variável (as mesmas em M02.condicao_expr, M04.liga_expr/desliga_expr, M08 e M10):
  WZ_07             resposta da WZ-07 (MULTIPLA: lista de opções marcadas)
  CK_C_10_1         resposta da pergunta 10.1 do checklist de consumo; CK_P_13_1 do checklist de permanentes
                    (SIM_NAO e UNICA: texto literal da opção, ex.: "Sim"; MULTIPLA: lista de textos literais;
                    TEXTO, NUMERO e TABELA: o valor; pergunta não respondida: ausente)
  VAR_001           valor da variável VAR-001 do M05
  itens             lista de itens (VAR-011), cada um com os atributos grupo, tratamento_me_epp, exige_amostra,
                    marca_indicada, perecivel, validade_minima, compatibilidade, faixa_temperatura, controle_especial,
                    garantia_minima_meses, quantidade, valor_unitario, catmat, classe
  parametros.*      listas mantidas pela OM (ex.: parametros.classes_tic); o sistema não inventa o conteúdo
Operadores usados: var, ==, !=, !, !!, and, or, in, some, all, none, if, merge, >, >=, <, <=, +, *.
"""
import json
from decimal import Decimal, getcontext

getcontext().prec = 50


def var(nome, padrao=None):
    return {"var": nome} if padrao is None else {"var": [nome, padrao]}


def ck(lista, numero):
    return "CK_" + lista + "_" + str(numero).replace(".", "_")


def eq(a, b):
    return {"==": [a if isinstance(a, dict) else var(a), b]}


def ne(a, b):
    return {"!=": [a if isinstance(a, dict) else var(a), b]}


def tem(a):
    """valor presente e não vazio"""
    return {"!!": [a if isinstance(a, dict) else var(a)]}


def vazio(a):
    return {"!": [a if isinstance(a, dict) else var(a)]}


def inn(valor, lista):
    return {"in": [valor, lista if isinstance(lista, (dict, list)) else var(lista)]}


def e(*xs):
    xs = [x for x in xs if x is not None]
    return xs[0] if len(xs) == 1 else {"and": list(xs)}


def ou(*xs):
    xs = [x for x in xs if x is not None]
    return xs[0] if len(xs) == 1 else {"or": list(xs)}


def nao(x):
    return {"!": [x]}


def algum_item(cond):
    return {"some": [var("itens"), cond]}


def nenhum_item(cond):
    return {"none": [var("itens"), cond]}


def dumps(x):
    return json.dumps(x, ensure_ascii=False, separators=(",", ":"))


def verdadeiro(v):
    """Falso: null, false, 0, "" e []. Todo o resto é verdadeiro (regra do motor, Marco 1)."""
    if v is None or v is False or v == "" or v == []:
        return False
    if isinstance(v, (int, float, Decimal)) and not isinstance(v, bool) and v == 0:
        return False
    return True


def numero(v):
    """Decimal exato a partir da forma escrita do número; None se não for número."""
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, Decimal):
        return v
    if isinstance(v, int):
        return Decimal(v)
    if isinstance(v, float):
        return Decimal(repr(v))
    return None


def igual(a, b):
    """Igualdade estrita: tipos diferentes são diferentes; números comparam por valor; null só é igual a null."""
    na, nb = numero(a), numero(b)
    if na is not None and nb is not None:
        return na == nb
    if (na is None) != (nb is None):
        return False
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    return type(a) is type(b) and a == b


def avaliar(ex, d):
    if isinstance(ex, list):
        return [avaliar(x, d) for x in ex]
    if not isinstance(ex, dict):
        return ex
    op, a = next(iter(ex.items()))
    if op == "var":
        nome = a[0] if isinstance(a, list) else a
        padrao = a[1] if isinstance(a, list) and len(a) > 1 else None
        if nome == "" or nome is None:
            return d
        v = d
        for parte in str(nome).split("."):
            if isinstance(v, dict) and parte in v:
                v = v[parte]
            else:
                return avaliar(padrao, d) if isinstance(padrao, (dict, list)) else padrao
        return v
    if op == "reduce":
        arr = avaliar(a[0], d)
        arr = arr if isinstance(arr, list) else []
        acc = avaliar(a[2], d) if len(a) > 2 else None
        for x in arr:
            acc = avaliar(a[1], {"current": x, "accumulator": acc})
        return acc
    if op in ("some", "all", "none"):
        arr = avaliar(a[0], d)
        arr = arr if isinstance(arr, list) else []
        res = [verdadeiro(avaliar(a[1], x)) for x in arr]
        return any(res) if op == "some" else (all(res) and bool(res)) if op == "all" else not any(res)
    if op == "if":
        for k in range(0, len(a) - 1, 2):
            if verdadeiro(avaliar(a[k], d)):
                return avaliar(a[k + 1], d)
        return avaliar(a[-1], d) if len(a) % 2 else None
    args = a if isinstance(a, list) else [a]
    if op == "and":
        r = True
        for x in args:
            r = avaliar(x, d)
            if not verdadeiro(r):
                return r
        return r
    if op == "or":
        r = False
        for x in args:
            r = avaliar(x, d)
            if verdadeiro(r):
                return r
        return r
    if op == "!":
        return not verdadeiro(avaliar(args[0], d))
    if op == "!!":
        return verdadeiro(avaliar(args[0], d))
    v = [avaliar(x, d) for x in args]
    if op == "merge":
        out = []
        for x in v:
            out.extend(x if isinstance(x, list) else [x])
        return out
    if op == "==":
        return igual(v[0], v[1])
    if op == "!=":
        return not igual(v[0], v[1])
    if op == "in":
        if v[0] is None or v[1] is None:
            return False
        if isinstance(v[1], str):
            return isinstance(v[0], str) and v[0] in v[1]
        if isinstance(v[1], list):
            return any(igual(v[0], x) for x in v[1])
        return False
    # conta e comparação de ordem: valor ausente (ou não numérico) dá ausente; divisão por zero dá ausente
    ns = [numero(x) for x in v]
    if any(n is None for n in ns):
        return None
    if op in (">", ">=", "<", "<="):
        x, y = ns[0], ns[1]
        return {">": x > y, ">=": x >= y, "<": x < y, "<=": x <= y}[op]
    if op == "*":
        r = Decimal(1)
        for x in ns:
            r *= x
        return r
    if op == "+":
        return sum(ns, Decimal(0))
    if op == "-":
        return ns[0] - ns[1] if len(ns) > 1 else -ns[0]
    if op in ("/", "%"):
        if ns[1] == 0:
            return None
        return ns[0] / ns[1] if op == "/" else ns[0] % ns[1]
    raise ValueError(f"operador JSON Logic não suportado: {op}")
