#!/usr/bin/env python3
"""Fase 10 - casos de reprodução R1 (TR 23/2026) e R2 (TR 58/2026), os dois TRs da base feitos sobre o modelo DEZ/2025.

Uso: python3 -I f10_reproducao.py <pasta_Matrizes_v1> <f6_comparacao.json>

entrada: respostas do wizard tiradas do texto do TR real (trecho citado em `origem_das_respostas`), itens fictícios que
         preservam o que decide as regras (categoria, valor acima ou abaixo do limite, quantidade, garantia); sem número
         de processo, nome, endereço ou UASG. Pergunta que o TR não responde fica sem resposta.
esperado.blocos: blocos do M02 que o TR real contém (classe IGUAL ou ALTERADO na comparação do f6_comparar_trs.py),
         na ordem do M02. Tabelas, notas e separadores 'OU' não entram na comparação e ficam em blocos_nao_comparados.
esperado.clausulas_m08: cláusulas setoriais com evidência no próprio TR (coluna evidencia_corpus do M08).
esperado.validacoes_m10: validações que o M09 aponta para os desvios deste TR (tratamento_no_sistema).
esperado.perguntas_sem_resposta: perguntas aplicáveis (texto de depende_de) que o TR não permite responder.
esperado.bloqueios_grupo_alternativas: vazio, porque o TR real é documento concluído (uma opção por grupo).
divergencias_conhecidas: linhas do M09 sobre o TR. referencia.diferencas_simulacao: o que a simulação pelas
         expressões monta a mais ou a menos que o TR real; serve de ponto de partida para o Marco 1, não é erro do motor.
"""
import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from f10_simulador import DERIVADAS, aplica_texto, caminho_expr, carregar, json_num, vazio  # noqa: E402

# classificação das divergências do M09 que não são erro do TR real
CLASSIF_DV = {"DV-09": "permitido (P25): não é divergência; a exigência entra pela WZ-60 e pela SET-23, com justificativa "
                       "no ETP (VAL-053)"}

CASOS = {
    "R1": {
        "doc": "TR 23/2026", "chave": "TR_exemplos_ae4297a4_a494_4822_980f_6cbcc6b4571c_pdf",
        "descricao": "Pregão eletrônico sem registro de preços, um bem permanente (veículo com equipamentos embarcados), "
                     "fornecimento integral com instalação, treinamento e garantia técnica",
        "wizard": {
            "WZ_01": ("LICITACAO", "p.1, item 1.1: 'por meio de Pregão Eletrônico Tradicional'"),
            "WZ_02": ("PREGAO", "p.1, item 1.1"),
            "WZ_03": ("MENOR_PRECO", "item 9.1: 'critério de julgamento pelo MENOR PREÇO'"),
            "WZ_06": ("COMUM", "item 1.3: 'caracterizados como comuns'"),
            "WZ_07": ("PERMANENTE", "informações básicas: 'Bens permanentes'"),
            "WZ_08": ("SIM", "item 1.3: 'incluindo instalação de equipamentos embarcados, treinamento de operação'"),
            "WZ_10": ("NAO", "item 1.1 e DV-11: pregão sem registro de preços"),
            "WZ_14": ("NAO_CONTINUO", "item 1.1: 'com fornecimento integral'"),
            "WZ_15": ("12 meses; assinatura do contrato", "item 1.4"),
            "WZ_17": ("SIM", "item 4.1: requisitos de sustentabilidade"),
            "WZ_22": ("NAO", "item 4.2: 'Não é admitida a subcontratação'"),
            "WZ_23": ("NAO", "item 4.3: 'Não haverá exigência da garantia da contratação'"),
            "WZ_26": ("REMESSA_UNICA", "item 5.1: 'de forma integral, em remessa única'"),
            "WZ_29": ("SIM", "item 5.7: prazo de garantia técnica"),
            "WZ_31": ("SIM", "item 6.5: reunião inicial para apresentação do plano de fiscalização"),
            "WZ_33": ("SIM", "item 7.2.4.7.1: infração específica (DV-05)"),
            "WZ_35": ("NAO", "sem previsão de pagamento antecipado no TR"),
            "WZ_37": ("SIM", "itens 9.23 a 9.29: qualificação econômico-financeira"),
            "WZ_38": (["ATESTADOS", "REQUISITO_DE_LEI_ESPECIAL"], "itens 9.12 e 9.30: AFE e AE da Anvisa e atestados"),
            "WZ_39": ("SIM", "item 9.12: Autorização de Funcionamento exigida"),
            "WZ_40": ("NAO", "item 10.1: valor estimado divulgado"),
            "WZ_43": ("CONTRATO", "item 1.4: 'assinatura do contrato ou instrumento equivalente'"),
            "WZ_54": ("DOIS_ULTIMOS_EXERCICIOS", "item 9.23: 'dos dois últimos exercícios sociais'"),
            "WZ_55": ("SIM", "item 9.29: declaração de profissional contábil"),
            "WZ_60": ("SIM", "item 9.30.1.1: 'garantia mínima de 12 (doze) meses prestada ao equipamento' (P25)"),
        },
        "itens": [{"numero": 1, "quantidade": 1, "valor_unitario": 400000.00, "categoria": "PERMANENTE",
                   "garantia_minima_meses": 12, "exige_amostra": "N", "controle_especial": "N", "classe_pdm": ""}],
        "nota_itens": "um item, uma unidade, valor fictício acima do limite de participação exclusiva (o TR real tem "
                      "um item de uma unidade e valor acima desse limite); garantia mínima de 12 meses (item 5.7)",
    },
    "R2": {
        "doc": "TR 58/2026", "chave": "TR_exemplos_f518d222_2d93_4dd0_8068_55769fe133c5_pdf",
        "descricao": "Pregão eletrônico sem registro de preços, vários bens permanentes (equipamentos hospitalares), com "
                     "instalação, treinamento, garantia, subcontratação parcial e garantia da contratação",
        "wizard": {
            "WZ_01": ("LICITACAO", "item 9.1: 'Pregão'"),
            "WZ_02": ("PREGAO", "item 9.1"),
            "WZ_03": ("MENOR_PRECO", "item 9.1: 'critério de julgamento pelo MENOR PREÇO'"),
            "WZ_06": ("COMUM", "item 1.2: 'caracterizados como comuns'"),
            "WZ_07": ("PERMANENTE", "item 1.1: 'Aquisição de materiais permanentes'"),
            "WZ_08": ("SIM", "item 1.1: 'incluindo instalação, treinamento e garantia'"),
            "WZ_10": ("NAO", "item 1.6: 'não se destina à formação de ata de registro de preços'"),
            "WZ_14": ("NAO_CONTINUO", "item 9.3: 'O fornecimento do objeto será integral'"),
            "WZ_15": ("180 dias; assinatura do contrato", "item 1.3"),
            "WZ_17": ("SIM", "item 4.1: requisitos de sustentabilidade"),
            "WZ_22": ("SIM", "item 4.2: 'É permitida a subcontratação parcial'"),
            "WZ_23": ("SIM", "item 4.10: 'Será exigida a garantia da contratação'"),
            "WZ_25": ("NAO", "item 4.27: 'não enquadra-se na margem de preferência'"),
            "WZ_26": ("REMESSA_UNICA", "item 5.1: 'em remessa única'"),
            "WZ_27": ("60 dias; assinatura do contrato", "item 5.1"),
            "WZ_29": ("SIM", "item 5.5: garantia contratual complementar à legal"),
            "WZ_31": ("SIM", "item 6.5: reunião inicial"),
            "WZ_35": ("NAO", "sem previsão de pagamento antecipado no TR"),
            "WZ_37": ("SIM", "itens 9.25 a 9.31: qualificação econômico-financeira"),
            "WZ_38": (["ATESTADOS", "REQUISITO_DE_LEI_ESPECIAL"], "itens 9.33 e 9.34: AE da Anvisa e atestados (DV-06)"),
            "WZ_39": ("SIM", "item 9.33: Autorização exigida"),
            "WZ_40": ("NAO", "item 10.1: valor estimado divulgado"),
            "WZ_43": ("CONTRATO", "item 5.1: 'contados da assinatura do contrato'"),
            "WZ_49": ("SIM", "item 2.2: previsto no Plano de Contratações Anual"),
            "WZ_54": ("DOIS_ULTIMOS_EXERCICIOS", "item 9.25"),
            "WZ_55": ("SIM", "item 9.31"),
            "WZ_60": ("SIM", "item 9.34.2.1: 'garantia mínima de 12 (doze) meses prestada ao equipamento' (P25)"),
        },
        "itens": [{"numero": 1, "quantidade": 2, "valor_unitario": 350000.00, "categoria": "PERMANENTE",
                   "garantia_minima_meses": 12, "exige_amostra": "N", "controle_especial": "N", "classe_pdm": ""},
                  {"numero": 2, "quantidade": 4, "valor_unitario": 150000.00, "categoria": "PERMANENTE",
                   "garantia_minima_meses": 12, "exige_amostra": "N", "controle_especial": "N", "classe_pdm": ""},
                  {"numero": 3, "quantidade": 10, "valor_unitario": 90000.00, "categoria": "PERMANENTE",
                   "garantia_minima_meses": 12, "exige_amostra": "N", "controle_especial": "N", "classe_pdm": ""}],
        "nota_itens": "três itens fictícios acima do limite de participação exclusiva, sem cota (item 4.26: 'não será "
                      "realizada a reserva de cota'); garantia mínima de 12 meses (item 9.34.2.1)",
    },
}


def main():
    pasta = Path(sys.argv[1])
    comp = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    m = carregar(pasta)
    m09 = list(csv.DictReader(open(pasta / "M09_desvios.csv", encoding="utf-8-sig")))
    ordem = [r["id"] for r in m["M02"]]
    for cod, c in CASOS.items():
        cl = {x["bloco"]: x["classe"] for x in comp[c["chave"]]["comparacao"]}
        presentes = [b for b in ordem if cl.get(b) in ("IGUAL", "ALTERADO")]
        nao_comp = [b for b in ordem if b not in cl]
        sets = [r["id"] for r in m["M08"] if re.search(re.escape(c["doc"]) + r" \(", r["evidencia_corpus"])]
        dvs = [r for r in m09 if r["documento"].startswith(c["doc"]) or (c["doc"] in r["descricao"] or
                                                                          (r["id"] == "DV-11" and cod == "R1"))]
        vals = []
        for r in dvs:
            vals += [v for v in re.findall(r"VAL-\d{3}", r["tratamento_no_sistema"]) if v not in vals]
        entrada = {"wizard": {k: v for k, (v, _) in c["wizard"].items()}, "checklist": {},
                   "itens": c["itens"], "variaveis": {"VAR_099": "DEZ/2025", "VAR_161": 12},
                   "metadados": {}}
        resp_txt = {k.replace("_", "-"): (";".join(v) if isinstance(v, list) else v) for k, v in entrada["wizard"].items()}
        sem = [r["id"] for r in m["M04"] if r["id"] not in DERIVADAS and aplica_texto(r["depende_de"], resp_txt)
               and vazio(resp_txt.get(r["id"]))]
        # a derivada WZ-09 (perecível) e afins entram pelo cálculo; aqui só perguntas respondidas pela equipe
        obt, extra = caminho_expr(m, entrada)
        sim = obt["blocos"]
        dif = {"no_tr_e_fora_da_simulacao": [b for b in presentes if b not in sim],
               "na_simulacao_e_ausentes_no_tr": [b for b in sim if b not in presentes and b in cl]}
        doc = {
            "id": cod, "descricao": c["descricao"],
            "observacao": f"Reprodução do {c['doc']} (modelo AGU DEZ/2025). Entrada anonimizada: sem número de processo, "
                          f"nome, endereço ou UASG; itens fictícios ({c['nota_itens']}). Blocos do TR real pela "
                          f"comparação automática do f6_comparar_trs.py (difflib sobre o texto extraído, limiar 0,60), "
                          f"conferida por amostragem na Fase 6; a comparação pode errar em bloco muito alterado.",
            "entrada": entrada,
            "origem_das_respostas": {k: f"{c['doc']}, {o}" for k, (_, o) in c["wizard"].items()},
            "esperado": {"blocos": presentes, "clausulas_m08": sets, "validacoes_m10": vals,
                         "perguntas_sem_resposta": sem, "bloqueios_grupo_alternativas": []},
            "blocos_nao_comparados": nao_comp,
            "divergencias_conhecidas": [{"dv": r["id"], "classificacao": CLASSIF_DV.get(r["id"], "TR real"),
                                         "tipo": r["tipo"], "local": r["local"],
                                         "descricao": r["descricao"], "referencia": r["referencia"],
                                         "tratamento_no_sistema": r["tratamento_no_sistema"]} for r in dvs],
            "referencia": {"diferencas_simulacao": dif, "blocos_simulados": len(sim),
                           "clausulas_m08_simuladas": obt["clausulas_m08"],
                           "bloqueios_grupo_alternativas_simulados": obt["bloqueios_grupo_alternativas"],
                           "validacoes_m10_simuladas": obt["validacoes_m10"],
                           "derivadas_simuladas": extra["derivadas"],
                           "nota": "Diferença entre o TR real e a simulação não é erro do motor: vem de resposta que o "
                                   "TR não permite ler, de bloco opcional mantido ou retirado pela equipe, de texto muito "
                                   "alterado (abaixo do limiar da comparação) ou dos desvios listados."}}
        (pasta / "cenarios" / f"{cod}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1, default=json_num) + "\n",
                                                         encoding="utf-8")
        print(f"{cod} ({c['doc']}): {len(presentes)} blocos presentes, {len(nao_comp)} não comparados; M08 {sets}; "
              f"M10 {vals}; DV {[r['id'] for r in dvs]}; sem resposta {len(sem)}; simulação {len(sim)} blocos, "
              f"{len(dif['no_tr_e_fora_da_simulacao'])} no TR e fora da simulação, "
              f"{len(dif['na_simulacao_e_ausentes_no_tr'])} simulados e ausentes no TR")


if __name__ == "__main__":
    main()
