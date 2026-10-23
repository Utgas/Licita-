#!/usr/bin/env python3
"""Fase 1 - Gera M03_notas_explicativas.csv (as 102 notas do modelo AGU de TR).

Uso: python3 -I f1_gerar_M03.py <modelo.docx> <f1_modelo.json> <f1_blocos.json> <pasta_saida> [M04_wizard.csv]

Campos EXTRAIDOS do docx: trecho_ancorado, texto_integral, citacoes (extrator citacoes.py + acrescimos
manuais marcados abaixo, sempre como escritos na nota), bloco_ancora (bloco do M02 onde a ancora comeca).
Campos INFERIDOS (leitura de cada nota): natureza, regra_derivada, afeta.
A coluna afeta recebe os IDs WZ do M04 (Fase 3) e os IDs VAL do M10 (Fase 7, dicionário VAL_NOTAS).
As colunas validacao e comentario_validacao (revisão do usuário no xlsx) são preservadas entre gerações (comum.gravar_csv).
"""
import csv
import json
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from citacoes import extrair  # noqa: E402
from comum import gravar_csv  # noqa: E402

# regras do M10 que dependem de cada nota (Fase 7)
VAL_NOTAS = {1: ["VAL-043"], 3: ["VAL-016", "VAL-017"], 12: ["VAL-018"], 13: ["VAL-012", "VAL-013"], 14: ["VAL-030"],
             22: ["VAL-014", "VAL-016", "VAL-017"], 27: ["VAL-026"], 29: ["VAL-026"], 60: ["VAL-041"],
             71: ["VAL-028", "VAL-029"], 73: ["VAL-011", "VAL-041"]}

COLS = ["id", "bloco_ancora", "trecho_ancorado", "texto_integral", "natureza", "regra_derivada", "afeta",
        "citacoes", "fonte", "status", "validacao", "comentario_validacao"]
DOCX = "TR exemplos/modelo-de-termo-de-referencia-compras-lei-no-14-133-dez-25.docx"

C, O, V, OR, RN, PF = ("CONDICAO", "OBRIGACAO", "VEDACAO", "ORIENTACAO_REDACAO", "REMISSAO_NORMATIVA",
                       "PROCEDIMENTO_FORA_DO_TR")

# natureza, regra, WZ afetados, citacoes acrescentadas a mao (como escritas), observacao
N = {
    1: (O, "OBRIGAÇÃO: (1) texto em preto é invariável; SE alterado ENTÃO exigir justificativa nos autos (item 2) SENÃO copiar literal; "
           "(2) texto em vermelho itálico é preenchido ou escolhido e deve repetir as mesmas definições no edital e no contrato (item 3); "
           "(3) as notas explicativas nunca entram na minuta final (item 4); (4) registrar a versão do modelo (mês e ano) na minuta ou no "
           "despacho (item 5); (5) SE não usar o modelo AGU ENTÃO justificar por escrito no processo (item 8); (6) considerar o relatório "
           "final de contratação anterior (item 9)", [], [], ""),
    2: (OR, "Orientação de redação: manter os termos 'fornecedor' e 'interessado', que abrangem licitantes e contratados", [], [], ""),
    3: (C, "SE valor do item até R$ 80.000,00 ENTÃO item de participação exclusiva de ME/EPP (nota 4) SENÃO ampla participação, avaliando "
           "cota reservada (NE-022); SE houver parcelamento ou não ENTÃO a justificativa fica no ETP (nota 2); SE contratação direta ENTÃO o "
           "parcelamento só é analisado em dispensa eletrônica ou outro regime competitivo (nota 3). A tabela é ilustrativa (nota 1). "
           "Nota 5 (BIM) trata de obras e serviços de engenharia, fora do escopo", ["WZ-24", "WZ-50", "WZ-05"], [], ""),
    4: (C, "SE orçamento sigiloso ENTÃO deixar em branco as colunas de valor unitário e total da tabela de itens (TR-1.1.TAB1) SENÃO "
           "preenchê-las com os valores da pesquisa de preços", ["WZ-40"], [], "Âncora de comprimento zero (posição na célula 'VALOR TOTAL')."),
    5: (C, "SE bem comum ENTÃO TR-1.2 SENÃO TR-1.3; a declaração da natureza comum cabe ao setor técnico (nota 1, ON AGU 54/2014) e "
           "segue as definições do art. 6º, XIII e XIV (nota 2)", ["WZ-06"], [], ""),
    6: (V, "VEDAÇÃO: não adquirir artigos de luxo; SE itens de consumo ENTÃO manter TR-1.4 e respeitar o enquadramento do Decreto "
           "10.818/2021", ["WZ-07"], [], ""),
    7: (C, "SE fornecimento não contínuo ENTÃO TR-1.5 (art. 105, créditos do exercício, salvo PPA); SE contínuo ENTÃO TR-1.6 e TR-1.7, "
           "com justificativa do enquadramento e ateste de maior vantagem econômica, prorrogável até 10 anos; SE emergência ou calamidade "
           "ENTÃO TR-1.8, até 1 ano, improrrogável, vedada a recontratação; SE dispensa por valor com vigência plurianual ENTÃO considerar o "
           "valor de 1 ano (nota 5, ON 87/2024)", ["WZ-14", "WZ-15", "WZ-04"], [], ""),
    8: (RN, "Remissão normativa: a fundamentação do TR é feita por referência ao ETP (TR-2.1, texto fixo); sem regra adicional", [], [], ""),
    9: (OR, "Orientação de redação: SE a descrição da solução mudou em relação ao ETP ENTÃO complementar no item 3.1; considerar o ciclo de "
            "vida, normas técnicas da ABNT, o catálogo eletrônico de padronização (justificar o não uso) e elementos concretos de "
            "sustentabilidade", ["WZ-17"], [], ""),
    10: (OR, "Orientação de redação: requisitos técnicos adicionais podem entrar na seção 4 (vindos do ETP); documentos de habilitação "
             "técnica ficam na seção 9; os requisitos devem constar também do TR Digital e do ETP Digital", [], [], ""),
    11: (C, "SE houver justificativa nos autos para não adotar critérios de sustentabilidade ENTÃO suprimir TR-4.H01 a TR-4.1.3 e registrar "
            "a justificativa no ETP SENÃO incluir critérios específicos, claros e com forma objetiva de comprovação, registrados também "
            "no ETP Digital", ["WZ-17"], [], ""),
    12: (C, "SE houver indicação de marca ou modelo ENTÃO justificar tecnicamente nas hipóteses do art. 41, I, e, quando a marca for "
            "referência, usar 'ou equivalente', 'ou similar' ou 'ou de melhor qualidade' SENÃO suprimir TR-4.H02 e TR-4.2",
         ["WZ-18"], [], ""),
    13: (C, "SE exigida amostra ENTÃO justificar no ETP e disciplinar no TR a forma e os critérios de avaliação SENÃO suprimir TR-4.H04 a "
            "TR-4.14; SE contratação direta ENTÃO só cabe em dispensa eletrônica", ["WZ-20", "WZ-05"], [], ""),
    14: (C, "SE exigida carta de solidariedade ENTÃO só em situação excepcional e motivada SENÃO suprimir TR-4.H05 e TR-4.15",
         ["WZ-21"], [], ""),
    15: (V, "VEDAÇÃO: não exigir subcontratação no fornecimento de bens, salvo serviço acessório; vedada a subcontratação completa ou da "
            "parcela principal; avaliar à luz do art. 122", ["WZ-22", "WZ-08"], [], ""),
    16: (C, "SE permitida subcontratação parcial ENTÃO detalhar limites, condições e parcelas (TR-4.17 a TR-4.23); SE aquisição com serviço "
            "acessório ENTÃO pode exigir subcontratação de ME/EPP com os itens sugeridos na nota 3, que não existem no corpo do modelo",
         ["WZ-22", "WZ-08"], [], "A nota 3 traz itens numerados 4.24 a 4.29 que não correspondem à numeração do corpo do modelo (P17, P18)."),
    17: (C, "SE exigida garantia da contratação ENTÃO percentual de até 5%, ou até 10% com justificativa de alta complexidade, acrescido de "
            "garantia adicional se houver antecipação e do valor de bens depositados; base: contínuo até 1 ano, valor total; acima de 1 ano, "
            "valor anual; demais, valor inicial; seguro-garantia antes da assinatura; demais modalidades em 10 dias úteis SENÃO TR-4.24",
         ["WZ-23", "WZ-35", "WZ-14", "WZ-53"], [], ""),
    18: (V, "VEDAÇÃO: não aceitar garantia prestada por Sociedade de Crédito Direto (SCD) ou Sociedade de Empréstimo entre Pessoas (SEP)",
         ["WZ-23"], [], "Âncora de uma palavra ('contratação') no item 4.25."),
    19: (C, "SE o contrato implicar entrega de bens pela Administração, com o contratado como depositário (art. 101), ENTÃO certificar o "
            "valor dos bens e acrescentar à garantia o item sugerido na nota", ["WZ-23"], [], "Âncora de comprimento zero no item 4.25."),
    20: (RN, "Remissão normativa: caução em dinheiro na Caixa Econômica Federal decorre do Decreto-Lei 1.737/1979; sem regra adicional",
         [], [], ""),
    21: (RN, "Remissão normativa: prazo de 10 dias úteis, prorrogável, para repor a garantia, por analogia à IN SEGES/MP 05/2017 "
             "aplicada pela IN SEGES/ME 98/2022", [], [], ""),
    22: (C, "SE licitação de bens divisíveis ENTÃO reservar cota de até 25% para ME/EPP por item (ou por grupo, considerado como item) e "
            "identificar no TR as cotas e os itens de origem, SALVO exceção justificada do art. 10, I, II ou IV do Decreto 8.538/2015; "
            "SE o item já for exclusivo para ME/EPP (até R$ 80.000,00) ENTÃO não cabe cota; a cota não se limita a R$ 80.000,00",
         ["WZ-24", "WZ-13", "WZ-50"], [], ""),
    23: (C, "SE o objeto estiver contemplado com margem de preferência normal ou adicional em resolução da CICS ENTÃO incluir TR-4.42 com "
            "a justificativa do enquadramento SENÃO suprimir TR-4.H09 e TR-4.42", ["WZ-25"], [], "Âncora de uma palavra ('por')."),
    24: (OR, "Orientação de redação: a seção 5 é exemplificativa e deve ser adaptada; as notas 2 e 3 tratam de serviços com mão de obra, "
             "fora do escopo de aquisições", [], [], ""),
    25: (C, "SE entrega parcelada ENTÃO discriminar parcelas, composição e prazos na tabela (TR-5.2.TAB1), que é ilustrativa SENÃO TR-5.1",
         ["WZ-26", "WZ-27"], [], ""),
    26: (O, "OBRIGAÇÃO: registrar no TR Digital os locais de entrega e as regras de recebimento; SE houver mais de um endereço ou endereço "
            "por entrega ENTÃO especificar cada um; SE houver agendamento com o almoxarifado ENTÃO especificar", ["WZ-28"], [], ""),
    27: (C, "SE exigida garantia contratual do bem ENTÃO fundamentar no próprio item e registrar no TR Digital SENÃO suprimir o item",
         ["WZ-29"], [], ""),
    28: (OR, "Orientação de redação: a redação do item 5.5 (garantia legal do CDC) é a sugerida para material de consumo",
         ["WZ-29", "WZ-07"], [], ""),
    29: (C, "SE material permanente ENTÃO a redação sugerida é a do item 5.6; a exigência e o prazo de garantia contratual devem ser "
            "justificados nos autos", ["WZ-29", "WZ-07"], [], ""),
    30: (C, "SE fundamentado no ETP ENTÃO pode exigir assistência técnica com deslocamento de técnico ou unidade em distância compatível",
         ["WZ-29"], [], ""),
    31: (PF, "Procedimento fora do TR: designação de gestores e fiscais pela autoridade e juntada dos atos de designação aos autos",
         [], [], ""),
    32: (C, "SE houver rotinas de fiscalização específicas do objeto ENTÃO incluir TR-6.15 e subitens SENÃO suprimir", ["WZ-30"], [], ""),
    33: (OR, "Orientação de redação: definir o prazo limite de mora a partir do qual a multa moratória é convertida em compensatória, com "
             "extinção do contrato; as multas podem ser escalonadas por dias de atraso", ["WZ-32"], [], ""),
    34: (C, "SE não exigida garantia da contratação ENTÃO suprimir TR-7.2.4.2 e TR-7.2.4.2.1 (nota 2) SENÃO manter os percentuais da "
            "IN SEGES/MP 05/2017 (nota 1)", ["WZ-23"], [], "Âncora de comprimento zero no item 7.2.4.2."),
    35: (OR, "Orientação de redação: a redação é exemplificativa; multas maiores para infrações mais graves (as sujeitas a inidoneidade "
             "são mais graves que as sujeitas a impedimento)", ["WZ-32"], [], ""),
    36: (O, "OBRIGAÇÃO: multa compensatória entre 0,5% e 30% do valor do contrato (art. 156, § 3º); a multa moratória não tem esses "
            "limites e fica limitada ao valor da obrigação principal", ["WZ-32"], [], ""),
    37: (OR, "Orientação de redação: o recebimento pode ser detalhado, inclusive por fiscal técnico e administrativo", [], [], ""),
    38: (O, "OBRIGAÇÃO: o prazo de recebimento definitivo deve caber no prazo de liquidação de 10 dias úteis, junto com o recebimento "
            "provisório e a liquidação", ["WZ-34"], [], ""),
    39: (C, "SE o valor não ultrapassar o limite do art. 75, II, ENTÃO o prazo de recebimento definitivo é reduzido à metade, como o de "
            "liquidação", ["WZ-34"], [], ""),
    40: (O, "OBRIGAÇÃO: indicar o índice de atualização monetária por atraso no pagamento (TR-8.21)", ["WZ-36"], [], ""),
    41: (OR, "Orientação de redação: a retenção tributária depende da natureza do contrato e do objeto", [], [], ""),
    42: (C, "SE adotado pagamento antecipado ENTÃO incluir a seção e demonstrar nos autos, com justificativa prévia, que é condição "
            "indispensável para obter o bem ou gera sensível economia SENÃO suprimir TR-8.H05 a TR-8.37", ["WZ-35"], [], ""),
    43: (OR, "Orientação de redação: ajustar os itens da antecipação (parcial, integral, por etapas) e justificar especificamente a forma "
             "escolhida", ["WZ-35", "WZ-52"], [], ""),
    44: (C, "SE adotadas as cautelas facultativas do art. 145, § 2º, ENTÃO justificar a adequação, valores e percentuais, inclusive se "
            "nenhuma for adotada", ["WZ-35", "WZ-53"], [], ""),
    45: (C, "SE houver antecipação durante a execução ENTÃO prever os momentos de comprovação (TR-8.36.1) SENÃO suprimir o subitem",
         ["WZ-52"], [], ""),
    46: (C, "SE exigida garantia adicional ENTÃO fixar percentual razoável e, na antecipação parcial, não superior ao valor antecipado",
         ["WZ-53"], [], ""),
    47: (OR, "Orientação de redação: manter a cláusula de cessão de crédito, admitida pelo Parecer JL-01/2020 salvo vedação expressa",
         [], [], ""),
    48: (C, "SE o órgão decidir vedar a cessão de crédito ENTÃO alterar o item 8.38 (texto em preto: exige justificativa) SENÃO manter",
         [], [], ""),
    49: (RN, "Remissão normativa: os condicionamentos da cessão de crédito vêm do Parecer JL-01/2020; sem regra adicional", [], [], ""),
    50: (OR, "Orientação de redação: operação de crédito pelo AntecipaGov não é cessão de crédito e independe de previsão no TR",
         [], [], "Texto sem o rótulo 'Nota Explicativa'."),
    51: (O, "OBRIGAÇÃO: indicar a data-base do orçamento estimado (TR-8.40), fixada pelo gestor em cada caso", ["WZ-36"],
         ["art. 25, § 7, e art. 92, inciso V e § 3º"], "Âncora de uma palavra ('AAAA')."),
    52: (O, "OBRIGAÇÃO: usar o índice mais próximo da variação dos preços, de preferência setorial ou específico; mais de um índice só "
            "com justificativa e indicação do insumo de cada um", ["WZ-36"], [], ""),
    53: (C, "Reajuste de ofício é a regra; SE condicionar o reajuste a pedido do contratado ENTÃO motivar nos autos e ajustar a minuta de "
            "contrato", ["WZ-36"], [], "Âncora de uma palavra ('ontratado')."),
    54: (C, "SE contratação direta ENTÃO adequar o título da subseção e registrar a justificativa da dispensa ou inexigibilidade; SE "
            "licitação ENTÃO pregão para bens comuns (menor preço ou maior desconto) e concorrência para bens especiais",
         ["WZ-01", "WZ-02", "WZ-03", "WZ-06"], ["art. 6º, inciso XLI, c/c art. 29", "art. 6º, inciso XXXVIII, c/c o art. 29"],
         "Âncora de uma palavra ('proposta')."),
    55: (C, "SE registro de preços com critério de menor preço ou maior desconto por grupo de itens ENTÃO incluir TR-9.4 e TR-9.4.1 "
            "SENÃO suprimir", ["WZ-10", "WZ-13", "WZ-03"], [], "Âncora de uma palavra ('será')."),
    56: (C, "VEDAÇÃO de requisito de habilitação sem suporte nos arts. 66 a 69; SE entrega imediata, valor abaixo de 1/4 do limite de "
            "dispensa ou produto para pesquisa e desenvolvimento ENTÃO qualificação técnica e econômica só excepcional e justificada; "
            "exigências podem variar por item", ["WZ-37", "WZ-38"], ["art. 182 da mesma Lei"], ""),
    57: (RN, "Remissão normativa: participação de pessoa física (IN SEGES/ME 116/2021) deve ser analisada no planejamento; sem regra "
             "para o TR", [], [], "Texto idêntico ao da NE-058, ancorada no mesmo trecho (P18)."),
    58: (RN, "Remissão normativa: participação de pessoa física (IN SEGES/ME 116/2021) deve ser analisada no planejamento; sem regra "
             "para o TR", [], [], "Texto idêntico ao da NE-057 (nota duplicada no modelo; P18)."),
    59: (OR, "Orientação de redação: empresa identificada como EIRELI deve ser tratada como SLU", [], [], ""),
    60: (C, "SE a atividade exigir registro ou autorização para funcionamento ENTÃO especificar documento, órgão expedidor e fundamento "
            "legal em TR-9.14 SENÃO suprimir", ["WZ-39"], [], ""),
    61: (C, "SE aquisição de bens ENTÃO inscrição e regularidade perante a Fazenda Estadual (ICMS); SE houver serviço ENTÃO ajustar para "
            "a municipal (ISS)", ["WZ-08"], [], ""),
    62: (OR, "Orientação de redação: o CCMEI supre a inscrição nos cadastros fiscais", [], [], ""),
    63: (C, "SE exigida qualificação econômico-financeira ENTÃO manter a subseção, podendo restringir a alguns itens SENÃO suprimir; "
            "SE contratação direta não precedida de dispensa eletrônica ENTÃO os critérios podem ficar só no processo",
         ["WZ-37", "WZ-05"], [], ""),
    64: (C, "SE exigidas demonstrações dos dois últimos exercícios ENTÃO justificar e apurar os índices em cada exercício SENÃO exigir só "
            "o último", ["WZ-37", "WZ-54"], [], "Âncora de uma palavra ('fórmulas')."),
    65: (C, "SE exigido capital mínimo ou patrimônio líquido mínimo ENTÃO escolher um dos dois, motivadamente, com percentual de até 10% "
            "proporcional ao risco (VEDADA a cumulação)", ["WZ-37"], [], ""),
    66: (C, "SE exigidas demonstrações dos dois últimos exercícios ENTÃO incluir TR-9.28 SENÃO suprimir", ["WZ-54"], [],
         "Âncora de uma palavra ('inabilitação')."),
    67: (C, "SE adotada declaração de profissional contábil sobre os índices ENTÃO justificar e incluir TR-9.32 SENÃO suprimir",
         ["WZ-55"], [], ""),
    68: (C, "SE contratação direta sem dispensa eletrônica ENTÃO a habilitação pode ficar só no processo; SE exigida qualificação técnica "
            "na compra ENTÃO só quando indispensável, ajustando todas as cláusulas com base no ETP; atestados de potencial subcontratado "
            "até 25% do objeto", ["WZ-38", "WZ-05", "WZ-22"], [], ""),
    69: (OR, "Orientação de redação: ajustar as cláusulas de qualificação técnica à demanda; a nota 2 remete a 'vistoria', item que não "
             "existe neste modelo", ["WZ-38"], [], "Nota 1 repete a nota 3 da NE-068; nota 2 cita item inexistente no modelo (P18)."),
    70: (C, "SE a lei sujeitar a atividade a conselho profissional ENTÃO TR-9.33 com a entidade indicada SENÃO excluir o subitem",
         ["WZ-38"], [], ""),
    71: (C, "SE houver atividade associada ao fornecimento (ex.: logística complexa, instalação de equipamento sofisticado) ENTÃO exigir "
            "atestados com quantitativos objetivos, até 50% das parcelas de maior relevância (valor individual de 4% ou mais), sem "
            "limitação de tempo ou local SENÃO não exigir; SE subcontratação de aspectos técnicos permitida ENTÃO admitir atestados de "
            "potencial subcontratado até 25%, com a disposição sugerida na nota 4", ["WZ-38", "WZ-08", "WZ-22"], [],
         "A nota 4 traz texto pronto para inserir no TR, fora do corpo do modelo (P17)."),
    72: (RN, "Remissão normativa: atestados podem estar em nome da matriz ou da filial (Parecer 00005/2021/CNMLC/CGU/AGU); sem regra "
             "adicional", ["WZ-38"], [], ""),
    73: (C, "SE lei específica exigir requisito técnico para a atividade ENTÃO indicar em TR-9.35 (ex.: Autorização Especial da Anvisa "
            "para medicamentos sujeitos a controle especial) SENÃO suprimir", ["WZ-38"], [], ""),
    74: (C, "SE critério de menor preço sem sigilo ENTÃO TR-10.1 (nota 3); a estimativa vem de pesquisa de preços regular (nota 1) e os "
            "preços unitários referenciais e memórias vão em anexo, sigiloso se o orçamento for sigiloso (nota 2)",
         ["WZ-03", "WZ-40"], [], ""),
    75: (PF, "Procedimento fora do TR: SE dispensa por valor (art. 75, I e II) ENTÃO a estimativa pode ser feita junto com a seleção, por "
             "cotações a fornecedores", ["WZ-04"], [], ""),
    76: (C, "SE critério de maior desconto ENTÃO TR-10.2", ["WZ-03"], [], ""),
    77: (C, "SE menor preço e opção por sigilo ENTÃO TR-10.3; SE maior desconto ENTÃO o orçamento NÃO pode ser sigiloso", ["WZ-40", "WZ-03"],
         [], ""),
    78: (C, "SE houver matriz de alocação de riscos ENTÃO incluir TR-10.4 e considerar os riscos alocados no custo estimado SENÃO suprimir",
         ["WZ-41"], [], ""),
    79: (C, "SE fornecimento continuado ENTÃO atestar créditos e vantagem no início de cada exercício e incluir TR-11.3; extinção por falta "
            "de crédito conforme o contrato", ["WZ-14", "WZ-42"], [], ""),
    80: (C, "SE registro de preços ENTÃO TR-11.4: a dotação só é exigida antes da assinatura do contrato", ["WZ-10"], [],
         "Âncora de uma palavra ('equivalente')."),
    81: (PF, "Procedimento fora do TR: avaliar a classificação do TR pela LAI; no TR, o item 12.1 leva o trecho do orçamento sigiloso só "
             "se houver sigilo", ["WZ-40"], [], ""),
    82: (PF, "Procedimento fora do TR: elaboração conjunta pelas áreas técnica e requisitante designadas, ou pela equipe de planejamento",
         [], [], ""),
    83: (C, "SE contratação de pequeno valor (art. 95, I: valor nos limites do art. 75, I ou II, ON AGU 84/2024) OU compra com entrega "
            "imediata (até 30 dias da ordem) e integral, sem obrigações futuras nem assistência técnica (art. 95, II) ENTÃO incluir o "
            "Anexo I e colher a assinatura no Anexo II SENÃO termo de contrato", ["WZ-43", "WZ-27", "WZ-29", "WZ-08"], [],
         "Âncora de uma letra ('I', do título 'ANEXO I')."),
    84: (C, "SE contratação de pequeno valor com fornecimento contínuo ENTÃO TR-AI-2.3 a TR-AI-2.7", ["WZ-43", "WZ-14"],
         ["art. 6º, XV do mesmo normativo"], ""),
    85: (O, "OBRIGAÇÃO: consultar o Cadin antes de aditar; registro no Cadin impede o aditamento nos contratos firmados desde 16/09/2024",
         [], [], "Âncora de uma palavra ('Cadin')."),
    86: (C, "SE emergência ou calamidade (art. 75, VIII) ENTÃO TR-AI-2.8", ["WZ-14", "WZ-43"], [], ""),
    87: (C, "SE não especificado o prazo para a Administração decidir ENTÃO vale um mês", ["WZ-44"], [], ""),
    88: (O, "OBRIGAÇÃO: fixar prazo de resposta ao pedido de reequilíbrio (cláusula necessária), podendo ser o mesmo do art. 123",
         ["WZ-44"], [], ""),
    89: (C, "SE contratação de pequeno valor (art. 95, I) ENTÃO TR-AI-3.1.10 se aplica SENÃO suprimir", ["WZ-43", "WZ-23"], [],
         "Trata do mesmo item que a NE-090 (P18)."),
    90: (RN, "Remissão normativa: o item decorre do art. 137, § 4º; sem regra adicional além da NE-089", [], [], "Trata do mesmo item que a NE-089 (P18)."),
    91: (OR, "Orientação de redação: as obrigações são gerais; incluir, modificar ou excluir conforme o objeto", ["WZ-08"], [], ""),
    92: (C, "SE contratação de pequeno valor (art. 95, I) ENTÃO manter o trecho sobre a rede de assistência técnica autorizada em "
            "TR-AI-4.1.1 SENÃO suprimir o trecho", ["WZ-43"], [], "Âncora de uma palavra ('autorizada')."),
    93: (OR, "Orientação de redação: o prazo de correção é fixado caso a caso pelo fiscal", [], [], ""),
    94: (C, "SE aquisição com serviço acessório ENTÃO avaliar TR-AI-4.1.17 a TR-AI-4.1.21; SE houver tratamento de dados pessoais ENTÃO "
            "incluir a cláusula de LGPD do modelo de serviços", ["WZ-08"], [],
         "A cláusula de LGPD está no modelo de serviços, fora da base (P17)."),
    95: (RN, "Remissão normativa: os itens TR-AI-4.1.22 a TR-AI-4.1.26 decorrem do art. 2º do Decreto 12.174/2024; a nota não diz "
             "quando suprimi-los (P16)", ["WZ-51"], [],
         "Âncora de uma palavra ('trabalho')."),
    96: (C, "SE compra com entrega imediata e integral (art. 95, II) ENTÃO TR-AI-5.1 a TR-AI-5.3.2", ["WZ-43", "WZ-14"], [], ""),
    97: (C, "SE contratação de pequeno valor de fornecimento contínuo (art. 95, I, c/c art. 106) ENTÃO TR-AI-5.4 a TR-AI-5.6",
         ["WZ-43", "WZ-14"], ["art. 95, inciso I, c/c o art. 106, da Lei n.º 14.133, de 2021"], ""),
    98: (C, "SE extinção antecipada por falta de crédito ou perda de vantagem ENTÃO sem ônus na data de aniversário, com aviso de dois "
            "meses; antes disso, só com ônus (art. 138, § 2º)", ["WZ-43", "WZ-14"], [], "Âncora de uma palavra ('vantagem')."),
    99: (C, "SE dispensa por emergência (art. 75, VIII) ENTÃO usar a redação de extinção própria (TR-AI-5.7)", ["WZ-14", "WZ-43"], [],
         "A nota manda usar 'a redação do item 12.4', numeração que não existe no Anexo I; o item correspondente é o 5.7 (P18). "
         "Âncora de uma palavra ('partes')."),
    100: (RN, "Remissão normativa: o CDC se aplica à Administração como consumidora (Acórdão TCU 2569/2018-Plenário); sem regra adicional",
          [], [], ""),
    101: (RN, "Remissão normativa: supressão consensual acima de 25% é possível (Parecer 00061/2024/DECOR/CGU/AGU); sem regra adicional",
          [], [], ""),
    102: (C, "SE o contrato for substituído por instrumento equivalente (art. 95, I e II) ENTÃO incluir o Anexo II para colher a "
             "concordância do contratado SENÃO suprimir", ["WZ-43"], [], "Âncora de uma palavra ('CONCORDÂNCIA')."),
}


def ancora_zero(doc_xml, cid):
    """Texto do mesmo paragrafo imediatamente antes de uma ancora de comprimento zero."""
    m = re.search(rf'<w:commentRangeStart w:id="{cid}"/>', doc_xml)
    ini = doc_xml.rfind("<w:p ", 0, m.start())
    ini2 = doc_xml.rfind("<w:p>", 0, m.start())
    ini = max(ini, ini2)
    antes = "".join(re.findall(r"<w:t(?: [^>]*)?>(.*?)</w:t>", doc_xml[ini:m.start()]))
    return antes[-60:]


def main():
    docx, modelo_json, blocos_json, saida = sys.argv[1:5]
    wz_csv = sys.argv[5] if len(sys.argv) > 5 else None
    z = zipfile.ZipFile(docx)
    doc_xml = z.read("word/document.xml").decode("utf-8")
    modelo = json.load(open(modelo_json, encoding="utf-8"))
    blocos = json.load(open(blocos_json, encoding="utf-8"))
    par_bloco = {n: b["id"] for b in blocos for n in b["paragrafos"]}
    wz_validos = None
    if wz_csv and Path(wz_csv).exists():
        wz_validos = {r["id"] for r in csv.DictReader(open(wz_csv, encoding="utf-8-sig"))}
    m10 = Path(saida) / "M10_validacoes.csv"
    val_validos = {r["id"] for r in csv.DictReader(open(m10, encoding="utf-8-sig"))} if m10.exists() else None
    linhas = []
    for c in modelo["comentarios"]:
        k = c["ordem"]
        natureza, regra, wz, extra, obs = N[k]
        vals = VAL_NOTAS.get(k, [])
        if val_validos is not None and [v for v in vals if v not in val_validos]:
            raise SystemExit(f"NE-{k:03d} cita VAL inexistente: {[v for v in vals if v not in val_validos]}")
        if wz_validos is not None:
            faltam = [w for w in wz if w not in wz_validos]
            if faltam:
                raise SystemExit(f"NE-{k:03d} cita WZ inexistente: {faltam}")
        trecho = re.sub(r"\s+", " ", c["trecho_ancorado"]).strip()
        if not trecho:
            trecho = f"(âncora sem trecho: posição logo após '...{ancora_zero(doc_xml, c['id_word'])}')"
        trecho = trecho[:200]
        ini, fim = c["par_inicio"], c["par_fim"]
        bloco = par_bloco[ini]
        blocos_cobertos = sorted({par_bloco[n] for n in range(ini, fim + 1) if n in par_bloco},
                                 key=lambda x: [b["id"] for b in blocos].index(x))
        cits = extrair(c["texto"])
        for e in extra:
            if e not in cits:
                cits.append(e)
        fonte = (f"{DOCX}, word/comments.xml, comentário w:id {c['id_word']}; âncora em word/document.xml, "
                 f"parágrafo{'s' if fim != ini else ''} {ini}{' a ' + str(fim) if fim != ini else ''} "
                 f"(blocos {', '.join(blocos_cobertos)}). trecho_ancorado, texto_integral e citacoes EXTRAIDOS; "
                 f"natureza, regra_derivada e afeta INFERIDOS da leitura da nota.")
        if extra:
            fonte += f" Citações acrescentadas na leitura (o extrator não as pegou): {'; '.join(extra)}."
        if obs:
            fonte += f" Observação: {obs}"
        linhas.append({
            "id": f"NE-{k:03d}", "bloco_ancora": bloco, "trecho_ancorado": trecho, "texto_integral": c["texto"],
            "natureza": natureza, "regra_derivada": regra, "afeta": ", ".join(list(wz) + vals),
            "citacoes": "; ".join(cits), "fonte": fonte, "status": "INFERIDO",
        })
    gravar_csv(Path(saida) / "M03_notas_explicativas.csv", COLS, linhas)
    from collections import Counter
    print(f"M03: {len(linhas)} notas | natureza {dict(Counter(l['natureza'] for l in linhas))} | "
          f"com WZ: {sum(1 for l in linhas if l['afeta'])}")


if __name__ == "__main__":
    main()
