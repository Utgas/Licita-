#!/usr/bin/env python3
"""Fase 1 - Gera M02_tr_blocos.csv a partir dos blocos do modelo AGU (f1_blocos.json).

Uso: python3 -I f1_gerar_M02.py <f1_blocos.json> <f1_modelo.json> <pasta_saida>

Campos copiados do docx (EXTRAIDO): texto_literal, formatacao, lacunas, notas, normas, item_modelo.
Campos de desenho (INFERIDO, listados em `fonte`): tipo quando nao decorre so da formatacao,
grupo_alternativa e opcao quando o grupo nao e delimitado so por paragrafos 'OU', condicao_inclusao,
origem_dado. Origem DFD so vale para campos presentes nos DFDs da base (P10); o resto vem do checklist ou do wizard.

Tipos: TF (texto fixo), EU (entrada do usuario), IA (redacao por IA com trecho de origem),
OP (inclusao ou escolha condicional), TB (tabela de dados); combinaveis com '+'.
"""
import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # pasta dos scripts (codigo proprio)
from f1_blocos import lacunas as achar_lacunas, normas as achar_normas  # noqa: E402
from comum import gravar_csv  # noqa: E402

COLS = ["id", "secao", "item_modelo", "texto_literal", "formatacao", "tipo", "grupo_alternativa", "opcao",
        "lacunas", "notas", "condicao_inclusao", "condicao_expr", "origem_dado", "normas", "fonte", "status"]
# condicao_expr (JSON Logic) é calculada pelo f6_gerar_expr.py a partir dos liga/desliga do M04 e preservada aqui

DOCX = "TR exemplos/modelo-de-termo-de-referencia-compras-lei-no-14-133-dez-25.docx"
ANEXO_I = "SE o contrato for substituído por instrumento equivalente (art. 95, I ou II, da Lei 14.133/2021; NE-083)"
ANEXO_II = "SE o contrato for substituído por instrumento equivalente (art. 95, I e II; NE-102)"

# --------------------------------------------------------------------------- regras curadas
# Cada regra: seletor (lista de IDs ou ('faixa', primeiro, ultimo) em ordem do documento) e campos.
# 'inferido' lista os campos que sao desenho e nao copia do modelo.
R = []


def regra(sel, **campos):
    R.append((sel, campos))


def faixa(a, b):
    return ("faixa", a, b)


# Cabecalho
regra(["TR-CAB.01", "TR-CAB.02"], tipo="TF",
      condicao="Não entra na minuta: é o título do modelo AGU; o TR Digital gera cabeçalho próprio (TRs do corpus)",
      origem="MODELO", inferido=["condicao_inclusao"])
regra(["TR-CAB.03"], tipo="EU", condicao="Sempre: substituir pela identificação do órgão ou entidade",
      origem="SISTEMA (perfil da OM do usuário)", inferido=["origem_dado"])
regra(["TR-CAB.04"], tipo="TF+EU", condicao="Sempre", origem="ETP:ETP-01.01 (número do processo)",
      inferido=["origem_dado"])
# Secao 1
regra(["TR-1.1"], tipo="TF+EU",
      origem="ETP:ETP-02.01 e ETP-06.01 (objeto); WIZARD (atividades incluídas, como instalação e montagem)",
      inferido=["origem_dado"])
regra(["TR-1.1.TAB1"], tipo="TB",
      condicao="Sempre (tabela ilustrativa, que pode ser alterada: NE-003 nota 1); colunas de valor em branco se orçamento "
               "sigiloso (NE-004); uma linha de cota reservada por item ou grupo com COTA, com o item ou grupo de origem "
               "(NE-022 nota 1; WZ-24 derivada); colunas de grupo, marca e validade mínima só quando algum item as tiver",
      origem="Tabela de itens VAR-011 (itens, CATMAT, unidade, quantidade, grupo, tratamento ME/EPP, marca, validade); "
             "PESQUISA_PRECOS (valores unitário e total); SISTEMA (linhas de cota, VAR-118)",
      inferido=["condicao_inclusao", "origem_dado"])
regra(["TR-1.1.1"], tipo="OP+TF",
      condicao="SE registro de preços (trecho com realce ciano, cor usada no modelo para os itens de SRP; P12)",
      origem="MODELO", inferido=["condicao_inclusao"])
regra(["TR-1.1.1.TAB1", "TR-1.1.1.TAB2", "TR-1.1.1.TAB3"], tipo="OP+TB",
      condicao="SE registro de preços; TAB1 para o órgão gerenciador e uma tabela por órgão participante",
      origem="ETP:ETP-07.02; WIZARD (quantidades mínima, máxima e total por órgão)",
      inferido=["condicao_inclusao", "origem_dado"])
regra(["TR-1.2"], grupo="GA-01", opcao="A",
      condicao="SE bem comum, com justificativa no ETP (NE-005: art. 6º, XIII e XIV)",
      origem="WIZARD (classificação); ETP (justificativa)", inferido=["condicao_inclusao", "origem_dado"])
regra(["TR-1.2.OU"], grupo="GA-01")
regra(["TR-1.3"], grupo="GA-01", opcao="B", condicao="SE bem especial, com justificativa no ETP (NE-005)",
      origem="WIZARD (classificação); ETP (justificativa)", inferido=["condicao_inclusao", "origem_dado"])
regra(["TR-1.4"], condicao="SE bens de consumo (NE-006 remete ao art. 20 da Lei 14.133/2021, sobre itens de consumo, "
                           "e ao Decreto 10.818/2021); para bens permanentes, decisão do usuário",
      inferido=["condicao_inclusao"])
regra(["TR-1.5"], grupo="GA-02", opcao="A", condicao="SE fornecimento não contínuo (art. 105; NE-007)",
      origem="WIZARD (prazo e termo inicial)", inferido=["condicao_inclusao", "origem_dado"])
regra(["TR-1.5.OU", "TR-1.7.OU"], grupo="GA-02")
regra(["TR-1.6"], grupo="GA-02", opcao="B",
      condicao="SE fornecimento contínuo (arts. 106 e 107; NE-007 nota 3: exige ateste de maior vantagem econômica)",
      origem="WIZARD (prazo, até 5 anos, e termo inicial)", inferido=["condicao_inclusao", "origem_dado"])
regra(["TR-1.7"], grupo="GA-02", opcao="B", tipo="OP+IA+EU",
      condicao="SE fornecimento contínuo: justificativa do enquadramento e da vigência plurianual",
      origem="ETP (justificativa, com trecho de origem); WIZARD (escolha entre texto livre, remissão ao ETP ou Nota Técnica)",
      inferido=["tipo", "condicao_inclusao", "origem_dado"])
regra(["TR-1.8"], grupo="GA-02", opcao="C",
      condicao="SE dispensa por emergência ou calamidade (art. 75, VIII; NE-007 nota 4: até 1 ano, improrrogável)",
      origem="WIZARD (prazo e termo inicial)", inferido=["condicao_inclusao", "origem_dado"])
# Secao 2
regra(["TR-2.2", "TR-2.2.I", "TR-2.2.II", "TR-2.2.III", "TR-2.2.IV", "TR-2.2.V"], grupo="GA-03", opcao="A",
      condicao="SE os dados do PCA forem detalhados no próprio TR",
      origem="WIZARD (vínculo com o item do PCA, informado pela equipe administrativa: ID PCA no PNCP, data de publicação, id do item, classe/grupo, "
             "identificador da futura contratação); ETP:ETP-11.01",
      inferido=["condicao_inclusao", "origem_dado"])
regra(["TR-2.2.V.OU"], grupo="GA-03")
regra(["TR-2.3"], grupo="GA-03", opcao="B",
      condicao="SE os dados do PCA já constarem das informações básicas do TR Digital",
      origem="WIZARD (ano do PCA); ETP:ETP-11.01", inferido=["condicao_inclusao", "origem_dado"])
# Secao 4 - sustentabilidade, marca, amostra, carta
regra(["TR-4.H01", "TR-4.1"],
      condicao="Sempre, salvo justificativa nos autos para não adotar critérios de sustentabilidade (NE-011 nota 5)",
      inferido=["condicao_inclusao"])
regra(["TR-4.1.1", "TR-4.1.2", "TR-4.1.3"],
      condicao="Sempre, salvo justificativa (NE-011 nota 5); um subitem por critério, com forma objetiva de comprovação (NE-011 nota 7)",
      origem="ETP:ETP-04.01 ou ETP-14.01 (critérios de sustentabilidade)", inferido=["condicao_inclusao", "origem_dado"])
regra(["TR-4.H02", "TR-4.2"], condicao="SE existir item com marca ou modelo indicado (WZ-18 derivada), com justificativa no "
                                       "ETP (art. 41, I; NE-012)",
      origem="SISTEMA (itens com marca indicada, VAR-115); ETP:ETP-04.01 (justificativa)", inferido=["condicao_inclusao", "origem_dado"])
regra(["TR-4.H03", "TR-4.3", "TR-4.3.1.1", "TR-4.3.1.2"],
      condicao="SE houver processo administrativo que fundamente a vedação de marca ou produto",
      origem="WIZARD (número do processo; produtos ou marcas vedados)", inferido=["condicao_inclusao", "origem_dado"])
regra([faixa("TR-4.H04", "TR-4.14")],
      condicao="SE existir item com amostra (WZ-20 derivada), com justificativa no ETP (NE-013 notas 2 e 3); em contratação "
               "direta, só na dispensa eletrônica (NE-013 nota 1)",
      inferido=["condicao_inclusao"])
regra(["TR-4.5.1", "TR-4.5.2", "TR-4.5.3"], origem="SISTEMA (itens com exige_amostra = S, VAR-114; uma linha por item)",
      inferido=["origem_dado"])
regra(["TR-4.9.1", "TR-4.9.2"], origem="ETP:ETP-04.01 (padrões mínimos de cada item com amostra, VAR-051)",
      inferido=["origem_dado"])
regra(["TR-4.6", "TR-4.13"], origem="WIZARD (endereço e prazos)", inferido=["origem_dado"])
regra(["TR-4.H05", "TR-4.15"], condicao="SE situação excepcional e motivada (NE-014)", inferido=["condicao_inclusao"])
# Subcontratacao
regra(["TR-4.16"], grupo="GA-04", opcao="A", condicao="SE subcontratação vedada (NE-015)", inferido=["condicao_inclusao"])
regra(["TR-4.16.OU"], grupo="GA-04")
regra([faixa("TR-4.17", "TR-4.23")], grupo="GA-04", opcao="B",
      condicao="SE permitida subcontratação parcial, com limites e parcelas definidos (NE-016 nota 2)",
      inferido=["condicao_inclusao"])
regra(["TR-4.17"], origem="WIZARD (percentual máximo)", inferido=["origem_dado"])
regra(["TR-4.18.1", "TR-4.18.2", "TR-4.18.3", "TR-4.19.1", "TR-4.19.2", "TR-4.19.3"],
      origem="ETP:ETP-06.01; WIZARD (parcelas vedadas e permitidas)", inferido=["origem_dado"])
# Garantia da contratacao
regra(["TR-4.24"], grupo="GA-05", opcao="A",
      condicao="SE não exigida garantia da contratação, com razões no ETP (NE-017 nota 1)", inferido=["condicao_inclusao"])
regra(["TR-4.24.OU"], grupo="GA-05")
regra([faixa("TR-4.25", "TR-4.40")], grupo="GA-05", opcao="B",
      condicao="SE exigida garantia da contratação (arts. 96 e seguintes; NE-017)", inferido=["condicao_inclusao"])
regra(["TR-4.25"], origem="WIZARD (percentual: até 5%, ou até 10% com justificativa; base total ou anual conforme NE-017 notas 2 e 3)",
      inferido=["origem_dado"])
# Cotas e margem
regra(["TR-4.H08"], condicao="Acompanha TR-4.41: sem cota reservada, o subtítulo fica sem conteúdo",
      inferido=["condicao_inclusao"])
regra(["TR-4.41", "TR-4.41.1", "TR-4.41.2", "TR-4.41.3"],
      condicao="SE licitação com item ou grupo com COTA (WZ-24 derivada: tratamento calculado por item ou grupo na VAR-011; "
               "cota de até 25%, art. 48, III, da LC 123/2006; NE-022), salvo exceção justificada do art. 10 do Decreto "
               "8.538/2015; não cabe nos itens e grupos exclusivos de até R$ 80.000,00 (NE-022 nota 2)",
      origem="SISTEMA (tratamento por item ou grupo, VAR-113; percentual da cota, VAR-057); ETP:ETP-09.01",
      inferido=["condicao_inclusao", "origem_dado"])
regra(["TR-4.H09"], condicao="Acompanha TR-4.42", inferido=["condicao_inclusao"])
regra(["TR-4.42"], condicao="SE o objeto estiver contemplado por margem de preferência em resolução da CICS (NE-023)",
      origem="WIZARD (normal ou adicional, percentual, decreto, resolução e enquadramento)",
      inferido=["condicao_inclusao", "origem_dado"])
# Secao 5
regra(["TR-5.1"], grupo="GA-06", opcao="A", condicao="SE entrega em remessa única",
      origem="WIZARD (prazo em dias e termo inicial); ETP:ETP-06.01", inferido=["condicao_inclusao", "origem_dado"])
regra(["TR-5.1.OU"], grupo="GA-06")
regra(["TR-5.2", "TR-5.2.TAB1"], grupo="GA-06", opcao="B", condicao="SE entrega parcelada (NE-025)",
      origem="WIZARD (parcelas, composição e prazos); ETP:ETP-06.01", inferido=["condicao_inclusao", "origem_dado"])
regra(["TR-5.3"], condicao="Sempre que houver prazo de entrega (vermelho itálico sem nota)",
      origem="WIZARD (antecedência em dias)", inferido=["condicao_inclusao", "origem_dado"])
regra(["TR-5.4"], condicao="Sempre que houver entrega física; com mais de um endereço, especificar cada um (NE-026)",
      origem="SISTEMA (endereço cadastrado da OMS requisitante); CHECKLIST (OMS e setor, CK-C-1.1 e CK-C-1.2; local por item, CK-P-4.2; agendamento e restrições de acesso, CK-C-12.6, CK-C-12.7, CK-P-8.5, CK-P-8.6)", inferido=["condicao_inclusao", "origem_dado"])
regra(["TR-5.4.1"], condicao="SE existir item perecível (WZ-09 derivada); validade mínima por item (VAR-117), sem valor "
                              "padrão (P21): valor único nas lacunas quando for igual para todos os perecíveis, senão coluna "
                              "na tabela do item 1.1 (NE-003 nota 1) e remissão a ela (P22)",
      origem="WIZARD (validade mínima por item, VAR-117)", inferido=["condicao_inclusao", "origem_dado"])
regra(["TR-5.5"], grupo="GA-07", opcao="A",
      condicao="SE sem garantia contratual do bem; redação sugerida para material de consumo (NE-028)",
      inferido=["condicao_inclusao"])
regra(["TR-5.5.OU"], grupo="GA-07")
regra([faixa("TR-5.6", "TR-5.17")], grupo="GA-07", opcao="B",
      condicao="SE exigida garantia contratual do bem, com justificativa (NE-027; NE-029: redação sugerida para material permanente)",
      inferido=["condicao_inclusao"])
regra(["TR-5.6", "TR-5.12"], origem="WIZARD (prazo de garantia em meses; prazo de reparo em dias úteis)",
      inferido=["origem_dado"])
# Secao 6
regra(["TR-6.5"], condicao="Opcional (vermelho itálico sem nota): reunião inicial com plano de fiscalização",
      inferido=["condicao_inclusao"])
regra(["TR-6.15", "TR-6.15.1", "TR-6.15.2", "TR-6.15.3"],
      condicao="SE houver rotinas de fiscalização específicas do objeto (NE-032)",
      origem="ETP:ETP-04.01; WIZARD", inferido=["condicao_inclusao", "origem_dado"])
# Secao 7
regra(["TR-7.2.4.1"], condicao="Sempre que prevista multa moratória; percentual diário e limite de dias definidos pela OM (NE-033)",
      origem="WIZARD (parâmetros da OM)", inferido=["condicao_inclusao", "origem_dado"])
regra(["TR-7.2.4.2", "TR-7.2.4.2.1"], condicao="SE exigida garantia da contratação (NE-034 nota 2)",
      inferido=["condicao_inclusao"])
regra([faixa("TR-7.2.4.3", "TR-7.2.4.7")],
      condicao="Sempre; percentuais entre 0,5% e 30% do valor do contrato (art. 156, § 3º, citado na NE-036), maiores para infrações mais graves (NE-035)",
      origem="WIZARD (parâmetros da OM)", inferido=["condicao_inclusao", "origem_dado"])
# texto sugerido nas notas e incluído por decisão do usuário (P17)
NE016_COND = ("SE subcontratação de ME/EPP exigida (WZ-22 = SIM_EXIGIDA_ME_EPP), só em aquisição com serviço acessório "
              "(WZ-08 = SIM; NE-016 nota 3)")
regra([faixa("TR-NE016.01", "TR-NE016.08")], grupo="GA-04", opcao="B", condicao=NE016_COND,
      origem="MODELO (NE-016 nota 3)", inferido=["condicao_inclusao", "grupo_alternativa"])
regra(["TR-NE016.02", "TR-NE016.03", "TR-NE016.04"], origem="MODELO (NE-016 nota 3); WIZARD (percentuais mínimo e máximo e parcelas)",
      inferido=["origem_dado"])
regra(["TR-NE071.01"], condicao="SE admitidos atestados de potencial subcontratado (WZ-38 = ATESTADO_POTENCIAL_SUBCONTRATADO, que "
                                "exige subcontratação permitida na WZ-22; NE-071 nota 4)",
      origem="MODELO (NE-071 nota 4); WIZARD (parcela do fornecimento)", inferido=["condicao_inclusao", "origem_dado"])
# observações ligadas às perguntas abertas
regra(["TR-1.7"], obs="O parágrafo começa com o número '1.6.1' digitado no texto, e o Word exibe '1.7. 1.6.1' (P18).")
regra(["TR-5.3", "TR-5.4", "TR-7.2.4.1", "TR-7.2.4.3", "TR-7.2.4.4", "TR-7.2.4.5", "TR-7.2.4.6"],
      obs="Inteiro em vermelho itálico e tratado como EU, sempre incluído (P20).")
regra(["TR-ASSIN.03"], obs="Texto em preto que funciona como rótulo de preenchimento (P20).")
regra([faixa("TR-AI-5.1", "TR-AI-5.3.2")], obs="Opção usada também no pequeno valor sem fornecimento contínuo, por inferência (P14).")
regra(["TR-10.1", "TR-10.3", "TR-10.3.1"], obs="Usado também em técnica e preço e na contratação direta, por analogia (P15).")
regra([faixa("TR-AI-4.1.22", "TR-AI-4.1.26")], obs="Inclusão decidida pela WZ-51, com padrão SIM (P16).")
# bloco que é inteiro um marcador de preenchimento (sem colchetes nem pontilhado)
regra(["TR-CAB.03"], lacunas_extra=["ÓRGÃO OU ENTIDADE PÚBLICA"], inferido=["lacunas"])
# vermelho itálico com inclusão "Sempre": variável (EU), não opcional; TR-7.2.4.7 mantém OP pelo trecho entre colchetes
regra(["TR-5.3", "TR-5.4", "TR-7.2.4.1", "TR-7.2.4.3", "TR-7.2.4.4", "TR-7.2.4.5", "TR-7.2.4.6"], tipo="EU", inferido=["tipo"])
regra(["TR-7.2.4.7"], tipo="EU+OP", inferido=["tipo"])
regra(["TR-7.2.4.7.1"], condicao="SE houver infrações de inexecução parcial com penalidade diversa",
      origem="WIZARD", inferido=["condicao_inclusao", "origem_dado"])
regra(["TR-7.7"], origem="WIZARD (prazo de recolhimento da multa)", inferido=["origem_dado"])
# Secao 8
regra(["TR-8.2"], origem="WIZARD (prazo de substituição em dias)", inferido=["origem_dado"])
regra(["TR-8.3"], origem="WIZARD (dias úteis; NE-038: recebimento e liquidação cabem em 10 dias úteis)", inferido=["origem_dado"])
regra(["TR-8.4"], origem="WIZARD (dias úteis; NE-039: metade do prazo)", inferido=["origem_dado"])
regra(["TR-8.21"], origem="WIZARD (índice de correção monetária; NE-040)", inferido=["origem_dado"])
regra([faixa("TR-8.H05", "TR-8.37")],
      condicao="SE adotado pagamento antecipado, com justificativa prévia (art. 145, § 1º; NE-042 e NE-043)",
      origem="WIZARD (forma, valores, etapas, prazos, índice)", inferido=["condicao_inclusao", "origem_dado"])
regra(["TR-8.36.1"], condicao="SE antecipação também durante a execução (NE-045)", inferido=["condicao_inclusao"])
regra(["TR-8.36.2"], condicao="SE exigida garantia adicional, não superior ao valor antecipado (NE-046)",
      inferido=["condicao_inclusao"])
regra(["TR-8.40"], origem="PESQUISA_PRECOS (data-base do orçamento estimado; NE-051)", inferido=["origem_dado"])
regra(["TR-8.41"], origem="WIZARD (índice, de preferência setorial ou específico; NE-052)", inferido=["origem_dado"])
# Secao 9
regra(["TR-9.1"], grupo="GA-08", opcao="A",
      condicao="SE licitação: pregão para bens comuns, concorrência para bens especiais (NE-054 nota 2)",
      origem="WIZARD (modalidade e critério de julgamento)", inferido=["condicao_inclusao", "origem_dado"])
regra(["TR-9.1.OU"], grupo="GA-08")
regra(["TR-9.2"], grupo="GA-08", opcao="B", tipo="OP+EU+IA",
      condicao="SE contratação direta (dispensa ou inexigibilidade); adequar o título da subseção (NE-054 nota 1)",
      origem="WIZARD (artigo, inciso e fundamentação, decisão da equipe administrativa); CHECKLIST (fatos de exclusividade, seção 6)", inferido=["tipo", "condicao_inclusao", "origem_dado"])
regra(["TR-9.3"], origem="WIZARD (integral, parcelado ou continuado; coerente com GA-02 e GA-06)", inferido=["origem_dado"])
regra(["TR-9.H03"], condicao="Acompanha TR-9.4 (subtítulo com realce ciano, de SRP; P12)", inferido=["condicao_inclusao"])
regra(["TR-9.4", "TR-9.4.1"],
      condicao="SE registro de preços com grupo de itens e critério de menor preço ou maior desconto (WZ-13 derivada; NE-055)",
      origem="WIZARD (planilha anexa ou item do TR)", inferido=["condicao_inclusao", "origem_dado"])
regra(["TR-9.14"], condicao="SE a atividade exigir autorização ou registro para funcionamento (NE-060)",
      origem="WIZARD (atividade, órgão expedidor e fundamento legal)", inferido=["condicao_inclusao", "origem_dado"])
regra([faixa("TR-9.H07", "TR-9.32")], tipo_preto="OP+TF",
      condicao="SE exigida qualificação econômico-financeira (NE-063: pode ser restrita a itens ou suprimida; "
               "excepcional nos casos do art. 70, III)", inferido=["tipo", "condicao_inclusao"])
regra(["TR-9.26.TAB1", "TR-9.26.TAB2", "TR-9.26.TAB3"], tipo="OP+TF", inferido=["tipo"])
regra(["TR-9.26"], origem="WIZARD (último ou dois últimos exercícios; NE-064)", inferido=["origem_dado"])
regra(["TR-9.27"], origem="WIZARD (capital ou patrimônio líquido mínimo, até 10%, e base; NE-065)", inferido=["origem_dado"])
regra(["TR-9.28"], condicao="SE exigidas as demonstrações dos dois últimos exercícios (NE-066)", inferido=["condicao_inclusao"])
regra(["TR-9.32"], condicao="SE adotada declaração de profissional contábil, com justificativa (NE-067)",
      inferido=["condicao_inclusao"])
regra(["TR-9.H08"], tipo="OP+TF",
      condicao="SE exigida qualificação técnica, com justificativa no ETP (NE-068 e NE-069); em contratação direta sem "
               "dispensa eletrônica pode ficar só no processo (NE-068 nota 1)", inferido=["tipo", "condicao_inclusao"])
regra(["TR-9.33", "TR-9.33.1"],
      condicao="SE a lei sujeitar a atividade à entidade profissional competente (NE-070)",
      origem="WIZARD (entidade profissional)", inferido=["condicao_inclusao", "origem_dado"])
regra([faixa("TR-9.34", "TR-9.34.4")],
      condicao="SE houver atividade associada ao fornecimento que justifique atestados (NE-071), com quantitativos objetivos",
      origem="ETP:ETP-04.01; WIZARD (características mínimas dos atestados)", inferido=["condicao_inclusao", "origem_dado"])
regra(["TR-9.35"], condicao="SE lei específica exigir requisito técnico para a atividade (NE-073, que dá como exemplo a "
                            "Autorização Especial da Anvisa para medicamentos sujeitos a controle especial)",
      origem="WIZARD (requisito e lei)", inferido=["condicao_inclusao", "origem_dado"])
# Secao 10
regra(["TR-10.1"], grupo="GA-09", opcao="A", condicao="SE critério de menor preço sem sigilo (NE-074 nota 3)",
      origem="PESQUISA_PRECOS (valor total); WIZARD (tabela do item 1.1 ou anexo)", inferido=["grupo_alternativa", "condicao_inclusao", "origem_dado"])
regra(["TR-10.2"], grupo="GA-09", opcao="B",
      condicao="SE critério de maior desconto (NE-076); nesse caso o valor não pode ser sigiloso (NE-077)",
      origem="PESQUISA_PRECOS (valor de referência)", inferido=["grupo_alternativa", "condicao_inclusao", "origem_dado"])
regra(["TR-10.2.OU"], grupo="GA-09")
regra(["TR-10.3", "TR-10.3.1"], grupo="GA-09", opcao="C", condicao="SE menor preço com orçamento sigiloso (NE-077)",
      inferido=["condicao_inclusao"])
regra(["TR-10.4"], condicao="SE houver matriz de alocação de riscos no contrato (NE-078)", inferido=["condicao_inclusao"])
regra([faixa("TR-10.5", "TR-10.5.4")], condicao="SE registro de preços (trecho com realce ciano; P12)",
      inferido=["condicao_inclusao"])
# Secao 11
regra(["TR-11.1", "TR-11.2", "TR-11.2.I", "TR-11.2.II", "TR-11.2.III", "TR-11.2.IV", "TR-11.2.V"], grupo="GA-10", opcao="A",
      condicao="SE a dotação for indicada no TR (contratação sem registro de preços)",
      origem="WIZARD (gestão/unidade, fonte, programa de trabalho, elemento de despesa, plano interno)",
      inferido=["grupo_alternativa", "condicao_inclusao", "origem_dado"])
regra(["TR-11.3"], grupo="GA-10", opcao="A", condicao="SE fornecimento contínuo com vigência plurianual (NE-079)",
      inferido=["grupo_alternativa", "condicao_inclusao"])
regra(["TR-11.3.OU"], grupo="GA-10")
regra(["TR-11.4"], grupo="GA-10", opcao="B",
      condicao="SE registro de preços (NE-080: dotação exigível só antes da assinatura do contrato)",
      inferido=["condicao_inclusao"])
# Secao 12 e fecho
regra(["TR-12.1"], tipo="TF+OP",
      condicao="Sempre; o trecho entre colchetes só entra se o orçamento for sigiloso (GA-09 C); avaliar classificação pela LAI (NE-081)",
      origem="MODELO; WIZARD (sigilo)", inferido=["tipo", "condicao_inclusao", "origem_dado"])
regra(["TR-ASSIN.01"], tipo="EU",
      condicao="Sempre na minuta em PDF; no TR Digital a assinatura fica na seção Responsáveis (TRs do corpus)",
      origem="SISTEMA (cidade da OM e data)", inferido=["condicao_inclusao", "origem_dado"])
regra(["TR-ASSIN.02", "TR-ASSIN.03"], tipo="TF",
      condicao="Sempre na minuta em PDF; no TR Digital a assinatura fica na seção Responsáveis (TRs do corpus)",
      origem="SISTEMA (servidores ou equipe designados; NE-082)", inferido=["condicao_inclusao", "origem_dado"])
# Anexo I
regra([faixa("TR-AI.CAB.01", "TR-AI-8.1")], condicao=ANEXO_I, inferido=["condicao_inclusao"])
regra(["TR-AI.CAB.03"], grupo="GA-11", opcao="A", condicao=ANEXO_I + " e contratação de pequeno valor (art. 95, I)",
      inferido=["condicao_inclusao"])
regra(["TR-AI.CAB.03.OU"], grupo="GA-11")
regra(["TR-AI.CAB.04"], grupo="GA-11", opcao="B",
      condicao=ANEXO_I + " e compra com entrega imediata e integral, sem obrigações futuras (art. 95, II)",
      inferido=["condicao_inclusao"])
regra(["TR-AI-1.1"], origem="WIZARD (prazo para aceite; instrumento equivalente)", inferido=["origem_dado"])
regra(["TR-AI-1.3.2"], origem="WIZARD (licitação ou contratação direta; coerente com GA-08)", inferido=["origem_dado"])
regra(["TR-AI-2.1", "TR-AI-2.2"], grupo="GA-12", opcao="A", condicao=ANEXO_I + " e vigência pelo art. 105 (coerente com TR-1.5)",
      inferido=["condicao_inclusao"])
regra(["TR-AI-2.2.OU", "TR-AI-2.7.OU"], grupo="GA-12")
regra([faixa("TR-AI-2.3", "TR-AI-2.7")], grupo="GA-12", opcao="B",
      condicao=ANEXO_I + " e fornecimento contínuo de pequeno valor (arts. 95, I, 106 e 107; NE-084), coerente com TR-1.6",
      inferido=["condicao_inclusao"])
regra(["TR-AI-2.8"], grupo="GA-12", opcao="C", condicao=ANEXO_I + " e emergência (art. 75, VIII; NE-086), coerente com TR-1.8",
      origem="WIZARD (prazo e data da emergência)", inferido=["condicao_inclusao", "origem_dado"])
regra(["TR-AI-3.1.8.1"], origem="WIZARD (prazo para decidir; sem especificação, um mês: NE-087)", inferido=["origem_dado"])
regra(["TR-AI-3.1.9"], origem="WIZARD (prazo de resposta; NE-088)", inferido=["origem_dado"])
regra(["TR-AI-3.1.10"], condicao=ANEXO_I + " e pequeno valor (art. 95, I; NE-089), com garantia da contratação exigida",
      inferido=["condicao_inclusao"])
regra(["TR-AI-4.1.1"], condicao=ANEXO_I + "; o trecho sobre rede de assistência técnica autorizada só no art. 95, I (NE-092)",
      inferido=["condicao_inclusao"])
regra([faixa("TR-AI-4.1.17", "TR-AI-4.1.21")],
      condicao=ANEXO_I + " e aquisição com prestação de serviço acessório (NE-094 nota 1)", inferido=["condicao_inclusao"])
regra([faixa("TR-AI-4.1.22", "TR-AI-4.1.26")],
      condicao=ANEXO_I + "; obrigações do art. 2º do Decreto 12.174/2024 (NE-095), a avaliar conforme o objeto",
      inferido=["condicao_inclusao"])
regra([faixa("TR-AI-5.1", "TR-AI-5.3.2")], grupo="GA-13", opcao="A",
      condicao=ANEXO_I + " e compra com entrega imediata e integral (art. 95, II; NE-096)", inferido=["condicao_inclusao"])
regra(["TR-AI-5.3.2.OU", "TR-AI-5.6.OU"], grupo="GA-13")
regra([faixa("TR-AI-5.4", "TR-AI-5.6")], grupo="GA-13", opcao="B",
      condicao=ANEXO_I + " e pequeno valor de fornecimento contínuo (art. 95, I, c/c art. 106; NE-097 e NE-098)",
      inferido=["condicao_inclusao"])
regra(["TR-AI-5.7"], grupo="GA-13", opcao="C", condicao=ANEXO_I + " e emergência (art. 75, VIII; NE-099)",
      inferido=["condicao_inclusao"])
regra(["TR-AI-8.1"], origem="SISTEMA (cidade e seção judiciária da OM)", inferido=["origem_dado"])
regra(["TR-AI-5.8.1"], normas_extra=["artigos 138 e 139 da mesma Lei"])
# Anexo II
regra([faixa("TR-AII.01", "TR-AII.06")], condicao=ANEXO_II, inferido=["condicao_inclusao"])
regra(["TR-AII.03", "TR-AII.04", "TR-AII.05", "TR-AII.06"], origem="Preenchido pelo contratado após a seleção", inferido=["origem_dado"])

NOMES_GRUPO = {
    "GA-01": "natureza do bem", "GA-02": "vigência", "GA-03": "PCA", "GA-04": "subcontratação",
    "GA-05": "garantia da contratação", "GA-06": "forma de entrega", "GA-07": "garantia do bem",
    "GA-08": "forma de seleção", "GA-09": "estimativa do valor", "GA-10": "dotação orçamentária",
    "GA-11": "hipótese do Anexo I", "GA-12": "vigência no Anexo I", "GA-13": "extinção no Anexo I",
}


def blocos_de_notas(modelo, blocos):
    """Blocos com o texto sugerido nas notas NE-016 (nota 3) e NE-071 (nota 4), copiados literalmente (P17).

    O número digitado na nota (ex.: '4.24.') é numeração, não conteúdo: vai para item_modelo e é recalculado na minuta.
    """
    por_ordem = {c["ordem"]: c for c in modelo["comentarios"]}
    pos = {b["id"]: b for b in blocos}
    novos = []
    # NE-016, nota 3: itens depois de 'das disposições a seguir:'
    c = por_ordem[16]
    trecho = c["texto"].split("das disposições a seguir:", 1)[1]
    itens = [l for l in trecho.split("\n") if l.strip()]
    if len(itens) != 8:
        raise SystemExit(f"NE-016: esperados 8 itens na nota 3, lidos {len(itens)}")
    for k, linha in enumerate(itens, 1):
        m = re.match(r"^\s*(\d+(?:\.\d+)+)\.?\s*(.*)$", linha)
        num, texto = m.group(1), m.group(2).strip()
        novos.append(("TR-4.23", {"id": f"TR-NE016.{k:02d}", "num": num, "texto": texto, "ne": "NE-016", "nota": "nota 3",
                                  "w": c["id_word"]}))
    # NE-071, nota 4: disposição entre aspas
    c = por_ordem[71]
    m = re.search(r'recomenda-se inserir a seguinte disposição:\s*\n?"([^"]+)"', c["texto"])
    if not m:
        raise SystemExit("NE-071: disposição da nota 4 não encontrada")
    novos.append(("TR-9.34.4", {"id": "TR-NE071.01", "num": "", "texto": m.group(1).strip(), "ne": "NE-071", "nota": "nota 4",
                                "w": c["id_word"]}))
    # insere depois do bloco âncora, na ordem
    saida = list(blocos)
    for depois, d in novos:
        base = pos[depois]
        i = max(k for k, b in enumerate(saida) if b["id"] == depois or b["id"].startswith(d["id"].rsplit(".", 1)[0] + "."))
        num_txt = f"{d['num']} (numeração digitada na nota; recalculada na minuta)" if d["num"] else "sem número na nota"
        saida.insert(i + 1, {
            "id": d["id"], "regiao": base["regiao"], "secao": base["secao"], "item_modelo": num_txt, "paragrafos": [],
            "texto": d["texto"], "contagem": {}, "realce": {}, "formatacao": "NOTA_EXPLICATIVA",
            "lacunas": achar_lacunas(d["texto"]), "notas": [d["ne"]], "normas": achar_normas(d["texto"]), "eh_tabela": False,
            "de_nota": d,
        })
    return saida


def secao_nome(blocos):
    nomes = {}
    for b in blocos:
        if re.fullmatch(r"TR-(?:AI-)?\d{1,2}", b["id"]):
            nomes[(b["regiao"], b["secao"])] = b["texto"].strip()
    return nomes


def main():
    blocos = json.load(open(sys.argv[1], encoding="utf-8"))
    modelo = json.load(open(sys.argv[2], encoding="utf-8"))
    blocos = blocos_de_notas(modelo, blocos)
    saida = Path(sys.argv[3])
    ordem = {b["id"]: i for i, b in enumerate(blocos)}
    nomes = secao_nome(blocos)
    linhas = []
    # aplica regras
    campos = {b["id"]: {"inferido": set()} for b in blocos}
    for sel, c in R:
        alvos = []
        for s in sel:
            if isinstance(s, tuple):
                a, z = ordem[s[1]], ordem[s[2]]
                alvos += [blocos[i]["id"] for i in range(a, z + 1)]
            else:
                if s not in ordem:
                    raise SystemExit(f"regra cita bloco inexistente: {s}")
                alvos.append(s)
        for bid in alvos:
            d = campos[bid]
            for k, v in c.items():
                if k == "inferido":
                    d["inferido"] |= set(v)
                else:
                    d[k] = v
    for b in blocos:
        c = campos[b["id"]]
        fmt = b["formatacao"]
        lac = b["lacunas"] + c.get("lacunas_extra", [])
        tem_lac = bool(lac)
        eh_ou = b["item_modelo"] == "OU"
        # tipo pela formatacao (regra 4), salvo regra curada
        if eh_ou:
            tipo = "OP"
        elif b["eh_tabela"]:
            tipo = "OP+TB" if fmt == "VERMELHO_ITALICO" else "TB"
        elif fmt == "PRETO":
            tipo = c.get("tipo_preto", "TF")
        elif fmt in ("VERMELHO_ITALICO", "NOTA_EXPLICATIVA"):
            tipo = "OP+EU" if tem_lac else "OP+TF"
        else:
            tipo = "TF+EU" if tem_lac else "TF+OP"
        tipo = c.get("tipo", tipo)
        # bloco de grupo de alternativas ou de inclusao condicionada sempre carrega OP
        if (c.get("grupo") or str(c.get("condicao", "")).startswith(("SE ", "Acompanha"))) and "OP" not in tipo:
            tipo += "+OP"
        ordem_tipo = ["TF", "EU", "IA", "OP", "TB"]
        tipo = "+".join(sorted(set(tipo.split("+")), key=ordem_tipo.index))
        if eh_ou:
            cond = f"Nunca entra na minuta: separa as opções do grupo {c.get('grupo', '?')}"
            origem = "MODELO"
        else:
            if fmt == "PRETO" and "condicao" not in c:
                cond = "Sempre (texto em preto, invariável; alteração exige justificativa nos autos: NE-001, item 2)"
            elif "condicao" not in c:
                cond = ("Sempre; trechos em vermelho são preenchidos ou escolhidos (NE-001, item 3)" if fmt == "MISTO"
                        else "Opcional (vermelho itálico; NE-001, item 3): decisão do usuário, sem critério em nota")
                if fmt != "MISTO":
                    c["inferido"].add("condicao_inclusao")
            else:
                cond = c["condicao"]
            origem = c.get("origem", "MODELO" if not tem_lac else "WIZARD")
            if tem_lac and "origem" not in c:
                c["inferido"].add("origem_dado")
        grupo = c.get("grupo", "")
        opcao = c.get("opcao", "")
        if grupo and not eh_ou and not opcao:
            raise SystemExit(f"{b['id']} em grupo sem opção")
        if grupo:
            grupo_txt = f"{grupo} ({NOMES_GRUPO[grupo]})"
        else:
            grupo_txt = ""
        sec = nomes.get((b["regiao"], b["secao"]), "")
        if b["regiao"] == "AI":
            sec = f"Anexo I - {b['secao']}. {sec}" if b["secao"] else "Anexo I - cabeçalho"
        elif b["regiao"] == "AII":
            sec = "Anexo II - Termo de Ciência e Concordância"
        elif b["id"].startswith("TR-CAB"):
            sec = "Cabeçalho"
        elif b["id"].startswith("TR-ASSIN"):
            sec = "Fecho e assinatura"
        else:
            sec = f"{b['secao']}. {sec}"
        if b.get("de_nota"):
            d = b["de_nota"]
            fonte = (f"{DOCX}, word/comments.xml, comentário w:id {d['w']} ({d['ne']}, {d['nota']}): texto sugerido pela nota, "
                     f"copiado literalmente; incluído por decisão do usuário (P17). Sem formatação de corpo: a regra da cor "
                     f"não se aplica. Fica fora do teste de cobertura dos parágrafos do corpo.")
            if d["num"]:
                fonte += f" O número digitado '{d['num']}.' está em item_modelo, não no texto (P17, P18)."
        else:
            cont = " ".join(f"{k}:{v}" for k, v in sorted(b["contagem"].items()))
            realce = (" Realce: " + ", ".join(f"{k} {v}" for k, v in b["realce"].items()) + ".") if b["realce"] else ""
            pars = b["paragrafos"]
            ptxt = f"parágrafo {pars[0]}" if len(pars) == 1 else f"parágrafos {pars[0]} a {pars[-1]}"
            fonte = (f"{DOCX}, word/document.xml, {ptxt} (contagem da Fase 0). Caracteres por formatação "
                     f"(P preto, Pi preto itálico, V vermelho, Vi vermelho itálico): {cont}.{realce}")
        inferidos = sorted(c["inferido"])
        status = "INFERIDO" if inferidos else "EXTRAIDO"
        if "DFD" in origem and not eh_ou:
            fonte += " Origem DFD conferida no formato dos DFDs da base (P10)."
        if inferidos:
            fonte += f" Campos INFERIDOS: {', '.join(inferidos)}."
        if c.get("obs"):
            fonte += f" Observação: {c['obs']}"
        linhas.append({
            "id": b["id"], "secao": sec, "item_modelo": b["item_modelo"], "texto_literal": b["texto"],
            "formatacao": fmt, "tipo": tipo, "grupo_alternativa": grupo_txt, "opcao": opcao,
            "lacunas": " | ".join(lac), "notas": ", ".join(b["notas"]), "condicao_inclusao": cond,
            "origem_dado": origem, "normas": "; ".join(b["normas"] + c.get("normas_extra", [])), "fonte": fonte, "status": status,
        })
    saida.mkdir(parents=True, exist_ok=True)
    gravar_csv(saida / "M02_tr_blocos.csv", COLS, linhas, preservar=("condicao_expr",))
    from collections import Counter
    print(f"M02: {len(linhas)} blocos | formatação {dict(Counter(l['formatacao'] for l in linhas))} | "
          f"status {dict(Counter(l['status'] for l in linhas))}")
    print("grupos:", dict(Counter(l['grupo_alternativa'].split(' ')[0] for l in linhas if l['grupo_alternativa'])))


if __name__ == "__main__":
    main()
