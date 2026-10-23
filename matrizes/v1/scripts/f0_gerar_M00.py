#!/usr/bin/env python3
"""Fase 0 - Gera M00_inventario.csv a partir da leitura dos documentos.

Uso: python3 -I f0_gerar_M00.py <pasta_Documentos> <_extracao.json> <pasta_saida>

Os campos descritivos (tipo, numero, UASG, objeto, SRP, par, problemas) foram levantados na leitura
dos textos extraidos e estao registrados abaixo, cada um com a pagina de origem em `fonte`.
Os campos tecnicos (formato e paginas lidas) sao calculados aqui a partir de _extracao.json.
Se algum nome de arquivo contiver nomes de pessoas, ele e registrado com [NOME] (NOME_REGISTRADO);
desde a Fase 1 nao ha nenhum caso, porque o unico arquivo nessa situacao foi renomeado (P01).

Status da linha: A_VERIFICAR se algum campo ficou sem evidencia; INFERIDO se algum campo foi
deduzido; EXTRAIDO se tudo foi lido diretamente. Os campos inferidos ou a verificar sao listados
no final da coluna `fonte`.
"""
import csv
import json
import sys
from pathlib import Path

COLS = ["arquivo", "pasta", "tipo_real", "numero_ano", "uasg", "om", "processo", "objeto_resumo",
        "categoria", "srp", "papel_srp", "formato", "paginas_lidas_total", "par", "problemas",
        "fonte", "status"]

# prefixo -> nome a registrar (so difere quando o nome real contem nomes de pessoas).
# Vazio desde a Fase 1: o arquivo do ETP 58/2025 foi renomeado (P01) e o nome atual nao tem nomes.
NOME_REGISTRADO = {}

DOCS = [
    # ---------------- ETPs na pasta ETP exemplos ----------------
    dict(prefixo="39f4f8bb", tipo_real="ETP", numero_ano="19/2026", uasg="160245",
         om="Policlínica Militar de Niterói (POMN)", processo="64657.001291/2026-69",
         objeto_resumo="Aquisição de 1 densitômetro ósseo DXA (fan beam) para o Setor de Radiologia, com instalação, treinamento e garantia; recurso Extra-PAASSEx 2026",
         categoria="PERMANENTE", srp="N", papel_srp="NA",
         par="NAO. Vínculo temático com o TR 58/2026 (PAASSEx 2026, entrega também na POMN), mas processos diferentes",
         problemas=("Escaneado (metadado do PDF: RICOH MP 501), sem camada de texto; lido por OCR em português; "
                    "só 5 das 9 páginas: presentes as páginas 1, 3, 5, 7 e 9 do original (rodapés '1 de 9', '3 de 9', '5 de 9', '7 de 9', '9 de 9'), faltam 2, 4, 6 e 8; "
                    "seções 6, 7, 12, 13 e 14 e o título da 15 não aparecem nas páginas presentes; "
                    "campo do sistema 'Valor (R$): 3.317,00' diverge do texto 8.1 'R$ 331.765,00' (conferido na imagem); "
                    "9.1 fala em 'licitação' e 15.12 em 'Dispensa Eletrônica'; "
                    "11.1 informa PCA 2025 num ETP de 2026; "
                    "requisito técnico exige integração com o PACS de outra OM ('HMilACG'); "
                    "cita Acórdão TCU 1375/2015-Plenário e IN SLTI/MP 01/2010 (conferir na Fase 5)"),
         fonte="p.1 (cabeçalho, seções 1-4), p.2-4 (seções 4, 5, 8-11), p.5 (15.1, 16); rodapés de todas as páginas; imagem da p.4 para o valor; srp=N porque as páginas presentes falam em licitação de unidade única e em dispensa, sem registro de preços",
         inferidos=["srp"], verificar=[]),
    dict(prefixo="Estudo Técnico Preliminar-2", tipo_real="ETP", numero_ano="117/2025", uasg="160242",
         om="Base Administrativa do Complexo de Saúde do RJ; demanda do HCE (Depósito de Material Cirúrgico)",
         processo="65475.000677/2025-73",
         objeto_resumo="OPME de Neurocirurgia III para o HCE, por registro de preços, com fornecimento em consignação",
         categoria="CONSUMO", srp="S", papel_srp="GERENCIADOR",
         par="SIM. TR 117/2025 (TR exemplos/Termo de Referência-3.pdf), mesmo processo 65475.000677/2025-73",
         problemas=("17 seções: seção extra '12. Justificativas pontuais' desloca as seguintes (Responsáveis vira 17); "
                    "subtítulos digitados dentro da seção 2 ('DO OBJETO DA CONTRATAÇÃO', 'O QUE SE ALMEJA ALCANÇAR'); "
                    "cita o Decreto 10.024/2019 na lista de referências das normas de OPME do EB (p.2); "
                    "trechos com palavras fora de ordem no próprio documento (p.8, conferido na imagem); "
                    "seção 4 fala em 'serviço' e em 'medicamentos' num objeto de OPME; "
                    "remete a anexos que não estão na base (normas listadas, Plano Diretor de Logística Sustentável do HCE)"),
         fonte="p.1 (cabeçalho, seções 1-3), p.2-3 (seção 4), p.8, p.15-17 (seções 11-17); papel no SRP conforme TR 117/2025 p.1, item 1.4",
         inferidos=["papel_srp"], verificar=[]),
    dict(prefixo="Outro-ETP160322_000058_2025", tipo_real="ETP", numero_ano="58/2025", uasg="160322",
         om="Hospital Central do Exército (HCE), Central de Abastecimento Farmacêutico",
         processo="64574.013082/2024-16",
         objeto_resumo="Medicamentos controlados para diversas clínicas do HCE, com fornecimento contínuo e reajuste",
         categoria="CONSUMO", srp="S", papel_srp="?",
         par="NAO. O TR 140/2025 trata de 'Controlados II' para o HCE, com outro processo",
         problemas=("Formato misto: páginas 4 a 8 são imagens (mapa comparativo de preços) lidas por OCR com confiança média de 77 a 83%; números dessas tabelas não são confiáveis; "
                    "fundamenta 'bem comum' no parágrafo único do art. 1º da Lei 10.520/2002 (p.1); "
                    "menciona prorrogação de Ata de Registro de Preços, mas não diz se a OM é gerenciadora ou participante; "
                    "arquivo renomeado na Fase 1 (P01): o nome original continha nomes de pessoas; renomear também na pasta original"),
         fonte="p.1 (cabeçalho, seções 1-3), p.3-9 (seção 5), p.9-10 (seção 6), p.15-18 (seções 8-16); UASG 160322 = HCE conforme cabeçalho do ETP 801/2025 p.1",
         inferidos=["categoria"], verificar=["papel_srp"]),
    dict(prefixo="d4ef8f94", tipo_real="ETP", numero_ano="99/2025", uasg="160332",
         om="Policlínica Militar da Praia Vermelha (PMPV)", processo="64659.007385/2025-41",
         objeto_resumo="Material de penso de Enfermagem I (consumo médico-hospitalar), como participante da IRP 134/2025 da UASG 160242",
         categoria="CONSUMO", srp="S", papel_srp="PARTICIPANTE",
         par="NAO. Participante da IRP 134/2025; o TR 190/2025 (penso cirúrgico de Enfermagem I, UASG 160242) é compatível, mas não cita o número da IRP",
         problemas=("Formato misto: a p.1 é imagem de página inteira (OCR, confiança média 95%); "
                    "participante de SRP que, ao contrário dos ETPs 151/2025 e 801/2025, escreve requisitos próprios; "
                    "validade contraditória: 4.3 'até no máximo 75% de vida útil' x 4.8.3 e 6.2.6 'mínimo de 75%'; "
                    "dois itens numerados 4.3; "
                    "requisitos de distribuidora de medicamentos (AFE, farmacêutico RT, SNCM) num objeto de material de penso; "
                    "12.3 descreve dispensa de licitação (art. 75, II), em conflito com a participação em SRP; "
                    "cita IN SLTI/MP 01/2010 e Portaria 01-SEF/2014 (conferir na Fase 5)"),
         fonte="p.1 (OCR: cabeçalho, seções 1-4), p.2-3 (seções 4-6), p.7-9 (seções 8-16)",
         inferidos=[], verificar=[]),
    dict(prefixo="ed187742", tipo_real="ETP", numero_ano="151/2025", uasg="160323",
         om="Hospital Geral do Rio de Janeiro (HGeRJ), Depósito de Material Cirúrgico",
         processo="(em branco no documento)",
         objeto_resumo="Materiais hospitalares, aquisição parcelada como UG participante da IRP 134/2025 da UASG 160242",
         categoria="CONSUMO", srp="S", papel_srp="PARTICIPANTE",
         par="NAO. Participante da IRP 134/2025; TR do gerenciador não identificado na base",
         problemas=("Número do processo em branco; "
                    "seções 4 e 5 remetem ao TR e à pesquisa de preços do gerenciador; "
                    "seções 13 e 14 marcadas como 'não se aplica'"),
         fonte="p.1 (cabeçalho, seções 1-6), p.2 (seção 7), p.8-9 (seções 8-16)",
         inferidos=["categoria"], verificar=[]),
    dict(prefixo="fdace9da", tipo_real="ETP", numero_ano="330/2025", uasg="160245",
         om="Policlínica Militar de Niterói (POMN), Pronto Atendimento",
         processo="65475003638202528 (sem máscara)",
         objeto_resumo="Equipo comum, equipo fotossensível e tramadol para o Pronto Atendimento",
         categoria="CONSUMO", srp="S", papel_srp="?",
         par="NAO",
         problemas=("Número do processo sem máscara (17 dígitos corridos); "
                    "tramadol aparece só no item 2.1: a seção 6 justifica apenas os equipos e a tabela se chama 'Material de Penso de Enfermagem I'; "
                    "2.3 fala em 'serviços laboratoriais', fora do objeto; "
                    "não declara o papel no SRP: só diz 'requisitos estabelecidos pelo órgão de origem da Ata de Registro de Preços'; "
                    "8 dos 9 códigos de 6 dígitos da tabela coincidem com os dos ETPs 99/2025 e 801/2025 (participantes da IRP 134/2025)"),
         fonte="p.1 (cabeçalho, seções 1-5), p.2 (seções 6-7), p.7-8 (seções 8-16); contagem de códigos por script (f0_inventario_apoio.py)",
         inferidos=["srp"], verificar=["papel_srp"]),
    # ---------------- ETPs arquivados na pasta TR exemplos ----------------
    dict(prefixo="08955b4e", tipo_real="ETP", numero_ano="801/2025", uasg="160322",
         om="Hospital Central do Exército (HCE), Depósito de Material Cirúrgico",
         processo="(em branco no documento)",
         objeto_resumo="Materiais de consumo para o Depósito de Material Cirúrgico, como participante da IRP 134/2025",
         categoria="CONSUMO", srp="S", papel_srp="PARTICIPANTE",
         par="NAO (com TR). Participante da IRP 134/2025; TR do gerenciador não identificado na base. Par DFD x ETP: DFD 710/2025 (mesmos 8 itens, com as mesmas quantidades na mesma ordem)",
         problemas=("Arquivado na pasta 'TR exemplos', mas é ETP (cabeçalho 'Estudo Técnico Preliminar 801/2025'); "
                    "número do processo em branco; "
                    "seções 4, 5, 6 e 9 remetem ao órgão gerenciador; "
                    "palavras fora de ordem no próprio documento (seções 2, 8, 13 e 14; conferido na imagem da p.9)"),
         fonte="p.1 (cabeçalho, seções 1-5), p.2 (seções 6-7), p.9-11 (seções 8-16)",
         inferidos=[], verificar=[]),
    dict(prefixo="4bcb2dfc", tipo_real="ETP", numero_ano="67/2026", uasg="160239",
         om="Hospital Militar de Resende (HMR), Seção de Manutenção e Transporte",
         processo="(em branco no documento)",
         objeto_resumo="1 ambulância tipo D (suporte avançado) para o HMR",
         categoria="PERMANENTE", srp="S", papel_srp="?",
         par="NAO CONFIRMADO. Mesmo objeto e OM do TR 23/2026, mas o ETP não tem número de processo e diverge do TR quanto ao SRP",
         problemas=("Arquivado na pasta 'TR exemplos', mas é ETP (cabeçalho 'Estudo Técnico Preliminar 67/2026'); "
                    "número do processo em branco; "
                    "fundamenta 'bem comum' no parágrafo único do art. 1º da Lei 10.520/2002 (2.2.2); "
                    "numeração quebrada: '21.', '3.3.' e '3.4.' dentro da seção 2 e '16.1' dentro da seção 13; "
                    "declara pregão com registro de preços (6.3 e 16.1), enquanto o TR 23/2026 declara pregão tradicional; "
                    "dois endereços de entrega (HGeRJ e HMR) para 1 unidade; "
                    "chama a ambulância de 'material de consumo de uso duradouro' (6.2); "
                    "cita IN SLTI/MP 01/2010 (conferir na Fase 5)"),
         fonte="p.1 (cabeçalho, seções 1-3), p.2-4 (seções 4-7), p.5-7 (seções 8-16)",
         inferidos=["categoria"], verificar=["papel_srp"]),
    # ---------------- TRs ----------------
    dict(prefixo="1e19dfeb", tipo_real="TR", numero_ano="190/2025", uasg="160242",
         om="Base Administrativa do Complexo de Saúde do RJ", processo="65475.002598/2025-05",
         objeto_resumo="Materiais de penso cirúrgico de Enfermagem I, por registro de preços com IRP",
         categoria="CONSUMO", srp="S", papel_srp="GERENCIADOR",
         par="NAO. Objeto compatível com o ETP 99/2025 (participante da IRP 134/2025), mas o TR não cita o número da IRP",
         problemas=("Rodapé do TR Digital indica modelo AGU 'Atualização: ABR/2025', não o DEZ/2025 da base; "
                    "título 'TERMO DE REFERÊNCIA - SRP (IRP)' sem número da IRP; "
                    "tabela de itens em anexo (Tabela Síntese) que não está na base"),
         fonte="p.1 (Informações Básicas, Outras informações, itens 1.1-1.4), rodapé de todas as páginas, p.15-20 (Anexos I e II)",
         inferidos=["papel_srp"], verificar=[]),
    dict(prefixo="Outros-TR160242_000140_2025", tipo_real="TR", numero_ano="140/2025", uasg="160242",
         om="Base Administrativa do Complexo de Saúde do RJ; demanda do HCE",
         processo="65475.001524/2025-43 (cabeçalho do sistema) x 65475.000645/2025-78 (corpo do documento)",
         objeto_resumo="Medicamentos controlados II para o HCE, por registro de preços com IRP",
         categoria="CONSUMO", srp="S", papel_srp="GERENCIADOR",
         par="NAO",
         problemas=("Número do processo diverge entre o cabeçalho do sistema e o corpo (p.1); "
                    "rodapé indica modelo AGU 'Atualização: NOV/2024'; "
                    "item 1.2 repetido; Anexo II numerado como 21 (salto depois do 13)"),
         fonte="p.1 (Informações Básicas, cabeçalho do corpo, itens 1.1-1.5), rodapé de todas as páginas, p.12-17 (Anexos)",
         inferidos=[], verificar=[]),
    dict(prefixo="Termo de Referência-3", tipo_real="TR", numero_ano="117/2025", uasg="160242",
         om="Base Administrativa do Complexo de Saúde do RJ; demanda do HCE", processo="65475.000677/2025-73",
         objeto_resumo="OPME de Neurocirurgia III em regime de consignação com comodato, por registro de preços com IRP",
         categoria="CONSUMO", srp="S", papel_srp="GERENCIADOR",
         par="SIM. ETP 117/2025 (ETP exemplos/Estudo Técnico Preliminar-2.pdf), mesmo processo",
         problemas=("Rodapé indica modelo AGU 'Atualização: NOV/2024'; "
                    "tabela de itens no Anexo III, que não está na base; "
                    "Anexo II numerado como 21 (salto depois do 13)"),
         fonte="p.1 (Informações Básicas, itens 1.1-1.5), rodapé de todas as páginas, p.20-25 (Anexos)",
         inferidos=[], verificar=[]),
    dict(prefixo="ae4297a4", tipo_real="TR", numero_ano="23/2026", uasg="160242",
         om="Base Administrativa do Complexo de Saúde do RJ; destino: Hospital Militar de Resende", processo="65475.002871/2025-93",
         objeto_resumo="1 ambulância de suporte avançado (tipo D) para o HMR, pregão tradicional, fornecimento integral, recurso de emenda parlamentar",
         categoria="PERMANENTE", srp="N", papel_srp="NA",
         par="NAO CONFIRMADO. Mesmo objeto do ETP 67/2026 (sem número de processo), que declara registro de preços",
         problemas=("Anexo I (tabela síntese) e Anexo II (descritivo complementar) listados na última página e não incluídos no arquivo; "
                    "rodapé numera 13 páginas, o arquivo tem 14 (a 14ª é a lista de anexos); "
                    "seções 13 (Anexo I) e 14 (Anexo II) marcadas 'não se aplica'"),
         fonte="p.1 (Informações Básicas, itens 1.1-1.7), p.12-14 (seções 13-15 e lista de anexos)",
         inferidos=[], verificar=[]),
    dict(prefixo="f518d222", tipo_real="TR", numero_ano="58/2026", uasg="160242",
         om="Base Administrativa do Complexo de Saúde do RJ; entrega no HCE e na POMN", processo="65475.002947/2025-81",
         objeto_resumo="Equipamentos hospitalares (material permanente) com recurso de emenda parlamentar, PAASSEx 2026, com instalação, treinamento e garantia",
         categoria="PERMANENTE", srp="N", papel_srp="NA",
         par="NAO",
         problemas=("Tabela de itens e descritivos complementares em anexo, que não estão na base; "
                    "seções 13 e 14 dizem 'Minuto já nos autos' e 'Termo já nos aut[os]'"),
         fonte="p.1 (Informações Básicas, itens 1.1-2.2), p.4-5 (item 5.4), p.17-18 (seções 13-15)",
         inferidos=[], verificar=[]),
    # ---------------- Modelo, escopo e rascunhos ----------------
    dict(prefixo="modelo-de-termo-de-referencia-compras-lei-no-14-133-dez-25", tipo_real="MODELO", numero_ano="DEZ/2025",
         uasg="NA", om="AGU, Câmara Nacional de Modelos de Licitações e Contratos (CNMLC/CGU)", processo="NA",
         objeto_resumo="Modelo AGU de TR para aquisições, exceto TIC, licitação e contratação direta (Lei 14.133/2021), com 102 notas explicativas em comentários do Word",
         categoria="OUTRO", srp="NA", papel_srp="NA", par="NA",
         problemas=("102 comentários (ids de 1 a 140, não contínuos), todos com commentRangeStart e commentRangeEnd; "
                    "3 âncoras de comprimento zero (ids 7, 29 e 49): a ligação ao bloco terá de ser pela posição; "
                    "605 parágrafos no corpo (556 não vazios, 117 dentro de tabelas); "
                    "a contagem de páginas depende do programa que abre o arquivo (29 no LibreOffice)"),
         fonte="word/document.xml, word/comments.xml, word/footer2.xml ('Atualização: DEZ/2025'); scripts f0_docx_modelo.py e f0_inventario_apoio.py",
         inferidos=[], verificar=[]),
    dict(prefixo="Escopo Inicial Gerador de ETP e TR", tipo_real="OUTRO", numero_ano="NA",
         uasg="NA", om="NA", processo="NA",
         objeto_resumo="Escopo inicial do gerador de ETP e TR, datado de 20/10/2026: visão, perfis, fluxo de 8 etapas, MVP, base normativa, regras anti-alucinação, segurança, auditoria, decisões e riscos",
         categoria="OUTRO", srp="NA", papel_srp="NA", par="NA",
         problemas=("Fluxo de 8 etapas está em imagem na p.2 (lido na imagem, não no texto); "
                    "deixa em aberto se o ETP Digital aceita o PDF como anexo ou exige preenchimento campo a campo"),
         fonte="p.1-7; imagem da p.2",
         inferidos=[], verificar=[]),
    dict(prefixo="01_Matriz_TR_AGU_Aquisicoes", tipo_real="OUTRO", numero_ano="NA", uasg="NA", om="NA", processo="NA",
         objeto_resumo="Rascunho da matriz 01 (TR AGU de aquisições): campos por seção com tipo TF/EU/IA/OP/TB",
         categoria="OUTRO", srp="NA", papel_srp="NA", par="NA",
         problemas=("Cita como fonte o arquivo media_1792606488039_644bd1c3.docx, ausente da base; "
                    "as referências de 'Linhas' coincidem com a numeração de parágrafos do docx DEZ/2025 nos 35 intervalos citados (30 conferidos por script, 5 na leitura), o que indica mesmo conteúdo, sem prova por hash; "
                    "não registra nenhuma das 102 notas explicativas (0 ocorrências de 'nota'); "
                    "resumo estatístico com '~' (linhas 315-319)"),
         fonte="linhas 10, 28-299 e 311-328; conferência por script contra word/document.xml do modelo DEZ/2025",
         inferidos=[], verificar=[]),
    dict(prefixo="02_Matriz_ETP_Digital_Lei14133", tipo_real="OUTRO", numero_ano="NA", uasg="NA", om="NA", processo="NA",
         objeto_resumo="Rascunho da matriz 02 (ETP Digital): campos por seção, tipo, regra anti-alucinação e destino no TR",
         categoria="OUTRO", srp="NA", papel_srp="NA", par="NA",
         problemas=("Cita o Decreto 10.024/2019 para classificar bem comum (linha 44); "
                    "trata subtítulos digitados no ETP 117/2025 como campos do sistema (linhas 42-43); "
                    "trata validade mínima de 50% como regra padrão (linha 62); "
                    "cita IN SLTI/MP 01/2010 (linha 168, conferir na Fase 5); "
                    "afirma 'mais de 80%' do TR preenchido por derivação sem cálculo (linha 231)"),
         fonte="linhas 8, 42-44, 62, 168, 231",
         inferidos=[], verificar=[]),
]


# ---------------- arquivos que entraram em 22/10/2026 ----------------
DOCS += [
    dict(prefixo="Checklist_Tecnico_Medicamentos", tipo_real="CHECKLIST", numero_ano="NA (versão em revisão)", uasg="NA",
         om="NA (formulário da área técnica requisitante da OMS)", processo="NA",
         objeto_resumo=("Checklist técnico de medicamentos e materiais de consumo em saúde, preenchido pela área requisitante: "
                        "23 seções, 124 perguntas numeradas, cabeçalho, lista de anexos e declaração do responsável técnico"),
         categoria="CONSUMO", srp="NA", papel_srp="NA",
         par="NAO. Formulário em branco, entrada técnica de qualquer processo de consumo",
         problemas=("Em revisão. 12.2 ambígua ('menor ou maior que 30 dias?' com Sim e Não); 20.1 repete 13.5 e 7.5 trata do mesmo "
                    "tema; 6.1 repete 5.5 e 5.6; perguntas que dependem da anterior sem dizer (ex.: 8.3 e 8.4 dependem de 8.2); não "
                    "diz se a marcação é única ou múltipla; não pede endereço de entrega; respostas por item (9.2, 13.1, 14.2) sem "
                    "tabela por item; caixas de marcação são o caractere digitado, sem controle de formulário (sugestoes_checklist.md)"),
         fonte=("word/document.xml: 520 parágrafos (426 não vazios), 98 tabelas; numeração digitada no texto; observação final "
                "sobre a divisão entre informação técnica e enquadramento jurídico; SHA-256 no README"),
         inferidos=[], verificar=[]),
    dict(prefixo="Checklist_Tecnico_Aquisicao_de_Materiais_Permanentes", tipo_real="CHECKLIST", numero_ano="NA (atualizado)",
         uasg="NA", om="NA (formulário da área técnica requisitante da OMS)", processo="NA",
         objeto_resumo=("Checklist técnico de materiais permanentes e equipamentos em saúde, preenchido pela área requisitante: "
                        "23 seções, 138 perguntas numeradas, cabeçalho, lista de anexos e declaração do responsável técnico"),
         categoria="PERMANENTE", srp="NA", papel_srp="NA",
         par="NAO. Formulário em branco, entrada técnica de qualquer processo de material permanente",
         problemas=("6.1 repete 5.5 e 5.6; perguntas que dependem da anterior sem dizer (ex.: 7.3 e 7.4 dependem de 7.2; 15.4 de "
                    "15.3); 13.1 pede prazo de garantia por item sem tabela por item; não pede endereço de entrega; 15.3 e 15.5 "
                    "(software e integração à rede) sinalizam objeto de TIC, fora do modelo AGU da base"),
         fonte=("word/document.xml: 791 parágrafos (529 não vazios), 127 tabelas; numeração digitada no texto; observação final "
                "lista as decisões jurídicas que não cabem à área técnica; SHA-256 no README"),
         inferidos=[], verificar=[]),
    dict(prefixo="3a85b163", tipo_real="DFD", numero_ano="18/2026", uasg="160242",
         om="Base Administrativa do Complexo de Saúde do RJ (Divisão Administrativa Interna)", processo="não consta no DFD",
         objeto_resumo=("Televisor 75 polegadas, tela de projeção, câmera e microfone de videoconferência, microcomputadores e SSD "
                        "(7 itens), gerado no Compras.gov"),
         categoria="PERMANENTE", srp="?", papel_srp="?",
         par="NAO. Caso negativo de escopo: objeto de TIC, fora do modelo AGU da base, que é 'exceto TIC' (achado 2)",
         problemas=("Itens de TIC (achado 2); descrição sucinta x tabela: '16GB RAM' x 'MEMÓRIA RAM: 32' e 'SSD 500GB' x "
                    "'ARMAZENAMENTO SSD: 110 A 300' no item 5; a justificativa trata só dos SSD; o acompanhamento registra operação "
                    "fora do prazo; tabela de itens sem código CATMAT (traz classe e PDM)"),
         fonte="p.1 (informações gerais, descrição sucinta, justificativa, itens 1 a 7), p.2 (fim do item 7, responsáveis, acompanhamento)",
         inferidos=["categoria"], verificar=[]),
    dict(prefixo="1c73a5b3", tipo_real="DFD", numero_ano="710/2025", uasg="160322",
         om="Hospital Central do Exército (HCE), Depósito de Material Cirúrgico", processo="não consta no DFD",
         objeto_resumo="Equipos para bomba de infusão, nutrição enteral e transfusão (8 itens), gerado no Compras.gov",
         categoria="CONSUMO", srp="S", papel_srp="PARTICIPANTE",
         par=("SIM, por itens: ETP 801/2025 (HCE, Depósito de Material Cirúrgico), com os mesmos 8 itens nas mesmas quantidades e "
              "na mesma ordem (15.000, 4.000, 12.000, 4.000, 9.000, 1, 6.000 e 3.500); nenhum dos dois traz número de processo"),
         problemas=("Fundamenta 'bem comum' no art. 1º, parágrafo único, da Lei 10.520/2002 (achado 3); tabela de itens sem "
                    "código CATMAT (classe e PDM); item 6 com quantidade 1; 'Relacionamentos: nenhum' embora o ETP 801/2025 trate "
                    "da mesma demanda"),
         fonte=("p.1 (informações gerais, justificativa com a Lei 10.520/2002, itens 1 a 3), p.2 (itens 3 a 8), p.3 (responsáveis, "
                "acompanhamento); quantidades comparadas por script com as linhas de itens do ETP 801/2025"),
         inferidos=["srp", "papel_srp"], verificar=[]),
    dict(prefixo="eb69c93a", tipo_real="DFD", numero_ano="sem número", uasg="160332",
         om="Policlínica Militar da Praia Vermelha (PMPV), Divisão de Medicina", processo="64659.003905/2024-65",
         objeto_resumo=("Materiais de consumo farmacológico e hospitalar para 12 meses da PMPV; itens em planilha anexa; "
                        "estimativa preliminar de R$ 65.516,46; modelo de DFD próprio da OM, em Word"),
         categoria="CONSUMO", srp="?", papel_srp="?",
         par="NAO. Mesma OM do ETP 99/2025, mas processo e objeto diferentes",
         problemas=("Formato próprio da OM, não gerado no Compras.gov; a planilha de itens anexa não está na base; o arquivo traz "
                    "nomes e números de CPF da equipe de planejamento (dado pessoal: não reproduzido nas matrizes; anonimizar o "
                    "arquivo antes de circular)"),
         fonte="p.1 (itens 1 a 8 do modelo de DFD), p.2 (itens 9 a 11, aprovação); UASG conforme o ETP 99/2025, da mesma OM",
         inferidos=["uasg"], verificar=[]),
    dict(prefixo="882d42e8", tipo_real="ETP", numero_ano="109/2024", uasg="160322",
         om="Hospital Central do Exército (HCE), Central de Abastecimento Farmacêutico", processo="64574.013078/2024-58",
         objeto_resumo="Medicamentos de alto custo para diversas clínicas do HCE, por registro de preços",
         categoria="CONSUMO", srp="S", papel_srp="?",
         par=("NAO. Processo vizinho ao do ETP 58/2025 (64574.013082/2024-16, mesma Central de Abastecimento Farmacêutico), "
              "mas objeto diferente; nenhum TR da base com o mesmo processo ou os mesmos códigos"),
         problemas=("Fundamenta 'bem comum' no art. 1º, parágrafo único, da Lei 10.520/2002 (achado 3, p.1); validade mínima de "
                    "50% do prazo de fábrica (p.2); a p.4 é imagem (tabela de preços) lida por OCR de baixa qualidade: códigos e "
                    "valores dessa página não são confiáveis (o OCR leu 338414 onde a seção 7 traz 338411); a seção 11 só afirma "
                    "alinhamento ao Plano Anual de Contratação do HCE, sem os dados do PCA; menciona prorrogação de Ata sem dizer "
                    "se a OM é gerenciadora"),
         fonte="p.1 (seções 1 e 2), p.2 (validade), p.4 (OCR), p.6 (Ata de Registro de Preços), p.10 (seção 11), p.12 (responsáveis)",
         inferidos=[], verificar=["papel_srp"]),
]


def acha_arquivo(base, prefixo):
    achados = [p for p in base.rglob("*") if p.is_file() and p.name.startswith(prefixo)]
    if len(achados) != 1:
        raise SystemExit(f"prefixo {prefixo!r} casou com {len(achados)} arquivos")
    return achados[0]


def formato_e_paginas(rel, ext, extracao):
    info = extracao[rel]
    if info["tipo_arquivo"] == "pdf":
        pags = info["paginas"]
        n = info["paginas_pdf"]
        sem_texto = sum(1 for p in pags if p.get("motivo_ocr") == "sem_camada_texto")
        mistas = [p["pagina"] for p in pags if p["ocr"]]
        if sem_texto == n:
            fmt = "ESCANEADO"
        elif mistas:
            fmt = "MISTO"
        else:
            fmt = "TEXTO"
        lidas = sum(1 for p in pags if p["chars_texto"] >= 20 or p.get("chars_ocr", 0) > 0)
        return fmt, f"{lidas}/{n}", mistas
    if info["tipo_arquivo"] == "docx":
        return "TEXTO", f"{info['paragrafos_nao_vazios']}/{info['paragrafos_nao_vazios']} parágrafos não vazios", []
    if info["tipo_arquivo"] == "md":
        return "TEXTO", f"{info['linhas']}/{info['linhas']} linhas", []
    return "?", "?", []


def main():
    base = Path(sys.argv[1])
    extracao = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    saida = Path(sys.argv[3])
    saida.mkdir(parents=True, exist_ok=True)
    linhas = []
    for d in DOCS:
        real = acha_arquivo(base, d["prefixo"])
        rel = str(real.relative_to(base))
        fmt, pags, paginas_ocr = formato_e_paginas(rel, real.suffix, extracao)
        nome = NOME_REGISTRADO.get(d["prefixo"], real.name)
        # o Escopo tem diagrama com conteudo em imagem na p.2: formato MISTO, lido visualmente
        if d["prefixo"].startswith("Escopo"):
            fmt = "MISTO"
        if d["numero_ano"] == "19/2026":
            pags += " (o original tem 9 páginas)"
        if paginas_ocr and fmt == "MISTO":
            if len(paginas_ocr) == 1:
                pags += f" (OCR na página {paginas_ocr[0]})"
            else:
                pags += f" (OCR nas páginas {', '.join(map(str, paginas_ocr))})"
        fonte = f"{rel.split('/')[0]}/{nome}: {d['fonte']}" if "/" in rel else f"{nome}: {d['fonte']}"
        status = "EXTRAIDO"
        if d["inferidos"]:
            status = "INFERIDO"
            fonte += f". Campos INFERIDOS: {', '.join(d['inferidos'])}"
        if d["verificar"]:
            status = "A_VERIFICAR"
            fonte += f". Campos sem evidência no documento: {', '.join(d['verificar'])}"
        linha = {
            "arquivo": nome,
            "pasta": str(real.parent.relative_to(base)) if real.parent != base else "Documentos",
            "tipo_real": d["tipo_real"], "numero_ano": d["numero_ano"], "uasg": d["uasg"], "om": d["om"],
            "processo": d["processo"], "objeto_resumo": d["objeto_resumo"], "categoria": d["categoria"],
            "srp": d["srp"], "papel_srp": d["papel_srp"], "formato": fmt, "paginas_lidas_total": pags,
            "par": d["par"], "problemas": d["problemas"], "fonte": fonte, "status": status,
        }
        if linha["pasta"] == ".":
            linha["pasta"] = "Documentos"
        else:
            linha["pasta"] = "Documentos/" + linha["pasta"]
        linhas.append(linha)
    # todo arquivo da base precisa estar no inventario
    todos = sorted(str(p.relative_to(base)) for p in base.rglob("*") if p.is_file())
    if len(todos) != len(linhas):
        raise SystemExit(f"inventario tem {len(linhas)} linhas, base tem {len(todos)} arquivos")
    out = saida / "M00_inventario.csv"
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS, quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(linhas)
    print(f"{out}: {len(linhas)} linhas")


if __name__ == "__main__":
    main()
