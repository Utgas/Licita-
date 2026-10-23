#!/usr/bin/env python3
"""M11: uma linha por pergunta dos dois checklists técnicos, com destino de cada resposta no sistema.

Uso: python3 -I ck_gerar_M11.py <ck_C.json> <ck_P.json> <pasta_Matrizes_v1> <saida_cobertura.txt>

Entrada: a leitura estrutural dos docx (ck_ler.py). Saída: M11_checklist.csv e o relatório de cobertura nos dois sentidos
(campos do M01 sem pergunta de origem; perguntas sem destino). O checklist está em revisão: qualquer mudança nele exige
refazer o M11 (o hash dos docx fica no README).

Campos EXTRAIDOS do docx: secao, numero, pergunta, opcoes, orientacao. Campos INFERIDOS: tipo_resposta (quando o docx
não diz se a escolha é única ou múltipla), condicional implícita, por_item, destinos, efeito e regra.
O cabeçalho do checklist de consumo tem 7 linhas de orientação (ORIENTAÇÕES PARA PREENCHIMENTO e seis tópicos): não são
perguntas e não entram no M11; duas delas fundamentam o M10 (VAL-048 e VAL-049).
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import gravar_csv, ler_csv  # noqa: E402

COLS = ["id", "checklist", "secao", "numero", "pergunta", "tipo_resposta", "opcoes", "orientacao", "condicional", "por_item",
        "destinos", "efeito", "regra", "fonte", "status"]
ARQ = {"C": ("Checklists/Checklist_Tecnico_Medicamentos_e_Materiais_de_Consumo_em_Saude_REVISAO__1_.docx", "CONSUMO",
             "6294e718c983"),
       "P": ("Checklists/Checklist_Tecnico_Aquisicao_de_Materiais_Permanentes_em_Saude_ATUALIZADO_SEM_19_3__2_.docx",
             "PERMANENTES", "7c6d3cc9bf16")}
EFEITOS = {"PREENCHE", "SUGERE", "JUSTIFICA", "ALERTA", "SO_CONTROLE"}
TIPOS = {"SIM_NAO", "UNICA", "MULTIPLA", "TEXTO", "NUMERO", "TABELA"}

# chave | tipo ('-' = inferido das opções) | por_item | destinos | efeito | regra (para SO_CONTROLE, o motivo)
MAPA = """
C|CAB.01|TEXTO|N|VAR-001; VAL-006|PREENCHE|Preenche VAR-001 quando vazia; se já houver número de processo, a diferença dispara VAL-006.
C|CAB.02|TEXTO|N|VAR-006; ETP-03.01|PREENCHE|OMS requisitante vai para a área requisitante do ETP. Não é a OM da UASG que compila o TR.
C|CAB.03|TEXTO|N|VAR-006; ETP-03.01|PREENCHE|Setor requisitante completa a área requisitante.
C|CAB.04|TEXTO|N|VAR-007; ETP-03.02|PREENCHE|Responsável técnico vai para ETP-03.02 e para as assinaturas (VAR-098); em matriz e exemplo, usar [RESPONSÁVEL].
C|CAB.05|TEXTO|N||SO_CONTROLE|Data do preenchimento: controla a versão das respostas e não entra na minuta.
C|1.1|TEXTO|N|VAR-006; ETP-03.01|PREENCHE|Mesma informação do cabeçalho (OMS requisitante); prevalece a resposta da 1.1.
C|1.2|TEXTO|N|VAR-006; ETP-03.01; VAR-064|PREENCHE|Setor usuário completa a área requisitante e sugere o setor de recebimento.
C|1.3|TEXTO|N|VAR-008; ETP-02.01; TR-1.1|SUGERE|Ponto de partida do objeto; a descrição final segue a tabela de itens.
C|1.4|TABELA|N|VAR-007; VAR-098; ETP-03.02; ETP-16.02|PREENCHE|Nome e posto vão para ETP-03.02 e assinaturas; telefone e e-mail ficam só no processo.
C|1.5|MULTIPLA|N|WZ-07; VAR-155; VAL-040|PREENCHE|Checklist de consumo preenchido: WZ-07 = CONSUMO e itens com categoria CONSUMO; com o de permanentes também, AMBOS.
C|2.1|TEXTO|N|VAR-010; ETP-02.01|PREENCHE|Texto da necessidade (ETP-02.01), com trecho de origem.
C|2.2|TEXTO|N|VAR-010; ETP-02.01|PREENCHE|Público e setores atendidos entram na necessidade.
C|2.3|MULTIPLA|N|WZ-14; VAR-010; ETP-02.01|SUGERE|'Recorrente' com necessidade permanente sugere WZ-14 = CONTINUO (decisão da equipe); demais opções entram na necessidade.
C|2.4|MULTIPLA|N|VAR-010; ETP-02.01|JUSTIFICA|Prejuízos marcados e a explicação concreta justificam a necessidade e o prazo.
C|2.5|SIM_NAO|N|VAR-010; ETP-02.01|JUSTIFICA|Sim: o número informado de pacientes entra na necessidade.
C|2.6|TEXTO|N|VAR-104; ETP-12.01|PREENCHE|Resultados pretendidos (ETP-12.01).
C|3.1|SIM_NAO|N|VAR-011; VAR-109; ETP-07.02; VAL-048|PREENCHE|A tabela anexa é a fonte da VAR-011 e da especificação; Não bloqueia a geração (VAL-048).
C|3.2|SIM_NAO|S|VAR-109; ETP-04.01|JUSTIFICA|Não: as características só desejáveis indicadas saem da especificação antes do TR.
C|3.3|SIM_NAO|S|VAR-121; ETP-04.01; VAL-018|PREENCHE|Sim: itens e equipamento existente vão para o atributo compatibilidade; compatibilidade que restringe marca segue NE-012.
C|3.4|SIM_NAO|S|VAR-115; VAR-046; WZ-18|SUGERE|Não: itens indicados são candidatos a marca indicada e o prejuízo vira justificativa (VAR-046); a indicação é confirmada pela equipe (NE-012).
C|4.1|MULTIPLA|N|VAR-012; ETP-07.01|PREENCHE|Método de cálculo da memória (ETP-07.01).
C|4.2|TEXTO|N|VAR-012; ETP-07.01|PREENCHE|Período de consumo analisado.
C|4.3|TEXTO|S|VAR-012; ETP-07.01|PREENCHE|Consumo médio por item, no texto ou em anexo.
C|4.4|UNICA|N|WZ-14; WZ-15; VAR-012|SUGERE|'Uso contínuo' sugere WZ-14 = CONTINUO; o período sugere o prazo de vigência (WZ-15), decidido pela equipe.
C|4.5|UNICA|N|VAR-012; ETP-07.01|JUSTIFICA|Desconto do estoque entra na memória de cálculo.
C|4.6|SIM_NAO|N|VAR-012; ETP-07.01|JUSTIFICA|Sim exige percentual e justificativa nos campos; o sistema não sugere percentual.
C|4.7|SIM_NAO|S|VAR-012; ETP-07.01; VAL-025|JUSTIFICA|Sim: a explicação por item entra na memória; item com quantidade 1 sem explicação dispara VAL-025.
C|4.8|SIM_NAO|N|VAR-012; VAL-048|ALERTA|Não: a memória de cálculo é exigida pelo próprio checklist (orientações) e dispara VAL-048.
C|5.1|UNICA|N|VAR-100; ETP-05.01|PREENCHE|Outras soluções técnicas entram no levantamento de mercado.
C|5.2|TEXTO|N|VAR-100; ETP-05.01|PREENCHE|Solução atual.
C|5.3|SIM_NAO|N|VAR-100; ETP-05.01|PREENCHE|Soluções diferentes identificadas.
C|5.4|SIM_NAO|N|VAR-100; ETP-05.01|JUSTIFICA|Solução descartada e motivo técnico.
C|5.5|SIM_NAO|N|VAR-100; ETP-05.01; VAL-023|PREENCHE|Fabricantes conhecidos entram no levantamento; resposta comparada com a 6.1 (VAL-023).
C|5.6|SIM_NAO|N|VAR-100; ETP-05.01; VAL-023|PREENCHE|Distribuidores; resposta comparada com a 6.1 (VAL-023).
C|5.7|MULTIPLA|S|VAR-109; ETP-04.01; VAR-115; VAR-046|PREENCHE|Aceitação de genéricos, similares e biossimilares entra nos requisitos; 'Apenas produto de referência' funciona como marca indicada e exige justificativa clínica (NE-012).
C|5.8|TEXTO|N|VAR-101; ETP-06.01|PREENCHE|Solução escolhida (descrição da solução).
C|5.9|TEXTO|N|VAR-100; ETP-05.01|JUSTIFICA|Justificativa da escolha.
C|6.1|SIM_NAO|N|VAL-023; VAL-019|ALERTA|Repete a 5.5 e a 5.6; divergência dispara VAL-023.
C|6.2|SIM_NAO|N|WZ-01; WZ-04; VAL-019|SUGERE|Sim indica possível inexigibilidade (WZ-04) ou marca indicada; decisão da equipe administrativa.
C|6.3|TEXTO|S|VAR-115; WZ-18|PREENCHE|Itens exclusivos recebem marca_indicada.
C|6.4|TEXTO|N|VAR-046; VAR-024|JUSTIFICA|Equivalentes avaliados e motivo de não atenderem: justificativa da marca ou da inexigibilidade.
C|6.5|SIM_NAO|N|WZ-04; WZ-21; VAL-019|ALERTA|Sim: há outros revendedores do mesmo fabricante, o que enfraquece a exclusividade de fornecedor.
C|6.6|SIM_NAO|N|VAR-024|JUSTIFICA|Documento de exclusividade anexado e identificado.
C|6.7|UNICA|N|VAR-024|JUSTIFICA|Território da exclusividade.
C|7.1|SIM_NAO|N|WZ-26; WZ-43; VAL-021|SUGERE|Sim sugere WZ-26 = REMESSA_UNICA; Não sugere PARCELADA; comparada com a 12.3 (VAL-021).
C|7.2|MULTIPLA|N|WZ-10; VAL-024|SUGERE|Causa de variação marcada sugere registro de preços (WZ-10); a escolha é da equipe.
C|7.3|SIM_NAO|N|WZ-10; WZ-26; VAL-024|SUGERE|Sim sugere registro de preços e entrega parcelada.
C|7.4|SIM_NAO|N|WZ-26; VAR-062|JUSTIFICA|Sim justifica entrega parcelada.
C|7.5|SIM_NAO|N|WZ-26; WZ-47|JUSTIFICA|Sim justifica entrega parcelada e pode exigir providência prévia.
C|7.6|UNICA|N|WZ-10; WZ-11; WZ-12; VAL-024|SUGERE|Sim sugere registro de preços com a OM como gerenciadora e participantes (IRP).
C|8.1|SIM_NAO|N|WZ-50; VAR-102; ETP-09.01|SUGERE|Não sugere agrupamento; a unidade de disputa é definida pelo atributo grupo.
C|8.2|SIM_NAO|S|VAR-112; WZ-13; WZ-50; VAL-014; VAL-015|PREENCHE|Sim: os itens indicados recebem o mesmo rótulo de grupo; grupo de um item é recusado (VAL-014).
C|8.3|MULTIPLA|N|VAR-102; ETP-09.01; VAL-015|JUSTIFICA|Motivos do agrupamento entram na justificativa do parcelamento.
C|8.4|TEXTO|N|VAR-102; ETP-09.01; VAL-015|JUSTIFICA|Prejuízo do fornecimento por empresas diferentes.
C|9.1|SIM_NAO|N|VAR-114; WZ-20|PREENCHE|Não: exige_amostra = N em todos os itens; Sim: responder 9.2 a 9.7.
C|9.2|TEXTO|S|VAR-114; WZ-20|PREENCHE|Itens listados recebem exige_amostra = S; a WZ-20 é derivada.
C|9.3|TEXTO|S|VAR-051; ETP-04.01|PREENCHE|Aspectos avaliados na amostra.
C|9.4|TEXTO|S|VAR-051; VAL-012|PREENCHE|Critérios objetivos de aprovação; vazio com amostra exigida dispara VAL-012.
C|9.5|TEXTO|N|VAR-051; ETP-04.01|JUSTIFICA|Justificativa da amostra no ETP (NE-013 nota 2).
C|9.6|TEXTO|S|VAR-051|PREENCHE|Quantidade de amostra por item, como informada.
C|9.7|TEXTO|N||SO_CONTROLE|Designação de quem avalia é ato interno; o TR não nomeia pessoas.
C|9.8|SIM_NAO|S|VAR-107; ETP-04.01|PREENCHE|Itens e informações a verificar em catálogo, bula ou ficha técnica entram nos requisitos.
C|10.1|SIM_NAO|N|WZ-56; SET-01; VAL-027|SUGERE|Sim: a equipe decide o comodato (WZ-56); sem decisão, VAL-027.
C|10.2|TEXTO|S|VAR-125; SET-01|PREENCHE|Itens que dependem do equipamento.
C|10.3|TEXTO|N|VAR-125; SET-01|PREENCHE|Equipamento a fornecer.
C|10.4|NUMERO|N|VAR-125; SET-01|PREENCHE|Quantidade de equipamentos, como informada.
C|10.5|TEXTO|N|VAR-101; ETP-06.01; WZ-56|JUSTIFICA|Por que o equipamento é indispensável (ETP-06.01).
C|10.6|SIM_NAO|N|ETP-06.01; WZ-56|JUSTIFICA|Sim exige explicar por que o equipamento próprio não serve.
C|10.7|SIM_NAO|N|VAR-126; WZ-08; SET-01; SET-11|PREENCHE|Sim: instalação do equipamento em comodato.
C|10.8|SIM_NAO|N|VAR-126; WZ-08; SET-01; SET-12|PREENCHE|Sim: treinamento, com a quantidade aproximada de profissionais do campo.
C|10.9|SIM_NAO|N|VAR-126; SET-01|PREENCHE|Sim: manutenção preventiva ou corretiva durante o fornecimento.
C|10.10|TEXTO|N|VAR-127; SET-01|PREENCHE|Prazo máximo para reparo ou substituição, como informado.
C|10.11|TEXTO|N|ETP-06.01; VAR-127|JUSTIFICA|Impacto da indisponibilidade justifica o prazo de reparo.
C|11.1|SIM_NAO|N|VAR-113; VAR-120; WZ-24|JUSTIFICA|Não é fato de apoio para afastar a cota (EXCECAO_JUSTIFICADA); a decisão é da equipe.
C|11.2|SIM_NAO|S|VAR-120; VAL-016|JUSTIFICA|Sim: itens e prejuízo vão para a justificativa da exceção.
C|11.3|SIM_NAO|N|VAR-120; VAR-121|JUSTIFICA|Sim: incompatibilidade entre fabricantes apoia exceção ou compatibilidade.
C|11.4|SIM_NAO|S|VAR-120; VAL-016|JUSTIFICA|Sim: necessidade de fornecimento integral por uma empresa apoia a exceção.
C|12.1|UNICA|N|VAR-060; WZ-27; VAL-020|PREENCHE|Prazo de entrega (VAR-060); campo 'Prazo solicitado' quando 'Outro'.
C|12.2|SIM_NAO|N|VAR-060; VAL-020|JUSTIFICA|Lida como 'o prazo da 12.1 é diferente de 30 dias?': Sim exige explicação; conferida com a 12.1 (VAL-020).
C|12.3|UNICA|N|WZ-26; VAR-059; VAR-062; VAL-021|PREENCHE|Única: REMESSA_UNICA; Parcelada ou Conforme pedidos: PARCELADA.
C|12.4|SIM_NAO|S|VAR-132; SET-10|PREENCHE|Sim: itens, prazo e motivo da entrega emergencial.
C|12.5|SIM_NAO|S|VAR-060; ETP-06.01|JUSTIFICA|Sim justifica prazo diferente para os itens indicados.
C|12.6|SIM_NAO|N|VAR-131; SET-09|PREENCHE|Sim: entrega com agendamento prévio (NE-026 nota 2).
C|12.7|SIM_NAO|N|VAR-131; VAR-064; SET-09|PREENCHE|Sim: restrições de horário, veículo ou acesso.
C|13.1|SIM_NAO|S|VAR-122; SET-02; VAL-009|PREENCHE|Sim: os itens da tabela recebem a faixa de temperatura.
C|13.2|SIM_NAO|N|VAR-129; SET-02; SET-03|PREENCHE|Sim: registro de temperatura no transporte.
C|13.3|MULTIPLA|S|VAR-128; SET-02; VAR-123|PREENCHE|Cuidados por item; 'Transporte de produto controlado' confere com controle_especial.
C|13.4|MULTIPLA|S|VAR-130; SET-03|PREENCHE|Documentos que acompanham a entrega.
C|13.5|SIM_NAO|N|WZ-47; VAR-105; ETP-13.01; VAL-022|SUGERE|Não sugere providência prévia (WZ-47); comparada com a 20.1 (VAL-022).
C|14.1|TEXTO|S|VAR-116; VAR-117|PREENCHE|Prazo total de validade marca o item como perecível e é a base dos critérios percentuais da 14.2.
C|14.2|UNICA|S|VAR-117; WZ-09; TR-5.4.1; VAL-007; VAL-008|PREENCHE|Uma opção por item (12 meses, 75% do prazo total, dois terços do prazo total ou outro critério); o sistema não sugere valor (P21).
C|14.3|TEXTO|N|VAR-107; ETP-04.01|JUSTIFICA|Por que a validade é necessária para o consumo da unidade.
C|14.4|SIM_NAO|N|VAR-133; WZ-57; SET-04|SUGERE|Sim: situações excepcionais; a admissão é decidida na WZ-57.
C|14.5|SIM_NAO|N|VAR-134; WZ-57; SET-04|PREENCHE|Sim: exige compromisso de substituição.
C|15.1|UNICA|N|SET-05|PREENCHE|Sim: cláusula de registro ou notificação na Anvisa.
C|15.2|SIM_NAO|S|VAR-123; SET-06; WZ-38; VAL-011|PREENCHE|Sim: itens indicados recebem controle_especial = S.
C|15.3|SIM_NAO|S|VAR-136; WZ-39; WZ-38; SET-06; VAL-011|SUGERE|Sim: Autorização Especial da empresa como requisito de lei especial (NE-073).
C|15.4|SIM_NAO|S|VAR-130; SET-03|PREENCHE|Sim: certificado de análise por lote para os itens indicados.
C|15.5|SIM_NAO|S|VAR-135; SET-07|PREENCHE|Sim: comprovação de esterilidade.
C|15.6|SIM_NAO|S|VAR-135; SET-07|PREENCHE|Sim: ausência de látex, biocompatibilidade ou outra característica.
C|15.7|SIM_NAO|S|VAR-135; SET-07|PREENCHE|Sim: normas técnicas indicadas pela área técnica, sem sugestão do sistema.
C|16.1|MULTIPLA|N|VAR-146; SET-20|PREENCHE|Itens conferidos na entrega.
C|16.2|TEXTO|N|VAR-146; SET-20; TR-8.2|PREENCHE|Situações de recusa.
C|16.3|UNICA|N|VAR-074; WZ-34|PREENCHE|Prazo de substituição de produto recusado (TR-8.2).
C|16.4|SIM_NAO|N|VAR-075; WZ-34; SET-20|JUSTIFICA|Sim justifica prazo de recebimento definitivo maior.
C|16.5|TEXTO|N||SO_CONTROLE|Designação de fiscal ou comissão é ato interno; o TR usa cargos, não nomes.
C|17.1|SIM_NAO|N|WZ-38|SUGERE|Sim sugere atestado; a exigência é da equipe (NE-071).
C|17.2|SIM_NAO|N|VAR-085; WZ-38|JUSTIFICA|Não: experiência específica a comprovar.
C|17.3|TEXTO|N|VAR-085; ETP-04.01|JUSTIFICA|Risco reduzido pela exigência.
C|17.4|SIM_NAO|N|VAR-085; VAL-028|PREENCHE|Sim: quantidade ou percentual e justificativa técnica, conferidos pela VAL-028.
C|17.5|MULTIPLA|N|VAR-136; WZ-39; SET-06; SET-08|PREENCHE|Autorizações marcadas: AFE e licença sanitária em TR-9.14; AE em TR-9.35.
C|18.1|SIM_NAO|N|WZ-29|SUGERE|Sim sugere garantia contratual do bem (WZ-29).
C|18.2|MULTIPLA|N|VAR-151; SET-21|PREENCHE|Situações de substituição.
C|18.3|SIM_NAO|S|WZ-08; VAR-009; SET-14|SUGERE|Sim: suporte técnico como atividade além da entrega.
C|18.4|SIM_NAO|S|WZ-08; VAR-138; SET-12|SUGERE|Sim: treinamento para uso dos produtos.
C|19.1|SIM_NAO|N|WZ-46; VAR-103; ETP-10.01|PREENCHE|Contrato, ata ou processo relacionado.
C|19.2|SIM_NAO|N|WZ-46; VAR-103; ETP-10.01|PREENCHE|Dependência de outro equipamento, serviço ou insumo.
C|19.3|SIM_NAO|N|VAR-100; ETP-05.01|JUSTIFICA|Dependência futura de fabricante entra no levantamento de mercado.
C|20.1|SIM_NAO|N|WZ-47; VAL-022|ALERTA|Repete a 13.5; divergência dispara VAL-022.
C|20.2|UNICA|N|WZ-47; VAR-105; VAL-010|SUGERE|Não: providência prévia de conservação.
C|20.3|UNICA|N|WZ-47; VAR-105; VAL-010|SUGERE|Não: providência prévia de energia alternativa.
C|20.4|SIM_NAO|N|WZ-47; VAR-105|SUGERE|Não: capacitação da equipe como providência prévia.
C|20.5|SIM_NAO|N|WZ-47; VAR-105; SET-12|SUGERE|Sim: capacitação antes do fornecimento.
C|20.6|SIM_NAO|N|WZ-47; VAR-105|SUGERE|Sim: adaptação física, elétrica ou operacional.
C|20.7|SIM_NAO|N|WZ-47; VAR-105|SUGERE|Não: designar ou capacitar profissional para o recebimento técnico.
C|21.1|MULTIPLA|N|WZ-48; VAR-106; ETP-14.01; WZ-17|PREENCHE|Resíduos gerados.
C|21.2|SIM_NAO|N|VAR-106; ETP-14.01; WZ-47|PREENCHE|Não: procedimento de descarte como providência.
C|21.3|MULTIPLA|N|VAR-147; SET-22; WZ-48|PREENCHE|Situações de logística reversa ou recolhimento.
C|21.4|SIM_NAO|N|VAR-106; ETP-14.01|PREENCHE|Plano de gerenciamento de resíduos aplicável.
C|22|MULTIPLA|N|VAL-048|ALERTA|Lista de anexos: tabela de itens e memória de cálculo ausentes disparam VAL-048.
C|23|MULTIPLA|N||SO_CONTROLE|Declaração do responsável técnico: fica no processo, não entra na minuta.
P|CAB.01|TEXTO|N|VAR-001; VAL-006|PREENCHE|Preenche VAR-001 quando vazia; diferença dispara VAL-006.
P|CAB.02|TEXTO|N|VAR-006; ETP-03.01|PREENCHE|OMS requisitante vai para a área requisitante do ETP.
P|CAB.03|TEXTO|N|VAR-006; ETP-03.01|PREENCHE|Setor requisitante.
P|CAB.04|TEXTO|N|VAR-007; ETP-03.02|PREENCHE|Responsável técnico (ETP-03.02).
P|CAB.05|TEXTO|N||SO_CONTROLE|Data do preenchimento: controla a versão das respostas.
P|1.1|TEXTO|N|VAR-006; ETP-03.01|PREENCHE|Mesma informação do cabeçalho; prevalece a 1.1.
P|1.2|TEXTO|N|VAR-006; ETP-03.01; VAR-064|PREENCHE|Setor usuário.
P|1.3|TEXTO|N|VAR-008; ETP-02.01; TR-1.1|SUGERE|Ponto de partida do objeto.
P|1.4|TABELA|N|VAR-007; VAR-098; ETP-03.02; ETP-16.02|PREENCHE|Nome e posto para ETP-03.02 e assinaturas; telefone e e-mail só no processo.
P|1.5|MULTIPLA|N|WZ-07; VAR-155; VAL-040|PREENCHE|Checklist de permanentes preenchido: WZ-07 = PERMANENTE e itens com categoria PERMANENTE; com o de consumo também, AMBOS.
P|2.1|TEXTO|N|VAR-010; ETP-02.01|PREENCHE|Necessidade.
P|2.2|TEXTO|N|VAR-010; ETP-02.01|PREENCHE|Público e atividades beneficiados.
P|2.3|MULTIPLA|N|VAR-010; ETP-02.01|PREENCHE|Finalidade da aquisição entra na necessidade.
P|2.4|UNICA|N|VAR-010; WZ-58; SET-18|SUGERE|Sim ou Parcialmente: equipamento substituído; sugere avaliar a desinstalação (WZ-58).
P|2.5|MULTIPLA|N|VAR-010; ETP-02.01|JUSTIFICA|Por que o equipamento atual não atende.
P|2.6|TEXTO|N|VAR-104; ETP-12.01|PREENCHE|Resultados mensuráveis (ETP-12.01).
P|3.1|SIM_NAO|N|VAR-011; VAR-109; ETP-07.02; VAL-048|PREENCHE|Descritivo anexo é a fonte da especificação; Não dispara VAL-048.
P|3.2|MULTIPLA|S|VAR-109; ETP-04.01|PREENCHE|Parâmetros mínimos de desempenho por item.
P|3.3|SIM_NAO|S|VAR-121; ETP-04.01; VAL-018|PREENCHE|Sim: compatibilidade exigida por item.
P|3.4|UNICA|S|VAR-109; ETP-06.01|PREENCHE|Acessórios e componentes incluídos no fornecimento.
P|3.5|MULTIPLA|S|VAR-135; ETP-04.01; SET-07|PREENCHE|Ambiente com requisito especial.
P|3.6|SIM_NAO|S|VAR-109; ETP-04.01|PREENCHE|Limites de dimensão, peso ou espaço.
P|3.7|UNICA|S|VAR-115; VAR-046; WZ-18|SUGERE|Não: itens candidatos a marca ou modelo indicado, com o prejuízo como justificativa (NE-012).
P|4.1|MULTIPLA|N|VAR-012; ETP-07.01|PREENCHE|Critério de quantidade.
P|4.2|TEXTO|S|VAR-064; WZ-28|PREENCHE|Local de instalação por item.
P|4.3|UNICA|N|VAR-012|JUSTIFICA|Equipamentos existentes considerados no quantitativo.
P|4.4|TEXTO|S|VAR-012; VAL-025|JUSTIFICA|Justificativa dos itens com uma unidade.
P|4.5|TEXTO|S|VAR-012; ETP-07.01|PREENCHE|Memória de cálculo dos itens com mais de uma unidade.
P|4.6|SIM_NAO|S|VAR-012|JUSTIFICA|Unidade reserva: item, quantidade e risco evitado.
P|4.7|SIM_NAO|N|VAL-048|ALERTA|Não: memória de cálculo não anexada.
P|5.1|UNICA|N|VAR-100; ETP-05.01|PREENCHE|Outras soluções técnicas.
P|5.2|UNICA|N|VAR-100; ETP-05.01|PREENCHE|Solução atual.
P|5.3|UNICA|N|VAR-100; ETP-05.01|PREENCHE|Outras formas (locação, comodato, serviço) entram no levantamento de mercado.
P|5.4|SIM_NAO|N|VAR-100; ETP-05.01|JUSTIFICA|Solução descartada e motivo.
P|5.5|UNICA|N|VAR-100; ETP-05.01; VAL-023|PREENCHE|Fabricantes; comparada com a 6.1.
P|5.6|UNICA|N|VAR-100; ETP-05.01; VAL-023|PREENCHE|Fornecedores; comparada com a 6.1.
P|5.7|TEXTO|N|VAR-101; ETP-06.01|PREENCHE|Solução escolhida.
P|5.8|TEXTO|N|VAR-100; ETP-05.01|JUSTIFICA|Justificativa da escolha.
P|6.1|UNICA|N|VAL-023; VAL-019|ALERTA|Repete a 5.5 e a 5.6; divergência dispara VAL-023.
P|6.2|SIM_NAO|N|WZ-01; WZ-04; VAL-019|SUGERE|Sim indica possível inexigibilidade ou marca indicada; decisão da equipe.
P|6.3|TEXTO|S|VAR-115; WZ-18|PREENCHE|Itens exclusivos recebem marca_indicada.
P|6.4|TEXTO|N|VAR-046; VAR-024|JUSTIFICA|Equivalentes avaliados e motivo técnico.
P|6.5|UNICA|N|WZ-04; WZ-21; VAL-019|ALERTA|Sim: outros revendedores enfraquecem a exclusividade de fornecedor.
P|6.6|UNICA|N|VAR-024|JUSTIFICA|Documento de exclusividade.
P|6.7|UNICA|N|VAR-024|JUSTIFICA|Território da exclusividade.
P|7.1|SIM_NAO|N|WZ-50; VAR-102; ETP-09.01|SUGERE|Não sugere agrupamento.
P|7.2|SIM_NAO|S|VAR-112; WZ-13; WZ-50; VAL-014; VAL-015|PREENCHE|Sim: itens indicados recebem o mesmo rótulo de grupo.
P|7.3|MULTIPLA|N|VAR-102; ETP-09.01; VAL-015|JUSTIFICA|Motivos do fornecimento conjunto.
P|7.4|TEXTO|N|VAR-102; ETP-09.01; VAL-015|JUSTIFICA|Problema do fornecimento por empresas diferentes.
P|7.5|SIM_NAO|S|VAR-112; VAR-102|SUGERE|Sim: acessório dependente sugere o mesmo grupo do equipamento principal.
P|8.1|UNICA|N|VAR-060; WZ-27|PREENCHE|Prazo de entrega.
P|8.2|SIM_NAO|S|VAR-060; ETP-06.01|JUSTIFICA|Condição especial que justifica o prazo por item.
P|8.3|UNICA|N|WZ-26; VAR-062|PREENCHE|Remessa única: REMESSA_UNICA; etapas ou cronograma: PARCELADA.
P|8.4|UNICA|S|VAR-060|JUSTIFICA|Itens importados ou sob encomenda justificam prazo.
P|8.5|SIM_NAO|N|VAR-131; SET-09|PREENCHE|Sim: agendamento prévio.
P|8.6|SIM_NAO|N|VAR-131; SET-09; SET-02|PREENCHE|Sim: restrições físicas ou operacionais de acesso.
P|8.7|SIM_NAO|N|VAR-128; SET-02|PREENCHE|Sim: logística especial de transporte ou movimentação.
P|8.8|SIM_NAO|N|VAR-143; SET-17; WZ-47|PREENCHE|Sim: condições do local antes da entrega.
P|9.1|SIM_NAO|S|VAR-064; VAR-143|PREENCHE|Local de instalação definido por item.
P|9.2|UNICA|N|WZ-47; VAR-105; SET-17|SUGERE|Não ou ainda não avaliada: providência prévia.
P|9.3|MULTIPLA|N|VAR-143; VAR-105; SET-17|PREENCHE|Adequações de infraestrutura e parâmetros.
P|9.4|UNICA|N|VAR-143|PREENCHE|Requisitos documentados e documento anexo.
P|9.5|SIM_NAO|N|VAR-143; SET-17; WZ-33|PREENCHE|Sim: levantamento técnico (site planning) pelo fornecedor.
P|9.6|SIM_NAO|N|WZ-47; VAR-105|SUGERE|Sim: projeto ou adequação antes da instalação.
P|9.7|UNICA|N|WZ-46; WZ-47; VAR-103|SUGERE|Sim: depende de obra ou serviço contratado à parte.
P|10.1|UNICA|N|WZ-46; VAR-103|PREENCHE|Contrato, obra ou processo relacionado.
P|10.2|SIM_NAO|N|WZ-46; VAR-103|PREENCHE|Dependência de outro equipamento, serviço, rede ou insumo.
P|10.3|SIM_NAO|N|WZ-47; VAR-105|PREENCHE|Providência antes da entrega ou operação.
P|10.4|UNICA|N|WZ-46; VAR-103; ETP-06.01|PREENCHE|Contratação recorrente após a garantia.
P|10.5|UNICA|N|VAR-100; ETP-05.01|JUSTIFICA|Dependência futura de fabricante.
P|10.6|SIM_NAO|N|WZ-46; VAR-103|PREENCHE|Aquisição simultânea necessária.
P|11.1|SIM_NAO|N|WZ-08; VAR-009; SET-11|PREENCHE|Sim: instalação ou montagem especializada.
P|11.2|UNICA|N|WZ-59; SET-15; VAL-030|SUGERE|Sim: instalação pelo fabricante ou autorizada, decidida na WZ-59.
P|11.3|MULTIPLA|S|VAR-137; SET-11|PREENCHE|Atividades antes da liberação para uso.
P|11.4|TEXTO|N|VAR-137; VAR-145; SET-11; SET-19|PREENCHE|Certificados, laudos ou relatórios após a instalação.
P|11.5|TEXTO|N|VAR-137; SET-11; SET-20|PREENCHE|Critérios objetivos de instalação concluída.
P|11.6|TEXTO|N||SO_CONTROLE|Designação de quem valida a instalação é ato interno.
P|11.7|UNICA|N|WZ-59; SET-15|SUGERE|Não: execução só pelo fabricante, decidida na WZ-59.
P|12.1|SIM_NAO|N|WZ-08; VAR-009; SET-12|PREENCHE|Sim: treinamento (responder 12.2 a 12.8).
P|12.2|TEXTO|N|VAR-138; SET-12|PREENCHE|Profissionais e quantidade aproximada.
P|12.3|TEXTO|N|VAR-138; SET-12|PREENCHE|Conteúdo mínimo.
P|12.4|TEXTO|N|VAR-138; SET-12|PREENCHE|Carga horária mínima, como informada.
P|12.5|MULTIPLA|N|VAR-138; SET-12|PREENCHE|Formato do treinamento.
P|12.6|UNICA|N|VAR-138; SET-12; SET-20|PREENCHE|Momento do treinamento em relação ao uso e ao recebimento definitivo.
P|12.7|SIM_NAO|N|VAR-138; SET-12|PREENCHE|Reciclagem durante a garantia.
P|12.8|UNICA|N|WZ-59; SET-15|SUGERE|Não: treinamento só pelo fornecedor principal, decidido na WZ-59.
P|13.1|UNICA|S|VAR-124; WZ-29; VAR-066; VAL-026; VAL-050|PREENCHE|Prazo mínimo de garantia por item (12, 24, 36 ou outro); acima de 12 meses exige a 13.2.
P|13.2|TEXTO|N|VAR-124; VAL-026|JUSTIFICA|Justificativa da garantia acima de 12 meses (NE-029).
P|13.3|UNICA|N|VAR-141; SET-13|PREENCHE|Marco inicial da garantia.
P|13.4|MULTIPLA|S|VAR-139; SET-13|PREENCHE|Serviços incluídos na garantia.
P|13.5|UNICA|N|VAR-139; SET-13|PREENCHE|Atendimento no local de instalação.
P|13.6|UNICA|N|VAR-140; SET-13|PREENCHE|Prazo para início do atendimento.
P|13.7|UNICA|N|VAR-067; WZ-29|PREENCHE|Prazo para restabelecer o funcionamento (TR-5.12).
P|13.8|UNICA|N|VAR-152; SET-13|PREENCHE|Equipamento substituto temporário (complementa TR-5.14).
P|14.1|SIM_NAO|N|WZ-08; SET-14|SUGERE|Sim: assistência técnica especializada.
P|14.2|UNICA|N|WZ-59; SET-15|SUGERE|Sim: assistência pelo fabricante ou autorizada, decidida na WZ-59.
P|14.3|SIM_NAO|N|VAR-140; SET-14|PREENCHE|Sim: atendimento presencial em prazo específico.
P|14.4|TEXTO|N|VAR-067; ETP-06.01|JUSTIFICA|Tempo máximo de indisponibilidade justifica prazos de reparo.
P|14.5|SIM_NAO|N|VAR-148; SET-14|PREENCHE|Sim: manutenção preventiva durante a garantia.
P|14.6|SIM_NAO|N|VAR-148; SET-14|PREENCHE|Sim: calibração ou teste periódico.
P|14.7|SIM_NAO|N|VAR-149; SET-14; VAL-001|PREENCHE|Sim: suporte remoto; com acesso à rede, alerta de TIC.
P|15.1|SIM_NAO|S|WZ-46; VAR-103|PREENCHE|Sim: consumíveis recorrentes (contratação correlata).
P|15.2|UNICA|N|VAR-100; ETP-05.01; VAL-019|JUSTIFICA|Consumível ou peça proprietária entra no levantamento de mercado.
P|15.3|SIM_NAO|N|VAR-142; SET-16; VAL-001|PREENCHE|Sim: software ou licença; dispara o alerta de TIC.
P|15.4|UNICA|N|VAR-142; SET-16|PREENCHE|Tipo de licença.
P|15.5|SIM_NAO|N|VAR-142; SET-16; VAL-001|ALERTA|Sim: integração à rede ou sistema da unidade; dispara o alerta de TIC.
P|15.6|UNICA|N|VAR-142; SET-16|PREENCHE|Atualizações durante a garantia.
P|15.7|TEXTO|N|VAR-101; ETP-06.01|PREENCHE|Vida útil esperada (descrição da solução).
P|15.8|SIM_NAO|N|VAR-142; SET-14|PREENCHE|Suporte do fabricante por período mínimo.
P|15.9|UNICA|N|WZ-46; ETP-06.01|JUSTIFICA|Custo recorrente após a compra.
P|16.1|UNICA|N|SET-05|PREENCHE|Sim: registro ou notificação na Anvisa.
P|16.2|UNICA|N|VAR-135; SET-07|PREENCHE|Sim: conformidade Inmetro.
P|16.3|SIM_NAO|S|VAR-135; SET-07|PREENCHE|Sim: norma ou certificação técnica indicada pela área técnica.
P|16.4|UNICA|N|VAR-148; VAR-145; SET-14|PREENCHE|Sim: certificado de calibração ou rastreabilidade metrológica.
P|16.5|UNICA|N|WZ-47; VAR-105|PREENCHE|Sim: licença técnica da unidade ou condição especial de segurança (providência prévia).
P|16.6|UNICA|N|VAR-150; SET-19|PREENCHE|Sim: manuais em português.
P|17.1|SIM_NAO|N|VAR-114; WZ-20|PREENCHE|Não: exige_amostra = N; Sim: responder 17.2 a 17.5.
P|17.2|TEXTO|S|VAR-114; WZ-20|PREENCHE|Itens com demonstração, teste ou amostra recebem exige_amostra = S.
P|17.3|TEXTO|S|VAR-051|PREENCHE|O que será avaliado.
P|17.4|TEXTO|S|VAR-051; VAL-012|PREENCHE|Critérios objetivos de aprovação.
P|17.5|TEXTO|N||SO_CONTROLE|Designação de quem avalia é ato interno.
P|18.1|SIM_NAO|N|WZ-38|SUGERE|Sim sugere atestado; exigência decidida pela equipe (NE-071).
P|18.2|SIM_NAO|N|VAR-085; WZ-38|JUSTIFICA|Não: experiência específica a comprovar.
P|18.3|MULTIPLA|N|VAR-085|PREENCHE|Atividades a comprovar nos atestados.
P|18.4|SIM_NAO|N|VAR-085; VAL-028|PREENCHE|Sim: quantidade mínima e justificativa (VAL-028).
P|18.5|SIM_NAO|N|WZ-38; VAR-084|SUGERE|Sim: habilitação profissional específica (registro em entidade, se a lei exigir).
P|18.6|UNICA|N|WZ-59; WZ-21; SET-15; VAL-030|SUGERE|Sim: execução por autorizado do fabricante, decidida na WZ-59.
P|18.7|TEXTO|N|VAR-085; ETP-04.01|JUSTIFICA|Risco reduzido pelas exigências.
P|19.1|MULTIPLA|N|VAR-146; SET-20|PREENCHE|Itens conferidos no recebimento provisório.
P|19.2|SIM_NAO|N|SET-20; VAR-075|PREENCHE|Sim: recebimento definitivo só após instalação, testes ou treinamento.
P|19.3|UNICA|N|VAR-075; WZ-34|PREENCHE|Prazo para testes e avaliação definitiva (TR-8.3).
P|19.4|TEXTO|N|VAR-146; SET-20|PREENCHE|Situações de recusa.
P|19.5|UNICA|N|VAR-074; WZ-34|PREENCHE|Prazo de correção ou substituição (TR-8.2).
P|19.6|TEXTO|N||SO_CONTROLE|Designação de quem emite a aceitação é ato interno.
P|19.7|MULTIPLA|N|VAR-145; SET-19; SET-20|PREENCHE|Documentos exigidos para o recebimento definitivo.
P|20.1|SIM_NAO|N|WZ-58; VAR-144; SET-18|SUGERE|Sim: equipamento a retirar; a obrigação do fornecedor é decidida na WZ-58.
P|20.2|UNICA|N|VAR-144; WZ-58; SET-18|PREENCHE|Sim: desinstalação técnica especializada.
P|20.3|MULTIPLA|N|VAR-144; SET-18|PREENCHE|Procedimentos especiais antes da retirada.
P|21.1|MULTIPLA|S|WZ-48; VAR-106|PREENCHE|Resíduos ou materiais que exigem cuidado.
P|21.2|UNICA|N|VAR-147; SET-22; WZ-48|PREENCHE|Sim: logística reversa ou recolhimento pelo fornecedor.
P|21.3|UNICA|N|VAR-106|PREENCHE|Procedimento de descarte da unidade.
P|21.4|UNICA|S|WZ-17; VAR-044; ETP-14.01|PREENCHE|Sim: critérios do Guia Nacional de Contratações Sustentáveis por item (TR-4.1.1..TR-4.1.3).
P|22|MULTIPLA|N|VAL-048|ALERTA|Lista de anexos: descritivo e memória de cálculo ausentes disparam VAL-048.
P|22.1|TEXTO|N||SO_CONTROLE|Observações sobre anexos: controle de completude do processo.
P|23|MULTIPLA|N||SO_CONTROLE|Declaração do responsável técnico: fica no processo, não entra na minuta.
"""

# condicionais explícitas no texto do checklist e implícitas (marcadas como tal)
IMPLICITAS = {
    ("C", "8.3"): "8.2", ("C", "8.4"): "8.2", ("C", "13.2"): "13.1", ("C", "17.2"): "17.1", ("C", "17.3"): "17.1",
    ("C", "17.4"): "17.1", ("C", "14.5"): "14.4", ("P", "2.5"): "2.4", ("P", "7.3"): "7.2", ("P", "7.4"): "7.2",
    ("P", "11.2"): "11.1", ("P", "11.3"): "11.1", ("P", "11.4"): "11.1", ("P", "11.5"): "11.1", ("P", "11.6"): "11.1",
    ("P", "11.7"): "11.1", ("P", "15.4"): "15.3", ("P", "20.2"): "20.1", ("P", "20.3"): "20.1", ("P", "18.2"): "18.1",
    ("P", "18.3"): "18.1", ("P", "18.4"): "18.1",
}
VALOR_IMPLICITO = {("P", "2.5"): "Sim ou Parcialmente"}


def num_key(n):
    if n.startswith("CAB."):
        return (0, int(n[4:]), 0)
    p = n.split(".")
    return (int(p[0]), int(p[1]) if len(p) > 1 else 0, 1)


def tipo_inferido(it):
    op = it["opcoes"]
    if not op:
        if len(it["campos"]) >= 2:
            return "TABELA"
        return "TEXTO"
    base = {"Sim", "Não"}
    if set(op) == base:
        return "SIM_NAO"
    return "UNICA"


def condicionais(itens, lista):
    cond = {}
    for it in itens:
        for o in it["orientacoes"]:
            m = re.search(r"responda (?:obrigatoriamente )?às perguntas (\d+\.\d+) a (\d+\.\d+)", o)
            if m:
                a, b = m.groups()
                for x in itens:
                    if not x["numero"].startswith("CAB") and "." in x["numero"] and \
                            num_key(a) <= num_key(x["numero"]) <= num_key(b):
                        cond[x["numero"]] = f"responder se CK-{lista}-{it['numero']} = Sim"
            m = re.search(r"Se não, siga para o item (\d+)", o)
            if m:
                prox = int(m.group(1))
                sec = int(it["numero"].split(".")[0])
                for x in itens:
                    if "." in x["numero"] and not x["numero"].startswith("CAB"):
                        s, q = map(int, x["numero"].split("."))
                        if s == sec and s < prox and num_key(x["numero"]) > num_key(it["numero"]):
                            cond[x["numero"]] = f"responder se CK-{lista}-{it['numero']} = Sim"
        if it["numero"] == "13.2" and lista == "P":
            cond["13.2"] = "responder se CK-P-13.1 for maior que 12 meses (condição escrita na própria pergunta)"
    for (l, n), pai in IMPLICITAS.items():
        if l == lista and n not in cond:
            v = VALOR_IMPLICITO.get((l, n), "Sim")
            cond[n] = f"responder se CK-{lista}-{pai} = {v} (implícito)"
    if lista == "C" and "12.2" not in cond:
        cond["12.2"] = "responder se CK-C-12.1 for diferente de 30 dias (implícito; redação ambígua, ver sugestoes_checklist.md)"
    return cond


def main():
    ck_c, ck_p, pasta, saida_cob = sys.argv[1], sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4])
    spec = {}
    for linha in MAPA.strip().splitlines():
        partes = linha.split("|")
        if len(partes) != 7:
            raise SystemExit(f"linha do MAPA com {len(partes)} campos: {linha}")
        lista, num, tipo, por_item, dest, efeito, regra = partes
        if efeito not in EFEITOS or (tipo not in TIPOS and tipo != "-"):
            raise SystemExit(f"efeito ou tipo inválido: {linha}")
        if (lista, num) in spec:
            raise SystemExit(f"chave repetida no MAPA: {lista} {num}")
        spec[(lista, num)] = (tipo, por_item, dest, efeito, regra)
    # IDs válidos para destinos
    validos = set()
    for nome in ("M01_etp_campos.csv", "M02_tr_blocos.csv", "M04_wizard.csv", "M05_variaveis.csv",
                 "M08_clausulas_setoriais.csv", "M10_validacoes.csv"):
        validos |= {r["id"] for r in ler_csv(pasta / nome)}
    m05 = ler_csv(pasta / "M05_variaveis.csv")
    linhas, usados = [], set()
    for lista, arq in (("C", ck_c), ("P", ck_p)):
        itens = [i for i in json.load(open(arq, encoding="utf-8"))
                 if not (lista == "C" and i["numero"].startswith("CAB.") and int(i["numero"][4:]) >= 6)]
        cond = condicionais(itens, lista)
        docx, nome_ck, hash12 = ARQ[lista]
        for it in itens:
            n = it["numero"]
            chave = (lista, n)
            if chave not in spec:
                raise SystemExit(f"pergunta sem mapeamento: CK-{lista}-{n}")
            usados.add(chave)
            tipo, por_item, dest, efeito, regra = spec[chave]
            if tipo == "-":
                tipo = tipo_inferido(it)
            for d in [x.strip() for x in dest.split(";") if x.strip()]:
                if d not in validos:
                    raise SystemExit(f"CK-{lista}-{n}: destino inexistente {d}")
            if efeito == "SO_CONTROLE" and dest:
                raise SystemExit(f"CK-{lista}-{n}: SO_CONTROLE com destino")
            if efeito != "SO_CONTROLE" and not dest:
                raise SystemExit(f"CK-{lista}-{n}: sem destino e sem SO_CONTROLE")
            opcoes = "; ".join(it["opcoes"])
            if it["campos"]:
                opcoes = (opcoes + "; " if opcoes else "") + "campos: " + "; ".join(it["campos"])
            pergunta = it["pergunta"] or it["secao"].split(". ", 1)[1]
            fonte = (f"{docx}, word/document.xml, parágrafos {it['par_ini']} a {it['par_fim']} (SHA-256 {hash12}...). "
                     f"secao, numero, pergunta, opcoes e orientacao EXTRAIDOS")
            if not it["pergunta"]:
                fonte += "; o item não tem pergunta numerada: pergunta = título da seção"
            if n.startswith("CAB."):
                fonte += "; campo do cabeçalho do checklist, numerado CAB.xx na ordem do documento"
            fonte += ". tipo_resposta, condicional implícita, por_item, destinos, efeito e regra INFERIDOS."
            linhas.append({"id": f"CK-{lista}-{n}", "checklist": nome_ck, "secao": it["secao"], "numero": n,
                           "pergunta": pergunta, "tipo_resposta": tipo, "opcoes": opcoes,
                           "orientacao": " / ".join(it["orientacoes"]), "condicional": cond.get(n, ""),
                           "por_item": por_item, "destinos": dest, "efeito": efeito, "regra": regra, "fonte": fonte,
                           "status": "INFERIDO"})
    sobra = sorted(set(spec) - usados)
    if sobra:
        raise SystemExit(f"MAPA com chaves que não existem nos checklists: {sobra}")
    gravar_csv(pasta / "M11_checklist.csv", COLS, linhas, preservar=())

    # ---------------------------------------------------------------- cobertura nos dois sentidos
    m01 = ler_csv(pasta / "M01_etp_campos.csv")
    var_m01 = {}
    for r in m05:
        for u in [x.strip() for x in r["usada_em"].split(";")]:
            if u.startswith("ETP-"):
                var_m01.setdefault(u, set()).add(r["id"])
    origem = {}
    for l in linhas:
        ds = [x.strip() for x in l["destinos"].split(";") if x.strip()]
        for d in ds:
            if d.startswith("ETP-"):
                origem.setdefault(d, set()).add(l["id"])
            if d.startswith("VAR-"):
                for campo, vs in var_m01.items():
                    if d in vs:
                        origem.setdefault(campo, set()).add(l["id"])
    out = ["# Cobertura do M11 nos dois sentidos", "",
           "## 1. Campos do M01 e perguntas de origem (direta ou pela variável do M05 que preenche o campo)"]
    sem_fonte = []
    for r in m01:
        o = sorted(origem.get(r["id"], []), key=lambda x: (x[3], num_key(x[5:])))
        if o:
            out.append(f"{r['id']} {r['campo']}: {len(o)} pergunta(s): {', '.join(o[:12])}{' ...' if len(o) > 12 else ''}")
        else:
            sem_fonte.append(r)
    out += ["", "## 2. Campos do M01 sem fonte no checklist"]
    for r in sem_fonte:
        out.append(f"{r['id']} {r['campo']}")
    out += ["", "## 3. Perguntas sem destino (SO_CONTROLE, com o motivo)"]
    for l in linhas:
        if l["efeito"] == "SO_CONTROLE":
            out.append(f"{l['id']}: {l['regra']}")
    from collections import Counter
    out += ["", "## 4. Totais",
            f"perguntas: {len(linhas)} (consumo {sum(1 for l in linhas if l['checklist'] == 'CONSUMO')}, permanentes "
            f"{sum(1 for l in linhas if l['checklist'] == 'PERMANENTES')})",
            f"efeito: {dict(Counter(l['efeito'] for l in linhas))}",
            f"tipo_resposta: {dict(Counter(l['tipo_resposta'] for l in linhas))}",
            f"por_item = S: {sum(1 for l in linhas if l['por_item'] == 'S')}",
            f"com condicional: {sum(1 for l in linhas if l['condicional'])} (implícitas: "
            f"{sum(1 for l in linhas if 'implícito' in l['condicional'])})",
            f"campos do M01 com origem no checklist: {len(m01) - len(sem_fonte)} de {len(m01)}"]
    saida_cob.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out[-7:]))


if __name__ == "__main__":
    main()
