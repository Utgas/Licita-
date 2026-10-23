#!/usr/bin/env python3
"""Fase 3 - Gera M04_wizard.csv (perguntas) e M05_variaveis.csv (variaveis de entrada).

Uso: python3 -I f3_gerar_M04_M05.py <M01_etp_campos.csv> <M02_tr_blocos.csv> <pasta_saida>

As perguntas saem das alternativas do M02 (grupos GA-xx e blocos com inclusao condicionada) e das regras
do M03. Blocos ligados e desligados usam IDs do M02 ou do M01; 'A..B' indica a faixa de blocos de A a B
na ordem do M02. Os blocos 'OU' nunca entram na minuta e nao sao listados.
Todo o conteudo e desenho (INFERIDO); origem DFD fica A_VERIFICAR (P10).
O script confere se todo ID citado existe e lista blocos condicionais do M02 que nenhuma pergunta controla.
"""
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # pasta dos scripts (codigo proprio)
from comum import gravar_csv  # noqa: E402

COLS4 = ["id", "pergunta", "documento", "tipo_resposta", "opcoes", "depende_de", "pre_preenchida_por", "liga_blocos", "liga_expr",
         "desliga_blocos", "desliga_expr", "exige_justificativa", "coerencia", "fundamento", "fonte", "status", "validacao",
         "comentario_validacao"]
COLS5 = ["id", "nome", "descricao", "tipo_dado", "validacao", "obrigatoria", "origem", "usada_em", "fonte", "status"]

# Perguntas do checklist técnico que respondem (ou apoiam) cada WZ (tarefa 4 de 22/10/2026). O checklist traz fatos
# técnicos; o enquadramento jurídico é da equipe administrativa (observação final dos dois checklists). Formatos:
#   lista de CK         o checklist responde ou sugere a resposta
#   DERIVADA: ...       a WZ é calculada dos atributos de item, que vêm das perguntas citadas
#   DECISAO_JURIDICA    o checklist não responde; entre parênteses, fatos de apoio quando houver
DJ = "DECISAO_JURIDICA (equipe administrativa)"
PRE = {
    "WZ-01": DJ + "; fatos de apoio: CK-C-6.2; CK-C-6.6; CK-P-6.2; CK-P-6.6",
    "WZ-02": DJ, "WZ-03": DJ,
    "WZ-04": DJ + "; fatos de apoio: CK-C-6.3; CK-C-6.4; CK-C-6.5; CK-C-6.6; CK-C-6.7; CK-P-6.3; CK-P-6.4; CK-P-6.5; CK-P-6.6; CK-P-6.7",
    "WZ-05": DJ,
    "WZ-06": DJ + "; fatos de apoio: CK-C-3.2; CK-P-3.1; CK-P-3.2",
    "WZ-07": "CK-C-1.5; CK-P-1.5 (checklist de consumo: CONSUMO; de permanentes: PERMANENTE; os dois: AMBOS)",
    "WZ-08": "CK-C-10.7; CK-C-10.8; CK-C-18.3; CK-C-18.4; CK-P-11.1; CK-P-12.1; CK-P-14.1",
    "WZ-09": "DERIVADA: atributo perecivel e validade_minima dos itens (CK-C-14.1; CK-C-14.2)",
    "WZ-10": "CK-C-7.2; CK-C-7.3; CK-C-7.6 (sugerem; a escolha do registro de preços é da equipe administrativa)",
    "WZ-11": "CK-C-7.6 (sugere); " + DJ,
    "WZ-12": DJ + "; fato de apoio: CK-C-7.6",
    "WZ-13": "DERIVADA: atributo grupo dos itens (CK-C-8.2; CK-P-7.2)",
    "WZ-14": "CK-C-2.3; CK-C-4.4 (sugerem; o enquadramento como contínuo é da equipe administrativa)",
    "WZ-15": "CK-C-4.4 (período a atender, sugere o prazo); termo inicial: " + DJ,
    "WZ-16": DJ,
    "WZ-17": "CK-C-21.1; CK-C-21.3; CK-P-21.1; CK-P-21.4",
    "WZ-18": "DERIVADA: atributo marca_indicada dos itens (CK-C-3.4; CK-C-5.7; CK-C-6.2; CK-C-6.3; CK-P-3.7; CK-P-6.2; CK-P-6.3)",
    "WZ-19": DJ,
    "WZ-20": "DERIVADA: atributo exige_amostra dos itens (CK-C-9.1; CK-C-9.2; CK-P-17.1; CK-P-17.2)",
    "WZ-21": DJ + "; fatos de apoio: CK-C-6.5; CK-P-6.5; CK-P-18.6",
    "WZ-22": DJ, "WZ-23": DJ,
    "WZ-24": "DERIVADA: atributo tratamento_me_epp, calculado pelo valor do item; exceção: " + DJ +
             " com fatos de CK-C-11.1; CK-C-11.2; CK-C-11.3; CK-C-11.4",
    "WZ-25": DJ,
    "WZ-26": "CK-C-7.1; CK-C-12.3; CK-P-8.3",
    "WZ-27": "CK-C-12.1; CK-P-8.1 (prazo); termo inicial e antecedência: " + DJ,
    "WZ-28": "CK-C-1.2; CK-P-4.2; CK-C-12.6; CK-C-12.7; CK-P-8.5; CK-P-8.6 (setor, local por item, agendamento e restrições); "
             "endereço: perfil da OM",
    "WZ-29": "CK-C-18.1; CK-P-13.1",
    "WZ-30": DJ, "WZ-31": DJ, "WZ-32": DJ, "WZ-33": DJ,
    "WZ-34": "CK-C-16.3; CK-C-16.4; CK-P-19.3; CK-P-19.5",
    "WZ-35": DJ, "WZ-36": DJ, "WZ-37": DJ,
    "WZ-38": "CK-C-17.1; CK-C-17.2; CK-C-17.4; CK-C-15.2; CK-P-18.1; CK-P-18.2; CK-P-18.3; CK-P-18.4; CK-P-18.5 (fatos; a "
             "exigência de atestado é decisão da equipe administrativa, NE-071)",
    "WZ-39": "CK-C-15.3; CK-C-17.5; CK-P-16.5",
    "WZ-40": DJ, "WZ-41": DJ, "WZ-42": DJ,
    "WZ-43": DJ + "; fatos de apoio: CK-C-7.1; CK-C-12.1",
    "WZ-44": DJ, "WZ-45": DJ,
    "WZ-46": "CK-C-19.1; CK-C-19.2; CK-P-10.1; CK-P-10.2; CK-P-10.4; CK-P-10.6; CK-P-15.1",
    "WZ-47": "CK-C-13.5; CK-C-20.2; CK-C-20.3; CK-C-20.4; CK-C-20.5; CK-C-20.6; CK-C-20.7; CK-P-8.8; CK-P-9.2; CK-P-9.6; "
             "CK-P-9.7; CK-P-10.3; CK-P-16.5",
    "WZ-48": "CK-C-21.1; CK-C-21.2; CK-C-21.3; CK-C-21.4; CK-P-21.1; CK-P-21.2; CK-P-21.3",
    "WZ-49": DJ,
    "WZ-50": "DERIVADA: atributo grupo dos itens (CK-C-8.1; CK-C-8.2; CK-P-7.1; CK-P-7.2)",
    "WZ-51": DJ, "WZ-52": DJ, "WZ-53": DJ, "WZ-54": DJ, "WZ-55": DJ,
    "WZ-56": DJ + "; fatos de apoio: CK-C-10.1; CK-C-10.5; CK-C-10.6",
    "WZ-57": DJ + "; fatos de apoio: CK-C-14.4; CK-C-14.5",
    "WZ-58": DJ + "; fatos de apoio: CK-P-2.4; CK-P-20.1; CK-P-20.2; CK-P-20.3",
    "WZ-59": DJ + "; fatos de apoio: CK-P-11.2; CK-P-11.7; CK-P-12.8; CK-P-14.2; CK-P-18.6",
    "WZ-60": DJ + "; fatos de apoio: CK-P-18.1; CK-P-18.3",
}

# id, pergunta, documento, tipo, opcoes, depende, liga, desliga, justificativa, coerencia, fundamento, status_extra
W = [
    ("WZ-01", "A compra será feita por licitação ou por contratação direta (dispensa ou inexigibilidade)?", "AMBOS", "UNICA",
     "LICITACAO; CONTRATACAO_DIRETA", "",
     "LICITACAO: TR-9.1 | CONTRATACAO_DIRETA: TR-9.2",
     "LICITACAO: TR-9.2 | CONTRATACAO_DIRETA: TR-9.1; TR-4.H08; TR-4.41..TR-4.41.3",
     "S se CONTRATACAO_DIRETA: fundamentação em TR-9.2 e justificativa da dispensa ou inexigibilidade no processo",
     "Contratação direta pelo art. 75, VIII exige vigência EMERGENCIAL (WZ-14); TR-AI-1.3.2 e TR-AII.03 usam 'Edital' na licitação "
     "e 'Aviso' ou 'Autorização de contratação direta' na contratação direta; a cota para ME/EPP (TR-4.41) só existe em licitação; "
     "na contratação direta a estimativa de valor usa TR-10.1 ou TR-10.3 (WZ-40) por analogia, porque as notas só tratam dos critérios "
     "de julgamento (P15)",
     "NE-054; grupo GA-08", ""),
    ("WZ-02", "Qual será a modalidade da licitação?", "TR", "UNICA", "PREGAO; CONCORRENCIA", "WZ-01=LICITACAO",
     "Preenche a escolha em TR-9.1 e em TR-AII.03", "",
     "N", "PREGAO exige bem comum (WZ-06=COMUM); CONCORRENCIA é a modalidade para bem especial (NE-054 nota 2)",
     "NE-054", ""),
    ("WZ-03", "Qual será o critério de julgamento?", "TR", "UNICA", "MENOR_PRECO; MAIOR_DESCONTO; TECNICA_E_PRECO",
     "WZ-01=LICITACAO",
     "MAIOR_DESCONTO: TR-10.2 (MENOR_PRECO e TECNICA_E_PRECO: TR-10.1 ou TR-10.3, conforme WZ-40)",
     "MENOR_PRECO e TECNICA_E_PRECO: TR-10.2 | MAIOR_DESCONTO: TR-10.1; TR-10.3; TR-10.3.1",
     "N",
     "Pregão admite só MENOR_PRECO ou MAIOR_DESCONTO; TECNICA_E_PRECO só na concorrência (NE-054 nota 2) e o modelo não traz "
     "critérios de pontuação técnica nem redação de estimativa própria para ele (P15); MAIOR_DESCONTO obriga "
     "orçamento público (WZ-40=NAO, NE-077); julgamento por grupo no registro de preços só com MENOR_PRECO ou MAIOR_DESCONTO "
     "(WZ-13; NE-055)", "NE-054; NE-055; NE-074; NE-076; NE-077; grupo GA-09", ""),
    ("WZ-04", "Qual é o fundamento legal da contratação direta?", "AMBOS", "UNICA",
     "ART75_II_VALOR; ART75_VIII_EMERGENCIA; ART75_OUTRO_INCISO; ART74_INEXIGIBILIDADE", "WZ-01=CONTRATACAO_DIRETA",
     "Preenche artigo, inciso e fundamentação em TR-9.2", "",
     "S: fundamentação descritiva em TR-9.2, com fonte no DFD ou no ETP",
     "ART75_VIII_EMERGENCIA exige WZ-14=EMERGENCIAL; ART75_II_VALOR exige que o gasto do exercício com objetos da mesma natureza, "
     "somado ao do contrato, caiba no limite atualizado, e em contrato plurianual conta o valor de um ano (NE-007 nota 5); nos incisos "
     "I, II, VII e VIII do art. 75 o ETP é facultativo (IN SEGES/ME 58/2022, art. 14)",
     "NE-007; NE-075; IN SEGES/ME 58/2022, art. 14 (gov.br, consultado em 21/10/2026)", ""),
    ("WZ-05", "A dispensa será feita pelo sistema de dispensa eletrônica?", "TR", "SIM_NAO", "SIM; NAO",
     "WZ-01=CONTRATACAO_DIRETA e WZ-04 diferente de ART74_INEXIGIBILIDADE", "",
     "NAO: TR-4.H04..TR-4.14",
     "N",
     "Amostra só cabe em dispensa eletrônica (NE-013 nota 1); sem dispensa eletrônica, a habilitação econômica e técnica pode ficar só "
     "no processo (NE-063 nota 3, NE-068 nota 1); o parcelamento só é analisado com regime competitivo (NE-003 nota 3)",
     "NE-003; NE-013; NE-063; NE-068", ""),
    ("WZ-06", "O bem é comum (padrões de desempenho e qualidade definidos por especificação usual de mercado) ou especial?", "AMBOS",
     "UNICA", "COMUM; ESPECIAL", "", "COMUM: TR-1.2 | ESPECIAL: TR-1.3", "COMUM: TR-1.3 | ESPECIAL: TR-1.2",
     "S: classificação e justificativa no ETP-02.01, declaradas pelo setor técnico (NE-005 nota 1)",
     "COMUM combina com PREGAO; ESPECIAL com CONCORRENCIA (WZ-02; NE-054 nota 2)", "NE-005; NE-054; grupo GA-01", ""),
    ("WZ-07", "Os bens são de consumo, permanentes ou dos dois tipos?", "AMBOS", "UNICA", "CONSUMO; PERMANENTE; AMBOS", "",
     "CONSUMO: TR-1.4 | AMBOS: TR-1.4", "PERMANENTE: TR-1.4",
     "N",
     "Sugere a resposta de WZ-29: consumo sem garantia contratual (TR-5.5, NE-028) e permanente com garantia contratual (TR-5.6, "
     "NE-029); TR-1.4 cita o Decreto 10.818/2021, que trata de itens de consumo (NE-006); a categoria deve bater com a do TR "
     "Digital ('Bens de consumo' ou 'Bens permanentes')",
     "NE-006; NE-028; NE-029", ""),
    ("WZ-08", "O fornecimento inclui atividades além da entrega, como instalação, montagem, treinamento ou assistência técnica?",
     "AMBOS", "SIM_NAO", "SIM; NAO", "",
     "SIM: trecho opcional de TR-1.1; TR-AI-4.1.17..TR-AI-4.1.21 (se houver Anexo I)",
     "NAO: trecho opcional de TR-1.1; TR-AI-4.1.17..TR-AI-4.1.21",
     "N",
     "Com assistência técnica, a compra não pode usar o art. 95, II (sem obrigações futuras, NE-083); serviço acessório permite "
     "exigir subcontratação de ME/EPP (NE-016 nota 3) e atestados de capacidade (NE-071); com serviço, revisar a inscrição fiscal "
     "municipal (NE-061)", "NE-015; NE-016; NE-061; NE-071; NE-091; NE-094", ""),
    ("WZ-09", "Existe item perecível? (derivada: o sistema calcula pela coluna perecivel da tabela de itens; o usuário não responde)",
     "AMBOS", "SIM_NAO", "SIM; NAO", "VAR-011 (colunas perecivel e validade_minima, VAR-116 e VAR-117)",
     "SIM: TR-5.4.1", "NAO: TR-5.4.1", "N",
     "Cada item perecível exige validade mínima própria (VAR-117), sem valor padrão (P21); se for igual em todos os perecíveis, "
     "ela preenche as lacunas de TR-5.4.1; se variar, entra em coluna da tabela do item 1.1 (NE-003 nota 1) e TR-5.4.1 remete a "
     "ela (P22); a validade é a mesma no ETP-04.01 e no TR e escrita como mínimo",
     "Item 5.4.1 do modelo (vermelho itálico, sem nota); NE-003 nota 1; achado 8 da seção 5 do prompt", ""),
    ("WZ-10", "A contratação será feita por Sistema de Registro de Preços?", "AMBOS", "SIM_NAO", "SIM; NAO", "",
     "SIM: TR-1.1.1; TR-1.1.1.TAB1; TR-1.1.1.TAB2; TR-1.1.1.TAB3; TR-10.5..TR-10.5.4; TR-11.4 | NAO: TR-11.1..TR-11.2.V",
     "SIM: TR-11.1..TR-11.3 | NAO: TR-1.1.1; TR-1.1.1.TAB1; TR-1.1.1.TAB2; TR-1.1.1.TAB3; TR-9.H03; TR-9.4; TR-9.4.1; "
     "TR-10.5..TR-10.5.4; TR-11.4",
     "N",
     "Com registro de preços, a dotação fica para a assinatura do contrato (TR-11.4, NE-080); SIM com WZ-11=PARTICIPANTE não gera TR "
     "(P13)", "NE-055; NE-080; grupo GA-10; realce ciano do modelo nos trechos de SRP", ""),
    ("WZ-11", "Nesse registro de preços a OM é o órgão gerenciador ou participante?", "AMBOS", "UNICA",
     "GERENCIADOR; PARTICIPANTE", "WZ-10=SIM",
     "GERENCIADOR: TR completo e ETP completo | PARTICIPANTE: ETP com ETP-04.01, ETP-05.01 e ETP-06.01 em remissão ao gerenciador",
     "PARTICIPANTE: TR inteiro (o TR é compilado pelo órgão gerenciador)",
     "N",
     "O participante continua obrigado a justificar quantidades (ETP-07.01) e parcelamento (ETP-09.01) com texto próprio; requisito "
     "copiado de outro tipo de processo vira alerta; TR pronto enviado por participante entra no processo do gerenciador como "
     "fonte de dados (itens, quantidades, endereço), não como texto da minuta, que sai do modelo AGU carregado (P13)",
     "Fluxo informado pelo usuário em 21/10/2026 (P13); achado 9 da seção 5 do prompt; ETPs 151/2025 e 801/2025 (remissão) e "
     "99/2025 (texto próprio)", ""),
    ("WZ-12", "Quantos órgãos participantes haverá?", "TR", "NUMERO", "0 ou mais", "WZ-11=GERENCIADOR",
     "Uma cópia de TR-1.1.1.TAB2 por participante (TR-1.1.1.TAB3 é a segunda cópia do modelo)",
     "0: TR-1.1.1.TAB2; TR-1.1.1.TAB3", "N", "", "Modelo AGU, tabelas de órgão participante do item 1.1.1", ""),
    ("WZ-13", "Existe grupo de itens num registro de preços julgado por menor preço ou maior desconto? (derivada da coluna grupo "
              "da tabela de itens)", "TR", "SIM_NAO", "SIM; NAO",
     "WZ-10=SIM e WZ-03 em MENOR_PRECO ou MAIOR_DESCONTO; VAR-011 (coluna grupo, VAR-112)",
     "SIM: TR-9.H03; TR-9.4; TR-9.4.1", "NAO: TR-9.H03; TR-9.4; TR-9.4.1",
     "S se SIM: agrupamento justificado no ETP-09.01",
     "O agrupamento consta do ETP-09.01 (WZ-50 derivada); no grupo, a cota para ME/EPP é definida pelo valor do grupo, "
     "considerado como um único item (NE-022 nota 1)", "NE-055; NE-022", ""),
    ("WZ-14", "O fornecimento é não contínuo, contínuo (necessidade permanente) ou emergencial?", "AMBOS", "UNICA",
     "NAO_CONTINUO; CONTINUO; EMERGENCIAL", "",
     "NAO_CONTINUO: TR-1.5; TR-AI-2.1; TR-AI-2.2; TR-AI-5.1..TR-AI-5.3.2 | CONTINUO: TR-1.6; TR-1.7; TR-11.3; TR-AI-2.3..TR-AI-2.7; TR-AI-5.4..TR-AI-5.6 | "
     "EMERGENCIAL: TR-1.8; TR-AI-2.8; TR-AI-5.7",
     "NAO_CONTINUO: TR-1.6; TR-1.7; TR-1.8; TR-11.3; TR-AI-2.3..TR-AI-2.8; TR-AI-5.4..TR-AI-5.7 | CONTINUO: TR-1.5; TR-1.8; "
     "TR-AI-2.1; TR-AI-2.2; TR-AI-2.8; TR-AI-5.1..TR-AI-5.3.2; TR-AI-5.7 | EMERGENCIAL: TR-1.5; TR-1.6; TR-1.7; TR-11.3; "
     "TR-AI-2.1..TR-AI-2.7; TR-AI-5.1..TR-AI-5.6",
     "S se CONTINUO: justificativa do enquadramento e da vigência plurianual em TR-1.7 e ateste de maior vantagem econômica pela autoridade (NE-007 nota 3)",
     "A vigência do TR (GA-02) e a do Anexo I (GA-12) têm de ser a mesma; CONTINUO combina com 'continuado' em TR-9.3; EMERGENCIAL "
     "exige WZ-04=ART75_VIII_EMERGENCIA e prazo de até 1 ano; CONTINUO tem prazo inicial de até 5 anos; CONTINUO não combina com "
     "WZ-43=SUBSTITUTIVO_ENTREGA_IMEDIATA; a base de cálculo da garantia da contratação (WZ-23) segue esta resposta (NE-017 nota 3); "
     "no Anexo I, a vigência (GA-12) e a extinção (GA-13) seguem esta resposta e a de WZ-43, e os blocos do Anexo I só entram "
     "com WZ-43 diferente de CONTRATO",
     "NE-007; NE-017; NE-079; NE-084; NE-086; NE-096; NE-097; NE-098; NE-099; grupos GA-02, GA-12 e GA-13", ""),
    ("WZ-15", "Qual o prazo de vigência e a partir de quando ele conta?", "TR", "NUMERO",
     "número e unidade (dias, meses ou anos) + termo inicial (texto, ex.: assinatura do contrato)", "WZ-14 respondida",
     "Preenche TR-1.5, TR-1.6 ou TR-1.8 e, na emergência, TR-AI-2.8", "", "N",
     "EMERGENCIAL até 1 ano; CONTINUO até 5 anos na vigência inicial; a vigência deve comportar o prazo de entrega (WZ-27)",
     "NE-007; texto dos itens 1.5, 1.6 e 1.8 do modelo", ""),
    ("WZ-16", "Os dados do PCA serão detalhados no TR ou só citados (já constam das informações básicas)?", "TR", "UNICA",
     "DETALHADO; REMISSAO", "WZ-49=SIM",
     "DETALHADO: TR-2.2; TR-2.2.I; TR-2.2.II; TR-2.2.III; TR-2.2.IV; TR-2.2.V | REMISSAO: TR-2.3",
     "DETALHADO: TR-2.3 | REMISSAO: TR-2.2; TR-2.2.I; TR-2.2.II; TR-2.2.III; TR-2.2.IV; TR-2.2.V", "N",
     "Dados do PCA iguais aos do ETP-11.01",
     "Grupo GA-03", ""),
    ("WZ-17", "Serão adotados critérios de sustentabilidade?", "AMBOS", "SIM_NAO", "SIM; NAO", "",
     "SIM: TR-4.H01; TR-4.1; TR-4.1.1; TR-4.1.2; TR-4.1.3", "NAO: TR-4.H01; TR-4.1; TR-4.1.1; TR-4.1.2; TR-4.1.3",
     "S se NAO: justificativa nos autos e no ETP (NE-011 nota 5)",
     "Os critérios do TR devem ser os mesmos do ETP-04.01 e do ETP-14.01, cada um com forma objetiva de comprovação (NE-011 nota 7)",
     "NE-009; NE-011", ""),
    ("WZ-18", "Existe item com marca ou modelo indicado? (derivada da coluna marca_indicada da tabela de itens)", "AMBOS",
     "SIM_NAO", "SIM; NAO", "VAR-011 (coluna marca_indicada, VAR-115)", "SIM: TR-4.H02; TR-4.2", "NAO: TR-4.H02; TR-4.2",
     "S se SIM: justificativa técnica no ETP-04.01 para cada item com marca (art. 41, I; NE-012)",
     "TR-4.2 lista a marca de cada item marcado; marca usada como referência na especificação precisa de 'ou equivalente', "
     "'ou similar' ou 'ou de melhor qualidade' (NE-012 nota 2)", "NE-012", ""),
    ("WZ-19", "Haverá vedação de marca ou produto, decidida em processo administrativo?", "TR", "SIM_NAO", "SIM; NAO", "",
     "SIM: TR-4.H03; TR-4.3; TR-4.3.1.1; TR-4.3.1.2", "NAO: TR-4.H03; TR-4.3; TR-4.3.1.1; TR-4.3.1.2",
     "S se SIM: número do processo que fundamenta a vedação, citado no item 4.3", "", "Item 4.3 do modelo", ""),
    ("WZ-20", "Existe item com amostra? (derivada da coluna exige_amostra da tabela de itens)", "AMBOS", "SIM_NAO", "SIM; NAO",
     "WZ-01=LICITACAO ou WZ-05=SIM; VAR-011 (coluna exige_amostra, VAR-114)",
     "SIM: TR-4.H04..TR-4.14", "NAO: TR-4.H04..TR-4.14",
     "S se SIM: justificativa no ETP-04.01 e critérios de avaliação de cada item no TR (NE-013 notas 2 e 3)",
     "TR-4.5.1 a TR-4.5.3 listam os itens marcados; item marcado em contratação direta sem dispensa eletrônica gera alerta, "
     "porque lá a amostra não cabe (NE-013 nota 1)", "NE-013", ""),
    ("WZ-21", "Será exigida carta de solidariedade do fabricante?", "AMBOS", "SIM_NAO", "SIM; NAO", "",
     "SIM: TR-4.H05; TR-4.15", "NAO: TR-4.H05; TR-4.15", "S se SIM: motivação da situação excepcional (NE-014)", "",
     "NE-014", ""),
    ("WZ-22", "A subcontratação será vedada, permitida, ou permitida com subcontratação obrigatória de ME/EPP?", "AMBOS", "UNICA",
     "NAO; SIM; SIM_EXIGIDA_ME_EPP", "",
     "SIM: TR-4.17..TR-4.23 | SIM_EXIGIDA_ME_EPP: TR-4.17..TR-4.23; TR-NE016.01..TR-NE016.08 | NAO: TR-4.16",
     "SIM: TR-4.16; TR-NE016.01..TR-NE016.08 | SIM_EXIGIDA_ME_EPP: TR-4.16 | NAO: TR-4.17..TR-4.23; TR-NE016.01..TR-NE016.08",
     "S se SIM ou SIM_EXIGIDA_ME_EPP: limites, condições e parcelas com base no ETP (NE-016 nota 2)",
     "Vedada a subcontratação completa ou da parcela principal (NE-015); SIM_EXIGIDA_ME_EPP só em aquisição com serviço "
     "acessório (WZ-08=SIM; NE-016 nota 3); com subcontratação de aspectos técnicos, admitir atestados de potencial "
     "subcontratado até 25% (WZ-38; NE-068, NE-071)", "NE-015; NE-016; grupo GA-04", ""),
    ("WZ-23", "Será exigida garantia da contratação (caução, seguro-garantia, fiança ou título de capitalização)?", "AMBOS",
     "SIM_NAO", "SIM; NAO", "",
     "SIM: TR-4.25..TR-4.40; TR-7.2.4.2; TR-7.2.4.2.1; TR-AI-3.1.10 (se WZ-43=SUBSTITUTIVO_PEQUENO_VALOR) | NAO: TR-4.24",
     "SIM: TR-4.24 | NAO: TR-4.25..TR-4.40; TR-7.2.4.2; TR-7.2.4.2.1; TR-AI-3.1.10",
     "S: se NAO, razões no ETP (TR-4.24 remete a ele); se SIM acima de 5%, justificativa de alta complexidade (NE-017 nota 2)",
     "Percentual até 5% (até 10% com justificativa), mais a garantia adicional se houver antecipação (WZ-35) e o valor de bens "
     "depositados (NE-019); base total ou anual conforme WZ-14 (NE-017 nota 3)",
     "NE-017; NE-018; NE-019; NE-034; NE-089; grupo GA-05", ""),
    ("WZ-24", "Existe item ou grupo com cota reservada para ME/EPP? (derivada: o sistema calcula o tratamento de cada item "
              "ou grupo pela tabela de itens; o usuário só escolhe a exceção justificada)", "AMBOS", "SIM_NAO", "SIM; NAO",
     "WZ-01=LICITACAO; VAR-011 (valor, quantidade, grupo e tratamento_me_epp, VAR-112, VAR-113, VAR-118 e VAR-119); VAR-057",
     "SIM: TR-4.H08; TR-4.41..TR-4.41.3; linha de cota em TR-1.1.TAB1",
     "NAO: TR-4.H08; TR-4.41..TR-4.41.3; linha de cota em TR-1.1.TAB1",
     "S por item ou grupo marcado EXCECAO_JUSTIFICADA: hipótese do art. 10, I, II ou IV do Decreto 8.538/2015 justificada no "
     "ETP-09.01 (NE-022 nota 1; VAR-120)",
     "Tratamento calculado por unidade de disputa, que é o item isolado ou o grupo inteiro, considerado como um único item "
     "(NE-022 nota 1): valor estimado até R$ 80.000,00 é EXCLUSIVO (NE-003 nota 4) e não leva cota (NE-022 nota 2); acima "
     "disso é COTA quando a parte inteira de quantidade x percentual da cota (VAR-057) dá ao menos uma unidade em cada item da "
     "unidade de disputa, e AMPLA quando não dá (P22); EXCECAO_JUSTIFICADA é a única escolha do usuário e, sobre o que seria "
     "EXCLUSIVO, fica A_VERIFICAR até a Fase 5 conferir o art. 10 do Decreto 8.538/2015 (P22); a cota não se limita a "
     "R$ 80.000,00 (NE-022 nota 3); o TR identifica cada cota e o item ou grupo de origem (NE-022 nota 1)",
     "NE-003; NE-022", ""),
    ("WZ-25", "O objeto está contemplado por margem de preferência em resolução da CICS?", "TR", "SIM_NAO", "SIM; NAO", "",
     "SIM: TR-4.H09; TR-4.42", "NAO: TR-4.H09; TR-4.42", "S se SIM: justificativa do enquadramento no item 4.42 (NE-023)", "",
     "NE-023", ""),
    ("WZ-26", "A entrega será em remessa única ou parcelada?", "AMBOS", "UNICA", "REMESSA_UNICA; PARCELADA", "",
     "REMESSA_UNICA: TR-5.1 | PARCELADA: TR-5.2; TR-5.2.TAB1", "REMESSA_UNICA: TR-5.2; TR-5.2.TAB1 | PARCELADA: TR-5.1", "N",
     "TR-9.3 deve dizer 'integral' para remessa única, 'parcelado' para parcelada e 'continuado' se WZ-14=CONTINUO",
     "NE-025; grupo GA-06", ""),
    ("WZ-27", "Qual o prazo de entrega, a partir de quando conta e com quantos dias de antecedência o fornecedor deve avisar um atraso?",
     "TR", "NUMERO", "dias de entrega + termo inicial (texto) + dias de antecedência", "WZ-26 respondida",
     "Preenche TR-5.1 ou TR-5.2.TAB1 e TR-5.3", "", "N",
     "Na compra pelo art. 95, II (WZ-43=SUBSTITUTIVO_ENTREGA_IMEDIATA) a entrega é de até 30 dias da ordem de fornecimento "
     "(NE-083); o prazo de entrega cabe na vigência (WZ-15); na entrega parcelada, prazo por parcela (NE-025)",
     "NE-025; NE-083; itens 5.1 a 5.3 do modelo", ""),
    ("WZ-28", "Onde os bens serão entregues (endereço, horário e setor de recebimento)?", "AMBOS", "TEXTO",
     "um ou mais endereços", "", "Preenche TR-5.4 e ETP-04.01", "", "N",
     "Os endereços do ETP e do TR devem ser os mesmos; mais de um endereço exige indicar o que vai para cada um (NE-026)", "NE-026", ""),
    ("WZ-29", "Será exigida garantia contratual do bem, além da garantia legal?", "AMBOS", "SIM_NAO", "SIM; NAO", "",
     "SIM: TR-5.6..TR-5.17 | NAO: TR-5.5", "SIM: TR-5.5 | NAO: TR-5.6..TR-5.17",
     "S se SIM: exigência e prazo justificados nos autos (NE-029 nota 2)",
     "Sugestão pela WZ-07 (consumo: NAO; permanente: SIM); SIM é incompatível com o art. 95, II, que não admite obrigações futuras "
     "nem assistência técnica (NE-083)", "NE-027; NE-028; NE-029; NE-030; grupo GA-07", ""),
    ("WZ-30", "Haverá rotinas de fiscalização específicas para este objeto?", "TR", "SIM_NAO", "SIM; NAO", "",
     "SIM: TR-6.15..TR-6.15.3", "NAO: TR-6.15..TR-6.15.3", "N", "", "NE-032", ""),
    ("WZ-31", "Haverá reunião inicial com o fornecedor para apresentar o plano de fiscalização?", "TR", "SIM_NAO", "SIM; NAO", "",
     "SIM: TR-6.5", "NAO: TR-6.5", "N", "", "Item 6.5 do modelo, em vermelho itálico e sem nota", ""),
    ("WZ-32", "Quais os percentuais das multas moratória e compensatórias e o limite de dias de atraso?", "TR", "NUMERO",
     "moratória: % ao dia e limite de dias; compensatórias: faixa mínima e máxima para cada alínea", "",
     "Preenche TR-7.2.4.1 e TR-7.2.4.3..TR-7.2.4.7", "", "N",
     "Multa compensatória entre 0,5% e 30% do valor do contrato (art. 156, § 3º, citado na NE-036); faixas maiores para infrações "
     "mais graves (NE-035); a moratória fica limitada ao valor da obrigação principal (NE-036)", "NE-033; NE-035; NE-036", ""),
    ("WZ-33", "Há infrações de inexecução parcial que devam ter penalidade diferente da prevista na alínea 'a'?", "TR", "SIM_NAO",
     "SIM; NAO", "", "SIM: TR-7.2.4.7.1 e trecho entre colchetes de TR-7.2.4.7",
     "NAO: TR-7.2.4.7.1 e trecho entre colchetes de TR-7.2.4.7", "N", "", "Itens 7.2.4.7 e 7.2.4.7.1 do modelo", ""),
    ("WZ-34", "Quais os prazos de substituição de bens rejeitados, de recebimento definitivo e de recolhimento de multa?", "TR",
     "NUMERO", "dias (substituição), dias úteis (recebimento definitivo e pequeno valor), dias (multa)", "",
     "Preenche TR-8.2, TR-8.3, TR-8.4 e TR-7.7", "", "N",
     "Recebimento definitivo e liquidação cabem em 10 dias úteis (NE-038); no limite do art. 75, II, metade do prazo (NE-039)",
     "NE-038; NE-039", ""),
    ("WZ-35", "Haverá pagamento antecipado?", "AMBOS", "SIM_NAO", "SIM; NAO", "",
     "SIM: TR-8.H05..TR-8.28; TR-8.30..TR-8.35; TR-8.37 (TR-8.29..TR-8.29.2 e TR-8.36.1 pela WZ-52; TR-8.36.2 pela WZ-53; "
     "TR-8.36 se uma das duas for SIM)",
     "NAO: TR-8.H05..TR-8.37",
     "S se SIM: justificativa prévia de que é condição indispensável ou gera sensível economia (art. 145, § 1º; NE-042) e "
     "justificativa da forma da antecipação (NE-043)",
     "Detalhes em WZ-52 (antecipação por etapas) e WZ-53 (garantia adicional); a garantia da contratação recebe acréscimo "
     "(WZ-23; NE-017 nota 2)", "NE-017; NE-042; NE-043; NE-044", ""),
    ("WZ-36", "Quais índices serão usados para correção por atraso e para reajuste, e qual a data-base do orçamento?", "TR", "TEXTO",
     "índice de correção; índice de reajuste; data-base (DD/MM/AAAA)", "",
     "Preenche TR-8.21, TR-8.41 e TR-8.40", "", "N",
     "Índice de reajuste preferencialmente setorial (NE-052); data-base igual à data do orçamento da pesquisa de preços (NE-051); "
     "reajuste de ofício é a regra (NE-053)", "NE-040; NE-051; NE-052; NE-053", ""),
    ("WZ-37", "Será exigida qualificação econômico-financeira?", "AMBOS", "SIM_NAO", "SIM; NAO", "",
     "SIM: TR-9.H07..TR-9.27; TR-9.29; TR-9.30; TR-9.31 (TR-9.28 pela WZ-54; TR-9.32 pela WZ-55)",
     "NAO: TR-9.H07..TR-9.32",
     "S: nas hipóteses do art. 70, III, só com justificativa (NE-056, NE-063)",
     "Pode valer só para alguns itens, por exemplo os não exclusivos de ME/EPP (NE-063 nota 1); capital mínimo e patrimônio "
     "líquido mínimo não se acumulam; percentual até 10% (NE-065)",
     "NE-056; NE-063; NE-064; NE-065", ""),
    ("WZ-38", "Quais exigências de qualificação técnica haverá?", "AMBOS", "MULTIPLA",
     "REGISTRO_ENTIDADE_PROFISSIONAL; ATESTADOS; ATESTADO_POTENCIAL_SUBCONTRATADO; REQUISITO_DE_LEI_ESPECIAL; NENHUMA", "",
     "REGISTRO_ENTIDADE_PROFISSIONAL: TR-9.H08; TR-9.33; TR-9.33.1 | ATESTADOS: TR-9.H08; TR-9.34..TR-9.34.4 | "
     "ATESTADO_POTENCIAL_SUBCONTRATADO: TR-9.H08; TR-NE071.01 | REQUISITO_DE_LEI_ESPECIAL: TR-9.H08; TR-9.35",
     "NENHUMA: TR-9.H08..TR-9.35 | opção não marcada: os blocos que ela liga, salvo o título TR-9.H08",
     "S: justificativa no ETP para cada exigência (NE-068, NE-071)",
     "Atestados sem limitação de tempo ou de local e com quantitativos até 50% das parcelas de maior relevância (NE-071); "
     "ATESTADO_POTENCIAL_SUBCONTRATADO exige subcontratação permitida (WZ-22 diferente de NAO) e vale até 25% do objeto "
     "(NE-071 nota 4); medicamentos sujeitos a controle especial levam a Autorização Especial da Anvisa como requisito de lei "
     "especial (NE-073); na entrega imediata e nos valores do art. 70, III, só exigência excepcional e justificada (NE-056)",
     "NE-056; NE-068; NE-069; NE-070; NE-071; NE-072; NE-073", ""),
    ("WZ-39", "A atividade do fornecedor exige autorização ou registro para funcionar?", "TR", "SIM_NAO", "SIM; NAO", "",
     "SIM: TR-9.14", "NAO: TR-9.14", "N", "", "NE-060", ""),
    ("WZ-40", "O orçamento estimado será sigiloso?", "AMBOS", "SIM_NAO", "SIM; NAO", "WZ-03 diferente de MAIOR_DESCONTO",
     "SIM: TR-10.3; TR-10.3.1; trecho entre colchetes de TR-12.1 | NAO: TR-10.1",
     "SIM: TR-10.1; TR-10.2; colunas de valor de TR-1.1.TAB1 | NAO: TR-10.2; TR-10.3; TR-10.3.1; trecho entre colchetes de TR-12.1",
     "N",
     "MAIOR_DESCONTO não admite sigilo (NE-077); com sigilo, o anexo de preços também é sigiloso (NE-074 nota 2) e o TR deve ser "
     "avaliado pela LAI (NE-081)", "NE-004; NE-074; NE-077; NE-081; grupo GA-09", ""),
    ("WZ-41", "Haverá matriz de alocação de riscos no contrato?", "TR", "SIM_NAO", "SIM; NAO", "", "SIM: TR-10.4",
     "NAO: TR-10.4", "N", "", "NE-078", ""),
    ("WZ-42", "Qual a dotação orçamentária (gestão/unidade, fonte, programa de trabalho, elemento de despesa e plano interno)?",
     "TR", "TEXTO", "cinco campos", "WZ-10=NAO", "Preenche TR-11.2.I..TR-11.2.V; TR-11.3 se WZ-14=CONTINUO", "", "N",
     "Fornecimento contínuo exige atestar créditos no início de cada exercício (NE-079)", "NE-079; grupo GA-10", ""),
    ("WZ-43", "Haverá termo de contrato ou instrumento substitutivo (nota de empenho, carta-contrato, autorização)?", "TR", "UNICA",
     "CONTRATO; SUBSTITUTIVO_PEQUENO_VALOR; SUBSTITUTIVO_ENTREGA_IMEDIATA", "",
     "SUBSTITUTIVO_PEQUENO_VALOR: TR-AI.CAB.01..TR-AI.CAB.03; TR-AI-1..TR-AI-8.1; TR-AII.01..TR-AII.06 | "
     "SUBSTITUTIVO_ENTREGA_IMEDIATA: TR-AI.CAB.01; TR-AI.CAB.02; TR-AI.CAB.04..TR-AI-8.1; TR-AII.01..TR-AII.06",
     "CONTRATO: TR-AI.CAB.01..TR-AI-8.1; TR-AII.01..TR-AII.06 | SUBSTITUTIVO_PEQUENO_VALOR: TR-AI.CAB.04 | "
     "SUBSTITUTIVO_ENTREGA_IMEDIATA: TR-AI.CAB.03; TR-AI-3.1.10; trecho de assistência técnica de TR-AI-4.1.1",
     "N",
     "Entrega imediata exige prazo de até 30 dias da ordem e nenhuma obrigação futura, nem assistência técnica (WZ-27, WZ-29, WZ-08; "
     "NE-083) e não combina com WZ-14=CONTINUO; pequeno valor de compras exige valor no limite atualizado do art. 75, II (ON AGU "
     "84/2024, transcrita na NE-083); a vigência e a extinção no Anexo I seguem esta resposta e WZ-14 (NE-084, NE-086, NE-096 a NE-099); "
     "pequeno valor sem fornecimento contínuo usa a vigência e a extinção da opção A de GA-12 e GA-13 por inferência (P14)",
     "NE-083; NE-084; NE-086; NE-089; NE-092; NE-096; NE-097; NE-098; NE-099; NE-102; grupos GA-11 e GA-13", ""),
    ("WZ-44", "No Anexo I: qual o prazo para o adjudicatário aceitar o instrumento, qual instrumento, e quais os prazos para a "
              "Administração decidir pedidos e responder pedidos de reequilíbrio?", "TR", "TEXTO",
     "prazo de aceite; NOTA_DE_EMPENHO, CARTA_CONTRATO, AUTORIZACAO ou ESTE_ANEXO; prazo de decisão; prazo de reequilíbrio",
     "WZ-43 diferente de CONTRATO", "Preenche TR-AI-1.1, TR-AI-3.1.8.1 e TR-AI-3.1.9", "", "N",
     "Sem prazo de decisão especificado vale um mês (NE-087); o prazo de reequilíbrio é cláusula necessária (NE-088)",
     "NE-087; NE-088", ""),
    ("WZ-45", "O foro sugerido pelo perfil da OM (cidade e seção judiciária da Justiça Federal) está correto?", "TR", "TEXTO",
     "confirmar ou informar cidade e seção judiciária",
     "WZ-43 diferente de CONTRATO", "Preenche TR-AI-8.1", "", "N", "", "Item 8.1 do Anexo I", ""),
    ("WZ-46", "Há contratações correlatas ou interdependentes (manutenção, insumos, descarte)?", "ETP", "SIM_NAO", "SIM; NAO", "",
     "SIM: texto próprio em ETP-10.01 | NAO: texto padrão de ETP-10.01", "", "N", "", "Lei 14.133/2021, art. 18, § 1º, XI; M01", ""),
    ("WZ-47", "Há providências a adotar antes do contrato (adequação de ambiente, licenças, capacitação de fiscais)?", "ETP",
     "SIM_NAO", "SIM; NAO", "", "SIM: texto próprio em ETP-13.01 | NAO: texto padrão de ETP-13.01", "", "N", "",
     "Lei 14.133/2021, art. 18, § 1º, X; M01", ""),
    ("WZ-48", "A contratação tem impactos ambientais relevantes (resíduos, logística reversa)?", "ETP", "SIM_NAO", "SIM; NAO", "",
     "SIM: texto próprio em ETP-14.01 | NAO: texto padrão de ETP-14.01", "", "S se NAO: justificar a ausência (art. 18, § 2º)",
     "Medidas mitigadoras do ETP-14.01 alimentam os critérios de sustentabilidade do TR (WZ-17)",
     "Lei 14.133/2021, art. 18, § 1º, XII e § 2º; M01", ""),
    ("WZ-49", "A contratação está prevista no Plano de Contratações Anual?", "AMBOS", "SIM_NAO", "SIM; NAO", "",
     "SIM: ETP-11.01 com os dados do PCA", "NAO: TR-2.2..TR-2.3",
     "S se NAO: justificar no ETP-11.01; o modelo AGU não tem redação para contratação fora do PCA",
     "Se o ano do PCA citado for diferente do ano da contratação, alertar (regra a confirmar na Fase 5; o ID do PNCP termina no "
     "ano do plano, e o plano é publicado no ano anterior)", "Lei 14.133/2021, art. 18, § 1º, II; M01; grupo GA-03", ""),
    ("WZ-50", "Como fica o parcelamento? (derivada da coluna grupo da tabela de itens)", "ETP", "UNICA",
     "POR_ITEM; POR_GRUPO; POR_ITEM_E_GRUPO; NAO_PARCELADO", "VAR-011 (coluna grupo, VAR-112)",
     "Define a estrutura de ETP-09.01 e de TR-1.1.TAB1", "",
     "S: sempre, porque o ETP-09.01 é obrigatório (art. 18, § 2º); todo agrupamento de itens exige justificativa",
     "POR_ITEM: nenhum grupo; POR_GRUPO: todo item em grupo; POR_ITEM_E_GRUPO: os dois; NAO_PARCELADO: uma única unidade de "
     "disputa (um item, ou um grupo com todos os itens); POR_GRUPO e POR_ITEM_E_GRUPO combinam com WZ-13=SIM no registro de "
     "preços; a cota para ME/EPP segue a unidade de disputa (NE-022)",
     "Lei 14.133/2021, art. 18, § 1º, VIII; NE-003; NE-022", ""),
    ("WZ-51", "O Anexo I terá as obrigações trabalhistas do art. 2º do Decreto 12.174/2024 (itens 4.1.22 a 4.1.26)?", "TR", "SIM_NAO",
     "SIM; NAO", "WZ-43 diferente de CONTRATO", "SIM: TR-AI-4.1.22..TR-AI-4.1.26", "NAO: TR-AI-4.1.22..TR-AI-4.1.26", "S",
     "Padrão SIM. O Decreto 12.174/2024, art. 2º, caput (não alterado pelo Decreto 12.926/2026), manda os contratos "
     "administrativos conterem essas cláusulas, sem restringir a serviços; NAO só com justificativa da assessoria jurídica (P16)",
     "NE-095; Decreto 12.174/2024, art. 2º", "INFERIDO"),
    ("WZ-52", "A antecipação será feita também durante a execução, por etapas, condicionada à comprovação da etapa anterior?", "TR",
     "SIM_NAO", "SIM; NAO", "WZ-35=SIM", "SIM: TR-8.29..TR-8.29.2; TR-8.36; TR-8.36.1",
     "NAO: TR-8.29..TR-8.29.2; TR-8.36.1 (e TR-8.36 se WZ-53=NAO)",
     "S: a forma da antecipação (integral no início, parcial ou por etapas) tem justificativa específica (NE-043)",
     "Com antecipação por etapas, prever os momentos de comprovação da execução (NE-045)", "NE-043; NE-045", ""),
    ("WZ-53", "Será exigida garantia adicional como condição da antecipação?", "TR", "SIM_NAO", "SIM; NAO", "WZ-35=SIM",
     "SIM: TR-8.36; TR-8.36.2", "NAO: TR-8.36.2 (e TR-8.36 se WZ-52=NAO)",
     "S: a adoção ou não das cautelas do art. 145, § 2º, e o percentual escolhido são justificados (NE-044)",
     "Percentual razoável e, na antecipação parcial, não superior ao valor antecipado (NE-046); a garantia da contratação recebe "
     "acréscimo quando houver antecipação (WZ-23; NE-017 nota 2)", "NE-017; NE-044; NE-046", ""),
    ("WZ-54", "As demonstrações contábeis exigidas serão as do último exercício ou as dos dois últimos?", "TR", "UNICA",
     "ULTIMO_EXERCICIO; DOIS_ULTIMOS_EXERCICIOS", "WZ-37=SIM",
     "DOIS_ULTIMOS_EXERCICIOS: TR-9.28; preenche a escolha em TR-9.26", "ULTIMO_EXERCICIO: TR-9.28",
     "S se DOIS_ULTIMOS_EXERCICIOS: justificativa nos autos (NE-064)",
     "Com dois exercícios, os índices devem ser atingidos em cada um deles (TR-9.28; NE-066)", "NE-064; NE-066", ""),
    ("WZ-55", "O atendimento dos índices econômicos será atestado por declaração de profissional contábil?", "TR", "SIM_NAO",
     "SIM; NAO", "WZ-37=SIM", "SIM: TR-9.32", "NAO: TR-9.32", "S se SIM: justificativa nos autos (NE-067)", "", "NE-067", ""),
    ("WZ-56", "O fornecimento incluirá equipamento em comodato, como obrigação acessória da aquisição dos materiais?", "AMBOS",
     "SIM_NAO", "SIM; NAO", "DESLIGADA: comodato fora do sistema por enquanto (P24, decisão 0008 de 23/10/2026); a pergunta "
     "não é oferecida e a SET-01 não entra na minuta. Condição anterior: CK-C-10.1=Sim", "SIM: SET-01", "NAO: SET-01",
     "S se SIM: ETP-06.01 explica por que o equipamento é indispensável e por que a Administração não usa equipamento próprio "
     "(CK-C-10.5 e CK-C-10.6)",
     "O modelo AGU não trata de comodato; o custo do equipamento fica embutido no preço do material. Com SIM, a WZ-08 tende a "
     "SIM (instalação, treinamento, manutenção do equipamento)", "M08 SET-01; prática no TR 117/2025 (só evidência)",
     "A_VERIFICAR"),
    ("WZ-57", "Será admitida, em caráter excepcional, a entrega de item com validade remanescente inferior à mínima, mediante "
     "compromisso de substituição?", "TR", "SIM_NAO", "SIM; NAO", "WZ-09=SIM", "SIM: SET-04", "NAO: SET-04",
     "S se SIM: as situações excepcionais vêm da CK-C-14.4 e entram no próprio subitem",
     "Só com item perecível (WZ-09 = SIM); a exceção é para situações descritas, não para qualquer entrega",
     "M08 SET-04; TR-5.4.1", ""),
    ("WZ-58", "A contratação incluirá a desinstalação e a retirada do equipamento existente como obrigação do fornecedor?",
     "AMBOS", "SIM_NAO", "SIM; NAO", "WZ-07 diferente de CONSUMO", "SIM: SET-18", "NAO: SET-18",
     "S se SIM: ETP-06.01 descreve a desinstalação como parte da solução",
     "Desinstalação é serviço associado ao bem: avaliar atestado (WZ-38, NE-071) e regularidade fiscal municipal (NE-061)",
     "M08 SET-18; NE-061; NE-071", ""),
    ("WZ-59", "Será exigido que instalação, treinamento ou assistência técnica sejam prestados pelo fabricante ou por empresa "
     "por ele credenciada?", "TR", "SIM_NAO", "SIM; NAO", "WZ-08=SIM", "SIM: SET-15", "NAO: SET-15",
     "S se SIM: motivo técnico das perguntas 11.2, 11.7, 12.8, 14.2 e 18.6 do checklist de permanentes",
     "Restringe a competição (VAL-030); exigência dirigida à habilitação passa pela carta de solidariedade (WZ-21, NE-014)",
     "M08 SET-15; NE-014", ""),
    ("WZ-60", "Os atestados deverão comprovar garantia técnica já prestada a equipamento compatível com o objeto, com prazo "
     "mínimo?", "TR", "SIM_NAO", "SIM; NAO", "WZ-38 contém ATESTADOS", "SIM: SET-23", "NAO: SET-23",
     "S se SIM: justificativa técnica no ETP (VAR-162) e prazo mínimo da garantia prestada (VAR-161), de 12 meses ou mais "
     "(VAL-052 e VAL-053)",
     "Permitido pela resposta da P25 (23/10/2026): a duração da garantia já prestada não é a limitação de tempo ou de época "
     "que a NE-071 veda; o período ou a época do contrato atestado continuam barrados (VAL-029)",
     "NE-071; M08 SET-23; P25", ""),
]

# id, nome, descricao, tipo, validacao, obrigatoria, origem, usada_em
V = [
    ("VAR-001", "numero_processo", "Número do processo administrativo", "TEXTO", "máscara 00000.000000/0000-00; 17 dígitos; igual no ETP e no TR", "S", "SISTEMA", "ETP-01.01; TR-CAB.04"),
    ("VAR-002", "uasg", "Código UASG da OM", "TEXTO", "6 dígitos, guardado como texto para não perder zeros à esquerda", "S", "SISTEMA", "ETP-01.02"),
    ("VAR-003", "nome_om", "Nome da organização militar", "TEXTO", "não vazio", "S", "SISTEMA", "ETP-01.02; TR-CAB.03"),
    ("VAR-004", "hierarquia_orgao", "Linhas do cabeçalho do órgão (ministério, força, comando, região, OM)", "LISTA", "não vazio", "S", "SISTEMA", "TR-CAB.03"),
    ("VAR-005", "cidade_uf_om", "Cidade e UF da OM", "TEXTO", "formato Cidade-UF", "S", "SISTEMA", "TR-ASSIN.01; TR-AI-8.1"),
    ("VAR-006", "area_requisitante", "OMS e setor requisitantes", "TEXTO", "não vazio", "S", "CHECKLIST", "ETP-03.01"),
    ("VAR-007", "responsavel_requisitante", "Posto ou cargo e nome do responsável pela demanda", "TEXTO", "não vazio; nunca reproduzido em exemplos", "S", "CHECKLIST", "ETP-03.02"),
    ("VAR-008", "objeto_descricao", "Descrição resumida do objeto", "TEXTO", "não vazio; marca só com 'ou equivalente'", "S", "CHECKLIST", "ETP-02.01; TR-1.1"),
    ("VAR-009", "atividades_incluidas", "Atividades além da entrega (instalação, montagem, treinamento, assistência)", "LISTA", "presente se WZ-08=SIM", "CONDICIONAL", "WIZARD", "TR-1.1; TR-AI-4.1.17"),
    ("VAR-010", "necessidade_texto", "Relato da necessidade e do problema a resolver", "TEXTO", "não vazio; cada trecho com origem", "S", "CHECKLIST", "ETP-02.01"),
    ("VAR-011", "tabela_itens", "Itens da contratação, uma linha por item: número, especificação, CATMAT quando houver, unidade, "
     "quantidade (no registro de preços, a soma dos órgãos), valor unitário estimado (VAR-013) e as colunas grupo (VAR-112), "
     "tratamento_me_epp (VAR-113), exige_amostra (VAR-114), marca_indicada (VAR-115), perecivel (VAR-116), validade_minima "
     "(VAR-117), quantidade_cota (VAR-118), valor_unidade_disputa (VAR-119), justificativa_excecao_me_epp (VAR-120), "
     "compatibilidade (VAR-121), faixa_temperatura (VAR-122), controle_especial (VAR-123), garantia_minima_meses (VAR-124), "
     "classe_pdm (VAR-153), tic (VAR-154) e categoria (VAR-155)",
     "TABELA", "quantidade inteira maior que zero; unidade preenchida; CATMAT numérico quando informado (o DFD do Compras.gov "
     "traz classe e PDM, sem o código); as colunas próprias seguem a validação das VAR-112 a VAR-124 e VAR-153 a VAR-155; "
     "origem: tabela do DFD do Compras.gov ou tabela anexa ao checklist (CK-C-3.1, CK-P-3.1)", "S", "DFD",
     "ETP-07.02; TR-1.1.TAB1"),
    ("VAR-012", "memoria_calculo_quantidades", "Método e dados de consumo que justificam as quantidades", "TEXTO", "números iguais aos da tabela de itens", "S", "CHECKLIST", "ETP-07.01"),
    ("VAR-013", "valores_unitarios_referenciais", "Valor unitário de referência por item", "TABELA", "moeda com 2 casas; um valor por item", "S", "PESQUISA_PRECOS", "ETP-07.02; ETP-08.02; TR-1.1.TAB1"),
    ("VAR-014", "valor_total_estimado", "Valor total estimado da contratação", "MOEDA", "igual à soma de quantidade x valor unitário; igual no campo ETP-08.01, no texto ETP-08.02 e em TR-10.1", "S", "PESQUISA_PRECOS", "ETP-08.01; ETP-08.02; TR-10.1"),
    ("VAR-015", "data_base_orcamento", "Data do orçamento estimado", "DATA", "DD/MM/AAAA; não futura", "S", "PESQUISA_PRECOS", "TR-8.40; ETP-08.02"),
    ("VAR-016", "valor_referencia_maior_desconto", "Valor de referência para o maior desconto", "MOEDA", "moeda; presente se WZ-03=MAIOR_DESCONTO", "CONDICIONAL", "PESQUISA_PRECOS", "TR-10.2"),
    ("VAR-017", "natureza_bem", "Bem comum ou especial", "LISTA", "COMUM ou ESPECIAL", "S", "WIZARD", "TR-1.2; TR-1.3"),
    ("VAR-018", "justificativa_natureza_bem", "Justificativa da classificação como bem comum ou especial", "TEXTO", "não vazio; sem citar a Lei 10.520/2002, revogada pela Lei 14.133/2021 (achado 3)", "S", "WIZARD", "ETP-02.01"),
    ("VAR-019", "categoria_bem", "Consumo, permanente ou ambos", "LISTA", "CONSUMO, PERMANENTE ou AMBOS", "S", "WIZARD", "TR-1.4; TR-5.5; TR-5.6"),
    ("VAR-020", "forma_selecao", "Licitação ou contratação direta", "LISTA", "valor de WZ-01", "S", "WIZARD", "TR-9.1; TR-9.2; TR-AI-1.3.2; TR-AII.03"),
    ("VAR-021", "modalidade", "Pregão ou concorrência", "LISTA", "valor de WZ-02", "CONDICIONAL", "WIZARD", "TR-9.1; TR-AII.03"),
    ("VAR-022", "criterio_julgamento", "Menor preço, maior desconto ou técnica e preço", "LISTA", "valor de WZ-03", "CONDICIONAL", "WIZARD", "TR-9.1; TR-10.1; TR-10.2"),
    ("VAR-023", "fundamento_contratacao_direta", "Artigo e inciso da contratação direta", "TEXTO", "art. 74 ou 75 e inciso válido", "CONDICIONAL", "WIZARD", "TR-9.2"),
    ("VAR-024", "fundamentacao_contratacao_direta", "Texto que enquadra o caso no dispositivo", "TEXTO", "não vazio; fatos de exclusividade vindos da seção 6 do checklist", "CONDICIONAL", "WIZARD", "TR-9.2"),
    ("VAR-025", "dispensa_eletronica", "Dispensa pelo sistema eletrônico", "LISTA", "SIM ou NAO", "CONDICIONAL", "WIZARD", "TR-4.4; TR-AI-1.3.2"),
    ("VAR-026", "srp", "Registro de preços", "LISTA", "SIM ou NAO", "S", "WIZARD", "TR-1.1.1; TR-11.4"),
    ("VAR-027", "papel_srp", "Gerenciador ou participante", "LISTA", "GERENCIADOR ou PARTICIPANTE", "CONDICIONAL", "WIZARD", "ETP-04.01; ETP-05.01; ETP-06.01"),
    ("VAR-028", "numero_irp", "Número da intenção de registro de preços", "TEXTO", "formato N/AAAA", "CONDICIONAL", "WIZARD", "ETP-04.01; ETP-05.01"),
    ("VAR-029", "quantidades_por_orgao", "Quantidades mínima, máxima e total por item para gerenciador e participantes", "TABELA", "mínima até máxima; total igual à soma", "CONDICIONAL", "WIZARD", "TR-1.1.1.TAB1; TR-1.1.1.TAB2; TR-1.1.1.TAB3"),
    ("VAR-030", "numero_orgaos_participantes", "Quantidade de órgãos participantes", "NUMERO", "inteiro maior ou igual a zero", "CONDICIONAL", "WIZARD", "TR-1.1.1.TAB2"),
    ("VAR-031", "julgamento_por_grupo", "Critério por grupo de itens no registro de preços (valor da WZ-13 derivada)", "LISTA", "SIM ou NAO", "CONDICIONAL", "SISTEMA", "TR-9.4"),
    ("VAR-032", "local_tabela_aceitabilidade", "Onde está a tabela de preços unitários máximos", "LISTA", "PLANILHA_ANEXA ou ITEM_DO_TR", "CONDICIONAL", "WIZARD", "TR-9.4.1"),
    ("VAR-033", "tipo_vigencia", "Não contínuo, contínuo ou emergencial", "LISTA", "valor de WZ-14", "S", "WIZARD", "TR-1.5; TR-1.6; TR-1.8; TR-AI-2.1; TR-AI-2.3; TR-AI-2.8"),
    ("VAR-034", "prazo_vigencia", "Prazo de vigência com unidade", "NUMERO", "maior que zero; emergencial até 1 ano; contínuo até 5 anos", "S", "WIZARD", "TR-1.5; TR-1.6; TR-1.8; TR-AI-2.8"),
    ("VAR-035", "termo_inicial_vigencia", "A partir de quando a vigência conta", "TEXTO", "não vazio", "S", "WIZARD", "TR-1.5; TR-1.6; TR-1.8"),
    ("VAR-036", "justificativa_continuidade", "Por que o fornecimento é contínuo e a vigência plurianual é vantajosa", "TEXTO", "fatos de uso contínuo vindos do checklist (período e variação da demanda)", "CONDICIONAL", "CHECKLIST", "TR-1.7"),
    ("VAR-037", "forma_pca", "Detalhar ou citar o PCA", "LISTA", "DETALHADO ou REMISSAO", "S", "WIZARD", "TR-2.2; TR-2.3"),
    ("VAR-038", "pca_ano", "Ano do Plano de Contratações Anual", "NUMERO", "AAAA; diferente do ano da contratação gera alerta (a confirmar na Fase 5)", "S", "WIZARD", "ETP-11.01; TR-2.2; TR-2.3"),
    ("VAR-039", "pca_id_pncp", "ID do PCA no PNCP", "TEXTO", "padrão observado no corpus: CNPJ-0-sequencial/AAAA (ex. 00394452000103-0-000363/2025)", "CONDICIONAL", "WIZARD", "TR-2.2.I; ETP-11.01"),
    ("VAR-040", "pca_data_publicacao", "Data de publicação do PCA no PNCP", "DATA", "DD/MM/AAAA", "CONDICIONAL", "WIZARD", "TR-2.2.II; ETP-11.01"),
    ("VAR-041", "pca_id_item", "Número do item no PCA", "NUMERO", "inteiro", "CONDICIONAL", "WIZARD", "TR-2.2.III; ETP-11.01"),
    ("VAR-042", "pca_classe_grupo", "Classe ou grupo do item no PCA", "TEXTO", "não vazio", "CONDICIONAL", "WIZARD", "TR-2.2.IV"),
    ("VAR-043", "pca_identificador_futura_contratacao", "Identificador da futura contratação", "TEXTO", "padrão observado no corpus: UASG-N/AAAA (ex. 160242-2/2025)", "CONDICIONAL", "WIZARD", "TR-2.2.V"),
    ("VAR-044", "criterios_sustentabilidade", "Critérios de sustentabilidade com forma de comprovação", "LISTA", "cada critério com forma objetiva de comprovação", "CONDICIONAL", "CHECKLIST", "ETP-04.01; ETP-14.01; TR-4.1.1; TR-4.1.2; TR-4.1.3"),
    ("VAR-045", "justificativa_sem_sustentabilidade", "Razão para não adotar critérios de sustentabilidade", "TEXTO", "presente se WZ-17=NAO", "CONDICIONAL", "WIZARD", "ETP-04.01"),
    ("VAR-046", "marcas_indicadas", "Justificativa técnica das marcas ou modelos indicados por item (VAR-115)", "TEXTO", "hipótese do art. 41, I identificada; fato técnico concreto, sem justificativa genérica", "CONDICIONAL", "CHECKLIST", "ETP-04.01; TR-4.2"),
    ("VAR-047", "processo_vedacao_marca", "Número do processo que fundamenta a vedação", "TEXTO", "máscara de processo", "CONDICIONAL", "WIZARD", "TR-4.3"),
    ("VAR-048", "produtos_marcas_vedados", "Produtos ou marcas vedados", "LISTA", "ao menos um item", "CONDICIONAL", "WIZARD", "TR-4.3.1.1; TR-4.3.1.2"),
    ("VAR-049", "amostra_itens", "Itens com amostra, tirados da coluna exige_amostra (VAR-114)", "LISTA", "itens existentes na tabela", "CONDICIONAL", "SISTEMA", "TR-4.5.1; TR-4.5.2; TR-4.5.3"),
    ("VAR-050", "amostra_endereco_prazo", "Endereço e prazo de entrega da amostra", "TEXTO", "endereço e prazo em dias", "CONDICIONAL", "WIZARD", "TR-4.6"),
    ("VAR-051", "amostra_padroes_minimos", "Aspectos e critérios objetivos de aprovação de cada item com amostra", "TABELA", "um critério objetivo por item com amostra", "CONDICIONAL", "CHECKLIST", "TR-4.9.1; TR-4.9.2"),
    ("VAR-052", "amostra_prazo_recolhimento", "Prazo para recolher amostras após o resultado", "NUMERO", "dias, maior que zero", "CONDICIONAL", "WIZARD", "TR-4.13"),
    ("VAR-053", "subcontratacao_percentual", "Limite da subcontratação parcial", "NUMERO", "percentual entre 0 e 100, menor que a parcela principal", "CONDICIONAL", "WIZARD", "TR-4.17"),
    ("VAR-054", "subcontratacao_parcelas", "Parcelas vedadas e parcelas permitidas", "LISTA", "ao menos uma de cada", "CONDICIONAL", "WIZARD", "TR-4.18.1; TR-4.18.2; TR-4.18.3; TR-4.19.1; TR-4.19.2; TR-4.19.3"),
    ("VAR-055", "garantia_contratacao_percentual", "Percentual da garantia da contratação", "NUMERO", "até 5; até 10 com justificativa; acréscimo se antecipação", "CONDICIONAL", "WIZARD", "TR-4.25"),
    ("VAR-056", "garantia_contratacao_base", "Base de cálculo da garantia", "LISTA", "TOTAL ou ANUAL conforme NE-017 nota 3", "CONDICIONAL", "WIZARD", "TR-4.25"),
    ("VAR-057", "percentual_cota_me_epp", "Percentual da cota reservada, aplicado a cada item ou grupo com COTA", "NUMERO", "maior que zero e até 25 (NE-022); sem valor padrão", "CONDICIONAL", "WIZARD", "TR-4.41; TR-1.1.TAB1"),
    ("VAR-058", "margem_preferencia", "Tipo, percentual, decreto, resolução da CICS e enquadramento", "TEXTO", "todos os campos preenchidos", "CONDICIONAL", "WIZARD", "TR-4.42"),
    ("VAR-059", "forma_entrega", "Remessa única ou parcelada", "LISTA", "valor de WZ-26", "S", "WIZARD", "TR-5.1; TR-5.2"),
    ("VAR-060", "prazo_entrega_dias", "Prazo de entrega em dias", "NUMERO", "maior que zero; até 30 se art. 95, II; dentro da vigência", "S", "WIZARD", "TR-5.1; ETP-04.01"),
    ("VAR-061", "termo_inicial_entrega", "A partir de quando conta o prazo de entrega", "TEXTO", "não vazio", "S", "WIZARD", "TR-5.1"),
    ("VAR-062", "parcelas_entrega", "Parcelas, composição e prazos", "TABELA", "soma das parcelas igual à quantidade total de cada item", "CONDICIONAL", "WIZARD", "TR-5.2.TAB1"),
    ("VAR-063", "antecedencia_aviso_atraso", "Dias de antecedência para comunicar atraso", "NUMERO", "maior que zero", "S", "WIZARD", "TR-5.3"),
    ("VAR-064", "enderecos_entrega", "Endereços, horários e setores de recebimento", "TABELA", "ao menos um endereço completo; o checklist identifica a OMS e o setor, mas não pede o endereço", "S", "SISTEMA", "TR-5.4; ETP-04.01"),
    ("VAR-065", "validade_minima_entrega", "Validade mínima comum aos itens perecíveis, quando todos têm o mesmo critério (derivada da VAR-117)", "TEXTO", "vazia quando os itens têm critérios diferentes; nesse caso a validade vai na tabela do item 1.1", "CONDICIONAL", "SISTEMA", "TR-5.4.1; ETP-04.01"),
    ("VAR-066", "garantia_bem_meses", "Prazo da garantia contratual do bem", "NUMERO", "meses, maior que zero", "CONDICIONAL", "WIZARD", "TR-5.6"),
    ("VAR-067", "prazo_reparo_dias_uteis", "Prazo para reparar ou substituir bem com defeito", "NUMERO", "dias úteis, maior que zero", "CONDICIONAL", "WIZARD", "TR-5.12"),
    ("VAR-068", "rotinas_fiscalizacao", "Rotinas específicas de fiscalização", "LISTA", "ao menos uma", "CONDICIONAL", "WIZARD", "TR-6.15.1; TR-6.15.2; TR-6.15.3"),
    ("VAR-069", "multa_moratoria_percentual_dia", "Percentual diário da multa moratória", "NUMERO", "maior que zero", "S", "WIZARD", "TR-7.2.4.1"),
    ("VAR-070", "multa_moratoria_limite_dias", "Limite de dias de atraso para a multa moratória", "NUMERO", "inteiro maior que zero", "S", "WIZARD", "TR-7.2.4.1"),
    ("VAR-071", "multas_compensatorias", "Faixa mínima e máxima de cada multa compensatória", "TABELA", "cada valor entre 0,5 e 30 por cento; mínimo até máximo", "S", "WIZARD", "TR-7.2.4.3; TR-7.2.4.4; TR-7.2.4.5; TR-7.2.4.6; TR-7.2.4.7"),
    ("VAR-072", "infracoes_especificas", "Infrações de inexecução parcial com penalidade diversa", "LISTA", "presente se WZ-33=SIM", "CONDICIONAL", "WIZARD", "TR-7.2.4.7.1"),
    ("VAR-073", "prazo_recolhimento_multa", "Prazo para recolher a multa", "NUMERO", "dias, maior que zero", "S", "WIZARD", "TR-7.7"),
    ("VAR-074", "prazo_substituicao_dias", "Prazo para substituir bens rejeitados", "NUMERO", "dias, maior que zero", "S", "WIZARD", "TR-8.2"),
    ("VAR-075", "prazo_recebimento_definitivo", "Prazo de recebimento definitivo", "NUMERO", "dias úteis, dentro dos 10 dias úteis da liquidação (NE-038)", "S", "WIZARD", "TR-8.3"),
    ("VAR-076", "prazo_recebimento_pequeno_valor", "Prazo de recebimento definitivo no limite do art. 75, II", "NUMERO", "dias úteis, dentro da metade do prazo de liquidação (NE-039)", "S", "WIZARD", "TR-8.4"),
    ("VAR-077", "indice_correcao_atraso", "Índice de correção monetária por atraso no pagamento", "TEXTO", "índice oficial nomeado", "S", "WIZARD", "TR-8.21"),
    ("VAR-078", "indice_reajuste", "Índice de reajuste", "TEXTO", "índice oficial nomeado; setorial de preferência", "S", "WIZARD", "TR-8.41"),
    ("VAR-079", "antecipacao_pagamento", "Forma, valores, etapas, prazo, índice e garantia adicional da antecipação", "TABELA", "garantia adicional até o valor antecipado", "CONDICIONAL", "WIZARD", "TR-8.27; TR-8.28; TR-8.29.1; TR-8.29.2; TR-8.32; TR-8.34; TR-8.36.2"),
    ("VAR-080", "qualif_econ_exercicios", "Último ou dois últimos exercícios sociais", "LISTA", "ULTIMO_EXERCICIO ou DOIS_ULTIMOS_EXERCICIOS (valor de WZ-54)", "CONDICIONAL", "WIZARD", "TR-9.26; TR-9.28"),
    ("VAR-081", "qualif_econ_capital_ou_pl", "Capital mínimo ou patrimônio líquido mínimo", "LISTA", "um dos dois, nunca ambos", "CONDICIONAL", "WIZARD", "TR-9.27"),
    ("VAR-082", "qualif_econ_percentual", "Percentual do capital ou patrimônio líquido mínimo", "NUMERO", "maior que zero e até 10", "CONDICIONAL", "WIZARD", "TR-9.27"),
    ("VAR-083", "qualif_econ_base", "Base do percentual", "LISTA", "VALOR_TOTAL ou VALOR_DA_PARCELA", "CONDICIONAL", "WIZARD", "TR-9.27"),
    ("VAR-084", "qualif_tecnica_entidade", "Entidade profissional competente", "TEXTO", "presente se exigido registro", "CONDICIONAL", "WIZARD", "TR-9.33"),
    ("VAR-085", "qualif_tecnica_atestados", "Características mínimas dos atestados", "LISTA", "sem limite de tempo ou local; quantitativo até 50% das parcelas de maior relevância", "CONDICIONAL", "CHECKLIST", "TR-9.34.1.1; TR-9.34.1.2; TR-9.34.1.3"),
    ("VAR-086", "qualif_tecnica_lei_especial", "Requisito técnico de lei especial e a lei", "TEXTO", "lei existente na base normativa (M07)", "CONDICIONAL", "WIZARD", "TR-9.35"),
    ("VAR-087", "autorizacao_funcionamento", "Atividade sujeita a autorização, órgão expedidor e fundamento", "TEXTO", "fundamento existente na base normativa (M07)", "CONDICIONAL", "WIZARD", "TR-9.14"),
    ("VAR-088", "orcamento_sigiloso", "Orçamento sigiloso", "LISTA", "SIM ou NAO; NAO obrigatório com maior desconto", "S", "WIZARD", "TR-10.1; TR-10.3; TR-12.1; TR-1.1.TAB1"),
    ("VAR-089", "local_tabela_valor", "Valores na tabela do item 1.1 ou em anexo", "LISTA", "ITEM_1.1 ou ANEXO", "CONDICIONAL", "WIZARD", "TR-10.1"),
    ("VAR-090", "matriz_riscos", "Contrato com matriz de alocação de riscos", "LISTA", "SIM ou NAO", "S", "WIZARD", "TR-10.4"),
    ("VAR-091", "dotacao", "Gestão/unidade, fonte, programa de trabalho, elemento de despesa e plano interno", "TABELA", "cinco campos preenchidos", "CONDICIONAL", "WIZARD", "TR-11.2.I; TR-11.2.II; TR-11.2.III; TR-11.2.IV; TR-11.2.V"),
    ("VAR-092", "instrumento_contratual", "Contrato ou instrumento substitutivo", "LISTA", "valor de WZ-43", "S", "WIZARD", "TR-AI.CAB.03; TR-AI.CAB.04; TR-AI-4.1.1; TR-AII.01"),
    ("VAR-093", "anexo1_prazo_aceite_instrumento", "Prazo de aceite e instrumento equivalente", "TEXTO", "prazo e instrumento informados", "CONDICIONAL", "WIZARD", "TR-AI-1.1"),
    ("VAR-094", "anexo1_prazo_decisao", "Prazo para a Administração decidir requerimentos", "TEXTO", "vazio significa um mês (NE-087)", "CONDICIONAL", "WIZARD", "TR-AI-3.1.8.1"),
    ("VAR-095", "anexo1_prazo_reequilibrio", "Prazo para responder pedido de reequilíbrio", "TEXTO", "obrigatório no Anexo I", "CONDICIONAL", "WIZARD", "TR-AI-3.1.9"),
    ("VAR-096", "foro", "Cidade e seção judiciária do foro", "TEXTO", "cidade e seção judiciária", "CONDICIONAL", "SISTEMA", "TR-AI-8.1"),
    ("VAR-097", "data_documento", "Data da minuta", "DATA", "DD/MM/AAAA", "S", "SISTEMA", "TR-ASSIN.01"),
    ("VAR-098", "responsaveis", "Cargo, nome e função de cada responsável", "TABELA", "ao menos um; nunca reproduzido em exemplos", "S", "SISTEMA", "ETP-16.02; TR-ASSIN.02; TR-ASSIN.03"),
    ("VAR-099", "versao_modelo_agu", "Versão do modelo AGU de onde vêm os blocos (mês e ano); metadado da minuta, não impresso no texto", "TEXTO", "MMM/AAAA; igual à versão carregada no sistema", "S", "SISTEMA", "TR-CAB.01"),
    ("VAR-100", "levantamento_mercado_texto", "Alternativas analisadas e justificativa da solução", "TEXTO", "com trecho de origem", "CONDICIONAL", "CHECKLIST", "ETP-05.01"),
    ("VAR-101", "descricao_solucao_texto", "Descrição da solução como um todo", "TEXTO", "com trecho de origem", "S", "CHECKLIST", "ETP-06.01"),
    ("VAR-102", "justificativa_parcelamento", "Justificativa do parcelamento ou não", "TEXTO", "com trecho de origem", "S", "CHECKLIST", "ETP-09.01"),
    ("VAR-103", "contratacoes_correlatas", "Contratações correlatas ou interdependentes", "TEXTO", "presente se WZ-46=SIM", "CONDICIONAL", "WIZARD", "ETP-10.01"),
    ("VAR-104", "resultados_pretendidos", "Resultados pretendidos", "TEXTO", "com trecho de origem", "S", "CHECKLIST", "ETP-12.01"),
    ("VAR-105", "providencias_previas", "Providências antes do contrato", "TEXTO", "presente se WZ-47=SIM", "CONDICIONAL", "WIZARD", "ETP-13.01"),
    ("VAR-106", "impactos_ambientais", "Impactos ambientais e medidas mitigadoras", "TEXTO", "com trecho de origem", "CONDICIONAL", "CHECKLIST", "ETP-14.01"),
    ("VAR-107", "requisitos_texto", "Requisitos da contratação vindos da demanda", "TEXTO", "com trecho de origem", "S", "CHECKLIST", "ETP-04.01"),
    ("VAR-108", "justificativa_viabilidade", "Posicionamento conclusivo compilado do ETP", "TEXTO", "sem fato que não esteja no ETP", "S", "SISTEMA", "ETP-15.02"),
    ("VAR-109", "especificacao_tecnica_itens", "Especificação técnica detalhada de cada item", "TABELA", "uma por item; marca só com 'ou equivalente'", "S", "DFD", "ETP-07.02; TR-1.1.TAB1"),
    ("VAR-112", "tabela_itens.grupo", "Coluna da VAR-011: rótulo do grupo ou lote; vazio = item isolado; itens com o mesmo rótulo "
     "formam um grupo", "TEXTO", "grupo com ao menos 2 itens; itens agrupados exigem o motivo técnico do checklist", "N", "CHECKLIST",
     "TR-1.1.TAB1; ETP-09.01; TR-9.4"),
    ("VAR-113", "tabela_itens.tratamento_me_epp", "Coluna da VAR-011: EXCLUSIVO, COTA, AMPLA ou EXCECAO_JUSTIFICADA, por unidade "
     "de disputa (item isolado ou grupo inteiro)", "LISTA",
     "calculado: até R$ 80.000,00 EXCLUSIVO (NE-003 nota 4); acima, COTA se a parte inteira de quantidade x VAR-057 der ao menos "
     "uma unidade em cada item, senão AMPLA (P22); EXCECAO_JUSTIFICADA só por escolha do usuário, com VAR-120; vazio em "
     "contratação direta", "CONDICIONAL", "SISTEMA", "TR-1.1.TAB1; TR-4.41; ETP-09.01"),
    ("VAR-114", "tabela_itens.exige_amostra", "Coluna da VAR-011: o item exige amostra (S ou N)", "LISTA",
     "S só em licitação ou dispensa eletrônica (NE-013 nota 1); item com S exige critérios na VAR-051", "S", "CHECKLIST",
     "TR-4.5.1; TR-4.5.2; TR-4.5.3; TR-4.9.1; TR-4.9.2"),
    ("VAR-115", "tabela_itens.marca_indicada", "Coluna da VAR-011: marca, fabricante ou modelo indicado; vazio = sem indicação",
     "TEXTO", "marca como referência acompanhada de 'ou equivalente', 'ou similar' ou 'ou de melhor qualidade' (NE-012 nota 2); "
     "indicação exige justificativa na VAR-046", "N", "CHECKLIST", "TR-4.2; TR-1.1.TAB1; ETP-04.01"),
    ("VAR-116", "tabela_itens.perecivel", "Coluna da VAR-011: o item tem prazo de validade (S ou N)", "LISTA",
     "S quando o checklist de consumo informar validade para o item; N nos materiais permanentes", "S", "SISTEMA", "TR-5.4.1"),
    ("VAR-117", "tabela_itens.validade_minima", "Coluna da VAR-011: validade remanescente mínima na entrega, por item",
     "LISTA", "uma das opções do checklist: 12 meses, 75% do prazo total, dois terços do prazo total ou outro critério (com o "
     "critério escrito); obrigatória se perecivel = S; sem valor padrão", "CONDICIONAL", "CHECKLIST", "TR-5.4.1; TR-1.1.TAB1; ETP-04.01"),
    ("VAR-118", "tabela_itens.quantidade_cota", "Coluna da VAR-011: quantidade reservada a ME/EPP no item com COTA", "NUMERO",
     "parte inteira de quantidade x VAR-057 / 100; ao menos 1 (P22)", "CONDICIONAL", "SISTEMA", "TR-1.1.TAB1; TR-4.41"),
    ("VAR-119", "tabela_itens.valor_unidade_disputa", "Coluna da VAR-011: valor estimado do item isolado, ou do grupo a que pertence",
     "MOEDA", "soma de quantidade x valor unitário dos itens da unidade de disputa", "S", "SISTEMA", "TR-4.41; ETP-09.01"),
    ("VAR-120", "tabela_itens.justificativa_excecao_me_epp", "Coluna da VAR-011: hipótese do art. 10, I, II ou IV do Decreto "
     "8.538/2015 e justificativa, quando o item ou grupo é EXCECAO_JUSTIFICADA", "TEXTO",
     "obrigatória com EXCECAO_JUSTIFICADA; fatos técnicos da seção 11 do checklist de consumo quando houver", "CONDICIONAL",
     "WIZARD", "ETP-09.01"),
    ("VAR-121", "tabela_itens.compatibilidade", "Coluna da VAR-011: equipamento, sistema ou produto com que o item deve ser "
     "compatível; vazio = sem exigência", "TEXTO", "identifica o item existente e a compatibilidade necessária", "N", "CHECKLIST",
     "TR-1.1.TAB1; ETP-04.01"),
    ("VAR-122", "tabela_itens.faixa_temperatura", "Coluna da VAR-011: faixa de temperatura de transporte e armazenamento; vazio = "
     "sem controle", "TEXTO", "faixa com limites mínimo e máximo", "N", "CHECKLIST", "ETP-04.01; TR-1.1.TAB1"),
    ("VAR-123", "tabela_itens.controle_especial", "Coluna da VAR-011: o item está sujeito a controle especial (S ou N)", "LISTA",
     "S exige Autorização Especial da empresa como requisito de lei especial (NE-073)", "N", "CHECKLIST", "TR-9.35; ETP-04.01"),
    ("VAR-124", "tabela_itens.garantia_minima_meses", "Coluna da VAR-011: prazo mínimo de garantia técnica do item permanente, em "
     "meses", "NUMERO", "uma das opções do checklist de permanentes (12, 24, 36 ou outro); acima de 12 meses exige "
     "justificativa técnica", "N", "CHECKLIST", "TR-5.6; TR-1.1.TAB1"),
    ("VAR-111", "forma_fornecimento", "Fornecimento integral, parcelado ou continuado (item 9.3)", "LISTA",
     "CONTINUADO se WZ-14=CONTINUO; senão INTEGRAL se WZ-26=REMESSA_UNICA e PARCELADO se WZ-26=PARCELADA", "S", "SISTEMA", "TR-9.3"),
    ("VAR-125", "comodato_equipamentos", "Itens que dependem do equipamento, equipamento e quantidade", "TABELA", "como informado no checklist; sem quantidade sugerida pelo sistema", "CONDICIONAL", "CHECKLIST", "SET-01; ETP-06.01"),
    ("VAR-126", "comodato_servicos", "Instalação, treinamento (com número de profissionais) e manutenção do equipamento em comodato", "LISTA", "opções marcadas nas perguntas 10.7 a 10.9", "CONDICIONAL", "CHECKLIST", "SET-01"),
    ("VAR-127", "comodato_prazo_reparo", "Prazo máximo para reparo ou substituição do equipamento em comodato", "TEXTO", "prazo com unidade, como informado", "CONDICIONAL", "CHECKLIST", "SET-01"),
    ("VAR-128", "transporte_cuidados", "Item e cuidado de transporte (cadeia de frio, luz, umidade, embalagem, produto controlado, logística especial)", "TABELA", "um cuidado marcado por linha", "CONDICIONAL", "CHECKLIST", "SET-02"),
    ("VAR-129", "registro_temperatura_transporte", "Exigência de registro da temperatura durante o transporte (S ou N)", "LISTA", "S ou N", "CONDICIONAL", "CHECKLIST", "SET-02; SET-03"),
    ("VAR-130", "documentos_entrega", "Itens e documentos que acompanham a entrega", "TABELA", "documentos marcados nas perguntas 13.4 e 15.4", "CONDICIONAL", "CHECKLIST", "SET-03"),
    ("VAR-131", "entrega_agendamento_restricoes", "Agendamento, antecedência e restrições de horário, veículo e acesso", "TEXTO", "como informado", "CONDICIONAL", "CHECKLIST", "SET-09; TR-5.4"),
    ("VAR-132", "entrega_emergencial", "Itens, prazo e motivo da entrega emergencial", "TABELA", "prazo informado pela área técnica", "CONDICIONAL", "CHECKLIST", "SET-10"),
    ("VAR-133", "validade_excecao_situacoes", "Situações em que se aceita validade inferior à mínima", "TEXTO", "situações descritas (CK-C-14.4)", "CONDICIONAL", "CHECKLIST", "SET-04"),
    ("VAR-134", "termo_compromisso_substituicao", "Exigência de compromisso de substituição (S ou N)", "LISTA", "S ou N", "CONDICIONAL", "CHECKLIST", "SET-04"),
    ("VAR-135", "requisitos_sanitarios_tecnicos", "Item e requisito (esterilidade, ausência de látex, biocompatibilidade, norma técnica, Inmetro, ambiente especial)", "TABELA", "norma técnica só a indicada pela área técnica", "CONDICIONAL", "CHECKLIST", "SET-07; ETP-04.01"),
    ("VAR-136", "autorizacoes_sanitarias_empresa", "Autorizações sanitárias exigidas da empresa (licença sanitária, AFE, AE para itens controlados, outra)", "LISTA", "opções da pergunta 17.5", "CONDICIONAL", "CHECKLIST", "SET-06; SET-08; TR-9.14; TR-9.35"),
    ("VAR-137", "instalacao_atividades", "Item, atividades de instalação e critérios objetivos de conclusão", "TABELA", "atividades marcadas na pergunta 11.3", "CONDICIONAL", "CHECKLIST", "SET-11"),
    ("VAR-138", "treinamento_requisitos", "Público e quantidade, conteúdo, carga horária, formato, momento e reciclagem do treinamento", "TEXTO", "como informado; sem carga horária sugerida", "CONDICIONAL", "CHECKLIST", "SET-12"),
    ("VAR-139", "garantia_servicos_incluidos", "Serviços incluídos na garantia e local de atendimento", "LISTA", "opções das perguntas 13.4 e 13.5", "CONDICIONAL", "CHECKLIST", "SET-13"),
    ("VAR-140", "prazo_inicio_atendimento", "Prazo máximo para início do atendimento após o chamado", "TEXTO", "opção da pergunta 13.6 ou prazo da 14.3", "CONDICIONAL", "CHECKLIST", "SET-13; SET-14"),
    ("VAR-141", "garantia_marco_inicial", "Marco a partir do qual a garantia conta", "LISTA", "opção da pergunta 13.3", "CONDICIONAL", "CHECKLIST", "SET-13; TR-5.6"),
    ("VAR-142", "software_licencas", "Módulos e tipo de licença, atualizações e suporte do fabricante", "TEXTO", "como informado", "CONDICIONAL", "CHECKLIST", "SET-16"),
    ("VAR-143", "local_requisitos_infraestrutura", "Condições do local e conteúdo do levantamento técnico (site planning)", "TEXTO", "como informado", "CONDICIONAL", "CHECKLIST", "SET-17; ETP-13.01"),
    ("VAR-144", "desinstalacao_requisitos", "Equipamento a retirar, local e procedimentos técnicos especiais", "TEXTO", "como informado", "CONDICIONAL", "CHECKLIST", "SET-18"),
    ("VAR-145", "documentos_recebimento_definitivo", "Documentos exigidos para o recebimento definitivo", "LISTA", "opções das perguntas 11.4 e 19.7", "CONDICIONAL", "CHECKLIST", "SET-11; SET-19; SET-20"),
    ("VAR-146", "conferencia_recebimento", "Itens conferidos no recebimento e situações de recusa", "LISTA", "opções das perguntas 16.1 e 19.1; texto das perguntas 16.2 e 19.4", "CONDICIONAL", "CHECKLIST", "SET-20; TR-8.2"),
    ("VAR-147", "logistica_reversa", "Materiais e situações de recolhimento pelo fornecedor", "TEXTO", "opções das perguntas 21.3 (consumo) e 21.2 (permanentes)", "CONDICIONAL", "CHECKLIST", "SET-22; ETP-14.01"),
    ("VAR-148", "manutencao_preventiva_calibracao", "Periodicidade de manutenção preventiva, calibração e comprovação", "TEXTO", "como informado", "CONDICIONAL", "CHECKLIST", "SET-14"),
    ("VAR-149", "suporte_remoto", "Finalidade e requisitos do suporte remoto", "TEXTO", "como informado; dispara o alerta de TIC (VAL-001) quando houver acesso à rede", "CONDICIONAL", "CHECKLIST", "SET-14"),
    ("VAR-150", "manuais_documentos", "Manuais e documentos técnicos exigidos em português", "LISTA", "como informado", "CONDICIONAL", "CHECKLIST", "SET-19"),
    ("VAR-151", "substituicao_situacoes", "Situações em que o fornecedor substitui o produto", "LISTA", "opções da pergunta 18.2", "CONDICIONAL", "CHECKLIST", "SET-21"),
    ("VAR-152", "equipamento_substituto", "Prazo e características mínimas do equipamento substituto durante o reparo", "TEXTO", "como informado (pergunta 13.8)", "CONDICIONAL", "CHECKLIST", "SET-13; TR-5.14"),
    ("VAR-153", "tabela_itens.classe_pdm", "Coluna da VAR-011: classe e PDM do item, como no DFD do Compras.gov", "TEXTO", "texto do DFD, sem alteração", "N", "DFD", "ETP-07.02"),
    ("VAR-154", "tabela_itens.tic", "Coluna da VAR-011: o item é de TIC segundo a lista de classes mantida pela OM (S ou N)", "LISTA", "calculado pela lista de classes da OM; o sistema não traz lista própria", "N", "SISTEMA", "ETP-07.02"),
    ("VAR-155", "tabela_itens.categoria", "Coluna da VAR-011: CONSUMO ou PERMANENTE, conforme o checklist que lista o item", "LISTA", "CONSUMO ou PERMANENTE", "S", "CHECKLIST", "TR-1.4; ETP-07.02"),
    ("VAR-110", "papel_srp_texto_remissao", "Número da IRP e órgão gerenciador citados na remissão do participante", "TEXTO", "IRP no formato N/AAAA; UASG do gerenciador com 6 dígitos", "CONDICIONAL", "WIZARD", "ETP-04.01; ETP-05.01; ETP-06.01"),
]


def expande(ref, ordem, lista):
    """Expande 'A..B' pela ordem do M02; devolve IDs."""
    if ".." in ref:
        a, b = ref.split("..")
        if a not in ordem or b not in ordem or ordem[a] > ordem[b]:
            raise SystemExit(f"faixa inválida: {ref}")
        return lista[ordem[a]:ordem[b] + 1]
    return [ref]


def ids_citados(texto):
    """IDs de M01, M02, M03 e M04 citados no texto, como escritos (faixas 'A..B' ficam inteiras)."""
    return [m.group(0).rstrip(".-") for m in
            re.finditer(r"\b(?:TR-[A-Za-z0-9.\-]+|ETP-\d{2}\.\d{2}|WZ-\d{2}|NE-\d{3}|VAR-\d{3}|SET-\d{2}|VAL-\d{3}|"
                        r"CK-[CP]-(?:CAB\.\d{2}|\d{1,2}(?:\.\d{1,2})?))", texto)]


def refs(texto, ordem, lista):
    """IDs citados com as faixas expandidas pela ordem do M02."""
    res = []
    for tok in ids_citados(texto):
        res.extend(expande(tok, ordem, lista) if ".." in tok else [tok])
    return res


def main():
    m01 = {r["id"] for r in csv.DictReader(open(sys.argv[1], encoding="utf-8-sig"))}
    m02_rows = list(csv.DictReader(open(sys.argv[2], encoding="utf-8-sig")))
    lista = [r["id"] for r in m02_rows]
    ordem = {k: i for i, k in enumerate(lista)}
    saida = Path(sys.argv[3])
    wz_ids = {w[0] for w in W}
    var_ids = {v[0] for v in V}
    # VAR acrescentadas pelo f10_gerar_expr (NOVAS_M05), que roda depois deste script
    from f10_gerar_expr import NOVAS_M05
    var_ids |= {v["id"] for v in NOVAS_M05}
    validos = set(lista) | m01 | wz_ids | var_ids | {f"NE-{k:03d}" for k in range(1, 103)}
    # IDs das matrizes das Fases 6 e 7 e do M11, quando já geradas (a conferência final é o teste 3 da Fase 9)
    for nome in ("M08_clausulas_setoriais.csv", "M10_validacoes.csv", "M11_checklist.csv"):
        if (saida / nome).exists():
            validos |= {r["id"] for r in csv.DictReader(open(saida / nome, encoding="utf-8-sig"))}
    ausentes = {"SET": not (saida / "M08_clausulas_setoriais.csv").exists(), "VAL": not (saida / "M10_validacoes.csv").exists(),
                "CK-": not (saida / "M11_checklist.csv").exists()}

    def existe(x):
        return x in validos or any(x.startswith(k) and v for k, v in ausentes.items())
    controlados = set()
    linhas4 = []
    for (wid, perg, doc, tipo, opc, dep, liga, desl, just, coer, fund, st) in W:
        for campo in (perg, opc, dep, liga, desl, just, coer, fund):
            for x in refs(campo, ordem, lista):
                if not existe(x):
                    raise SystemExit(f"{wid}: ID inexistente {x}")
        for x in refs(PRE[wid], ordem, lista):
            if not existe(x):
                raise SystemExit(f"{wid}: pre_preenchida_por cita ID inexistente {x}")
        for campo in (liga, desl):  # trecho 'Preenche ...' só preenche lacunas: não conta como ligar ou desligar
            for seg in campo.split("|"):
                if not re.match(r"\s*(?:[A-Z_]+:\s*)?Preenche", seg):
                    controlados.update(x for x in refs(seg, ordem, lista) if x.startswith("TR-"))
        status = st or "INFERIDO"
        fonte = ("Desenho a partir das alternativas do M02 e das regras do M03 (Fase 3); liga_blocos e desliga_blocos usam IDs do M02 "
                 "e do M01, com 'A..B' para faixa na ordem do M02. Campos INFERIDOS: todos, exceto os IDs citados. "
                 "pre_preenchida_por: perguntas dos checklists técnicos (M11) que respondem ou apoiam a WZ (22/10/2026); "
                 "liga_expr e desliga_expr: JSON Logic gerado pelo f6_gerar_expr.py a partir de liga_blocos e desliga_blocos.")
        if wid == "WZ-60":
            fonte += " Pergunta criada na Fase 12 (23/10/2026) pela resposta da P25 (característica de atestado permitida)."
        if wid in ("WZ-56", "WZ-57", "WZ-58", "WZ-59"):
            fonte += " Pergunta criada na Fase 6 para as cláusulas setoriais do M08 (numeração a partir de WZ-56)."
        if wid == "WZ-11":
            fonte += (" O participante faz o ETP e não elabora TR; o TR é compilado pela OM gerenciadora (informado pelo usuário "
                      "em 21/10/2026, P13).")
        if wid == "WZ-51":
            fonte += (" P16 fechada em 23/10/2026: Decreto 12.174/2024 conferido no planalto.gov.br (art. 1º, caput: garantias "
                      "trabalhistas na execução dos contratos administrativos; art. 2º, caput: 'Os contratos administrativos "
                      "conterão cláusulas que disponham sobre:'), com a alteração do Decreto 12.926/2026, que não tocou o art. 2º. "
                      "INFERIDO: a aplicação ao instrumento substitutivo do Anexo I (WZ-43 diferente de CONTRATO) é leitura "
                      "minha, não texto do decreto.")
        if status == "A_VERIFICAR":
            fonte += " A_VERIFICAR: ver perguntas_abertas.md."
        linhas4.append({"id": wid, "pergunta": perg, "documento": doc, "tipo_resposta": tipo, "opcoes": opc,
                        "depende_de": dep, "pre_preenchida_por": PRE[wid], "liga_blocos": liga, "desliga_blocos": desl, "exige_justificativa": just,
                        "coerencia": coer, "fundamento": fund, "fonte": fonte, "status": status})
    # blocos condicionais do M02 sem pergunta que os controle
    sem_controle = []
    for r in m02_rows:
        if "OP" in r["tipo"] and r["item_modelo"] != "OU" and r["id"] not in controlados and not r["id"].startswith(("TR-CAB", "TR-ASSIN")):
            sem_controle.append(r["id"])
    linhas5 = []
    for (vid, nome, desc, tipo, val, obr, origem, usada) in sorted(V, key=lambda v: v[0]):
        for ref in [x.strip() for x in usada.split(";")]:
            if not existe(ref):
                raise SystemExit(f"{vid}: usada_em inexistente {ref}")
        status = "INFERIDO"
        fonte = "Desenho a partir das lacunas do M02, dos campos do M01 e das perguntas do M04 (Fase 3)."
        if origem == "DFD":
            fonte += (" Campo presente nos DFDs da base: DFD 18/2026 e DFD 710/2025 (formato do Compras.gov: 1. Informações "
                      "Gerais, 2. Justificativa de Necessidade, 3. Materiais/Serviços, 4. Responsáveis) e DFD da PMPV (formato próprio).")
        elif origem == "CHECKLIST":
            fonte += " Origem no checklist técnico da área requisitante: as perguntas estão nos destinos do M11."
        if vid in ("VAR-038", "VAR-039", "VAR-040", "VAR-041", "VAR-042", "VAR-043"):
            fonte += " Os DFDs e os checklists da base não trazem os dados do PCA: a equipe administrativa os informa (WZ-49)."
        if "VAR-125" <= vid <= "VAR-152":
            fonte += " Variável criada na Fase 6 para o texto das cláusulas setoriais do M08 (fonte: checklist)."
        if vid in ("VAR-153", "VAR-154", "VAR-155"):
            fonte += " Atributo de item criado na Fase 7 para as regras VAL-001 e VAL-050 do M10."
        if vid in ("VAR-112", "VAR-113", "VAR-114", "VAR-115", "VAR-116", "VAR-117", "VAR-118", "VAR-119", "VAR-120",
                   "VAR-121", "VAR-122", "VAR-123", "VAR-124"):
            fonte += " Atributo de item criado no ajuste 1 da revisão de 21/10/2026, com origem no checklist (tarefa 5 de 22/10/2026)."
        if vid in ("VAR-039", "VAR-043"):
            fonte += " O padrão de validação foi observado nos documentos do corpus, não em norma."
        linhas5.append({"id": vid, "nome": nome, "descricao": desc, "tipo_dado": tipo, "validacao": val, "obrigatoria": obr,
                        "origem": origem, "usada_em": usada, "fonte": fonte, "status": status})
    saida.mkdir(parents=True, exist_ok=True)
    gravar_csv(saida / "M04_wizard.csv", COLS4, linhas4,
               preservar=("validacao", "comentario_validacao", "liga_expr", "desliga_expr"))
    gravar_csv(saida / "M05_variaveis.csv", COLS5, linhas5, preservar=())
    print(f"M04: {len(linhas4)} perguntas | M05: {len(linhas5)} variáveis")
    print(f"blocos condicionais do M02 sem pergunta que os ligue ou desligue ({len(sem_controle)}): {sem_controle}")


if __name__ == "__main__":
    main()
