#!/usr/bin/env python3
"""Condições em JSON Logic: M04.liga_expr e M04.desliga_expr, e M02.condicao_expr (tarefa 10 de 22/10/2026).

Uso: python3 -I f6_gerar_expr.py <pasta_Matrizes_v1> <saida_log.txt>

Tradução mecânica dos textos liga_blocos e desliga_blocos do M04 (que continuam como comentário legível), com a mesma
semântica do teste de simulação (f3_simular_wizard.py):
  - opção de SIM_NAO ou UNICA: {"==": [{"var": "WZ_xx"}, "OPCAO"]}; opção de MULTIPLA: {"in": ["OPCAO", {"var": "WZ_xx"}]};
  - perguntas derivadas (WZ-09, WZ-13, WZ-18, WZ-20, WZ-24): a condição é calculada dos atributos de item, com a mesma
    dependência do M04 (ex.: WZ-24 só existe em licitação);
  - liga_expr e desliga_expr devolvem a lista de blocos: {"merge": [{"if": [cond, [ids], []]}, ...]};
  - em MULTIPLA, opção não marcada desliga os blocos que só ela liga.
M02.condicao_expr por bloco: separador 'OU' e bloco 'Não entra na minuta' = false; bloco condicional (condicao_inclusao começa por 'SE', 'Acompanha' ou
'Opcional') = alguma condição que liga E nenhuma que desliga; demais blocos = nenhuma condição que desliga (true se nenhuma).
Menções parciais ('trecho de', 'Preenche', colunas) não viram condição de bloco inteiro: vão para o log e para
perguntas_abertas.md.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import gravar_csv, ler_csv  # noqa: E402
from f3_simular_wizard import PARCIAL, efeitos  # noqa: E402
from jlogic import algum_item, dumps, e, eq, inn, nao, nenhum_item, ou, tem, var  # noqa: E402


def dep_wz13():
    return e(eq("WZ_10", "SIM"), {"in": [var("WZ_03"), ["MENOR_PRECO", "MAIOR_DESCONTO"]]})


def dep_wz20():
    return ou(eq("WZ_01", "LICITACAO"), eq("WZ_05", "SIM"))


DERIVADAS = {
    "WZ-09": {"SIM": algum_item(eq("perecivel", "S")), "NAO": nenhum_item(eq("perecivel", "S"))},
    "WZ-13": {"SIM": e(dep_wz13(), algum_item(tem("grupo"))), "NAO": e(dep_wz13(), nenhum_item(tem("grupo")))},
    "WZ-18": {"SIM": algum_item(tem("marca_indicada")), "NAO": nenhum_item(tem("marca_indicada"))},
    "WZ-20": {"SIM": e(dep_wz20(), algum_item(eq("exige_amostra", "S"))),
              "NAO": e(dep_wz20(), nenhum_item(eq("exige_amostra", "S")))},
    "WZ-24": {"SIM": e(eq("WZ_01", "LICITACAO"), algum_item(eq("tratamento_me_epp", "COTA"))),
              "NAO": e(eq("WZ_01", "LICITACAO"), nenhum_item(eq("tratamento_me_epp", "COTA")))},
}


def cond_opcao(wz, tipo, opc):
    if wz in DERIVADAS:
        if opc not in DERIVADAS[wz]:
            raise SystemExit(f"{wz}: opção derivada sem expressão: {opc}")
        return DERIVADAS[wz][opc]
    nome = wz.replace("-", "_")
    if tipo == "MULTIPLA":
        return inn(opc, var(nome, []))
    return eq(nome, opc)


def main():
    pasta = Path(sys.argv[1])
    m02 = ler_csv(pasta / "M02_tr_blocos.csv")
    m04 = ler_csv(pasta / "M04_wizard.csv")
    m08 = ler_csv(pasta / "M08_clausulas_setoriais.csv")
    lista = [r["id"] for r in m02]
    ordem = {k: i for i, k in enumerate(lista)}
    ids_set = {r["id"] for r in m08}
    liga_b, desl_b = {}, {}
    log = []
    for r in m04:
        wz, tipo = r["id"], r["tipo_resposta"]
        li = efeitos(r["liga_blocos"], ordem, lista)
        de = efeitos(r["desliga_blocos"], ordem, lista)
        for campo in ("liga_blocos", "desliga_blocos"):
            for m in PARCIAL.finditer(r[campo]):
                log.append(f"PARCIAL {wz} {campo}: '{m.group(0)}' (não vira condição de bloco inteiro)")
        for d in (li, de):
            for ids in d.values():
                desconhecidos = [x for x in ids if x not in ordem and x not in ids_set]
                if desconhecidos:
                    raise SystemExit(f"{wz}: IDs desconhecidos em liga/desliga: {desconhecidos}")
        partes_l, partes_d = [], []
        for opc, ids in li.items():
            c = cond_opcao(wz, tipo, opc)
            partes_l.append({"if": [c, sorted(ids, key=lambda x: ordem.get(x, 10 ** 6)), []]})
            for b in ids:
                liga_b.setdefault(b, []).append(c)
        for opc, ids in de.items():
            c = cond_opcao(wz, tipo, opc)
            partes_d.append({"if": [c, sorted(ids, key=lambda x: ordem.get(x, 10 ** 6)), []]})
            for b in ids:
                desl_b.setdefault(b, []).append(c)
        if tipo == "MULTIPLA":
            for opc, ids in li.items():
                outros = set().union(*(v for k, v in li.items() if k != opc)) if len(li) > 1 else set()
                so_esta = sorted(ids - outros, key=lambda x: ordem.get(x, 10 ** 6))
                if so_esta:
                    c = nao(inn(opc, var(wz.replace("-", "_"), [])))
                    partes_d.append({"if": [c, so_esta, []]})
                    for b in so_esta:
                        desl_b.setdefault(b, []).append(c)
        r["liga_expr"] = dumps({"merge": partes_l}) if partes_l else ""
        r["desliga_expr"] = dumps({"merge": partes_d}) if partes_d else ""
    sem_liga = []
    for r in m02:
        b = r["id"]
        if r["item_modelo"] == "OU" or r["condicao_inclusao"].startswith(("Não entra", "Nunca")):
            ex = False
        elif r["condicao_inclusao"].startswith(("SE ", "Acompanha", "Opcional")):
            if liga_b.get(b):
                ex = e(ou(*liga_b[b]), nao(ou(*desl_b[b]))) if desl_b.get(b) else ou(*liga_b[b])
            else:
                ex = False
                sem_liga.append(b)
        else:
            ex = nao(ou(*desl_b[b])) if desl_b.get(b) else True
        r["condicao_expr"] = dumps(ex)
    cols2 = list(m02[0].keys())
    cols4 = list(m04[0].keys())
    gravar_csv(pasta / "M02_tr_blocos.csv", cols2, m02, preservar=())
    gravar_csv(pasta / "M04_wizard.csv", cols4, m04, preservar=())
    from collections import Counter
    tipos = Counter("false" if r["condicao_expr"] == "false" else "true" if r["condicao_expr"] == "true" else "expressao"
                    for r in m02)
    log.append(f"M02 condicao_expr: {dict(tipos)}; condicionais sem condição de ligar: {sem_liga}")
    log.append(f"M04: liga_expr em {sum(1 for r in m04 if r['liga_expr'])} perguntas; desliga_expr em "
               f"{sum(1 for r in m04 if r['desliga_expr'])}")
    Path(sys.argv[2]).write_text("\n".join(log) + "\n", encoding="utf-8")
    print("\n".join(log[-2:]))
    print(f"menções parciais: {sum(1 for x in log if x.startswith('PARCIAL'))}")


if __name__ == "__main__":
    main()
