#!/usr/bin/env python3
"""Fase 10 - M11 em JSON Logic: condicional_expr, preenche_expr (efeito PREENCHE) e sugere_expr (efeito SUGERE).

Lido por f10_gerar_expr.py. Tradução da coluna `regra` de cada pergunta (e da M04.pre_preenchida_por, que diz quais
perguntas do checklist alimentam cada WZ). Regras de leitura:
  - preenche_expr e sugere_expr são objetos {destino: expressão}; destino WZ_xx, VAR_xxx ou itens.<atributo>;
  - só são avaliadas quando a pergunta tem resposta e a condicional_expr é verdadeira (ou vazia);
  - expressão que dá null não contribui; destino itens.<atributo> é avaliado item a item, no contexto do item, e o
    `if` diz quais itens recebem o valor;
  - destino VAR_xxx que não é atributo de item recebe a resposta da pergunta (contribuição com o ID da pergunta), salvo
    regra própria; em SUGERE só entra o que a regra diz;
  - WZ só recebe valor quando a regra do M11 ou a M04 diz qual é; quando não diz, nada é preenchido e a linha vai
    para o log (P31). Respostas compostas (WZ-15, WZ-27, WZ-34) não são preenchidas pelo checklist;
  - número só aparece como tradução literal de opção da própria pergunta ('36 meses' -> 36).
"""
import re

from jlogic import e, eq, inn, nao, ne, ou, tem, var, vazio

SIM, NAO = "Sim", "Não"
ATRIB_ITEM = {"VAR-112": "grupo", "VAR-113": "tratamento_me_epp", "VAR-114": "exige_amostra",
              "VAR-115": "marca_indicada", "VAR-116": "perecivel", "VAR-117": "validade_minima",
              "VAR-118": "quantidade_cota", "VAR-119": "valor_unidade_disputa",
              "VAR-120": "justificativa_excecao_me_epp", "VAR-121": "compatibilidade", "VAR-122": "faixa_temperatura",
              "VAR-123": "controle_especial", "VAR-124": "garantia_minima_meses", "VAR-153": "classe_pdm",
              "VAR-154": "tic", "VAR-155": "categoria", "VAR-156": "numero", "VAR-157": "catmat",
              "VAR-158": "quantidade", "VAR-159": "valor_unitario"}


def ckn(cid):
    return "CK_" + cid[3:].replace("-", "_").replace(".", "_")


def se(c, a, b=None):
    return {"if": [c, a, b]}


def r_eq(cid, valor):
    return eq(ckn(cid), valor)


def opcao_ou_texto(cid, outro="Outro", mapa=None, sufixo_outro="_texto"):
    """valor da opção; 'Outro' vira o texto escrito (ou o número lido dele, sufixo _numero, S20); mapa traduz opção
    literal em número."""
    n = ckn(cid)
    if mapa:
        partes = []
        for op, v in mapa.items():
            partes += [eq(n, op), v]
        return {"if": partes + [eq(n, outro), var(n + sufixo_outro), None]}
    return se(eq(n, outro), var(n + "_texto"), var(n))


def sim_para(cid, valor, resposta=SIM):
    return se(r_eq(cid, resposta), valor)


# --------------------------------------------------------------------------- regras explícitas
# id -> {"pre": {destino: expr}, "sug": {destino: expr}, "sem_padrao": {VAR-xxx que não recebe a resposta}}
X = {}


def regra(cid, pre=None, sug=None, sem_padrao=()):
    X[cid] = {"pre": pre or {}, "sug": sug or {}, "sem_padrao": set(sem_padrao)}


for L, O in (("C", "P"), ("P", "C")):
    regra(f"CK-{L}-CAB.01", pre={"VAR_001": se(vazio("VAR_001"), var(ckn(f"CK-{L}-CAB.01")))})
    regra(f"CK-{L}-CAB.02", pre={"VAR_006": se(vazio(ckn(f"CK-{L}-1.1")), var(ckn(f"CK-{L}-CAB.02")))})
    # S03: a seção 1 prevalece sobre o cabeçalho também para o responsável técnico
    regra(f"CK-{L}-CAB.04", pre={"VAR_007": se(vazio(ckn(f"CK-{L}-1.4")), var(ckn(f"CK-{L}-CAB.04")))})
    cat = "CONSUMO" if L == "C" else "PERMANENTE"
    regra(f"CK-{L}-1.5", pre={"WZ_07": se(tem(ckn(f"CK-{O}-1.5")), "AMBOS", cat),
                              "itens.categoria": se(vazio(ckn(f"CK-{O}-1.5")), cat)})
    regra(f"CK-{L}-1.4", pre={})  # padrão: VAR-007 e VAR-098 recebem a tabela (ver log)
    regra(f"CK-{L}-3.1", sem_padrao=("VAR-109",))
    regra(f"CK-{L}-3.3", pre={"itens.compatibilidade": se(r_eq(f"CK-{L}-3.3", SIM), var(ckn(f"CK-{L}-3.3") + "_texto"))})
    regra(f"CK-{L}-6.2", sug={})
    regra(f"CK-{L}-1.3", sug={"VAR_008": var(ckn(f"CK-{L}-1.3"))})
    regra(f"CK-{L}-6.3", pre={"itens.marca_indicada": se(tem(ckn(f"CK-{L}-6.3")), var(ckn(f"CK-{L}-6.3")))})

# consumo
C = "CK-C-"
regra(C + "1.2", sem_padrao=("VAR-064",))
regra(C + "2.3", sug={"WZ_14": se(inn("Recorrente", var(ckn(C + "2.3"), [])), "CONTINUO"), "VAR_010": var(ckn(C + "2.3"))})
regra(C + "3.4", sug={"VAR_046": se(r_eq(C + "3.4", NAO), var(ckn(C + "3.4") + "_texto"))})
regra(C + "4.4", sug={"WZ_14": sim_para(C + "4.4", "CONTINUO", "Uso contínuo"), "VAR_012": var(ckn(C + "4.4"))})
regra(C + "5.7", sem_padrao=("VAR-046",))
regra(C + "7.1", sug={"WZ_26": {"if": [r_eq(C + "7.1", SIM), "REMESSA_UNICA", r_eq(C + "7.1", NAO), "PARCELADA", None]}})
regra(C + "7.2", sug={"WZ_10": se(e(tem(ckn(C + "7.2")), nao(inn(NAO, var(ckn(C + "7.2"), [])))), "SIM")})
regra(C + "7.3", sug={"WZ_10": sim_para(C + "7.3", "SIM"), "WZ_26": sim_para(C + "7.3", "PARCELADA")})
regra(C + "7.6", sug={"WZ_10": sim_para(C + "7.6", "SIM"), "WZ_11": sim_para(C + "7.6", "GERENCIADOR")})
regra(C + "8.1", sug={})
regra(C + "8.2", pre={"itens.grupo": se(r_eq(C + "8.2", SIM), var(ckn(C + "8.2") + "_texto"))}, sem_padrao=("VAR-102",))
regra(C + "9.1", pre={"itens.exige_amostra": se(r_eq(C + "9.1", NAO), "N")})
regra(C + "9.2", pre={"itens.exige_amostra": se(tem(ckn(C + "9.2")), "S", se(r_eq(C + "9.1", SIM), "N"))})
regra(C + "10.1", sug={"WZ_56": sim_para(C + "10.1", "SIM")})
regra(C + "10.7", pre={"WZ_08": sim_para(C + "10.7", "SIM")})
regra(C + "10.8", pre={"WZ_08": sim_para(C + "10.8", "SIM")})
regra(C + "12.1", pre={"VAR_060": opcao_ou_texto(C + "12.1", mapa={"15 dias": 15, "30 dias": 30, "45 dias": 45,
                                                                     "60 dias": 60}, sufixo_outro="_numero")})
regra(C + "12.3", pre={"WZ_26": {"if": [r_eq(C + "12.3", "Única"), "REMESSA_UNICA",
                                         inn(var(ckn(C + "12.3")), ["Parcelada", "Conforme pedidos da unidade"]),
                                         "PARCELADA", None]}})
regra(C + "13.1", pre={"itens.faixa_temperatura": se(r_eq(C + "13.1", SIM), var(ckn(C + "13.1") + "_texto"))})
regra(C + "13.3", sem_padrao=("VAR-123",))
regra(C + "13.5", sug={"WZ_47": sim_para(C + "13.5", "SIM", NAO)})
regra(C + "14.1", sem_padrao=("VAR-116", "VAR-117"))
regra(C + "14.2", pre={"itens.validade_minima": opcao_ou_texto(C + "14.2", outro="Outro critério")})
regra(C + "14.4", sug={"WZ_57": sim_para(C + "14.4", "SIM"), "VAR_133": se(r_eq(C + "14.4", SIM), var(ckn(C + "14.4") + "_texto"))})
regra(C + "15.2", pre={"itens.controle_especial": se(r_eq(C + "15.2", SIM), "S")})
regra(C + "15.3", sug={"WZ_39": sim_para(C + "15.3", "SIM"), "WZ_38": sim_para(C + "15.3", ["REQUISITO_DE_LEI_ESPECIAL"]),
                       "VAR_136": sim_para(C + "15.3", ["AE para itens controlados"])})
regra(C + "16.3", pre={"VAR_074": opcao_ou_texto(C + "16.3", mapa={"2 dias": 2, "5 dias": 5, "10 dias": 10},
                                                      sufixo_outro="_numero")})
regra(C + "17.1", sug={"WZ_38": sim_para(C + "17.1", ["ATESTADOS"])})
regra(C + "17.5", pre={"WZ_39": se(tem(ckn(C + "17.5")), "SIM")})
regra(C + "18.1", sug={"WZ_29": sim_para(C + "18.1", "SIM")})
regra(C + "18.3", sug={"WZ_08": sim_para(C + "18.3", "SIM")})
regra(C + "18.4", sug={"WZ_08": sim_para(C + "18.4", "SIM")})
regra(C + "19.1", pre={"WZ_46": sim_para(C + "19.1", "SIM")})
regra(C + "19.2", pre={"WZ_46": sim_para(C + "19.2", "SIM")})
for n, resp in (("20.2", NAO), ("20.3", NAO), ("20.4", NAO), ("20.5", SIM), ("20.6", SIM), ("20.7", NAO)):
    regra(C + n, sug={"WZ_47": sim_para(C + n, "SIM", resp)})
regra(C + "21.2", pre={"WZ_47": sim_para(C + "21.2", "SIM", NAO)})

# permanentes
P = "CK-P-"
regra(P + "1.2", sem_padrao=("VAR-064",))
regra(P + "2.4", sug={"WZ_58": se(inn(var(ckn(P + "2.4")), [SIM, "Parcialmente"]), "SIM")})
regra(P + "3.7", sug={"VAR_046": se(r_eq(P + "3.7", NAO), var(ckn(P + "3.7") + "_texto"))})
regra(P + "7.1", sug={})
regra(P + "7.2", pre={"itens.grupo": se(r_eq(P + "7.2", SIM), var(ckn(P + "7.2") + "_texto"))}, sem_padrao=("VAR-102",))
regra(P + "7.5", sug={"itens.grupo": se(r_eq(P + "7.5", SIM), var(ckn(P + "7.5") + "_texto"))})
regra(P + "8.1", pre={"VAR_060": opcao_ou_texto(P + "8.1", mapa={"30 dias": 30, "60 dias": 60, "90 dias": 90,
                                                                    "120 dias": 120, "180 dias": 180}, sufixo_outro="_numero")})
regra(P + "8.3", pre={"WZ_26": {"if": [r_eq(P + "8.3", "Em remessa única por item"), "REMESSA_UNICA",
                                        inn(var(ckn(P + "8.3")), ["Em etapas previamente definidas",
                                                                   "Conforme cronograma de implantação"]),
                                        "PARCELADA", None]}})
regra(P + "8.8", pre={"WZ_47": sim_para(P + "8.8", "SIM")})
regra(P + "9.2", sug={"WZ_47": se(inn(var(ckn(P + "9.2")), [NAO, "Ainda não foi avaliada"]), "SIM")})
regra(P + "9.6", sug={"WZ_47": sim_para(P + "9.6", "SIM")})
regra(P + "9.7", sug={"WZ_46": sim_para(P + "9.7", "SIM")})
for n in ("10.1", "10.2", "10.4", "10.6", "15.1"):
    regra(P + n, pre={"WZ_46": sim_para(P + n, "SIM")})
regra(P + "10.3", pre={"WZ_47": sim_para(P + "10.3", "SIM")})
regra(P + "11.1", pre={"WZ_08": sim_para(P + "11.1", "SIM")})
regra(P + "11.2", sug={"WZ_59": sim_para(P + "11.2", "SIM")})
regra(P + "11.7", sug={"WZ_59": sim_para(P + "11.7", "SIM", NAO)})
regra(P + "12.1", pre={"WZ_08": sim_para(P + "12.1", "SIM")})
regra(P + "12.8", sug={"WZ_59": sim_para(P + "12.8", "SIM", NAO)})
regra(P + "13.1", pre={"itens.garantia_minima_meses": opcao_ou_texto(
    P + "13.1", outro="Outro: ______ meses", mapa={"12 meses": 12, "24 meses": 24, "36 meses": 36},
    sufixo_outro="_numero")},
    sem_padrao=("VAR-066",))
regra(P + "13.7", pre={"VAR_067": opcao_ou_texto(P + "13.7", mapa={"2 dias úteis": 2, "5 dias úteis": 5,
                                                                     "10 dias úteis": 10},
                                                     sufixo_outro="_numero")})
regra(P + "14.1", sug={"WZ_08": sim_para(P + "14.1", "SIM")})
regra(P + "14.2", sug={"WZ_59": sim_para(P + "14.2", "SIM")})
regra(P + "16.5", pre={"WZ_47": sim_para(P + "16.5", "SIM")})
regra(P + "17.1", pre={"itens.exige_amostra": se(r_eq(P + "17.1", NAO), "N")})
regra(P + "17.2", pre={"itens.exige_amostra": se(tem(ckn(P + "17.2")), "S", se(r_eq(P + "17.1", SIM), "N"))})
regra(P + "18.1", sug={"WZ_38": sim_para(P + "18.1", ["ATESTADOS"])})
regra(P + "18.5", sug={"WZ_38": sim_para(P + "18.5", ["REGISTRO_ENTIDADE_PROFISSIONAL"])})
regra(P + "18.6", sug={"WZ_59": sim_para(P + "18.6", "SIM")})
# P32.1 (23/10/2026): número também no 'Outro'; '30 dias' (corridos) não vira dias úteis: fica vazio e vai para revisão
regra(P + "19.3", pre={"VAR_075": opcao_ou_texto(P + "19.3", mapa={"2 dias úteis": 2, "5 dias úteis": 5, "8 dias úteis": 8,
                                                                     "15 dias úteis": 15}, sufixo_outro="_numero")})
regra(P + "19.5", pre={"VAR_074": opcao_ou_texto(P + "19.5", mapa={"5 dias": 5, "10 dias": 10, "30 dias": 30},
                                                     sufixo_outro="_numero")})
regra(P + "20.1", sug={"WZ_58": sim_para(P + "20.1", "SIM")})
regra(P + "21.4", pre={"WZ_17": sim_para(P + "21.4", "SIM")})

# WZ citadas em destinos sem valor dito na regra (log): (pergunta, WZ, motivo)
SEM_VALOR = {
    ("CK-C-3.4", "WZ-18"): "derivada da coluna marca_indicada; a regra não dá a marca, só aponta candidatos",
    ("CK-P-3.7", "WZ-18"): "derivada da coluna marca_indicada; a regra não dá a marca, só aponta candidatos",
    ("CK-C-4.4", "WZ-15"): "resposta composta (prazo e termo inicial); termo inicial é decisão da equipe",
    ("CK-C-6.2", "WZ-01"): "a regra admite duas leituras (inexigibilidade ou marca indicada)",
    ("CK-C-6.2", "WZ-04"): "a regra admite duas leituras (inexigibilidade ou marca indicada)",
    ("CK-P-6.2", "WZ-01"): "a regra admite duas leituras (inexigibilidade ou marca indicada)",
    ("CK-P-6.2", "WZ-04"): "a regra admite duas leituras (inexigibilidade ou marca indicada)",
    ("CK-C-7.1", "WZ-43"): "a regra só diz que a resposta serve de fato de apoio",
    ("CK-C-7.6", "WZ-12"): "a regra não dá o número de participantes",
    ("CK-C-8.1", "WZ-50"): "derivada da coluna grupo; a regra não dá o rótulo do grupo",
    ("CK-P-7.1", "WZ-50"): "derivada da coluna grupo; a regra não dá o rótulo do grupo",
    ("CK-C-12.1", "WZ-27"): "resposta composta (prazo, termo inicial e antecedência); o prazo vai para a VAR-060",
    ("CK-P-8.1", "WZ-27"): "resposta composta (prazo, termo inicial e antecedência); o prazo vai para a VAR-060",
    ("CK-C-16.3", "WZ-34"): "resposta composta (três prazos); o prazo de substituição vai para a VAR-074",
    ("CK-P-19.3", "WZ-34"): "resposta composta (três prazos); o prazo de recebimento vai para a VAR-075",
    ("CK-P-19.5", "WZ-34"): "resposta composta (três prazos); o prazo de substituição vai para a VAR-074",
    ("CK-C-21.1", "WZ-48"): "a regra só lista os resíduos; 'impacto relevante' é juízo da equipe",
    ("CK-C-21.1", "WZ-17"): "a regra não liga resíduo a critério de sustentabilidade",
    ("CK-C-21.3", "WZ-48"): "a regra só lista as situações; 'impacto relevante' é juízo da equipe",
    ("CK-P-21.1", "WZ-48"): "a regra só lista os resíduos; 'impacto relevante' é juízo da equipe",
    ("CK-P-21.2", "WZ-48"): "a regra só diz que há logística reversa; 'impacto relevante' é juízo da equipe",
    ("CK-P-13.1", "WZ-29"): "a regra não diz se o prazo mínimo por item implica garantia contratual",
    ("CK-P-13.7", "WZ-29"): "a regra não diz se o prazo de reparo implica garantia contratual",
    ("CK-P-4.2", "WZ-28"): "o local de instalação não é o endereço de entrega completo (perfil da OM)",
    ("CK-P-9.5", "WZ-33"): "a WZ-33 trata de infração com penalidade própria; a ligação com o site planning não tem valor "
                           "dito (ver DV-05)",
    ("CK-P-9.7", "WZ-47"): "a regra fala de obra ou serviço à parte (WZ-46), não de providência prévia",
    ("CK-P-18.6", "WZ-21"): "a regra não diz que execução por autorizado implica carta de solidariedade",
    ("CK-P-20.2", "WZ-58"): "decisão jurídica (WZ-58); a pergunta só traz o fato técnico",
    ("CK-C-14.5", "WZ-57"): "decisão jurídica (WZ-57); a pergunta só traz o fato técnico",
    ("CK-C-15.2", "WZ-38"): "a regra liga o fato ao atributo controle_especial; a exigência é decidida na WZ-38",
}


DERIVADAS = {"WZ-09", "WZ-13", "WZ-18", "WZ-20", "WZ-24", "WZ-50"}
SEM_PRE = {
    "CK-C-3.1": "a tabela anexa entra pela importação de itens (VAR-011); a VAL-048 lê a resposta",
    "CK-P-3.1": "o descritivo anexo entra pela importação de itens (VAR-011); a VAL-048 lê a resposta",
    "CK-C-14.1": "o prazo total de validade marca o item como perecível pelo M05.calculo_expr da VAR-116",
    "CK-C-15.1": "a SET-05 lê a resposta na M08.condicao_expr",
    "CK-P-16.1": "a SET-05 lê a resposta na M08.condicao_expr",
}


def condicional(cid, texto):
    if not texto:
        return None
    m = re.match(r"responder se (CK-[CP]-[\d.]+) = (.+?)(?: \(implícito\))?$", texto)
    if m:
        alvo, val = m.group(1), m.group(2)
        vals = [v.strip() for v in val.split(" ou ")]
        return eq(ckn(alvo), vals[0]) if len(vals) == 1 else inn(var(ckn(alvo)), vals)
    if texto.startswith("responder se CK-C-12.1 for diferente de 30 dias"):
        # VAR-060 recebe da CK-C-12.1 o prazo em número ('30 dias' -> 30) ou o texto de 'Outro'
        return e(tem(ckn("CK-C-12.1")), ne("VAR_060", var("parametros.prazo_entrega_referencia")))
    if texto.startswith("responder se CK-P-13.1 for maior que 12 meses"):
        return {"some": [var("itens"), {">": [var("garantia_minima_meses"), var("parametros.garantia_padrao_meses")]}]}
    raise SystemExit(f"condicional sem tradução: {cid}: {texto}")


def regras_m11(m11):
    log = []
    ids = {r["id"] for r in m11}
    for k in X:
        if k not in ids:
            raise SystemExit(f"regra para pergunta inexistente: {k}")
    out = {}
    for r in m11:
        cid, ef = r["id"], r["efeito"]
        cond = condicional(cid, r["condicional"])
        destinos = [d.strip() for d in r["destinos"].split(";") if d.strip()]
        x = X.get(cid, {"pre": {}, "sug": {}, "sem_padrao": set()})
        pre, sug = None, None
        if ef == "PREENCHE":
            pre = dict(x["pre"])
            for d in destinos:
                if d.startswith("VAR-") and d not in ATRIB_ITEM and d != "VAR-011" and d not in x["sem_padrao"]:
                    pre.setdefault(d.replace("-", "_"), var(ckn(cid)))
            if x["sug"]:
                raise SystemExit(f"{cid}: PREENCHE com sugestão")
        elif ef == "SUGERE":
            sug = dict(x["sug"])
            if x["pre"]:
                raise SystemExit(f"{cid}: SUGERE com preenchimento")
        elif x["pre"] or x["sug"]:
            raise SystemExit(f"{cid}: efeito {ef} não leva expressão nesta fase")
        exprs = (pre or {}) | (sug or {})
        for d in destinos:
            if d.startswith("WZ-") and ef in ("PREENCHE", "SUGERE") and d.replace("-", "_") not in exprs:
                motivo = SEM_VALOR.get((cid, d), "") or (
                    "pergunta derivada: o valor sai do M04.calculo_expr a partir do atributo de item preenchido"
                    if d in DERIVADAS else "")
                log.append(f"M11 {cid} ({ef}): destino {d} sem expressão; {motivo or 'a regra não diz o valor'}")
            if d.startswith("VAR-") and ef in ("PREENCHE", "SUGERE"):
                tem_expr = d.replace("-", "_") in exprs or (d in ATRIB_ITEM and f"itens.{ATRIB_ITEM[d]}" in exprs)
                if not tem_expr:
                    log.append(f"M11 {cid} ({ef}): destino {d} sem expressão"
                               + (" (atributo de item calculado ou sem valor dito na regra)" if d in ATRIB_ITEM else
                                  " (VAR-011 vem da importação da tabela)" if d == "VAR-011" else
                                  " (só sugestão explícita em SUGERE)" if ef == "SUGERE" else
                                  " (a regra pede só conferência ou o valor não sai da resposta)"))
        if ef == "PREENCHE" and not pre:
            log.append(f"M11 {cid}: PREENCHE sem expressão; " + SEM_PRE.get(
                cid, f"destinos {r['destinos']} são blocos, cláusulas ou validações que leem a resposta direto"))
        if ef == "SUGERE" and not sug:
            log.append(f"M11 {cid}: SUGERE sem expressão; a regra não dá valor a sugerir")
        out[cid] = (cond, pre or None, sug or None)
    return out, log
