#!/usr/bin/env python3
"""Teste de consistência do M04 contra o M02 por simulação de respostas (análise, não código do sistema).

Uso: python3 -I f3_simular_wizard.py <M02_tr_blocos.csv> <M04_wizard.csv> <saida.txt>

Cada cenário traz respostas do wizard e a tabela de itens (dados fictícios de teste). As perguntas derivadas
(WZ-09, WZ-13, WZ-18, WZ-20, WZ-24 e WZ-50) não são respondidas: o teste as calcula dos itens, como o M04 descreve,
e acusa erro se o cenário tentar respondê-las.

Semântica dos textos liga_blocos/desliga_blocos: um bloco condicional (condicao_inclusao iniciada por 'SE',
'Acompanha' ou 'Opcional') entra se alguma resposta o liga e nenhuma o desliga; os demais entram, salvo se desligados;
desligar vence ligar. Em pergunta MULTIPLA, opção não marcada desliga os blocos que só ela liga. Menções parciais
('trecho ... de', 'colunas de valor de', 'linha de cota em', 'Preenche') e texto entre parênteses são informativos.

Conferências por cenário:
  1. grupos GA-xx: no máximo uma opção ativa, e exatamente uma nos grupos que o cenário exige;
  2. bloco filho ativo com o pai (mesmo prefixo de numeração, presente no M02) inativo;
  3. bloco condicional sem decisão (nenhuma resposta liga ou desliga);
  4. regras de item: tratamento de ME/EPP, validade dos perecíveis, amostra fora de licitação ou dispensa eletrônica,
     grupo com um item só;
  5. quando o M02 tem condicao_expr e o M04 tem liga_expr/desliga_expr (JSON Logic), o conjunto de blocos calculado
     pelas expressões tem de ser igual ao calculado pelos textos.
"""
import csv
import json
import re
import sys
from pathlib import Path

LIMITE_EXCLUSIVO = 80000.00  # NE-003 nota 4
DERIVADAS = {"WZ-09", "WZ-13", "WZ-18", "WZ-20", "WZ-24", "WZ-50"}


def item(n, qtd, unit, grupo="", amostra="N", marca="", validade="", temperatura="", controle="N", excecao="",
         categoria="CONSUMO", garantia="", catmat="000000", tic="N"):
    return {"numero": n, "quantidade": qtd, "valor_unitario": unit, "grupo": grupo, "exige_amostra": amostra,
            "marca_indicada": marca, "validade_minima": validade, "perecivel": "S" if validade else "N",
            "faixa_temperatura": temperatura, "controle_especial": controle, "excecao": excecao,
            "justificativa_excecao_me_epp": excecao, "categoria": categoria, "garantia_minima_meses": garantia,
            "catmat": catmat, "tic": tic}


# dados fictícios de teste (quantidades e preços não vêm do corpus)
CENARIOS = {
    "C1 pregão SRP gerenciador, consumo, não contínuo, contrato, entrega parcelada": {
        "resp": {"WZ-01": "LICITACAO", "WZ-02": "PREGAO", "WZ-03": "MENOR_PRECO", "WZ-06": "COMUM", "WZ-07": "CONSUMO",
                 "WZ-08": "NAO", "WZ-10": "SIM", "WZ-11": "GERENCIADOR", "WZ-12": "2", "WZ-14": "NAO_CONTINUO",
                 "WZ-16": "DETALHADO", "WZ-17": "SIM", "WZ-19": "NAO", "WZ-21": "NAO", "WZ-22": "NAO", "WZ-23": "NAO",
                 "WZ-25": "NAO", "WZ-26": "PARCELADA", "WZ-29": "NAO", "WZ-30": "NAO", "WZ-31": "NAO", "WZ-33": "NAO",
                 "WZ-35": "NAO", "WZ-37": "SIM", "WZ-54": "ULTIMO_EXERCICIO", "WZ-55": "NAO", "WZ-38": "NENHUMA",
                 "WZ-39": "NAO", "WZ-40": "NAO", "WZ-41": "NAO", "WZ-43": "CONTRATO", "WZ-49": "SIM"},
        "pct_cota": 25,
        "itens": [item(1, 20000, 6.00, validade="12 meses"), item(2, 500, 30.00, validade="75% do prazo total")],
        "esperado": {"WZ-24": "SIM", "WZ-09": "SIM", "WZ-13": "NAO", "WZ-20": "NAO", "WZ-18": "NAO", "WZ-50": "POR_ITEM"},
    },
    "C2 dispensa por valor eletrônica, entrega imediata, sem SRP": {
        "resp": {"WZ-01": "CONTRATACAO_DIRETA", "WZ-04": "ART75_II_VALOR", "WZ-05": "SIM", "WZ-06": "COMUM",
                 "WZ-07": "CONSUMO", "WZ-08": "NAO", "WZ-10": "NAO", "WZ-14": "NAO_CONTINUO", "WZ-16": "REMISSAO",
                 "WZ-17": "SIM", "WZ-19": "NAO", "WZ-21": "NAO", "WZ-22": "NAO", "WZ-23": "NAO", "WZ-25": "NAO",
                 "WZ-26": "REMESSA_UNICA", "WZ-29": "NAO", "WZ-30": "NAO", "WZ-31": "NAO", "WZ-33": "NAO", "WZ-35": "NAO",
                 "WZ-37": "NAO", "WZ-38": "NENHUMA", "WZ-39": "NAO", "WZ-40": "NAO", "WZ-41": "NAO",
                 "WZ-43": "SUBSTITUTIVO_ENTREGA_IMEDIATA", "WZ-51": "SIM", "WZ-49": "SIM"},
        "pct_cota": None,
        "itens": [item(1, 100, 50.00), item(2, 40, 20.00)],
        "esperado": {"WZ-09": "NAO", "WZ-20": "NAO", "WZ-18": "NAO", "WZ-50": "POR_ITEM"},
    },
    "C3 emergência sem dispensa eletrônica, instrumento de pequeno valor": {
        "resp": {"WZ-01": "CONTRATACAO_DIRETA", "WZ-04": "ART75_VIII_EMERGENCIA", "WZ-05": "NAO", "WZ-06": "COMUM",
                 "WZ-07": "AMBOS", "WZ-08": "SIM", "WZ-10": "NAO", "WZ-14": "EMERGENCIAL", "WZ-16": "DETALHADO",
                 "WZ-17": "NAO", "WZ-19": "NAO", "WZ-21": "NAO", "WZ-22": "SIM", "WZ-23": "SIM", "WZ-25": "NAO",
                 "WZ-26": "REMESSA_UNICA", "WZ-29": "SIM", "WZ-30": "SIM", "WZ-31": "SIM", "WZ-33": "SIM", "WZ-35": "NAO",
                 "WZ-37": "NAO", "WZ-38": "NENHUMA", "WZ-39": "SIM", "WZ-40": "NAO", "WZ-41": "NAO",
                 "WZ-43": "SUBSTITUTIVO_PEQUENO_VALOR", "WZ-51": "NAO", "WZ-49": "SIM", "WZ-56": "NAO"},
        "pct_cota": None,
        "itens": [item(1, 10, 900.00, validade="Dois terços do prazo total"), item(2, 1, 4000.00)],
        "ck": {"CK_C_10_1": "Sim"},
        "esperado": {"WZ-09": "SIM", "WZ-18": "NAO", "WZ-50": "POR_ITEM"},
    },
    "C4 concorrência, técnica e preço, contínuo, contrato, antecipação por etapas": {
        "resp": {"WZ-01": "LICITACAO", "WZ-02": "CONCORRENCIA", "WZ-03": "TECNICA_E_PRECO", "WZ-06": "ESPECIAL",
                 "WZ-07": "PERMANENTE", "WZ-08": "SIM", "WZ-10": "NAO", "WZ-14": "CONTINUO", "WZ-16": "DETALHADO",
                 "WZ-17": "SIM", "WZ-19": "SIM", "WZ-21": "SIM", "WZ-22": "SIM_EXIGIDA_ME_EPP", "WZ-23": "SIM",
                 "WZ-25": "SIM", "WZ-26": "PARCELADA", "WZ-29": "SIM", "WZ-30": "SIM", "WZ-31": "SIM", "WZ-33": "SIM",
                 "WZ-35": "SIM", "WZ-52": "SIM", "WZ-53": "NAO", "WZ-37": "SIM", "WZ-54": "DOIS_ULTIMOS_EXERCICIOS",
                 "WZ-55": "SIM", "WZ-38": "REGISTRO_ENTIDADE_PROFISSIONAL;ATESTADOS;ATESTADO_POTENCIAL_SUBCONTRATADO",
                 "WZ-39": "NAO", "WZ-40": "SIM", "WZ-41": "SIM", "WZ-43": "CONTRATO", "WZ-49": "SIM"},
        "pct_cota": 25,
        "itens": [item(1, 1, 950000.00, amostra="S", marca="Modelo de referência X ou equivalente")],
        "esperado": {"WZ-24": "NAO", "WZ-20": "SIM", "WZ-18": "SIM", "WZ-09": "NAO", "WZ-50": "NAO_PARCELADO"},
    },
    "C5 pregão maior desconto, pequeno valor contínuo, antecipação só com garantia adicional": {
        "resp": {"WZ-01": "LICITACAO", "WZ-02": "PREGAO", "WZ-03": "MAIOR_DESCONTO", "WZ-06": "COMUM", "WZ-07": "CONSUMO",
                 "WZ-08": "NAO", "WZ-10": "NAO", "WZ-14": "CONTINUO", "WZ-16": "REMISSAO", "WZ-17": "SIM", "WZ-19": "NAO",
                 "WZ-21": "NAO", "WZ-22": "NAO", "WZ-23": "SIM", "WZ-25": "NAO", "WZ-26": "PARCELADA", "WZ-29": "NAO",
                 "WZ-30": "NAO", "WZ-31": "NAO", "WZ-33": "NAO", "WZ-35": "SIM", "WZ-52": "NAO", "WZ-53": "SIM",
                 "WZ-37": "NAO", "WZ-38": "REQUISITO_DE_LEI_ESPECIAL", "WZ-39": "NAO", "WZ-41": "NAO",
                 "WZ-43": "SUBSTITUTIVO_PEQUENO_VALOR", "WZ-51": "SIM", "WZ-49": "NAO"},
        "pct_cota": 25,
        "itens": [item(1, 300, 40.00, controle="S", validade="12 meses"), item(2, 200, 35.00, validade="12 meses")],
        "esperado": {"WZ-24": "NAO", "WZ-09": "SIM", "WZ-20": "NAO", "WZ-18": "NAO", "WZ-50": "POR_ITEM"},
    },
    "C6 misto: itens exclusivos, itens com cota e um grupo, registro de preços por menor preço": {
        "resp": {"WZ-01": "LICITACAO", "WZ-02": "PREGAO", "WZ-03": "MENOR_PRECO", "WZ-06": "COMUM", "WZ-07": "AMBOS",
                 "WZ-08": "NAO", "WZ-10": "SIM", "WZ-11": "GERENCIADOR", "WZ-12": "1", "WZ-14": "NAO_CONTINUO",
                 "WZ-16": "DETALHADO", "WZ-17": "SIM", "WZ-19": "NAO", "WZ-21": "NAO", "WZ-22": "NAO", "WZ-23": "NAO",
                 "WZ-25": "NAO", "WZ-26": "PARCELADA", "WZ-29": "NAO", "WZ-30": "NAO", "WZ-31": "NAO", "WZ-33": "NAO",
                 "WZ-35": "NAO", "WZ-37": "NAO", "WZ-38": "NENHUMA", "WZ-39": "NAO", "WZ-40": "NAO", "WZ-41": "NAO",
                 "WZ-43": "CONTRATO", "WZ-49": "SIM"},
        "pct_cota": 25,
        "itens": [
            item(1, 10000, 0.50, validade="12 meses"),                       # 5.000,00: exclusivo
            item(2, 3000, 20.00, amostra="S", validade="75% do prazo total"),  # 60.000,00: exclusivo
            item(3, 20000, 6.00, validade="Dois terços do prazo total", temperatura="2 a 8 °C"),  # 120.000,00: cota
            item(4, 9, 15000.00),                                              # 135.000,00: cota (parte inteira de 2,25 = 2)
            item(5, 4, 30000.00, grupo="G1", marca="Marca de referência Y ou equivalente"),  # grupo G1 = 128.000,00: cota
            item(6, 4, 2000.00, grupo="G1"),
            item(7, 3, 40000.00),                                              # 120.000,00, parte inteira de 0,75 = 0: ampla
        ],
        "esperado": {"WZ-24": "SIM", "WZ-13": "SIM", "WZ-20": "SIM", "WZ-18": "SIM", "WZ-09": "SIM",
                     "WZ-50": "POR_ITEM_E_GRUPO"},
        "tratamento_esperado": {1: "EXCLUSIVO", 2: "EXCLUSIVO", 3: "COTA", 4: "COTA", 5: "COTA", 6: "COTA", 7: "AMPLA"},
    },
    "C7 permanentes com instalação, treinamento, garantia de 36 meses, software e retirada do equipamento antigo": {
        "resp": {"WZ-01": "LICITACAO", "WZ-02": "PREGAO", "WZ-03": "MENOR_PRECO", "WZ-06": "COMUM", "WZ-07": "PERMANENTE",
                 "WZ-08": "SIM", "WZ-10": "NAO", "WZ-14": "NAO_CONTINUO", "WZ-16": "REMISSAO", "WZ-17": "SIM", "WZ-19": "NAO",
                 "WZ-21": "NAO", "WZ-22": "NAO", "WZ-23": "NAO", "WZ-25": "NAO", "WZ-26": "REMESSA_UNICA", "WZ-29": "SIM",
                 "WZ-30": "SIM", "WZ-31": "NAO", "WZ-33": "SIM", "WZ-35": "NAO", "WZ-37": "NAO", "WZ-38": "ATESTADOS",
                 "WZ-39": "NAO", "WZ-40": "NAO", "WZ-41": "NAO", "WZ-43": "CONTRATO", "WZ-49": "SIM", "WZ-58": "SIM",
                 "WZ-59": "NAO"},
        "pct_cota": 25,
        "itens": [item(1, 1, 450000.00, categoria="PERMANENTE", garantia=36),
                  item(2, 2, 30000.00, categoria="PERMANENTE", garantia=12)],
        "ck": {"CK_P_11_1": "Sim", "CK_P_12_1": "Sim", "CK_P_13_1": "36 meses", "CK_P_14_1": "Sim", "CK_P_15_3": "Sim",
               "CK_P_15_5": "Não", "CK_P_16_1": "Sim", "CK_P_16_6": "Sim", "CK_P_8_8": "Sim", "CK_P_19_2": "Sim",
               "CK_P_20_1": "Sim"},
        "var": {"VAR_001": "00000.000000/0000-00", "VAR_099": "DEZ/2025", "VAR_085": "fornecimento e instalação de "
                "equipamento compatível"},
        "esperado": {"WZ-24": "NAO", "WZ-09": "NAO", "WZ-20": "NAO", "WZ-18": "NAO", "WZ-50": "POR_ITEM"},
        "tratamento_esperado": {1: "AMPLA", 2: "EXCLUSIVO"},
        "sets_esperados": ["SET-05", "SET-11", "SET-12", "SET-13", "SET-14", "SET-16", "SET-17", "SET-18", "SET-19", "SET-20"],
        "vals_esperadas": ["VAL-001", "VAL-025", "VAL-026"],
    },
    "C8 consumo com comodato, temperatura, controle especial e respostas incoerentes no checklist": {
        "resp": {"WZ-01": "LICITACAO", "WZ-02": "PREGAO", "WZ-03": "MENOR_PRECO", "WZ-06": "COMUM", "WZ-07": "CONSUMO",
                 "WZ-08": "SIM", "WZ-10": "SIM", "WZ-11": "GERENCIADOR", "WZ-12": "0", "WZ-14": "NAO_CONTINUO",
                 "WZ-16": "DETALHADO", "WZ-17": "SIM", "WZ-19": "NAO", "WZ-21": "NAO", "WZ-22": "NAO", "WZ-23": "NAO",
                 "WZ-25": "NAO", "WZ-26": "PARCELADA", "WZ-29": "NAO", "WZ-30": "NAO", "WZ-31": "NAO", "WZ-33": "NAO",
                 "WZ-35": "NAO", "WZ-37": "NAO", "WZ-38": "NENHUMA", "WZ-39": "SIM", "WZ-40": "NAO", "WZ-41": "NAO",
                 "WZ-43": "CONTRATO", "WZ-49": "SIM", "WZ-56": "SIM", "WZ-57": "SIM", "WZ-59": "NAO"},
        "pct_cota": 25,
        "itens": [item(1, 5000, 4.00, validade="12 meses", temperatura="2 a 8 °C"),
                  item(2, 800, 150.00, validade="75% do prazo total", controle="S")],
        "ck": {"CK_C_10_1": "Sim", "CK_C_13_1": "Sim", "CK_C_13_4": ["Certificado de análise"], "CK_C_14_4": "Sim",
               "CK_C_15_1": "Sim", "CK_C_12_6": "Sim", "CK_C_17_5": ["Licença sanitária", "AFE"], "CK_C_18_2": ["Recall"],
               "CK_C_21_3": ["Recall"], "CK_C_20_2": "Não", "CK_C_20_3": "Sim", "CK_C_12_1": "45 dias",
               "CK_C_12_2": "Sim", "CK_C_13_5": "Sim", "CK_C_20_1": "Não"},
        "var": {"VAR_001": "00000.000000/0000-00", "VAR_099": "DEZ/2025"},
        "meta": {"textos_livres": "Bens comuns nos termos da Lei 10.520, de 2002."},
        "esperado": {"WZ-24": "SIM", "WZ-09": "SIM", "WZ-20": "NAO", "WZ-18": "NAO", "WZ-13": "NAO", "WZ-50": "POR_ITEM"},
        "tratamento_esperado": {1: "EXCLUSIVO", 2: "COTA"},
        "sets_esperados": ["SET-01", "SET-02", "SET-03", "SET-04", "SET-05", "SET-06", "SET-08", "SET-09", "SET-21",
                           "SET-22"],
        "vals_esperadas": ["VAL-004", "VAL-010", "VAL-011", "VAL-020", "VAL-022"],
    },
}


# --------------------------------------------------------------------------- derivação a partir dos itens
def unidades(itens):
    u = {}
    for it in itens:
        chave = ("G", it["grupo"]) if it["grupo"] else ("I", it["numero"])
        u.setdefault(chave, []).append(it)
    return u


def tratamento(itens, licitacao, pct):
    """Tratamento de ME/EPP por unidade de disputa (item isolado ou grupo inteiro), como WZ-24 e VAR-113 descrevem."""
    if not licitacao:
        return {}
    res = {}
    for chave, its in unidades(itens).items():
        valor = sum(i["quantidade"] * i["valor_unitario"] for i in its)
        if any(i["excecao"] for i in its):
            t = "EXCECAO_JUSTIFICADA"
        elif valor <= LIMITE_EXCLUSIVO:
            t = "EXCLUSIVO"
        elif pct and all(int(i["quantidade"] * pct / 100) >= 1 for i in its):
            t = "COTA"
        else:
            t = "AMPLA"
        for i in its:
            res[i["numero"]] = t
    return res


def derivar(resp, itens, pct):
    licit = resp.get("WZ-01") == "LICITACAO"
    trat = tratamento(itens, licit, pct)
    d = {}
    if licit:
        d["WZ-24"] = "SIM" if "COTA" in trat.values() else "NAO"
    d["WZ-09"] = "SIM" if any(i["perecivel"] == "S" for i in itens) else "NAO"
    if resp.get("WZ-10") == "SIM" and resp.get("WZ-03") in ("MENOR_PRECO", "MAIOR_DESCONTO"):
        d["WZ-13"] = "SIM" if any(i["grupo"] for i in itens) else "NAO"
    d["WZ-18"] = "SIM" if any(i["marca_indicada"] for i in itens) else "NAO"
    if licit or resp.get("WZ-05") == "SIM":
        d["WZ-20"] = "SIM" if any(i["exige_amostra"] == "S" for i in itens) else "NAO"
    us = unidades(itens)
    grupos = [k for k in us if k[0] == "G"]
    isolados = [k for k in us if k[0] == "I"]
    if len(us) == 1:
        d["WZ-50"] = "NAO_PARCELADO"
    elif grupos and isolados:
        d["WZ-50"] = "POR_ITEM_E_GRUPO"
    elif grupos:
        d["WZ-50"] = "POR_GRUPO"
    else:
        d["WZ-50"] = "POR_ITEM"
    return d, trat


def checar_itens(resp, itens, trat, pct):
    probs = []
    for chave, its in unidades(itens).items():
        valor = sum(i["quantidade"] * i["valor_unitario"] for i in its)
        t = trat.get(its[0]["numero"])
        if t == "EXCLUSIVO" and valor > LIMITE_EXCLUSIVO:
            probs.append(f"unidade {chave} EXCLUSIVO com valor {valor:.2f} acima de 80.000,00")
        if t == "COTA" and valor <= LIMITE_EXCLUSIVO:
            probs.append(f"unidade {chave} com COTA e valor até 80.000,00 (NE-022 nota 2)")
        if chave[0] == "G" and len(its) < 2:
            probs.append(f"grupo {chave[1]} com um item só")
    for i in itens:
        if i["perecivel"] == "S" and not i["validade_minima"]:
            probs.append(f"item {i['numero']} perecível sem validade mínima")
        if i["exige_amostra"] == "S" and not (resp.get("WZ-01") == "LICITACAO" or resp.get("WZ-05") == "SIM"):
            probs.append(f"item {i['numero']} com amostra fora de licitação ou dispensa eletrônica (NE-013 nota 1)")
    return probs


# --------------------------------------------------------------------------- leitura dos textos do M04
PARCIAL = re.compile(r"(?:trecho[^;|]*?\s+(?:de|em)|colunas de valor de|linha de cota em|[Pp]reenche[^;|]*?)\s+TR-[A-Za-z0-9.\-]+")


def tokens(t):
    return [m.group(0).rstrip(".-") for m in re.finditer(r"\b(?:TR-[A-Za-z0-9.\-]+|SET-\d{2})", t)]


def expande(tok, ordem, lista):
    if ".." in tok:
        a, b = tok.split("..")
        return lista[ordem[a]:ordem[b] + 1]
    return [tok]


def efeitos(campo, ordem, lista):
    """{opção: set(ids)} a partir de 'OPC1 e OPC2: ids | OPC3: ids'."""
    res = {}
    for seg in campo.split("|"):
        m = re.match(r"\s*([A-Z0-9_]+(?:(?:,\s*|\s+e\s+)[A-Z0-9_]+)*):\s*(.*)$", seg.strip(), flags=re.S)
        if not m:
            continue
        opcs = re.split(r",\s*|\s+e\s+", m.group(1))
        corpo = PARCIAL.sub("", re.sub(r"\([^()]*\)", "", m.group(2)))
        ids = set()
        for t in tokens(corpo):
            ids.update(expande(t, ordem, lista))
        for o in opcs:
            res.setdefault(o, set()).update(ids)
    return res


def pai(i, ids):
    m = re.match(r"^(TR-(?:AI-)?[\d.]+?)\.(\d+|[a-z]|[IVX]+)$", i)
    if m and m.group(1) in ids:
        return m.group(1)
    return None


# --------------------------------------------------------------------------- JSON Logic (avaliador em jlogic.py)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from jlogic import avaliar as jl  # noqa: E402


def dados_jl(resp, itens, trat, derivadas, multipla, cen):
    d = {}
    for k, v in list(resp.items()) + list(derivadas.items()):
        chave = k.replace("-", "_")
        d[chave] = [x for x in v.split(";") if x] if multipla.get(k) else v
    valor_ud = {}
    for chave, its in unidades(itens).items():
        for i in its:
            valor_ud[i["numero"]] = sum(x["quantidade"] * x["valor_unitario"] for x in its)
    d["itens"] = [dict(i, tratamento_me_epp=trat.get(i["numero"], ""), valor_unidade_disputa=valor_ud[i["numero"]])
                  for i in itens]
    d.update(cen.get("ck", {}))
    d.update(cen.get("var", {}))
    d.update(cen.get("meta", {}))
    return d


def main():
    m02 = list(csv.DictReader(open(sys.argv[1], encoding="utf-8-sig")))
    m04 = list(csv.DictReader(open(sys.argv[2], encoding="utf-8-sig")))
    pasta = Path(sys.argv[2]).parent
    m08 = list(csv.DictReader(open(pasta / "M08_clausulas_setoriais.csv", encoding="utf-8-sig"))) \
        if (pasta / "M08_clausulas_setoriais.csv").exists() else []
    m10 = list(csv.DictReader(open(pasta / "M10_validacoes.csv", encoding="utf-8-sig"))) \
        if (pasta / "M10_validacoes.csv").exists() else []
    lista = [r["id"] for r in m02]
    ordem = {k: i for i, k in enumerate(lista)}
    ids = set(lista)
    por_wz = {r["id"]: (efeitos(r["liga_blocos"], ordem, lista), efeitos(r["desliga_blocos"], ordem, lista)) for r in m04}
    multipla = {r["id"]: r["tipo_resposta"] == "MULTIPLA" for r in m04}
    grupo = {r["id"]: (r["grupo_alternativa"].split(" ")[0], r["opcao"]) for r in m02 if r["grupo_alternativa"] and r["opcao"]}
    tem_expr = "condicao_expr" in m02[0] and all(r["condicao_expr"] for r in m02 if r["item_modelo"] != "OU")
    sempre = {"GA-01", "GA-02", "GA-04", "GA-05", "GA-06", "GA-07", "GA-08", "GA-09", "GA-10"}
    linhas = []
    total = 0
    for nome, cen in CENARIOS.items():
        resp, itens, pct = cen["resp"], cen["itens"], cen["pct_cota"]
        probs = [f"{k} é derivada e não pode vir respondida no cenário" for k in resp if k in DERIVADAS]
        derivadas, trat = derivar(resp, itens, pct)
        for k, v in cen.get("esperado", {}).items():
            if derivadas.get(k) != v:
                probs.append(f"{k} derivada = {derivadas.get(k)}, esperado {v}")
        for n, t in cen.get("tratamento_esperado", {}).items():
            if trat.get(n) != t:
                probs.append(f"item {n}: tratamento {trat.get(n)}, esperado {t}")
        probs += checar_itens(resp, itens, trat, pct)
        todas = dict(resp, **derivadas)
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
        ativo, sem_decisao = set(), []
        for r in m02:
            i = r["id"]
            if r["item_modelo"] == "OU" or i in desl or r["condicao_inclusao"].startswith(("Não entra", "Nunca")):
                continue
            cond = r["condicao_inclusao"].startswith(("SE ", "Acompanha", "Opcional"))
            if not cond or i in liga:
                ativo.add(i)
            else:
                sem_decisao.append(i)
        ops = {}
        for i, (g, o) in grupo.items():
            if i in ativo:
                ops.setdefault(g, set()).add(o)
        for g, o in sorted(ops.items()):
            if len(o) > 1:
                probs.append(f"grupo {g} com mais de uma opção ativa: {sorted(o)}")
        esperados = set(sempre)
        if resp.get("WZ-49") == "SIM":
            esperados.add("GA-03")
        if resp.get("WZ-43") != "CONTRATO":
            esperados |= {"GA-11", "GA-12", "GA-13"}
        for g in sorted(esperados - set(ops)):
            probs.append(f"grupo {g} esperado e sem opção ativa")
        for i in sorted(ativo, key=ordem.get):
            p = pai(i, ids)
            if p and p not in ativo:
                probs.append(f"{i} ativo com o pai {p} inativo")
        if sem_decisao:
            probs.append(f"condicionais sem decisão ({len(sem_decisao)}): {sem_decisao}")
        # 5. JSON Logic
        jl_txt = ""
        if tem_expr:
            dados = dados_jl(resp, itens, trat, derivadas, multipla, cen)
            ativo_jl = {r["id"] for r in m02 if r["item_modelo"] != "OU" and jl(json.loads(r["condicao_expr"]), dados)}
            dif = sorted((ativo ^ ativo_jl), key=ordem.get)
            jl_txt = f"; JSON Logic: {len(ativo_jl)} blocos"
            if dif:
                probs.append(f"JSON Logic diverge dos textos em {len(dif)} blocos: {dif[:15]}")
            liga_jl, desl_jl = set(), set()
            for r in m04:
                if r.get("liga_expr"):
                    liga_jl |= set(jl(json.loads(r["liga_expr"]), dados) or [])
                if r.get("desliga_expr"):
                    desl_jl |= set(jl(json.loads(r["desliga_expr"]), dados) or [])
            if liga_jl != liga:
                probs.append(f"liga_expr diverge de liga_blocos: {sorted(liga_jl ^ liga)[:10]}")
            if desl_jl != desl:
                probs.append(f"desliga_expr diverge de desliga_blocos: {sorted(desl_jl ^ desl)[:10]}")
        if m08:
            dados = dados_jl(resp, itens, trat, derivadas, multipla, cen)
            sets = {r["id"] for r in m08 if jl(json.loads(r["condicao_expr"]), dados)}
            controlados = {x for wz in por_wz for d in por_wz[wz] for v in d.values() for x in v if x.startswith("SET-")}
            texto_sets = {x for x in liga if x.startswith("SET-")} - desl
            for x in sorted(controlados):
                if (x in sets) != (x in texto_sets):
                    probs.append(f"{x}: M08 condicao_expr {'ativa' if x in sets else 'inativa'} e M04 "
                                 f"{'liga' if x in texto_sets else 'não liga'}")
            for x in sorted(set(cen.get("sets_esperados", [])) - sets):
                probs.append(f"{x} esperada e inativa")
            jl_txt += f"; cláusulas setoriais: {sorted(sets)}"
        if m10:
            disparadas = [r["id"] for r in m10 if r["condicao_expr"] and jl(json.loads(r["condicao_expr"]), dados)]
            for x in sorted(set(cen.get("vals_esperadas", [])) - set(disparadas)):
                probs.append(f"{x} esperada e não disparada")
            for x in sorted(set(disparadas) - set(cen.get("vals_esperadas", disparadas))):
                probs.append(f"{x} disparada sem estar prevista no cenário")
            jl_txt += f"; validações disparadas: {disparadas}"
        total += len(probs)
        cont = {t: list(trat.values()).count(t) for t in sorted(set(trat.values()))}
        linhas.append(f"== {nome}")
        linhas.append(f"   blocos na minuta: {len(ativo)} de {len([r for r in m02 if r['item_modelo'] != 'OU'])}{jl_txt}; "
                      f"derivadas: {', '.join(f'{k}={v}' for k, v in sorted(derivadas.items()))}; tratamento ME/EPP: {cont}")
        linhas.append(f"   grupos ativos: {', '.join(f'{g}={sorted(o)[0]}' for g, o in sorted(ops.items()))}")
        linhas += [f"   PROBLEMA: {p}" for p in probs] or ["   sem problemas"]
    linhas.append(f"TOTAL DE PROBLEMAS: {total}")
    open(sys.argv[3], "w", encoding="utf-8").write("\n".join(linhas) + "\n")
    print("\n".join(linhas))


if __name__ == "__main__":
    main()
