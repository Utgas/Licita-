#!/usr/bin/env python3
"""Fase 2 - Gera M01_etp_campos.csv (campos do ETP Digital).

Uso: python3 -I f2_gerar_M01.py <f2_corpus_etp.json> <M02_tr_blocos.csv> <pasta_saida>

Fontes:
  - secoes e campos: os ETPs do corpus (impressoes do ETP Digital), pelo nome da secao (P06);
  - art. 18, § 1º (incisos) e § 2º (obrigatorios) da Lei 14.133/2021: planalto.gov.br, consultado em 21/10/2026;
  - art. 9º e § 1º da IN SEGES/ME 58/2022: gov.br/compras, consultado em 21/10/2026 (a ferramenta de leitura devolve
    resumo, por isso o vinculo e de dispositivo, sem texto literal);
  - estatistica do corpus: f2_corpus_etp.py.
Nao ha modelo oficial de ETP na base: todo texto padrao proposto e INFERIDO e vai para validacao.
Campo cuja origem principal e o DFD fica A_VERIFICAR ate os DFDs entrarem na base (P10).
"""
import csv
import json
import sys
from pathlib import Path

COLS = ["id", "secao_numero", "secao_nome", "campo", "inciso_art18", "obrigatorio_par2", "dispositivo_in58", "tipo",
        "regra_preenchimento", "regra_anti_alucinacao", "quando_nao_se_aplica", "destino_tr",
        "corpus_preenchido_omitido_na", "fonte", "status"]

LEI = "Lei 14.133/2021, art. 18 (planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm, consultado em 21/10/2026)"
IN58 = ("IN SEGES/ME 58/2022, art. 9º (gov.br/compras/pt-br/acesso-a-informacao/legislacao/instrucoes-normativas/"
        "instrucao-normativa-seges-no-58-de-8-de-agosto-de-2022, consultado em 21/10/2026)")
ANTI = "Só fatos do DFD ou do relatório, cada parágrafo com o trecho de origem; sem trecho, o campo volta vazio com a marca 'não consta no relatório'; números nunca gerados; normas só da base curada (M07)"

# id, secao, nome, campo, inciso, obrig, in58, tipo, regra, anti, nao_se_aplica, destino, origem_dfd, inferido(lista), obs
F = [
    ("ETP-01.01", "01", "Informações Básicas", "Número do processo", "", "N", "", "EU",
     "Número do processo administrativo no formato 00000.000000/0000-00, igual ao do TR (TR-CAB.04)",
     "Nunca gerar; copiar do processo e validar a máscara", "Nunca: o campo deve ser preenchido",
     "TR-CAB.04", False, ["regra_preenchimento"], "No corpus o campo aparece sem máscara em 1 ETP (330/2025)."),
    ("ETP-01.02", "01", "Informações Básicas", "UASG e nome da OM (cabeçalho)", "", "N", "", "EU",
     "Gerado pelo sistema a partir do perfil da OM", "Nunca gerar por IA", "Nunca", "TR-CAB.03", False,
     ["tipo", "regra_preenchimento"], ""),
    ("ETP-01.03", "01", "Informações Básicas", "Número e ano do ETP (cabeçalho)", "", "N", "", "EU",
     "Gerado pelo ETP Digital", "Nunca gerar por IA", "Nunca", "TR-2.1; TR-3.1 (o TR remete ao ETP)", False,
     ["tipo", "regra_preenchimento"], ""),
    ("ETP-02.01", "02", "Descrição da necessidade", "Descrição da necessidade da contratação", "I", "S", "art. 9º, I", "EU+IA",
     "Problema a resolver sob a perspectiva do interesse público: o que adquirir, para qual setor, qual problema resolve e o efeito "
     "da não contratação; registrar aqui a classificação de bem comum ou especial e sua justificativa, que o TR cita (TR-1.2/TR-1.3); "
     "subtítulos digitados pelo requisitante não são campos do sistema",
     ANTI, "Nunca: elemento obrigatório (art. 18, § 2º)", "TR-1.1; TR-1.2; TR-1.3; TR-2.1", True,
     ["tipo", "regra_preenchimento"], ""),
    ("ETP-03.01", "03", "Área requisitante", "Área requisitante", "", "N", "", "EU",
     "Nome da seção requisitante, como no DFD", "Copiar do DFD; nunca gerar", "Nunca", "", True,
     ["regra_preenchimento"], "A IN 58/2022 (art. 8º) atribui a elaboração do ETP às áreas técnica e requisitante; o campo não é inciso do art. 9º."),
    ("ETP-03.02", "03", "Área requisitante", "Responsável pela área requisitante", "", "N", "", "EU",
     "Posto ou cargo e nome do responsável, vindos do DFD", "Nas matrizes e exemplos usar [RESPONSÁVEL]; nunca copiar nomes do corpus",
     "Nunca", "", True, ["regra_preenchimento"], ""),
    ("ETP-04.01", "04", "Descrição dos Requisitos da Contratação", "Requisitos da contratação", "III", "N", "art. 9º, II", "EU+IA+OP",
     "Requisitos necessários e suficientes à escolha da solução, inclusive critérios de sustentabilidade e padrões mínimos de qualidade; "
     "aqui entram as justificativas que o TR cita: marca (TR-4.2), amostra (TR-4.4 a TR-4.14), garantia da contratação, cláusulas "
     "setoriais da OM (M08)",
     ANTI + "; cláusula setorial só do repertório curado (M08)",
     "SE a OM for participante de registro de preços ENTÃO remeter ao TR do órgão gerenciador (prática em {rem04} de {n} ETPs; achado 9) "
     "SENÃO justificar a ausência (art. 18, § 2º). Texto padrão proposto: 'Os requisitos da contratação são os definidos no Termo "
     "de Referência do órgão gerenciador da IRP nº [número].'",
     "TR-4.1.1; TR-4.1.2; TR-4.1.3; TR-4.2; TR-4.5.1; TR-4.9.1; TR-5.4.1; TR-6.15.1; TR-9.34.1.1", True,
     ["tipo", "regra_preenchimento", "quando_nao_se_aplica", "destino_tr"], ""),
    ("ETP-05.01", "05", "Levantamento de Mercado", "Levantamento de mercado e justificativa da solução", "V", "N", "art. 9º, III",
     "EU+IA",
     "Alternativas analisadas e justificativa técnica e econômica da escolha; pode incluir contratações similares (alínea a), "
     "consulta pública (b), comparação entre compra, locação ou acesso (c) e opções logísticas como doação e permuta (d); não "
     "confundir com a pesquisa de preços (IN SEGES/ME 65/2021), que fica fora do sistema",
     ANTI + "; não inventar órgãos, contratações similares nem preços",
     "SE participante de registro de preços ENTÃO remeter ao gerenciador ({rem05} de {n} ETPs) SENÃO justificar a ausência. Texto padrão "
     "proposto: 'O levantamento de mercado foi realizado pelo órgão gerenciador da IRP nº [número].'",
     "TR-3.1 (o TR remete ao ETP)", True, ["tipo", "regra_preenchimento", "quando_nao_se_aplica"], ""),
    ("ETP-06.01", "06", "Descrição da solução como um todo", "Descrição da solução como um todo", "VII", "N", "art. 9º, IV", "EU+IA",
     "Solução escolhida considerando o ciclo de vida, inclusive manutenção e assistência técnica quando for o caso; forma de "
     "fornecimento (entrega única ou parcelada, contínuo ou não), garantia do bem e demais decisões que o TR transcreve",
     ANTI, "SE participante de registro de preços ENTÃO remeter ao ETP do gerenciador ({rem06} de {n} ETPs) SENÃO justificar a ausência",
     "TR-3.1; TR-1.1; TR-1.5; TR-1.6; TR-1.7; TR-5.1; TR-5.2; TR-5.6", True,
     ["tipo", "regra_preenchimento", "quando_nao_se_aplica", "destino_tr"], ""),
    ("ETP-07.01", "07", "Estimativa das Quantidades a serem Contratadas", "Memória de cálculo das quantidades", "IV", "S",
     "art. 9º, V", "EU+IA",
     "Método da estimativa (consumo histórico, séries, sistema de controle) e documentos de suporte; a IA só estrutura a explicação",
     ANTI + "; quantidades vêm da planilha do usuário e o sistema confere se os números do texto batem com a tabela",
     "Nunca: elemento obrigatório (art. 18, § 2º)", "TR-1.1.TAB1; TR-1.1.1.TAB1", True, ["tipo", "regra_preenchimento"], ""),
    ("ETP-07.02", "07", "Estimativa das Quantidades a serem Contratadas", "Tabela de itens", "IV", "S", "art. 9º, V", "TB",
     "Item, descrição, CATMAT, unidade de fornecimento, quantidade e, quando houver, valores unitário e total",
     "Linhas vêm da planilha do usuário; nada é gerado por IA; o CATMAT é conferido no formato", "Nunca: elemento obrigatório",
     "TR-1.1.TAB1; TR-1.1.1.TAB1; TR-1.1.1.TAB2", True, ["regra_preenchimento"], ""),
    ("ETP-08.01", "08", "Estimativa do Valor da Contratação", "Valor (R$), campo do sistema", "VI", "S", "art. 9º, VI", "EU",
     "Valor total vindo da pesquisa de preços",
     "Nunca gerado; deve ser igual ao valor do texto (ETP-08.02) e à soma da tabela (ETP-07.02)",
     "Nunca: elemento obrigatório; SE orçamento sigiloso ENTÃO o valor pode ir em anexo classificado (Lei 14.133/2021, art. 18, § 1º, VI)",
     "TR-10.1; TR-10.2; TR-1.1.TAB1", False, ["regra_preenchimento"],
     "No corpus o campo aparece em {valor_sim} de {n} ETPs e diverge do texto no ETP 19/2026 (3.317,00 x 331.765,00)."),
    ("ETP-08.02", "08", "Estimativa do Valor da Contratação", "Texto da estimativa do valor", "VI", "S", "art. 9º, VI", "EU+IA",
     "Preços unitários referenciais, memórias de cálculo e documentos de suporte; fonte da pesquisa de preços",
     "Números só da pesquisa de preços; a IA não calcula nem arredonda", "Nunca: elemento obrigatório", "TR-10.1; TR-10.2; TR-10.3; TR-8.40",
     False, ["tipo", "regra_preenchimento"], ""),
    ("ETP-09.01", "09", "Justificativa para o Parcelamento ou não da Solução", "Justificativa do parcelamento", "VIII", "S",
     "art. 9º, VII", "IA+OP",
     "Adjudicação por item, grupo ou lote e a razão da escolha (NE-003 nota 2); define a estrutura da tabela de itens, a cota para ME/EPP "
     "e o critério por grupo no registro de preços",
     ANTI, "Nunca: elemento obrigatório; a remissão ao gerenciador ({rem09} de {n} ETPs) não supre a justificativa própria",
     "TR-1.1.TAB1; TR-4.41; TR-9.4; TR-9.3", False, ["tipo", "regra_preenchimento", "quando_nao_se_aplica", "destino_tr"], ""),
    ("ETP-10.01", "10", "Contratações Correlatas e/ou Interdependentes", "Contratações correlatas e/ou interdependentes", "XI", "N",
     "art. 9º, VIII", "TF+IA+OP",
     "Contratações das quais o objeto depende ou que dependem dele (manutenção, insumos, descarte)",
     ANTI, "SE não houver ENTÃO texto padrão proposto: 'Não foram identificadas contratações correlatas ou interdependentes.' "
           "({dec10} de {n} ETPs usam declaração equivalente)",
     "", False, ["tipo", "regra_preenchimento", "quando_nao_se_aplica"], ""),
    ("ETP-11.01", "11", "Alinhamento entre a Contratação e o Planejamento", "Previsão no Plano de Contratações Anual", "II", "N",
     "art. 9º, IX", "EU+TF",
     "Ano do PCA, ID PCA no PNCP, data de publicação, item, classe ou grupo e identificador da futura contratação, vindos do DFD",
     "Copiar do DFD ou do PCA; nunca gerar; ano do PCA diferente do ano da contratação gera alerta (regra a confirmar na Fase 5)",
     "SE não houver previsão no PCA ENTÃO justificar (texto do usuário)", "TR-2.2; TR-2.2.I; TR-2.2.II; TR-2.2.III; TR-2.2.IV; TR-2.2.V; TR-2.3",
     True, ["regra_preenchimento"], "No ETP 19/2026 o PCA citado é de 2025 num ETP de 2026."),
    ("ETP-12.01", "12", "Resultados Pretendidos", "Resultados pretendidos", "IX", "N", "art. 9º, X", "IA",
     "Resultados em economicidade e melhor aproveitamento dos recursos; nome alternativo no corpus: 'Benefícios a serem alcançados com a contratação' (P07)",
     ANTI + "; sem promessas genéricas que não estejam no relatório", "SE omitido ENTÃO justificar a ausência (art. 18, § 2º)",
     "", True, ["regra_preenchimento"], ""),
    ("ETP-13.01", "13", "Providências a serem Adotadas", "Providências prévias ao contrato", "X", "N", "art. 9º, XI", "IA+OP",
     "Adequações de ambiente, licenças, autorizações e capacitação de fiscais e gestores antes do contrato",
     ANTI, "SE não houver providências ENTÃO texto padrão proposto: 'Não há providências a serem adotadas pela Administração antes "
           "da celebração do contrato.' (1 ETP declara inexistência, 1 marca 'não se aplica')",
     "", False, ["tipo", "regra_preenchimento", "quando_nao_se_aplica"], ""),
    ("ETP-14.01", "14", "Possíveis Impactos Ambientais", "Impactos ambientais e medidas mitigadoras", "XII", "N", "art. 9º, XII",
     "IA+EU",
     "Impactos e medidas mitigadoras, inclusive logística reversa e descarte de resíduos de saúde; alimenta os critérios de sustentabilidade do TR",
     ANTI, "SE não houver impacto relevante ENTÃO justificar; texto padrão proposto: 'Não foram identificados impactos ambientais "
           "relevantes decorrentes da contratação além do descarte regular das embalagens.' ({na14} de {n} ETPs marca 'não se aplica')",
     "TR-4.1.1; TR-4.1.2; TR-4.1.3", False, ["tipo", "regra_preenchimento", "quando_nao_se_aplica", "destino_tr"], ""),
    ("ETP-15.01", "15", "Declaração de Viabilidade", "Declaração de viabilidade (texto do sistema)", "XIII", "S", "art. 9º, XIII", "TF",
     "Frase fixa impressa em todos os ETPs do corpus: 'Esta equipe de planejamento declara viável esta contratação.'",
     "Texto fixo; não passa pela IA", "Nunca: elemento obrigatório", "", False, ["tipo"], ""),
    ("ETP-15.02", "15", "Declaração de Viabilidade", "Justificativa da viabilidade", "XIII", "S", "art. 9º, XIII", "IA",
     "Posicionamento conclusivo sobre a adequação da contratação, compilado das seções anteriores do próprio ETP",
     "A IA só compila o que já está no ETP; sem fato novo; frase circular ('declara viável') não basta",
     "Nunca: elemento obrigatório", "", False, ["regra_preenchimento"],
     "No ETP 801/2025 a justificativa repete a declaração ('Esta equipe de planejamento declara viável.')."),
    ("ETP-16.01", "16", "Responsáveis", "Texto do sistema sobre assinaturas eletrônicas", "", "N", "", "TF",
     "Frase fixa do sistema sobre horário oficial e o Decreto 10.543/2020", "Texto fixo; não passa pela IA", "Nunca",
     "TR-ASSIN.01; TR-ASSIN.02; TR-ASSIN.03", False, ["tipo"], ""),
    ("ETP-16.02", "16", "Responsáveis", "Nome, cargo e assinatura de cada responsável", "", "N", "", "EU",
     "Integrantes designados (IN 58/2022, art. 8º: áreas técnica e requisitante ou equipe de planejamento)",
     "Nunca gerar; nas matrizes e exemplos usar [RESPONSÁVEL]", "Nunca", "TR-ASSIN.03", False, ["regra_preenchimento"], ""),
    ("ETP-90.01", "90", "Seção adicional (no corpus: 'Justificativas pontuais')", "Seção livre criada pelo requisitante", "", "N", "",
     "EU+IA",
     "Observada só no ETP 117/2025, com justificativas de qualificação técnica e de compatibilidade com o Plano de Logística "
     "Sustentável; renumera as seções seguintes. Seção opcional, sem texto padrão: só entra se o requisitante escrever",
     ANTI, "Opcional e sem texto padrão: o ETP Digital aceita a seção (P19, resposta de 23/10/2026); quando não há conteúdo "
           "próprio, não entra, e o assunto cabe em ETP-04.01 e ETP-14.01", "TR-9.34; TR-4.1", False,
     ["tipo", "regra_preenchimento", "quando_nao_se_aplica", "destino_tr"],
     "P19 fechada em 23/10/2026: o ETP Digital aceita a seção; campo opcional, sem texto padrão."),
]

ROT = {"PREENCHIDO": "preenchido", "REMISSAO": "remissão", "NAO_SE_APLICA": "não se aplica", "OMITIDO": "omitido",
       "NAO_LIDO": "não lido", "EM_BRANCO": "em branco"}


def resumo_corpus(res, sec, campo_id, etps):
    if campo_id == "ETP-08.01":
        com = [r for r, v in etps.items() if v["valor_campo"]]
        sem = [r for r, v in etps.items() if not v["valor_campo"]]
        return f"campo presente em {len(com)} de {len(etps)}; ausente em {', '.join(s.replace('ETP ', '') for s in sem)}"
    cont = res.get(sec, {})
    if not cont:
        return "sem ocorrência no corpus"
    partes = []
    for k in ("PREENCHIDO", "EM_BRANCO", "REMISSAO", "NAO_SE_APLICA", "OMITIDO", "NAO_LIDO"):
        if cont.get(k):
            txt = f"{ROT[k]} {cont[k]}"
            if k == "PREENCHIDO" and cont.get("PREENCHIDO_COM_DECLARACAO_DE_INEXISTENCIA"):
                n = cont['PREENCHIDO_COM_DECLARACAO_DE_INEXISTENCIA']
                txt += f" ({n} só declara{'m' if n > 1 else ''} inexistência)"
            partes.append(txt)
    if sec == "01" and campo_id != "ETP-01.01":
        return f"cabeçalho presente em {len(etps)} de {len(etps)}"
    if sec == "90":
        return f"observada em {cont.get('PREENCHIDO', 0)} de {len(etps)} ETPs (117/2025)"
    total = sum(v for k, v in cont.items() if k != "PREENCHIDO_COM_DECLARACAO_DE_INEXISTENCIA")
    return "; ".join(partes) + f" (de {total} ETPs)"


def detalhe(sec, etps):
    itens = []
    for rot, v in etps.items():
        x = v["secoes"].get(sec)
        if x and x["situacao"] != "PREENCHIDO":
            itens.append(f"{rot}: {ROT.get(x['situacao'], x['situacao'])}")
    return "; ".join(itens)


# origem principal dos campos que antes dependiam do DFD (P10), revista com os DFDs e os checklists da base (22/10/2026)
ORIGEM = {
    "ETP-02.01": "DFD (2. Justificativa de Necessidade) e checklist (seção 2)",
    "ETP-03.01": "DFD (área requisitante) e checklist (cabeçalho e 1.2)",
    "ETP-03.02": "DFD (Responsáveis) e checklist (1.4), com o nome nunca reproduzido nas matrizes",
    "ETP-04.01": "checklist (seções 3, 9, 12, 13, 14, 15 e 17 de consumo; 3, 8, 9, 16 e 18 de permanentes)",
    "ETP-05.01": "checklist (seção 5)",
    "ETP-06.01": "checklist (5.8 e 5.9 de consumo; 5.7 e 5.8 de permanentes)",
    "ETP-07.01": "checklist (seção 4)",
    "ETP-07.02": "DFD (3.1 Materiais: classe, PDM, descrição, quantidade e valores) e checklist (3.1, tabela anexa)",
    "ETP-11.01": "equipe administrativa (WZ-49): os DFDs e os checklists da base não trazem os dados do PCA",
    "ETP-12.01": "checklist (2.6)",
}


def main():
    corpus = json.load(open(sys.argv[1], encoding="utf-8"))
    m02 = {r["id"] for r in csv.DictReader(open(sys.argv[2], encoding="utf-8-sig"))}
    saida = Path(sys.argv[3])
    etps, res = corpus["etps"], corpus["resumo"]
    # contagens do corpus usadas nos textos das regras (calculadas aqui, nunca digitadas)
    def conta(sec, sit):
        return sum(1 for v in etps.values() if v["secoes"].get(sec, {}).get("situacao") == sit)
    CT = {"n": len(etps), "rem04": conta("04", "REMISSAO"), "rem05": conta("05", "REMISSAO"), "rem06": conta("06", "REMISSAO"),
          "rem09": conta("09", "REMISSAO"), "na14": conta("14", "NAO_SE_APLICA"),
          "valor_sim": sum(1 for v in etps.values() if v["valor_campo"]),
          "dec10": sum(1 for v in etps.values() if v["secoes"].get("10", {}).get("declara_inexistencia"))}
    linhas = []
    for (cid, sec, nome, campo, inc, obr, in58, tipo, regra, anti, nsa, destino, origem_dfd, inferido, obs) in F:
        regra, nsa, obs = (x.format(**CT) if "{" in x else x for x in (regra, nsa, obs))
        for d in [x.strip().split(" ")[0] for x in destino.split(";") if x.strip()]:
            if d not in m02:
                raise SystemExit(f"{cid}: destino {d} não existe no M02")
        cor = resumo_corpus(res, sec, cid, etps)
        # na seção 01, a situação do corpus (número do processo em branco) só vale para o campo ETP-01.01
        det = detalhe(sec, etps) if sec != "90" and (sec != "01" or cid == "ETP-01.01") else ""
        fonte = f"{LEI}" + (f"; {IN58}" if in58 else "") + \
                f"; corpus: f2_corpus_etp.py sobre os {CT['n']} ETPs (M00), seção reconhecida pelo nome (P06)"
        if det:
            fonte += f" [{det}]"
        if obs:
            fonte += f". {obs.rstrip('.')}"
        fonte += f". Campos INFERIDOS: {', '.join(inferido)}." if inferido else "."
        status = "INFERIDO" if inferido else "EXTRAIDO"
        if origem_dfd:
            origem = ORIGEM[cid]
            fonte += f" Origem principal: {origem}."
        if cid == "ETP-90.01":
            fonte += " Ver P19."
        linhas.append({
            "id": cid, "secao_numero": sec, "secao_nome": nome, "campo": campo, "inciso_art18": inc,
            "obrigatorio_par2": obr, "dispositivo_in58": f"IN SEGES/ME 58/2022, {in58}" if in58 else "", "tipo": tipo,
            "regra_preenchimento": regra, "regra_anti_alucinacao": anti, "quando_nao_se_aplica": nsa,
            "destino_tr": destino, "corpus_preenchido_omitido_na": cor, "fonte": fonte, "status": status,
        })
    saida.mkdir(parents=True, exist_ok=True)
    with open(saida / "M01_etp_campos.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS, quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(linhas)
    obrig = sorted({l["inciso_art18"] for l in linhas if l["obrigatorio_par2"] == "S"})
    print(f"M01: {len(linhas)} campos | incisos obrigatórios marcados: {obrig}")


if __name__ == "__main__":
    main()
