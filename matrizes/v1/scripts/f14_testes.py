#!/usr/bin/env python3
"""Testes da Fase 14 (chamados pelo f9_testes.py): mapa do M08, valores padrão marcados, motivos de revisão do M11,
decisões sobre a reprodução (R1 e R2) e TR-1.4 só para consumo. A linha de cota no fim da tabela está no f13_testes.py.

testes(pasta, M) devolve uma lista de (ok, mensagem).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f10_simulador as sim  # noqa: E402
from f11_checklist import CASOS_ESPECIFICOS, MOTIVOS_FIXOS, dados_condicional  # noqa: E402
from f13_lacunas import marcadores_m08  # noqa: E402
from f13_texto import Montagem  # noqa: E402
from jlogic import avaliar, ou  # noqa: E402

GERAIS = {"var", "==", "!=", "!", "!!", "and", "or", "if", "in", "merge", "some", "none", "<=", ">"}


def _ck(rid):
    return "CK_" + rid[3:].replace("-", "_").replace(".", "_")


def _ops(x, out):
    if isinstance(x, dict):
        for k, v in x.items():
            out.add(k)
            _ops(v, out)
    elif isinstance(x, list):
        for v in x:
            _ops(v, out)
    return out


# casos por motivo escritos à mão (id: [(dados, motivos que disparam)]); os do pedido de 23/10/2026 primeiro
CASOS_MOTIVO = {
    "CK-C-12.1": [({}, {"SEM_RESPOSTA"}),
                  ({"CK_C_12_1": "Outro", "CK_C_12_1_texto": "a combinar"}, {"OUTRO_ILEGIVEL"}),
                  ({"CK_C_12_1": "Outro", "CK_C_12_1_numero": 45}, set()),
                  ({"checklist": {"marcas_multiplas": ["CK-C-12.1"]}}, {"MARCAS_MULTIPLAS", "SEM_RESPOSTA"})],
    "CK-C-14.1": [({}, {"SEM_RESPOSTA"}),
                  ({"CK_C_14_1": "24 meses", "checklist": {"resposta_unica_por_item": ["CK-C-14.1"]}},
                   {"RESPOSTA_UNICA_POR_ITEM"}),
                  ({"CK_C_14_1": "24 meses"}, set())],
    "CK-C-14.2": [({}, {"SEM_RESPOSTA"}),
                  ({"CK_C_14_2": "12 meses", "checklist": {"resposta_unica_por_item": ["CK-C-14.2"]}},
                   {"RESPOSTA_UNICA_POR_ITEM"}),
                  ({"CK_C_14_2": "12 meses"}, set())],
    "CK-P-13.1": [({"CK_P_13_1": "Outro: ______ meses"}, {"OUTRO_ILEGIVEL"}),
                  ({"CK_P_13_1": "36 meses", "checklist": {"resposta_unica_por_item": ["CK-P-13.1"]}},
                   {"RESPOSTA_UNICA_POR_ITEM"})],
    "CK-P-19.3": [({"CK_P_19_3": "30 dias"}, {"CONTRADICAO"}), ({"CK_P_19_3": "Outro"}, {"OUTRO_ILEGIVEL"}),
                  ({"CK_P_19_3": "5 dias úteis"}, set())],
    "CK-C-9.7": [({"CK_C_9_7": "[RESPONSÁVEL]"}, {"NOME_DE_PESSOA"})],
    "CK-C-13.5": [({"CK_C_13_5": "Sim", "CK_C_20_1": "Não"}, {"DIVERGENCIA"}),
                  ({"CK_C_13_5": "Sim", "CK_C_20_1": "Sim"}, set())],
}


def testes(pasta, M):
    out = []
    reg = lambda ok, msg: out.append((ok, msg))  # noqa: E731
    vars5 = {r["id"].replace("-", "_") for r in M["M05"]}
    wz = {r["id"].replace("-", "_") for r in M["M04"]}
    cks = {_ck(r["id"]) for r in M["M11"]}
    attr = {r["nome"].split(".", 1)[1] for r in M["M05"] if r["nome"].startswith("tabela_itens.")}

    def fonte_ok(f):
        if f is None:
            return True
        if f.startswith("itens."):
            return f[6:] in attr
        base = f.removesuffix("_texto").removesuffix("_numero")
        return f in vars5 or f in wz or base in cks

    # ------------------------------------------------ 1. M08.lacunas_mapa: todo marcador, na ordem
    ruins, n = [], 0
    for r in M["M08"]:
        marc = marcadores_m08(r["texto_proposto"])
        mapa = json.loads(r["lacunas_mapa"]) if r["lacunas_mapa"] else []
        n += len(mapa)
        if [x["marcador"] for x in mapa] != marc:
            ruins.append(f"{r['id']}: {len(marc)} marcadores x {len(mapa)} no mapa")
            continue
        ult = -1
        for x in mapa:
            ps, i = [], 0
            while (p := r["texto_proposto"].find(x["marcador"], i)) >= 0:
                ps.append(p)
                i = p + len(x["marcador"])
            if ps[x["ocorrencia"] - 1] <= ult:
                ruins.append(f"{r['id']}: ordem")
            ult = ps[x["ocorrencia"] - 1]
            for f in [x.get("fonte")] + x.get("alternativas", []):
                if not fonte_ok(f):
                    ruins.append(f"{r['id']}: fonte {f}")
            if x.get("fonte") is None and x.get("acao", "PREENCHER") == "PREENCHER":
                ruins.append(f"{r['id']}: fonte null sem ação")
            if x.get("acao") == "EQUIPE" and not x.get("comentario"):
                ruins.append(f"{r['id']}: EQUIPE sem motivo")
            for ex in [x.get("quando"), x.get("filtro_item")] + [o["quando"] for o in x.get("opcoes", [])]:
                if isinstance(ex, (dict, list)) and _ops(ex, set()) - GERAIS:
                    ruins.append(f"{r['id']}: operador")
    repetidas = [r["id"] for r in M["M08"] if any(
        len([m for m in marcadores_m08(r["texto_proposto"]) if v in m]) > 1
        for v in {m[1:8] for m in marcadores_m08(r["texto_proposto"]) if m.startswith("[VAR-")})]
    reg(not ruins and n > 0, f"M08.lacunas_mapa: todo marcador do texto_proposto (colchetes de primeiro nível) aparece no "
        f"mapa, na ordem ({n} marcadores; cláusulas com a mesma VAR em vários marcadores cobertas: {repetidas}); fontes "
        f"existem; EQUIPE com motivo" + (f" | {ruins[:6]}" if ruins else ""))
    # montagem: cláusulas com a mesma VAR em vários marcadores, cada parte da sua pergunta
    m08 = {r["id"]: r for r in M["M08"]}
    d = {"CK_P_12_2": "equipe de enfermagem, 10 pessoas", "CK_P_12_3": "operação e limpeza", "CK_P_12_4": "8 horas",
         "CK_P_12_5": ["Prática presencial", "Certificado"], "CK_P_12_6": "Antes da utilização", "parametros": sim.VALORES}
    t, lac = Montagem(d).clausula(m08["SET-12"])
    alvo = ("O Contratado ministrará treinamento equipe de enfermagem, 10 pessoas, com o conteúdo mínimo operação e "
            "limpeza, carga horária mínima 8 horas e prática presencial e certificado, concluído antes da utilização.")
    t9, lac9 = Montagem({"VAR_131": "entrada pela doca", "parametros": sim.VALORES}).clausula(m08["SET-09"])
    reg(t == alvo and not lac and "entrada pela doca" in t9 and "[[LACUNA CK_X_15]]" in t9 and "[[LACUNA CK_X_16]]" in t9,
        "M08: SET-12 montada com uma pergunta por marcador (CK-P-12.2 a 12.6), sem repetir texto; SET-09 com a restrição "
        "no marcador dela e setor e antecedência nos complementos CK-X-15 e CK-X-16 (Fase 15)" + ("" if t == alvo else f" | {t}"))
    # ------------------------------------------------ 2. valor padrão marcado (P37)
    sem_marca, marcados = [], []
    for nome, linhas in (("M02", M["M02"]), ("M08", M["M08"])):
        for r in linhas:
            for x in json.loads(r.get("lacunas_mapa") or "[]"):
                for op in x.get("opcoes", []):
                    padrao_de_fato = op["quando"] is True or op["quando"] == {"var": ""}
                    if padrao_de_fato and not op.get("padrao"):
                        sem_marca.append(f"{nome} {r['id']}")
                    if op.get("padrao"):
                        marcados.append(f"{nome} {r['id']}")
    log = (pasta / "logs" / "f13_lacunas.txt").read_text(encoding="utf-8")
    fora_log = [m for m in marcados if f"padrao: {m} " not in log]
    reg(not sem_marca and not fora_log and set(marcados) == {"M02 TR-1.7", "M02 TR-AI-3.1.8.1"},
        f"P37: toda opção que entra sem valor informado tem padrao: true e está no log ({marcados})"
        + (f" | sem marca {sem_marca}; fora do log {fora_log}" if sem_marca or fora_log else ""))
    # ------------------------------------------------ 3. motivos de revisão do M11
    incoerentes, nomes_ruins, p34, n_mot = [], [], [], 0
    por_id = {r["id"]: r for r in M["M11"]}
    for r in M["M11"]:
        mot = json.loads(r["revisao_motivos"]) if r["revisao_motivos"] else []
        n_mot += len(mot)
        if any(m["motivo"] not in MOTIVOS_FIXOS for m in mot):
            nomes_ruins.append(r["id"])
        if any(m["bloqueia"] and m["motivo"] in ("SEM_RESPOSTA", "NOME_DE_PESSOA", "DIVERGENCIA") for m in mot):
            p34.append(r["id"])
        resumo = json.loads(r["revisao_expr"]) if r["revisao_expr"] else None
        bloq = [m for m in mot if m["bloqueia"]]
        pe = json.loads(r["revisao_pergunta_expr"]) if r["revisao_pergunta_expr"] else None
        if (resumo != (ou(*[m["expr"] for m in mot]) if mot else None)
                or pe != (ou(*[m["expr"] for m in bloq]) if bloq else None)
                or r["revisao_pergunta"] != " | ".join(m["texto"] for m in bloq)):
            incoerentes.append(r["id"])
    reg(not incoerentes and not nomes_ruins and not p34,
        f"M11.revisao_motivos: {n_mot} motivos em {sum(1 for r in M['M11'] if r['revisao_motivos'])} perguntas, só "
        f"motivos fixos; revisao_expr, revisao_pergunta_expr e revisao_pergunta iguais ao resumo dos motivos; sem "
        f"resposta, nome de pessoa e divergência com prevalência nunca bloqueiam (P34)"
        + (f" | {(incoerentes + nomes_ruins + p34)[:6]}" if incoerentes or nomes_ruins or p34 else ""))

    def disparam(r, dados):
        cond = json.loads(r["condicional_expr"]) if r["condicional_expr"] else None
        base = dict(dados_condicional(cond), **dados)
        base.setdefault("itens", [])
        base["parametros"] = sim.VALORES
        base["itens"] = [dict(it, parametros=sim.VALORES) for it in base["itens"]]  # item carrega as globais
        return {m["motivo"] for m in json.loads(r["revisao_motivos"]) if avaliar(m["expr"], base)}
    falhas = []
    for cid, casos in CASOS_MOTIVO.items():
        for dados, esperado in casos:
            obtido = disparam(por_id[cid], dados)
            if obtido != esperado:
                falhas.append(f"{cid}: {dados} -> {sorted(obtido)}, esperado {sorted(esperado)}")
    # cada motivo de cada pergunta dispara e não dispara em algum caso (casos gerais e os específicos da Fase 11)
    sem_par = []
    for r in M["M11"]:
        if not r["revisao_motivos"]:
            continue
        n_ = _ck(r["id"])
        casos = [d_ for d_, _ in CASOS_ESPECIFICOS.get(r["id"], [])] + [d_ for d_, _ in CASOS_MOTIVO.get(r["id"], [])]
        casos += [{}, {n_: "resposta"}, {"checklist": {"marcas_multiplas": [r["id"]]}}, {n_: "resposta", "checklist": {
            "marcas_multiplas": [r["id"]]}}]
        vistos = [disparam(r, c) for c in casos]
        for m in json.loads(r["revisao_motivos"]):
            if not (any(m["motivo"] in v for v in vistos) and any(m["motivo"] not in v for v in vistos)):
                sem_par.append(f"{r['id']} {m['motivo']}")
    textos = {m["texto"] for m in json.loads(por_id["CK-C-12.1"]["revisao_motivos"])}
    reg(not falhas and not sem_par and len(textos) == 3,
        f"M11.revisao_motivos: casos à mão de {len(CASOS_MOTIVO)} perguntas (CK-C-12.1 sem resposta não vira 'Outro "
        f"não é número'; CK-C-14.1 e 14.2 idem) e todo motivo de toda pergunta dispara e não dispara em algum caso"
        + (f" | {(falhas + sem_par)[:6]}" if falhas or sem_par else ""))
    # ------------------------------------------------ 4. reprodução: decisões de 23/10/2026
    r1 = json.loads((pasta / "cenarios" / "R1.json").read_text(encoding="utf-8"))
    r2 = json.loads((pasta / "cenarios" / "R2.json").read_text(encoding="utf-8"))
    tirar1 = {"TR-CAB.02", "TR-1.3", "TR-1.6", "TR-AI-2.1", "TR-AI-2.3", "TR-AI-4.1.7.3"}
    tirar2 = {"TR-CAB.02", "TR-1.3", "TR-1.6", "TR-5.2", "TR-AI-1.2", "TR-AI-2.1", "TR-AI-2.3", "TR-AI-3.1.10",
              "TR-AI-4.1.7.3", "TR-AI-5.11"}
    dv1 = {x["dv"] for x in r1["divergencias_conhecidas"]}
    dv2 = {x["dv"] for x in r2["divergencias_conhecidas"]}
    ok = (not tirar1 & set(r1["esperado"]["blocos"]) and not tirar2 & set(r2["esperado"]["blocos"])
          and {"TR-1.2", "TR-1.5", "TR-5.1"} <= set(r1["esperado"]["blocos"])
          and {"TR-1.2", "TR-1.5", "TR-5.1"} <= set(r2["esperado"]["blocos"])
          and {"DV-35", "DV-36", "DV-37", "DV-38", "DV-40"} <= dv1 and {"DV-37", "DV-39", "DV-41", "DV-42"} <= dv2
          and not {"DV-39", "DV-41", "DV-42"} & dv1 and not {"DV-35", "DV-36", "DV-38", "DV-40"} & dv2
          and all(x["classificacao"] == "TR real" for x in r1["divergencias_conhecidas"] + r2["divergencias_conhecidas"]
                  if x["dv"] in ("DV-35", "DV-36", "DV-37", "DV-38", "DV-39", "DV-40", "DV-41", "DV-42")))
    reg(ok, "R1 e R2: blocos achados por engano pela comparação saem do esperado (título do modelo, opção B de GA-01, "
        "GA-02 e GA-06, Anexo I), TR-5.1 entra; DV-36 a DV-42 do M09 em divergencias_conhecidas como 'TR real'")
    # TR-1.4 só para consumo
    t14 = json.loads(next(r for r in M["M02"] if r["id"] == "TR-1.4")["condicao_expr"])
    ok14 = [bool(avaliar(t14, {"WZ_07": v})) for v in ("CONSUMO", "AMBOS", "PERMANENTE")]
    reg(ok14 == [True, True, False], f"TR-1.4 (bem que não é de luxo): consumo e ambos entram, permanente não ({ok14})")
    return out
