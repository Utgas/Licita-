#!/usr/bin/env python3
"""Fase 7 - M10: validações e alertas (regras de consistência que o sistema aplica antes de gerar a minuta).

Uso: python3 -I f7_gerar_M10.py <pasta_Matrizes_v1>

Especificação reconstruída (ver README). Cada regra tem condicao (texto) e condicao_expr (JSON Logic sobre WZ, CK,
VAR, itens e metadados do sistema). Quando a condição depende de comparação de texto livre, de contagem por grupo ou
de diferença entre a minuta e o modelo, condicao_expr fica vazia e a regra vai para perguntas_abertas.md (P27).
Metadados do sistema usados nas expressões (não são variáveis do M05):
  textos_livres            concatenação das respostas em texto do checklist e dos campos de texto do ETP
  importacao.*             dados lidos de documento importado (páginas, versão do modelo no rodapé, seções, valores)
  checklist.*              hash do docx preenchido, lista de leituras incertas, lista de perguntas sem resposta
  CK_x_n_texto             texto escrito na caixa de resposta de pergunta que também tem opções (ex.: CK_C_12_2_texto)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import gravar_csv  # noqa: E402
from jlogic import algum_item, ck, dumps, e, eq, inn, nao, ne, nenhum_item, ou, tem, var, vazio  # noqa: E402

COLS = ["id", "regra", "tipo", "momento", "condicao", "condicao_expr", "mensagem", "afeta", "base", "achado", "fonte",
        "status"]
C, P = "C", "P"
SIM, NAO = "Sim", "Não"


def sim(lista, n):
    return eq(ck(lista, n), SIM)


def nao_resp(lista, n):
    return eq(ck(lista, n), NAO)


def lista_alem_de(lista, n, opcao):
    return nao(eq(var(ck(lista, n)), [opcao]))


def txt(nome):
    return var(nome, "")


def gt(a, b):
    return {">": [var(a), b]}


def le(a, b):
    return {"<=": [var(a), b]}


TL = "textos_livres"

V = [
    ("VAL-001", "Objeto possivelmente de TIC, fora do modelo AGU da base", "ALERTA", "CHECKLIST",
     "SE o equipamento depender de software ou licença (CK-P-15.3 = Sim) OU se integrar à rede (CK-P-15.5 = Sim). Só as "
     "perguntas do checklist de permanentes (P28 fechada em 23/10/2026: a lista de classes de TIC, PAR-12, fica vazia)",
     ou(sim(P, "15.3"), sim(P, "15.5")),
     "O objeto pode ser de Tecnologia da Informação e Comunicação. O modelo AGU usado pelo sistema é o de aquisições 'exceto "
     "TIC'. Confirme o enquadramento com a equipe administrativa antes de gerar o TR.",
     "CK-P-15.3; CK-P-15.5; VAR-154; SET-16; SET-14", "TR-CAB.01 (título do modelo: 'AQUISIÇÕES, EXCETO TIC'); M00",
     "anexo 22/10, achado 2 (DFD 18/2026)", "INFERIDO"),
    ("VAL-002", "Divergência entre a descrição sucinta do DFD e a tabela de itens", "ALERTA", "IMPORTACAO",
     "SE um atributo numérico com unidade (ex.: GB, ml, mg) da descrição sucinta do DFD for diferente do mesmo atributo na "
     "especificação do item na tabela",
     None,
     "A descrição sucinta do DFD e a tabela de itens trazem valores diferentes para a mesma característica. Corrija a fonte "
     "antes de importar: o ETP e o TR usam a tabela de itens.",
     "VAR-008; VAR-011; VAR-109", "Coerência entre DFD, ETP e TR (M06)",
     "anexo 22/10, achado 2 (DFD 18/2026: 16 GB x 32 GB; SSD 500GB x 110 A 300)", "INFERIDO"),
    ("VAL-003", "Justificativa do DFD que cobre só parte dos itens", "ALERTA", "IMPORTACAO",
     "SE a justificativa de necessidade do DFD citar só uma parte dos itens da tabela", None,
     "A justificativa de necessidade não trata de todos os itens. Complete a necessidade (ETP-02.01) para os itens sem "
     "justificativa.", "VAR-010; ETP-02.01", "Lei 14.133/2021, art. 18, § 1º, I (descrição da necessidade)",
     "anexo 22/10, achado 2 (DFD 18/2026: justificativa só dos SSD)", "INFERIDO"),
    ("VAL-004", "Citação de norma revogada ou do regime anterior em texto livre", "ALERTA", "CHECKLIST",
     "SE o texto livre citar a Lei 10.520/2002 (revogada pela Lei 14.133/2021, conferido no planalto.gov.br), a Lei 8.666/1993, "
     "o Decreto 10.024/2019 ou a IN SLTI/MP 01/2010 (situação a conferir)",
     ou(*(inn(var("parametros." + n), txt(TL)) for n in (
         "marcador_lei_pregao_revogada", "marcador_lei_pregao_revogada_sem_ponto", "marcador_lei_licitacoes_anterior",
         "marcador_decreto_pregao_eletronico_anterior", "marcador_in_sustentabilidade_anterior"))),
     "O texto cita norma revogada ou do regime anterior. A Lei 10.520/2002 foi revogada pela Lei 14.133/2021; para bem comum, "
     "use a justificativa do ETP (TR-1.2).", "VAR-018; ETP-02.01; TR-1.2",
     "planalto.gov.br, L10520.htm, nota '(Revogado pela Lei nº 14.133, de 2021)', consultado em 22/10/2026; NRM da Lei "
     "10.520/2002 no M07", "seção 5, achado 6; anexo 22/10, achado 3", "INFERIDO"),
    ("VAL-005", "Processo sem número", "BLOQUEIO", "WIZARD", "SE VAR-001 estiver vazia", vazio("VAR_001"),
     "Informe o número do processo administrativo antes de gerar o ETP e o TR.", "VAR-001; ETP-01.01; TR-CAB.04",
     "M01 ETP-01.01", "seção 5, achado 5 (ETPs sem número de processo)", "INFERIDO"),
    ("VAL-006", "Número do processo do checklist diferente do cadastrado", "ALERTA", "CHECKLIST",
     "SE o número do processo do cabeçalho do checklist for diferente de VAR-001",
     ou(e(tem(ck(C, "CAB.01")), ne(ck(C, "CAB.01"), var("VAR_001"))), e(tem(ck(P, "CAB.01")), ne(ck(P, "CAB.01"), var("VAR_001")))),
     "O checklist traz número de processo diferente do processo em edição. Confira se o checklist é deste processo.",
     "CK-C-CAB.01; CK-P-CAB.01; VAR-001", "M11", "", "INFERIDO"),
    ("VAL-007", "Item perecível sem validade mínima", "BLOQUEIO", "ITENS",
     "SE algum item tiver perecivel = S e validade_minima vazia", algum_item(e(eq("perecivel", "S"), vazio("validade_minima"))),
     "Informe a validade mínima na entrega para cada item perecível (CK-C-14.2).", "VAR-116; VAR-117; TR-5.4.1",
     "TR-5.4.1; CK-C-14.2", "seção 5, achado 8", "INFERIDO"),
    ("VAL-008", "Validade 'Outro critério' sem descrição", "BLOQUEIO", "ITENS",
     "SE algum item tiver validade_minima igual a 'Outro critério' sem o texto do critério",
     algum_item(eq("validade_minima", "Outro critério")), "Descreva o critério de validade mínima do item.",
     "VAR-117; CK-C-14.2", "CK-C-14.2 (opção 'Outro critério')", "", "INFERIDO"),
    ("VAL-009", "Controle de temperatura sem faixa por item", "BLOQUEIO", "CHECKLIST",
     "SE CK-C-13.1 = Sim e nenhum item tiver faixa de temperatura", e(sim(C, "13.1"), nenhum_item(tem("faixa_temperatura"))),
     "Informe os itens e a faixa de temperatura (tabela da pergunta 13.1).", "VAR-122; CK-C-13.1; SET-02", "CK-C-13.1", "",
     "INFERIDO"),
    ("VAL-010", "Item com temperatura controlada e unidade sem câmara fria ou sem energia alternativa", "ALERTA", "CHECKLIST",
     "SE algum item tiver faixa de temperatura E (CK-C-20.2 = Não OU CK-C-20.3 = Não)",
     e(algum_item(tem("faixa_temperatura")), ou(nao_resp(C, "20.2"), nao_resp(C, "20.3"))),
     "Há item com temperatura controlada e a unidade informou que não tem câmara fria ou energia alternativa. Registre a "
     "providência prévia no ETP-13.01 (WZ-47).", "VAR-122; WZ-47; ETP-13.01", "Lei 14.133/2021, art. 18, § 1º, X (M01)",
     "", "INFERIDO"),
    ("VAL-011", "Item sujeito a controle especial sem a Autorização Especial exigida", "ALERTA", "WIZARD",
     "SE algum item tiver controle_especial = S E (WZ-38 sem REQUISITO_DE_LEI_ESPECIAL OU CK-C-17.5 sem 'AE para itens "
     "controlados')",
     e(algum_item(eq("controle_especial", "S")),
       ou(nao(inn("REQUISITO_DE_LEI_ESPECIAL", var("WZ_38", []))), nao(inn("AE para itens controlados", var(ck(C, "17.5"), []))))),
     "Há item sujeito a controle especial. A NE-073 cita a Autorização Especial da Anvisa como requisito de lei especial "
     "(TR-9.35). Confirme a exigência com a equipe administrativa.", "VAR-123; WZ-38; TR-9.35; SET-06",
     "NE-073", "", "INFERIDO"),
    ("VAL-012", "Amostra sem critérios objetivos de aprovação", "BLOQUEIO", "CHECKLIST",
     "SE CK-C-9.1 = Sim e CK-C-9.4 vazia, OU CK-P-17.1 = Sim e CK-P-17.4 vazia",
     ou(e(sim(C, "9.1"), vazio(ck(C, "9.4"))), e(sim(P, "17.1"), vazio(ck(P, "17.4")))),
     "A exigência de amostra precisa de critérios objetivos de aprovação ou reprovação (NE-013).", "VAR-051; WZ-20",
     "NE-013 nota 2 (o TR disciplina a forma e os critérios de avaliação)", "", "INFERIDO"),
    ("VAL-013", "Amostra em contratação direta sem dispensa eletrônica", "ALERTA", "ITENS",
     "SE algum item exigir amostra E não for licitação nem dispensa eletrônica",
     e(algum_item(eq("exige_amostra", "S")), nao(ou(eq("WZ_01", "LICITACAO"), eq("WZ_05", "SIM")))),
     "Fora da licitação, a NE-013 só admite amostra na dispensa eletrônica. Reveja a exigência.", "VAR-114; WZ-20; WZ-05",
     "NE-013 nota 1", "", "INFERIDO"),
    ("VAL-014", "Grupo com um item só", "BLOQUEIO", "ITENS", "SE algum rótulo de grupo tiver um único item", None,
     "Grupo precisa de dois ou mais itens; um item isolado é a própria unidade de disputa.", "VAR-112; WZ-50",
     "NE-022 (grupo considerado como item)", "", "INFERIDO"),
    ("VAL-015", "Grupo sem justificativa técnica", "BLOQUEIO", "ITENS", "SE algum item tiver grupo E VAR-102 estiver vazia",
     e(algum_item(tem("grupo")), vazio("VAR_102")),
     "Todo agrupamento de itens exige justificativa no ETP-09.01 (CK-C-8.3 e 8.4; CK-P-7.3 e 7.4).",
     "VAR-102; VAR-112; ETP-09.01", "NE-003 nota 2; Lei 14.133/2021, art. 18, § 1º, VIII", "", "INFERIDO"),
    ("VAL-016", "Exceção ao tratamento de ME/EPP sem justificativa", "BLOQUEIO", "ITENS",
     "SE algum item tiver tratamento_me_epp = EXCECAO_JUSTIFICADA e justificativa vazia",
     algum_item(e(eq("tratamento_me_epp", "EXCECAO_JUSTIFICADA"), vazio("justificativa_excecao_me_epp"))),
     "Indique a hipótese do art. 10 do Decreto 8.538/2015 e a justificativa.", "VAR-113; VAR-120",
     "NE-003 nota 4; NE-022; Decreto 8.538/2015, art. 10 (planalto.gov.br, conferido em 22/10/2026)", "", "INFERIDO"),
    ("VAL-017", "Exceção ao tratamento de ME/EPP em item que seria de participação exclusiva", "ALERTA", "ITENS",
     "SE algum item com EXCECAO_JUSTIFICADA tiver valor da unidade de disputa até R$ 80.000,00",
     algum_item(e(eq("tratamento_me_epp", "EXCECAO_JUSTIFICADA"), le("valor_unidade_disputa", var("parametros.limite_exclusivo_me_epp")))),
     "O item seria de participação exclusiva de ME/EPP. Afastar a exclusividade é decisão da equipe administrativa (P22).",
     "VAR-113; VAR-119; VAR-120", "NE-003 nota 4; Decreto 8.538/2015, arts. 6º e 10", "", "A_VERIFICAR"),
    ("VAL-018", "Marca ou modelo indicado sem justificativa técnica", "BLOQUEIO", "ITENS",
     "SE algum item tiver marca_indicada E VAR-046 estiver vazia", e(algum_item(tem("marca_indicada")), vazio("VAR_046")),
     "Indicação de marca ou modelo exige justificativa técnica e, quando a marca for referência, 'ou equivalente' (NE-012).",
     "VAR-046; VAR-115; WZ-18; TR-4.2", "NE-012", "", "INFERIDO"),
    ("VAL-019", "Fornecedor exclusivo indicado pela área técnica", "ALERTA", "WIZARD",
     "SE CK-C-6.2 ou CK-P-6.2 = Sim E WZ-04 diferente de ART74_INEXIGIBILIDADE",
     e(ou(sim(C, "6.2"), sim(P, "6.2")), ne("WZ_04", "ART74_INEXIGIBILIDADE")),
     "A área técnica indicou produto ou fornecedor exclusivo. Decida com a equipe administrativa entre inexigibilidade e "
     "licitação com marca indicada justificada (VAL-018).", "WZ-01; WZ-04; CK-C-6.2; CK-P-6.2", "M04 (WZ-01, WZ-04)", "",
     "INFERIDO"),
    ("VAL-020", "Prazo de entrega diferente de 30 dias sem explicação", "ALERTA", "CHECKLIST",
     "SE a CK-C-12.1 estiver respondida E o prazo de entrega (VAR-060, preenchido pela CK-C-12.1) for diferente do prazo "
     "de referência (PAR-05, 30 dias corridos) E a caixa de explicação da CK-C-12.2 estiver vazia",
     e(tem(ck(C, "12.1")), ne("VAR_060", var("parametros.prazo_entrega_referencia")), vazio(ck(C, "12.2") + "_texto")),
     "O prazo de entrega escolhido é diferente de 30 dias. Explique a necessidade (pergunta 12.2).",
     "CK-C-12.1; CK-C-12.2; VAR-060", "CK-C-12.2 (o próprio checklist pede explicação do prazo diferente)",
     "anexo 22/10, achado 6 (12.2 ambígua)", "INFERIDO"),
    ("VAL-021", "Entrega única no checklist incompatível com entrega parcelada", "ALERTA", "CHECKLIST",
     "SE CK-C-7.1 = Sim E (CK-C-12.3 diferente de 'Única' OU WZ-26 = PARCELADA), OU CK-C-7.1 = Não E CK-C-12.3 = 'Única'",
     ou(e(sim(C, "7.1"), ou(e(tem(ck(C, "12.3")), ne(ck(C, "12.3"), "Única")), eq("WZ_26", "PARCELADA"))),
        e(nao_resp(C, "7.1"), eq(ck(C, "12.3"), "Única"))),
     "As respostas sobre entrega única ou parcelada não batem (7.1, 12.3 e WZ-26).", "CK-C-7.1; CK-C-12.3; WZ-26", "M11",
     "", "INFERIDO"),
    ("VAL-022", "Respostas divergentes sobre espaço de armazenamento", "ALERTA", "CHECKLIST",
     "SE CK-C-13.5 e CK-C-20.1 tiverem respostas diferentes",
     e(tem(ck(C, "13.5")), tem(ck(C, "20.1")), ne(ck(C, "13.5"), var(ck(C, "20.1")))),
     "As perguntas 13.5 e 20.1 tratam do armazenamento e foram respondidas de forma diferente.", "CK-C-13.5; CK-C-20.1",
     "sugestoes_checklist.md (duplicidade)", "anexo 22/10, achado 6 (20.1 repete 13.5)", "INFERIDO"),
    ("VAL-023", "Respostas divergentes sobre número de fabricantes ou fornecedores", "ALERTA", "CHECKLIST",
     "SE 6.1 = Não e (5.5 = Sim ou 5.6 = Sim), OU 6.1 = Sim e 5.5 = Não e 5.6 = Não, em qualquer dos checklists",
     ou(e(nao_resp(C, "6.1"), ou(sim(C, "5.5"), sim(C, "5.6"))), e(sim(C, "6.1"), nao_resp(C, "5.5"), nao_resp(C, "5.6")),
        e(nao_resp(P, "6.1"), ou(sim(P, "5.5"), sim(P, "5.6"))), e(sim(P, "6.1"), nao_resp(P, "5.5"), nao_resp(P, "5.6"))),
     "A pergunta 6.1 repete as perguntas 5.5 e 5.6 e as respostas não batem.", "CK-C-5.5; CK-C-5.6; CK-C-6.1; CK-P-5.5; "
     "CK-P-5.6; CK-P-6.1", "sugestoes_checklist.md (duplicidade)", "anexo 22/10, achado 6 (6.1 repete 5.5 e 5.6)",
     "INFERIDO"),
    ("VAL-024", "Checklist indica demanda variável ou pedidos parcelados e não há registro de preços", "ALERTA", "WIZARD",
     "SE WZ-10 = NAO E (CK-C-7.3 = Sim OU CK-C-7.6 = Sim OU CK-C-7.2 com causa de variação marcada)",
     e(eq("WZ_10", "NAO"), ou(sim(C, "7.3"), sim(C, "7.6"), e(tem(ck(C, "7.2")), lista_alem_de(C, "7.2", "Não")))),
     "As respostas do checklist sugerem registro de preços. Confirme a decisão da WZ-10 com a equipe administrativa.",
     "WZ-10; CK-C-7.2; CK-C-7.3; CK-C-7.6", "M04 (WZ-10)", "", "INFERIDO"),
    ("VAL-025", "Item com quantidade 1 sem justificativa", "ALERTA", "ITENS",
     "SE algum item tiver quantidade 1 E as caixas de justificativa (CK-C-4.7 e CK-P-4.4) estiverem vazias",
     e(algum_item(eq("quantidade", var("parametros.quantidade_unitaria"))), vazio(ck(C, "4.7") + "_texto"), vazio(ck(P, "4.4"))),
     "Há item com quantidade 1. Justifique na memória de cálculo (ETP-07.01).", "VAR-012; ETP-07.01; CK-C-4.7; CK-P-4.4",
     "Lei 14.133/2021, art. 18, § 1º, IV (M01)", "", "INFERIDO"),
    ("VAL-026", "Garantia acima de 12 meses sem justificativa", "BLOQUEIO", "ITENS",
     "SE algum item tiver garantia_minima_meses acima de 12 E CK-P-13.2 estiver vazia",
     e(algum_item(gt("garantia_minima_meses", var("parametros.garantia_padrao_meses"))), vazio(ck(P, "13.2"))),
     "Garantia acima de 12 meses precisa de justificativa técnica (pergunta 13.2) registrada nos autos (NE-029).",
     "VAR-124; VAR-066; WZ-29", "NE-027; NE-029", "", "INFERIDO"),
    ("VAL-027", "Comodato indicado no checklist sem decisão da equipe administrativa", "ALERTA", "WIZARD",
     "DESLIGADA: comodato fora do sistema por enquanto (P24, decisão 0008 de 23/10/2026; S21); condicao_expr = false. "
     "Condição anterior: SE CK-C-10.1 = Sim E WZ-56 sem resposta", False,
     "O checklist indica fornecimento com equipamento em comodato. A equipe administrativa precisa decidir o enquadramento "
     "(WZ-56).", "WZ-56; SET-01", "M08 SET-01", "", "INFERIDO"),
    ("VAL-028", "Exigência de experiência com quantidade mínima", "ALERTA", "WIZARD",
     "SE CK-C-17.4 = Sim OU CK-P-18.4 = Sim", ou(sim(C, "17.4"), sim(P, "18.4")),
     "Quantitativo mínimo em atestado deve ser objetivo e limitado às parcelas de maior relevância (NE-071). Confira o "
     "percentual com a equipe administrativa.", "VAR-085; WZ-38; TR-9.34", "NE-071", "", "INFERIDO"),
    ("VAL-029", "Atestado com limitação de tempo ou de época", "BLOQUEIO", "WIZARD",
     "SE algum item da lista de características dos atestados (VAR-085) contiver 'últimos' (época), ou contiver 'período "
     "mínimo' sem tratar de garantia (período do contrato atestado), com ou sem inicial maiúscula. A duração da garantia "
     "técnica já prestada não é barrada: é permitida pela resposta da P25 (23/10/2026) e entra pela WZ-60 e pela SET-23",
     {"some": [var("VAR_085", []), ou(inn("últimos", var("")), inn("Últimos", var("")),
                                      e(ou(inn("período mínimo", var("")), inn("Período mínimo", var(""))),
                                        nao(ou(inn("garantia", var("")), inn("Garantia", var(""))))))]},
     "A NE-071 veda limitação de tempo ou de época nos atestados (período mínimo do contrato atestado, contratos dos "
     "últimos anos). Retire a limitação. Se a intenção é exigir garantia técnica já prestada, use a WZ-60.",
     "VAR-085; TR-9.34; WZ-60", "NE-071; P25", "M09: ETP 117/2025 (atestado 'pelo período mínimo de 12 meses', DV-12)",
     "INFERIDO"),
    ("VAL-030", "Execução por fabricante, rede credenciada ou carta de solidariedade", "ALERTA", "WIZARD",
     "SE WZ-59 = SIM OU WZ-21 = SIM", ou(eq("WZ_59", "SIM"), eq("WZ_21", "SIM")),
     "A exigência restringe a competição. Registre a justificativa técnica (checklist de permanentes, 11.2, 11.7, 12.8, 14.2 e "
     "18.6) e a motivação excepcional (NE-014).", "WZ-21; WZ-59; SET-15; TR-4.15", "NE-014", "", "INFERIDO"),
    ("VAL-031", "Documento importado com páginas ausentes", "ALERTA", "IMPORTACAO",
     "SE o rodapé 'X de N' indicar páginas que não estão no arquivo",
     e(tem("importacao.paginas_total"), ne("importacao.paginas_lidas", var("importacao.paginas_total"))),
     "O documento importado está incompleto. As seções das páginas ausentes ficam como não lidas.", "M00; M01",
     "M00 (ETP 19/2026: páginas 1, 3, 5, 7 e 9 de 9)", "seção 5, achado 4", "INFERIDO"),
    ("VAL-032", "TR importado feito sobre versão do modelo AGU diferente de DEZ/2025", "ALERTA", "IMPORTACAO",
     "SE o rodapé do TR importado indicar versão diferente da carregada no sistema (VAR-099; hoje DEZ/2025)",
     e(tem("importacao.versao_modelo"), ne("importacao.versao_modelo", var("VAR_099"))),
     "O TR importado foi feito sobre outra versão do modelo AGU. Use-o só como referência de prática.", "VAR-099; M02",
     "M00 (TRs 117/2025 e 140/2025: NOV/2024; TR 190/2025: ABR/2025)", "seção 5, achado 7", "INFERIDO"),
    ("VAL-033", "ETP importado com seção fora do padrão do ETP Digital", "INFORMATIVO", "IMPORTACAO",
     "SE o ETP importado tiver seção extra ou nome de seção variante",
     ou(tem("importacao.secoes_extras"), tem("importacao.secoes_nome_variante")),
     "O ETP importado tem seção a mais ou com nome diferente do ETP Digital. O sistema reconhece cada seção pelo nome, "
     "não pelo número impresso: por exemplo, 'Benefícios a serem alcançados com a contratação' é lida como 'Resultados "
     "Pretendidos'. Confira se cada seção foi lida no lugar certo.", "M01; ETP-12.01; ETP-90.01", "P06; P07",
     "seção 5, achado 10", "INFERIDO"),
    ("VAL-034", "ETP de participante com requisitos copiados de outro tipo de processo", "ALERTA", "MINUTA",
     "SE WZ-11 = PARTICIPANTE e o texto de requisitos trouxer trechos de outro tipo de processo (ex.: dispensa)", None,
     "O participante remete os requisitos ao órgão gerenciador; texto próprio copiado de outro processo é revisto.",
     "WZ-11; ETP-04.01", "M04 WZ-11 (coerência)", "seção 5, achado 9 (ETP 99/2025)", "INFERIDO"),
    ("VAL-035", "Validade mínima diferente no ETP e no TR", "BLOQUEIO", "MINUTA",
     "SE o texto de validade do ETP-04.01 e o do TR-5.4.1 vierem de valores diferentes", None,
     "ETP e TR usam a mesma validade mínima por item (VAR-117). Edite o item, não o texto.", "VAR-117; ETP-04.01; TR-5.4.1",
     "M04 WZ-09 (coerência); M06", "seção 5, achado 8", "INFERIDO"),
    ("VAL-036", "Checklist preenchido em versão diferente da mapeada no M11", "ALERTA", "CHECKLIST",
     "SE o hash da versão em branco do checklist usado for diferente do registrado no README do M11",
     ne("checklist.sha256_modelo", var("checklist.sha256_m11")),
     "O checklist está em versão diferente da mapeada. O M11 precisa ser refeito antes da leitura automática.", "M11",
     "README (hash dos dois docx)", "", "INFERIDO"),
    ("VAL-037", "Leitura automática do checklist com pendências", "BLOQUEIO", "CHECKLIST",
     "SE a leitura do checklist preenchido registrar pergunta sem marcação clara, duas opções em pergunta UNICA ou resposta "
     "fora da caixa", tem("checklist.leitura_pendencias"),
     "Algumas respostas do checklist não puderam ser lidas com segurança. Confirme-as antes de seguir.", "M11",
     "perguntas_abertas.md (leitura do checklist preenchido)", "", "INFERIDO"),
    ("VAL-038", "Valor do campo 'Valor (R$)' diferente do texto da estimativa no ETP", "BLOQUEIO", "IMPORTACAO",
     "SE o valor do campo do sistema e o valor escrito na seção 8 do ETP forem diferentes",
     e(tem("importacao.valor_campo"), ne("importacao.valor_campo", var("importacao.valor_texto"))),
     "O valor da estimativa difere entre o campo do sistema e o texto. Use um só valor (VAR-014).", "VAR-014; ETP-08.01; "
     "ETP-08.02", "M01 ETP-08.01", "P04 (ETP 19/2026)", "INFERIDO"),
    ("VAL-039", "Item sem código CATMAT", "ALERTA", "ITENS", "SE algum item estiver sem CATMAT", algum_item(vazio("catmat")),
     "O DFD do Compras.gov traz classe e PDM, sem código CATMAT. Informe o CATMAT antes do TR.", "VAR-011; TR-1.1.TAB1",
     "TR-1.1.TAB1 (coluna CATMAT); M00 (DFDs 18/2026 e 710/2025)", "anexo 22/10, achado 4", "INFERIDO"),
    ("VAL-040", "Objeto com bens de consumo e permanentes sem os dois checklists", "ALERTA", "CHECKLIST",
     "SE WZ-07 = AMBOS e faltar um dos checklists",
     e(eq("WZ_07", "AMBOS"), ou(vazio("checklist.consumo"), vazio("checklist.permanentes"))),
     "Objeto com bens de consumo e permanentes precisa dos dois checklists técnicos.", "WZ-07; CK-C-1.5; CK-P-1.5", "M11",
     "", "INFERIDO"),
    ("VAL-041", "Autorização Especial chamada de 'Autorização de Funcionamento (AE)'", "ALERTA", "MINUTA",
     "SE o texto trouxer 'Autorização de Funcionamento (AE)'", inn("Autorização de Funcionamento (AE)", txt(TL)),
     "AE é a Autorização Especial (NE-073); AFE é a Autorização de Funcionamento. Corrija a denominação.",
     "SET-06; SET-08; TR-9.14; TR-9.35", "NE-060; NE-073", "M09 (TRs 23/2026 e 58/2026)", "INFERIDO"),
    ("VAL-042", "Cláusula sem pertinência com o objeto", "ALERTA", "MINUTA",
     "SE a minuta trouxer cláusula de outro tipo de objeto (ex.: 'sala de exames' em TR de veículo; importação de "
     "medicamento em TR de equipamento)", None,
     "Há cláusula que parece copiada de outro processo. Confira a pertinência.", "M08; M02",
     "NE-001 item 1 (adaptação à luz da contratação)", "M09 (TRs 23/2026 e 58/2026)", "INFERIDO"),
    ("VAL-043", "Texto em preto do modelo alterado sem justificativa", "BLOQUEIO", "MINUTA",
     "SE um bloco PRETO do M02 na minuta diferir do texto literal do modelo", None,
     "Texto em preto do modelo foi alterado. Registre a justificativa nos autos (NE-001, item 2) ou restaure o texto.",
     "M02 (blocos PRETO)", "NE-001 item 2", "M09 (TRs 23/2026 e 58/2026, item 1.9 e outros)", "INFERIDO"),
    ("VAL-044", "Marca de comentário do editor no texto final", "ALERTA", "MINUTA",
     "SE a minuta contiver marca de comentário como '[A5]' ou '[A8]'", None,
     "O texto tem marca de comentário do editor. Retire antes de publicar.", "M02", "", "M09 (TR 23/2026)", "INFERIDO"),
    ("VAL-045", "Dado do TR diferente do ETP de origem", "BLOQUEIO", "MINUTA",
     "SE um dado que o TR herda do ETP (M06) tiver valor diferente nos dois documentos", None,
     "O TR repete o que o ETP decidiu. Altere o dado na origem e gere os dois de novo.", "M06",
     "M06 (teste no par 117/2025 e no caso 67/2026 x 23/2026)", "seção 5, achado 5", "INFERIDO"),
    ("VAL-046", "Estimativa ou aproximação na memória de cálculo", "ALERTA", "WIZARD",
     "SE a memória de cálculo (VAR-012) contiver '~'", inn("~", txt("VAR_012")),
     "A memória de cálculo deve trazer números calculados, sem '~' ou estimativa sem base.", "VAR-012; ETP-07.01",
     "Regra da seção 1 do prompt (contagens por script; '~' proibido)", "seção 5, achado 3 (matriz 01 com '~')",
     "INFERIDO"),
    ("VAL-047", "Minuta sem registro da versão do modelo AGU", "BLOQUEIO", "MINUTA", "SE VAR-099 estiver vazia",
     vazio("VAR_099"), "Registre a versão do modelo AGU usada (ex.: DEZ/2025) como metadado da minuta.", "VAR-099; M02",
     "M02 (fonte: docx DEZ/2025)", "seção 5, achado 2 (matriz 01 sem arquivo-fonte identificável)", "INFERIDO"),
    ("VAL-048", "Pergunta do checklist sem resposta ou anexo obrigatório ausente", "BLOQUEIO", "CHECKLIST",
     "SE a leitura registrar pergunta sem resposta ou se a tabela de itens ou a memória de cálculo não estiverem anexadas",
     ou(tem("checklist.sem_resposta"), nao_resp(C, "3.1"), nao_resp(C, "4.8"), nao_resp(P, "3.1"), nao_resp(P, "4.7")),
     "Todas as perguntas devem ser respondidas e a memória de cálculo deve ser anexada (orientações do checklist).",
     "M11; VAR-011; VAR-012", "Orientações de preenchimento do checklist de consumo (cabeçalho)", "", "INFERIDO"),
    ("VAL-049", "Justificativa genérica no checklist", "ALERTA", "CHECKLIST",
     "SE o texto livre trouxer 'melhor qualidade', 'necessidade do serviço' ou 'para segurança'",
     ou(inn("melhor qualidade", txt(TL)), inn("necessidade do serviço", txt(TL)), inn("para segurança", txt(TL))),
     "O checklist não aceita justificativa genérica. Explique o motivo técnico concreto.", "M11",
     "Orientações de preenchimento do checklist de consumo (cabeçalho)", "", "INFERIDO"),
    ("VAL-050", "Item permanente sem prazo de garantia com garantia contratual exigida", "BLOQUEIO", "ITENS",
     "SE WZ-29 = SIM E algum item permanente estiver sem garantia_minima_meses",
     e(eq("WZ_29", "SIM"), algum_item(e(eq("categoria", "PERMANENTE"), vazio("garantia_minima_meses")))),
     "Informe o prazo mínimo de garantia de cada item permanente (pergunta 13.1 do checklist de permanentes).",
     "VAR-124; VAR-155; WZ-29", "NE-027; NE-029", "", "INFERIDO"),
    ("VAL-051", "Cota calculada em zero: item em ampla participação", "ALERTA", "ITENS",
     "SE algum item ficar em AMPLA porque a cota calculada (VAR-160, parte inteira de quantidade x VAR-057 / 100) deu zero "
     "nele",
     algum_item(e(eq("tratamento_me_epp", "AMPLA"), eq("cota_calculada", 0))),
     "Com o percentual de cota informado, a quantidade reservada a ME/EPP neste item dá zero unidade. O item (ou o grupo "
     "dele) fica sem cota, em ampla participação. Confira o percentual ou a composição do grupo.",
     "VAR-113; VAR-118; VAR-160; VAR-057; WZ-24", "NE-022; decisão do dono do projeto de 23/10/2026 (decisão 0008 do repositório)",
     "", "INFERIDO"),
    ("VAL-052", "Garantia já prestada nos atestados abaixo de 12 meses ou sem prazo", "BLOQUEIO", "WIZARD",
     "SE WZ-60 = SIM E o prazo da garantia prestada (VAR-161) estiver vazio ou for menor que o mínimo (PAR-13, 12 meses)",
     e(eq("WZ_60", "SIM"), ou(vazio("VAR_161"), {">": [var("parametros.garantia_atestado_minima_meses"), var("VAR_161")]})),
     "Informe o prazo mínimo da garantia já prestada que os atestados devem comprovar: 12 meses ou mais (resposta da P25).",
     "WZ-60; VAR-161; SET-23", "P25 (decisão 0008, 23/10/2026)", "", "INFERIDO"),
    ("VAL-053", "Garantia já prestada nos atestados sem justificativa no ETP", "BLOQUEIO", "WIZARD",
     "SE WZ-60 = SIM E a justificativa técnica (VAR-162) estiver vazia",
     e(eq("WZ_60", "SIM"), vazio("VAR_162")),
     "A exigência de garantia já prestada nos atestados precisa de justificativa técnica no ETP (resposta da P25).",
     "WZ-60; VAR-162; ETP-04.01", "P25 (decisão 0008, 23/10/2026); NE-071", "", "INFERIDO"),
]


def main():
    pasta = Path(sys.argv[1])
    linhas = []
    for (vid, regra, tipo, momento, cond, expr, msg, afeta, base, achado, st) in V:
        fonte = ("Regra desenhada na Fase 7 a partir das matrizes M01 a M09 e M11, com a base indicada na coluna base. "
                 "condicao_expr em JSON Logic (convenções em jlogic.py e no README).")
        if expr is None:
            fonte += " Sem condicao_expr: a condição não cabe em JSON Logic (perguntas_abertas.md, P27)."
        linhas.append({"id": vid, "regra": regra, "tipo": tipo, "momento": momento, "condicao": cond,
                       "condicao_expr": dumps(expr) if expr is not None else "", "mensagem": msg, "afeta": afeta,
                       "base": base, "achado": achado, "fonte": fonte, "status": st})
    gravar_csv(pasta / "M10_validacoes.csv", COLS, linhas, preservar=())
    print(f"M10: {len(linhas)} regras; sem expressão: {[l['id'] for l in linhas if not l['condicao_expr']]}")


if __name__ == "__main__":
    main()
