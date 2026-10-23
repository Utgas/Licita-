#!/usr/bin/env python3
"""Fases 6 e 8 - M09: desvios encontrados nos documentos da base.

Uso: python3 -I f6_gerar_M09.py <pasta_Matrizes_v1> <f6_comparacao.json>

Especificação reconstruída (ver README). Um desvio é um ponto em que um documento da base se afasta do modelo AGU
DEZ/2025, de nota explicativa, de norma conferida ou de si mesmo. Origem das linhas:
  - Fase 6: comparação dos TRs 23/2026 e 58/2026 com o DEZ/2025 (f6_comparar_trs.py; regra do usuário em 21/10/2026);
    os TRs 117/2025, 140/2025 e 190/2025 não geram desvio (só evidência de prática no M08);
  - corpus de ETPs, DFDs e checklists (achados da seção 5 do prompt, reconstruídos, e achados de 22/10/2026);
  - Fase 8: matrizes 01 e 02 (rascunhos), detalhadas em auditoria_matrizes_01_02.md.
Todo desvio aponta o tratamento no sistema (regra do M10, pergunta do M04 ou cláusula do M08).
Na comparação automática, falso positivo conferido e descartado: TR-7.11 no TR 58/2026 (quebra de página com rodapé no
meio do parágrafo); TR-AI-* (blocos do Anexo I casados por semelhança com itens do corpo); TR-CAB.01, TR-CAB.02 e
TR-ASSIN.* (cabeçalho e assinaturas que o ETP Digital gera em formato próprio).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import gravar_csv  # noqa: E402

COLS = ["id", "documento", "local", "tipo", "descricao", "referencia", "tratamento_no_sistema", "achado", "fonte", "status"]

TR23 = "TR 23/2026 (TR exemplos/ae4297a4-a494-4822-980f-6cbcc6b4571c.pdf)"
TR58 = "TR 58/2026 (TR exemplos/f518d222-2d93-4dd0-8068-55769fe133c5.pdf)"
ETP117 = "ETP 117/2025 (ETP exemplos/Estudo Técnico Preliminar-2.pdf)"
ETP58 = "ETP 58/2025 (ETP exemplos/Outro-ETP160322_000058_2025 Controlado ASSINADO.pdf)"
ETP67 = "ETP 67/2026 (TR exemplos/4bcb2dfc-623c-44fa-a3c1-2ef2e28dbd08.pdf)"
ETP99 = "ETP 99/2025 (ETP exemplos/d4ef8f94-2e0a-4181-8d58-22ed3bdf305c.pdf)"
ETP19 = "ETP 19/2026 (ETP exemplos/39f4f8bb-fab9-4793-bbba-6d8cc9196eab.pdf)"
ETP109 = "ETP 109/2024 (ETP exemplos/882d42e8-38d4-410a-bf44-cdaa7da1673c.pdf)"
DFD18 = "DFD 18/2026 (DFD exemplos/3a85b163-9b6c-4517-874e-800f070e3d95.pdf)"
DFD710 = "DFD 710/2025 (DFD exemplos/1c73a5b3-9a6c-4f24-8e5c-aeaaa96e06ea.pdf)"
CKC = "Checklist de consumo (Checklists/Checklist_Tecnico_Medicamentos_e_Materiais_de_Consumo_em_Saude_REVISAO__1_.docx)"
M01 = "Matriz 01 (Matriz/01_Matriz_TR_AGU_Aquisicoes.md)"
M02R = "Matriz 02 (Matriz/02_Matriz_ETP_Digital_Lei14133.md)"

# Classificação dos parágrafos dos TRs 23/2026 e 58/2026 que não casam com bloco do modelo (razão < 0,60):
#   PREENCHIMENTO  trecho em vermelho do modelo preenchido (o valor preenchido baixa a semelhança)
#   SET-xx         cláusula setorial (M08)          DV-xx  desvio (M09)
#   ARTEFATO       quebra de página, rodapé ou alíneas na mesma linha (o texto do modelo está lá)
#   PROPRIO        texto próprio do órgão sem cláusula setorial nem desvio (registrado, sem tratamento)
CLASSIF = {
    "ae4297a4": {
        "1.1": "PREENCHIMENTO TR-1.1", "1.2": "PROPRIO (fonte de recursos)", "1.6": "PROPRIO (prevalência do descritivo "
        "complementar; ver VAL-002)", "3.1": "PREENCHIMENTO TR-3.1", "4.1.1": "PREENCHIMENTO TR-4.1.1 (critério de "
        "sustentabilidade de veículo)", "4.1.2": "SET-05; SET-07", "4.2.1": "PREENCHIMENTO TR-4.16 (justificativa)",
        "4.4.1": "PREENCHIMENTO TR-4.41 (justificativa sem cota, VAR-120)", "5.1": "PREENCHIMENTO TR-5.1",
        "5.2": "PREENCHIMENTO TR-5.1", "5.4": "PREENCHIMENTO TR-5.4; SET-09", "5.5": "PROPRIO (exigência própria de "
        "veículo: licenciamento)", "5.6": "SET-11; SET-19", "5.8": "PREENCHIMENTO TR-5.9; SET-13",
        "5.9": "PREENCHIMENTO TR-5.12", "5.9.1": "PREENCHIMENTO TR-5.14; SET-13", "5.11": "PROPRIO (exigência própria de "
        "veículo: documentação no órgão de trânsito)", "6.12": "ARTEFATO", "7.1": "ARTEFATO", "7.2": "ARTEFATO",
        "7.2.4.7.1": "PREENCHIMENTO TR-7.2.4.7.1; DV-05", "7.2.4.7.2": "PREENCHIMENTO TR-7.2.4.7.1",
        "7.2.4.7.3": "PREENCHIMENTO TR-7.2.4.7.1", "7.9.3": "ARTEFATO", "8.9": "ARTEFATO", "8.12.1": "ARTEFATO",
        "8.12.2": "ARTEFATO", "8.25": "ARTEFATO; DV-10", "8.36": "ARTEFATO", "9.1": "PREENCHIMENTO TR-9.1",
        "9.12.1": "SET-08", "9.12.2": "SET-06; DV-04", "9.30.1": "PREENCHIMENTO TR-9.34.1",
        "9.30.1.1": "PREENCHIMENTO TR-9.34.1.1; DV-09", "9.30.5": "DV-08; SET-13", "9.30.6": "DV-08; SET-14",
        "9.30.7": "DV-08; SET-15", "9.30.8": "DV-08; SET-12", "11.2": "PREENCHIMENTO TR-11.2", "12.1": "ARTEFATO"},
    "f518d222": {
        "1.1": "PREENCHIMENTO TR-1.1; SET-11; SET-12; SET-13", "1.5": "PROPRIO (prevalência do descritivo complementar; ver "
        "VAL-002)", "1.6": "DV-07", "2.2": "PREENCHIMENTO TR-2.3", "4.1.1": "SET-05", "4.1.2": "SET-07",
        "4.16": "ARTEFATO", "4.26.1": "PREENCHIMENTO TR-4.41 (justificativa sem cota, VAR-120)",
        "4.27": "PROPRIO (declara que não há margem de preferência; o modelo só traz o texto para quando há)",
        "5.1": "PREENCHIMENTO TR-5.1", "5.2": "SET-02", "5.2.1": "SET-02", "5.2.2": "SET-17",
        "5.4.1": "PREENCHIMENTO TR-5.4", "5.4.2": "PREENCHIMENTO TR-5.4", "6.12": "ARTEFATO", "7.1": "ARTEFATO",
        "7.2.4.6": "PREENCHIMENTO TR-7.2.4.6", "7.2.4.7.1": "PREENCHIMENTO TR-7.2.4.7.1",
        "7.2.4.7.2": "PREENCHIMENTO TR-7.2.4.7.1", "7.2.4.7.3": "PREENCHIMENTO TR-7.2.4.7.1", "8.9": "ARTEFATO",
        "8.12.1": "ARTEFATO", "8.12.2": "ARTEFATO", "8.20": "ARTEFATO", "8.30": "PREENCHIMENTO TR-8.40 (índice de reajuste)",
        "8.36": "ARTEFATO", "9.24": "ARTEFATO", "9.32": "DV-06", "9.33": "SET-06; DV-04", "9.33.1": "ARTEFATO",
        "9.34.1": "PREENCHIMENTO TR-9.34.1.1", "9.34.2.1": "DV-09", "9.34.6": "DV-08; SET-13", "9.34.7": "DV-08; SET-14",
        "9.34.8": "DV-08; SET-15", "9.34.9": "DV-08; SET-12", "11.2": "PREENCHIMENTO TR-11.2",
        "12.2": "PROPRIO (registra que as especificações vêm da OM demandante e a Base Administrativa consolida: a mesma "
        "divisão de trabalho entre checklist e wizard)"},
}


# id, documento, local, tipo, descricao, referencia, tratamento, achado, status, origem_da_linha
D = [
    ("DV-01", TR23, "p.1, item 1.5", "TEXTO_PRETO_ALTERADO",
     "Texto em preto do modelo alterado: 'vigência e execução do objeto' no lugar de 'vigência da contratação', sem "
     "justificativa no documento.", "TR-1.9; NE-001 item 2", "VAL-043", "", "EXTRAIDO", "comparação f6"),
    ("DV-02", TR58, "p.1, item 1.4", "TEXTO_PRETO_ALTERADO",
     "Texto em preto do modelo alterado: retirado 'ou outro instrumento hábil que o substitua' ('O contrato oferece maior "
     "detalhamento...').", "TR-1.9; NE-001 item 2", "VAL-043", "", "EXTRAIDO", "comparação f6"),
    ("DV-03", TR58, "p.16, item 9.36", "TEXTO_PRETO_ALTERADO",
     "Texto em preto adaptado ao caso (sem registro de preços): retirado 'ou da ata de registro de preços ou do aceite do "
     "instrumento equivalente'. A adaptação é coerente com o caso, mas o modelo pede justificativa nos autos.",
     "TR-9.37; NE-001 item 2", "VAL-043", "", "EXTRAIDO", "comparação f6"),
    ("DV-04", f"{TR23}; {TR58}", "TR 23/2026 p.9, item 9.12.2; TR 58/2026 p.15, item 9.33", "TERMINOLOGIA",
     "A Autorização Especial é chamada de 'Autorização de Funcionamento (AE)'. A NE-073 trata da 'Autorização Especial, "
     "emitida pela Agência Nacional de Vigilância Sanitária'; AFE é a Autorização de Funcionamento.",
     "NE-060; NE-073; TR-9.14; TR-9.35", "VAL-041; SET-06; SET-08", "", "EXTRAIDO", "comparação f6"),
    ("DV-05", TR23, "p.5, item 7.2.4.7.1", "CLAUSULA_SEM_PERTINENCIA",
     "Infração específica 'Não apresentar site planning e projeto de infraestrutura e adequação da sala de exames' num TR de "
     "ambulância; o mesmo texto está no TR 58/2026 (p.9), de equipamentos hospitalares.", "TR-7.2.4.7.1; WZ-33",
     "VAL-042", "", "EXTRAIDO", "comparação f6"),
    ("DV-06", TR58, "p.15, item 9.32", "CLAUSULA_SEM_PERTINENCIA",
     "Exige Declaração do Detentor de Registro 'quando for o caso de importação de medicamento' num TR de equipamentos "
     "médico-hospitalares.", "TR-9.35; WZ-38", "VAL-042", "", "EXTRAIDO", "comparação f6"),
    ("DV-07", TR58, "p.1, item 1.6", "TERMINOLOGIA",
     "Diz que o pregão se destina 'à contratação direta e exclusiva' do órgão. Contratação direta é a dispensa ou a "
     "inexigibilidade (WZ-01); o texto quis dizer que não haverá ata de registro de preços.", "WZ-01; WZ-10",
     "O sistema escreve a forma de seleção a partir da WZ-01 e da WZ-10, sem texto livre no objeto", "", "EXTRAIDO",
     "comparação f6"),
    ("DV-08", f"{TR23}; {TR58}", "TR 23/2026 p.11, itens 9.30.5 a 9.30.8; TR 58/2026 p.16, itens 9.34.6 a 9.34.9",
     "CONTRARIA_NOTA_AGU",
     "Declarações de garantia de 36 meses, de peças por dez anos, de assistência pelo fabricante e de treinamento exigidas "
     "como documento de habilitação técnica. São obrigações de execução; a NE-056 veda requisito de habilitação sem suporte "
     "nos arts. 66 a 69 da Lei 14.133/2021.", "NE-056; TR-9.H08; WZ-38",
     "SET-12; SET-13; SET-14; SET-15 (obrigações na seção 5); WZ-38 só para atestado", "", "INFERIDO", "comparação f6"),
    ("DV-09", f"{TR23}; {TR58}", "TR 23/2026 p.11, item 9.30.1.1; TR 58/2026 p.16, item 9.34.2.1", "A_CONFERIR",
     "O atestado deve comprovar 'garantia mínima de 12 (doze) meses prestada ao equipamento'. A NE-071 veda limitação de "
     "tempo ou de época nos atestados; não estava claro se a duração da garantia atestada entra nessa vedação. Resposta "
     "da P25 (23/10/2026): permitida, com justificativa no ETP, de 12 meses ou mais.",
     "NE-071; TR-9.34; WZ-60; SET-23", "WZ-60, SET-23, VAL-052 e VAL-053; a VAL-029 não barra a duração da garantia (P25)",
     "", "INFERIDO", "comparação f6"),
    ("DV-10", TR23, "p.7, item 8.25; p.9, item 9.18", "MARCA_DE_EDICAO",
     "Marcas de comentário do editor no texto final ('[A5]' e '[A8]').", "M02", "VAL-044", "", "EXTRAIDO", "comparação f6"),
    ("DV-11", f"{ETP67}; {TR23}", "ETP 67/2026 p.1, p.3 a p.6; TR 23/2026 p.1 e p.11", "DIVERGENCIA_ETP_TR",
     "Mesmo objeto (ambulância tipo D para o mesmo hospital). O ETP prevê registro de preços (p.3, p.4 e p.6) e o TR é "
     "pregão sem registro de preços com fornecimento integral (p.1); os valores estimados diferem (ETP p.4 e p.5; TR p.11); "
     "o ETP não tem número de processo (p.1).", "M06; WZ-10; VAR-014; VAR-001", "VAL-045; VAL-005", "seção 5, achado 5",
     "EXTRAIDO", "Fase 4 (M06)"),
    ("DV-12", ETP117, "p.15", "CONTRARIA_NOTA_AGU",
     "Atestado de capacidade técnica de no mínimo 50% 'pelo período mínimo de 12 meses'. A NE-071 veda limitação de tempo "
     "ou de época; o TR 117/2025 do mesmo processo usa o texto genérico (M06).", "NE-071; TR-9.34; M06",
     "VAL-029", "", "EXTRAIDO", "Fase 4 (M06)"),
    ("DV-13", ETP58, "p.1", "NORMA_REVOGADA",
     "Fundamenta 'bem comum' no art. 1º, parágrafo único, da Lei 10.520/2002, revogada pela Lei 14.133/2021.",
     "TR-1.2; VAR-018; M07 (Lei 10.520/2002)", "VAL-004", "seção 5, achado 6", "EXTRAIDO", "corpus"),
    ("DV-14", ETP67, "p.1", "NORMA_REVOGADA",
     "Fundamenta 'bem comum' no art. 1º, parágrafo único, da Lei 10.520/2002, revogada pela Lei 14.133/2021.",
     "TR-1.2; VAR-018; M07 (Lei 10.520/2002)", "VAL-004", "seção 5, achado 6", "EXTRAIDO", "corpus"),
    ("DV-15", DFD710, "p.1", "NORMA_REVOGADA",
     "Fundamenta 'bem comum' no art. 1º, parágrafo único, da Lei 10.520/2002, revogada pela Lei 14.133/2021.",
     "VAR-018; M07 (Lei 10.520/2002)", "VAL-004", "anexo 22/10, achado 3", "EXTRAIDO", "corpus"),
    ("DV-16", ETP109, "p.1", "NORMA_REVOGADA",
     "Fundamenta 'bem comum' no art. 1º, parágrafo único, da Lei 10.520/2002, revogada pela Lei 14.133/2021; o texto é igual "
     "ao do DFD 710/2025.", "VAR-018; M07 (Lei 10.520/2002)", "VAL-004", "anexo 22/10, achado 3", "EXTRAIDO", "corpus"),
    ("DV-17", ETP117, "p.2", "NORMA_A_CONFERIR",
     "Cita o Decreto 10.024/2019 (pregão no regime da Lei 10.520/2002). Situação do decreto não conferida em fonte oficial.",
     "M07 (Decreto 10.024/2019)", "VAL-004", "seção 5, achado 6", "A_VERIFICAR", "corpus"),
    ("DV-18", f"{ETP19}; {ETP117}; {ETP99}; {ETP67}", "ETP 19/2026 p.2; ETP 117/2025 p.16; ETP 99/2025 p.8; ETP 67/2026 "
     "p.2, p.3 e p.6", "NORMA_A_CONFERIR",
     "Citam a IN SLTI/MP 01/2010 para critérios de sustentabilidade. Situação não conferida em fonte oficial; o modelo AGU "
     "remete ao Guia Nacional de Contratações Sustentáveis (NE-011). O TR 190/2025 também cita, mas fica fora do M09 "
     "(regra de 21/10/2026).", "NE-011; WZ-17; M07 (IN SLTI/MP 01/2010)", "VAL-004", "seção 5, achado 6", "A_VERIFICAR",
     "corpus"),
    ("DV-19", ETP99, "p.2 e p.3", "INCONSISTENCIA_INTERNA",
     "Validade contraditória: 'deverá contemplar até no máximo 75% de vida útil' (p.2, item 4.3) e 'mínimo de 75% a contar "
     "da data de entrega' (p.2 e p.3).", "TR-5.4.1; VAR-117", "VAL-007; VAL-035", "seção 5, achado 8", "EXTRAIDO", "corpus"),
    ("DV-20", ETP99, "p.8, item 12.3", "INCONSISTENCIA_INTERNA",
     "ETP de participante de registro de preços que justifica 'dispensa de licitação eletrônica baseada no art. 75, inciso "
     "II', texto de outro tipo de processo.", "WZ-11; ETP-04.01", "VAL-034", "seção 5, achado 9", "EXTRAIDO", "corpus"),
    ("DV-21", ETP19, "p.4, seção 8", "INCONSISTENCIA_INTERNA",
     "Campo 'Valor (R$)' com um valor e texto da seção 8 com outro (conferido na imagem, P04).", "ETP-08.01; ETP-08.02; "
     "VAR-014", "VAL-038", "", "EXTRAIDO", "corpus"),
    ("DV-22", ETP19, "arquivo inteiro", "DOCUMENTO_INCOMPLETO",
     "O arquivo traz só as páginas 1, 3, 5, 7 e 9 de 9 (rodapé 'X de 9'); seções das páginas ausentes ficam não lidas.",
     "M00; M01", "VAL-031", "seção 5, achado 4", "EXTRAIDO", "corpus"),
    ("DV-23", "ETPs 151/2025, 801/2025 e 67/2026; ETP 330/2025", "p.1 (Informações Básicas)", "OMISSAO",
     "Número do processo em branco em três ETPs; no ETP 330/2025, sem máscara.", "ETP-01.01; VAR-001", "VAL-005",
     "seção 5, achado 5", "EXTRAIDO", "corpus (M00)"),
    ("DV-24", DFD18, "p.1", "FORA_DO_ESCOPO",
     "Objeto de TIC (computadores, SSD, câmera e microfone de videoconferência). O modelo AGU da base é de aquisições, "
     "exceto TIC (TR-CAB.01). Caso negativo de escopo.", "TR-CAB.01", "VAL-001", "anexo 22/10, achado 2", "EXTRAIDO",
     "corpus"),
    ("DV-25", DFD18, "p.1 (descrição sucinta e tabela de itens)", "INCONSISTENCIA_INTERNA",
     "A descrição sucinta diz '16GB RAM' e 'SSD 500GB'; a tabela diz 'MEMÓRIA RAM: 32' e 'ARMAZENAMENTO SSD: 110 A 300' no "
     "mesmo item.", "VAR-008; VAR-011", "VAL-002", "anexo 22/10, achado 2", "EXTRAIDO", "corpus"),
    ("DV-26", DFD18, "p.1 (2. Justificativa de Necessidade)", "OMISSAO",
     "A justificativa trata só das unidades SSD; os demais itens ficam sem justificativa.", "VAR-010; ETP-02.01", "VAL-003",
     "anexo 22/10, achado 2", "EXTRAIDO", "corpus"),
    ("DV-27", f"{DFD18}; {DFD710}", "tabela de itens", "OMISSAO",
     "A tabela do DFD do Compras.gov traz classe e PDM, sem código CATMAT; serve para importar itens, mas o CATMAT precisa "
     "ser completado.", "VAR-011; VAR-153; TR-1.1.TAB1", "VAL-039", "anexo 22/10, achado 4", "EXTRAIDO", "corpus"),
    ("DV-28", CKC, "pergunta 12.2", "INCONSISTENCIA_INTERNA",
     "Pergunta ambígua: 'O prazo solicitado é menor ou maior que 30 dias?' com respostas Sim e Não.", "M11 (CK-C-12.2)",
     "VAL-020; sugestoes_checklist.md", "anexo 22/10, achado 6", "EXTRAIDO", "checklist"),
    ("DV-29", CKC, "perguntas 13.5 e 20.1", "INCONSISTENCIA_INTERNA",
     "A 20.1 repete a 13.5 (espaço de armazenamento).", "M11 (CK-C-13.5; CK-C-20.1)", "VAL-022; sugestoes_checklist.md",
     "anexo 22/10, achado 6", "EXTRAIDO", "checklist"),
    ("DV-30", CKC, "perguntas 5.5, 5.6 e 6.1", "INCONSISTENCIA_INTERNA",
     "A 6.1 repete a 5.5 e a 5.6 (mais de um fabricante ou fornecedor). O checklist de permanentes tem a mesma repetição.",
     "M11 (CK-C-5.5; CK-C-5.6; CK-C-6.1; CK-P-5.5; CK-P-5.6; CK-P-6.1)", "VAL-023; sugestoes_checklist.md",
     "anexo 22/10, achado 6", "EXTRAIDO", "checklist"),
    ("DV-31", M01, "arquivo inteiro", "MATRIZ_RASCUNHO",
     "Não registra as notas explicativas do modelo (a palavra 'nota' não aparece), e o modelo DEZ/2025 tem 102.",
     "M03", "M03 com as 102 notas; NE-001 (notas nunca entram na minuta)", "seção 5, achado 1", "EXTRAIDO", "Fase 8"),
    ("DV-32", M01, "referências 'Linhas'", "MATRIZ_RASCUNHO",
     "Cita o arquivo 'media_1792606488039_644bd1c3.docx' e intervalos de linhas sem hash; 30 de 35 intervalos batem pelo "
     "título com o docx DEZ/2025, 5 pedem leitura.", "M02 (fonte por parágrafo); P11", "VAL-047",
     "seção 5, achado 2", "EXTRAIDO", "Fase 8"),
    ("DV-33", M01, "13 ocorrências", "MATRIZ_RASCUNHO",
     "Usa '~' (estimativa) em 13 pontos, onde o prompt exige contagem por script.", "README (contagens por script)",
     "VAL-046", "seção 5, achado 3", "EXTRAIDO", "Fase 8"),
    ("DV-34", M02R, "linhas 44 e 168", "NORMA_A_CONFERIR",
     "Cita o Decreto 10.024/2019 (linha 44) e a IN SLTI/MP 01/2010 (linha 168), do regime anterior; situação não conferida "
     "em fonte oficial.", "M01; M07", "VAL-004", "seção 5, achado 6", "A_VERIFICAR", "Fase 8"),
    ("DV-35", TR23, "p.2, item 4.4 e subtítulo anterior", "CLAUSULA_SEM_PERTINENCIA",
     "Mantém o subtítulo 'Reserva de cotas para microempresas e empresas de pequeno porte' e o item 4.4 do modelo, "
     "alterado para negar a cota: '4.4. Na presente licitação, não será realizada a reserva de cota de até 25% para "
     "microempresas e empresas de pequeno porte.', com justificativa no 4.4.1. No modelo, os blocos TR-4.H08 e TR-4.41 só "
     "entram quando há item ou grupo com cota. Classificado pelo dono do projeto em 23/10/2026 como erro do TR real (decisão 0008).",
     "TR-4.H08; TR-4.41; WZ-24; VAR-113", "Blocos ligados só pela WZ-24 = SIM (derivada da VAR-113); sem cota, não entram. "
     "No caso de reprodução R1, a diferença é do tipo 'TR real'.", "", "EXTRAIDO", "comparação f6; decisão 0008"),
    # Fase 14: respostas do dono do projeto sobre a reprodução do R1 e do R2 (decisão 0008, seção 'Reprodução')
    ("DV-36", TR23, "p.1, item 1.7", "CLAUSULA_SEM_PERTINENCIA",
     "Mantém a declaração do modelo '1.7. O objeto desta contratação não se enquadra como bem de luxo, conforme Decreto nº "
     "10.818, de 27 de setembro de 2021.' numa aquisição de bem permanente. O bloco TR-1.4 só entra para bens de consumo "
     "(NE-006). Classificado pelo dono do projeto em 23/10/2026: para permanentes, não entra (decisão 0008, reprodução).",
     "TR-1.4; WZ-07; NE-006", "TR-1.4 só com WZ-07 = CONSUMO ou AMBOS. No caso de reprodução R1, a diferença é do tipo "
     "'TR real'.", "", "EXTRAIDO", "comparação f6; decisão 0008"),
    ("DV-37", f"{TR23}; {TR58}", "TR 23/2026 p.12, item 11.3; TR 58/2026 p.17, item 11.3", "CLAUSULA_SEM_PERTINENCIA",
     "TR 23/2026 e TR 58/2026 mantêm o item do modelo '11.3. A dotação relativa aos exercícios financeiros subsequentes "
     "será indicada após aprovação da Lei Orçamentária respectiva e liberação dos créditos correspondentes, mediante "
     "apostilamento.' em fornecimento não contínuo. O bloco TR-11.3 só entra em fornecimento contínuo com vigência "
     "plurianual (NE-079). Classificado pelo dono do projeto em 23/10/2026 como erro do TR real (decisão 0008).",
     "TR-11.3; WZ-14; NE-079", "TR-11.3 só com WZ-14 = CONTINUO. Nos casos de reprodução R1 e R2, a diferença é do tipo "
     "'TR real'.", "", "EXTRAIDO", "comparação f6; decisão 0008"),
    ("DV-38", TR23, "p.11, item 9.31", "INCONSISTENCIA_INTERNA",
     "Mantém o subitem do modelo sobre sociedades empresárias estrangeiras ('9.31. Sociedades empresárias estrangeiras "
     "atenderão à exigência por meio da apresentação, no momento da assinatura do contrato ou...') sem o item que ele "
     "complementa (registro ou inscrição na entidade profissional competente, TR-9.33). Classificado pelo dono do projeto "
     "em 23/10/2026 como erro do TR real (decisão 0008).",
     "TR-9.33.1; TR-9.33; WZ-38", "Filho sem o pai não entra (regra do motor): TR-9.33.1 depende do TR-9.33 (WZ-38 com "
     "REGISTRO_ENTIDADE_PROFISSIONAL). No caso de reprodução R1, a diferença é do tipo 'TR real'.", "", "EXTRAIDO",
     "comparação f6; decisão 0008"),
    ("DV-39", TR58, "p.13, subtítulo 'Critérios de aceitabilidade de preços' e itens 9.4 e 9.4.1", "CLAUSULA_SEM_PERTINENCIA",
     "Mantém '9.4. Em se tratando de contratação para registro de preços, caso adotado o critério de julgamento de menor "
     "preço ou de maior desconto por grupo de itens, o critério de aceitabilidade de preços unitários máximos será:' e o "
     "9.4.1 num pregão sem registro de preços ('não se destina à formação de ata de registro de preços', item 1.6). "
     "Classificado pelo dono do projeto em 23/10/2026 como erro do TR real (decisão 0008).",
     "TR-9.H03; TR-9.4; TR-9.4.1; WZ-10; WZ-13; NE-055", "Blocos só com registro de preços, grupo de itens e menor preço "
     "ou maior desconto (WZ-13 derivada). No caso de reprodução R2, a diferença é do tipo 'TR real'.", "", "EXTRAIDO",
     "comparação f6; decisão 0008"),
    ("DV-40", TR23, "p.3, subtítulo 'Garantia, Manutenção e Assistência Técnica' e itens 5.7 a 5.10",
     "TEXTO_PRETO_ALTERADO",
     "Troca os itens de garantia contratual do modelo (TR-5.6 a TR-5.17) por redação própria de garantia técnica: '5.7. O "
     "prazo de garantia técnica é de, no mínimo, 12 (doze) meses, ou o prazo do fabricante, se superior, contado do "
     "recebimento definitivo.', '5.8. A garantia abrange a manutenção corretiva (peças e mão de obra) sem ônus para o "
     "Contratante...', '5.9. Uma vez notificada, a Contratada deverá realizar o reparo em até 30 (trinta) dias.' e 5.10. "
     "Classificado pelo dono do projeto em 23/10/2026 como diferença de redação do TR real; o sistema usa o texto do "
     "modelo (GA-07 B) e a SET-13 (decisão 0008).",
     "TR-5.6; TR-5.17; GA-07; WZ-29; SET-13", "Com WZ-29 = SIM a minuta traz o GA-07 B do modelo e a SET-13. No caso de "
     "reprodução R1, os blocos TR-5.7 a TR-5.17 da minuta são diferença do tipo 'TR real'.", "", "EXTRAIDO",
     "comparação f6; decisão 0008"),
    ("DV-41", TR58, "p.4, subtítulo 'Reserva de cotas para microempresas e empresas de pequeno porte:' e itens 4.26 e "
                    "4.26.1", "CLAUSULA_SEM_PERTINENCIA",
     "Mantém o subtítulo de reserva de cotas e o item do modelo alterado para negar a cota: '4.26. Na presente licitação, "
     "não será realizada a reserva de cota de até 25% (vinte e cinco por cento) do objeto para a...', com justificativa "
     "no 4.26.1. Mesmo caso da DV-35. Classificado pelo dono do projeto em 23/10/2026 como erro do TR real "
     "(decisão 0008).",
     "TR-4.H08; TR-4.41; WZ-24; VAR-113", "Blocos ligados só pela WZ-24 = SIM (derivada da VAR-113); sem cota, não "
     "entram. No caso de reprodução R2, a diferença é do tipo 'TR real'.", "", "EXTRAIDO", "comparação f6; decisão 0008"),
]


def main():
    pasta = Path(sys.argv[1])
    comp = json.load(open(sys.argv[2], encoding="utf-8"))
    linhas = []
    for (did, doc, local, tipo, desc, ref, trat, achado, st, origem) in D:
        fonte = f"{doc}, {local}. Origem da linha: {origem}."
        if origem.startswith("comparação f6"):
            fonte += (" Comparação automática bloco a bloco com o M02 (f6_comparar_trs.py, difflib sobre texto normalizado), "
                      "conferida na página citada.")
        fonte += " descricao EXTRAIDA do documento citado; tipo, referencia e tratamento INFERIDOS."
        linhas.append({"id": did, "documento": doc, "local": local, "tipo": tipo, "descricao": desc, "referencia": ref,
                       "tratamento_no_sistema": trat, "achado": achado, "fonte": fonte, "status": st})
    gravar_csv(pasta / "M09_desvios.csv", COLS, linhas, preservar=())
    # resumo da comparação (para o README e a auditoria)
    res = []
    for nome, v in comp.items():
        from collections import Counter
        c = Counter((x["formatacao"], x["classe"]) for x in v["comparacao"])
        res.append(f"{nome}: {dict(sorted(c.items()))}; parágrafos novos: {len(v['novos'])}")
    res.append("")
    res.append("Parágrafos novos (sem bloco correspondente no modelo) e classificação:")
    from collections import Counter
    cont = Counter()
    for nome, v in comp.items():
        chave = "ae4297a4" if "ae4297a4" in nome else "f518d222"
        doc = "TR 23/2026" if chave == "ae4297a4" else "TR 58/2026"
        for x in v["novos"]:
            c = CLASSIF[chave].get(x["tr_num"])
            if not c:
                raise SystemExit(f"parágrafo novo sem classificação: {doc} {x['tr_num']}")
            cont[c.split(" ")[0].split(";")[0]] += 1
            trecho = x["texto"][:110]
            if "TR-5.4" in c or "TR-11.2" in c:
                trecho = "(trecho omitido: endereço de entrega ou dados orçamentários)"
            res.append(f"{doc} p.{x['tr_pagina']} item {x['tr_num']} (razão {x['razao']}): {c} | {trecho}")
        sobra = set(CLASSIF[chave]) - {x["tr_num"] for x in v["novos"]}
        if sobra:
            raise SystemExit(f"classificação de parágrafo que não aparece como novo: {doc} {sorted(sobra)}")
    res.append(f"Totais por classe: {dict(cont)}")
    (pasta / "logs" / "f6_comparacao_trs.txt").write_text("\n".join(res) + "\n", encoding="utf-8")
    print(f"M09: {len(linhas)} desvios")
    print("\n".join(res))


if __name__ == "__main__":
    main()
