# Licita+ | Matrizes v1

Estado em 23/10/2026: Fases 0 a 10 concluídas. Na Fase 10 as regras que o motor executa ficaram todas em JSON Logic (dependências do wizard, condições e preenchimento do checklist, atributos calculados), com os parâmetros no M12 e os cenários de ouro e de reprodução em `cenarios/`. Antes, na mesma data, a tarefa extra da Fase 10 conferiu o M07 com o repositório auxiliar ctresb/leis e fechou a P16.

## Arquivos

| Arquivo | Conteúdo | Linhas |
|---|---|---|
| `M00_inventario.csv` | inventário dos documentos da base (DFDs, ETPs, TRs, checklists, modelo, matrizes rascunho) | 23 |
| `M01_etp_campos.csv` | campos do ETP Digital, com inciso do art. 18, obrigatoriedade e situação no corpus | 24 |
| `M02_tr_blocos.csv` | blocos do modelo AGU de TR (DEZ/2025), com texto literal, formatação, condição em texto e em JSON Logic | 499 |
| `M03_notas_explicativas.csv` | as 102 notas explicativas do modelo, com regra derivada, perguntas e regras afetadas e colunas de revisão | 102 |
| `M04_wizard.csv` | decisões do wizard (jurídicas e derivadas dos itens), perguntas do checklist que as pré-preenchem, liga/desliga em texto e em JSON Logic, colunas de revisão | 59 |
| `M05_variaveis.csv` | variáveis de entrada e atributos de item, com origem, validação e onde são usadas | 159 |
| `M06_derivacao_etp_tr.csv` | derivação ETP para TR por bloco, com o teste no par 117/2025 e o caso 67/2026 x 23/2026 | 499 |
| `M07_normas.csv` | normas e orientações citadas nas matrizes, com origem e situação conferida quando possível | 104 |
| `M08_clausulas_setoriais.csv` | cláusulas setoriais de saúde que o modelo não traz, com fonte no checklist e evidência no corpus | 22 |
| `M09_desvios.csv` | desvios encontrados nos documentos da base e nas matrizes rascunho, com o tratamento no sistema | 34 |
| `M10_validacoes.csv` | validações e alertas, com condição em JSON Logic quando cabe | 50 |
| `M11_checklist.csv` | uma linha por pergunta dos dois checklists técnicos, com tipo, condicional, destino e efeito, e as mesmas regras em JSON Logic | 276 |
| `M12_parametros.csv` | valores numéricos, limites e marcadores usados pelas regras, com base, vigência e onde são usados | 12 |
| `matrizes_v1.xlsx` | cópia de leitura e revisão: aba LEIA_ME e uma aba por CSV; colunas de revisão em amarelo no M03 e no M04 | |
| `cenarios/` | cenários de ouro C1 a C8 (8) e casos de reprodução R1 e R2 (2) em JSON, com entrada e esperado | |
| `perguntas_abertas.md` | decisões pendentes e adotadas, P01 a P31 | |
| `sugestoes_checklist.md` | lacunas, duplicidades e ambiguidades dos checklists, com redação proposta | |
| `auditoria_matrizes_01_02.md` | auditoria das matrizes rascunho 01 e 02 (Fase 8) | |
| `log_fase10_repo_leis.md` | arquivos do repositório auxiliar ctresb/leis (commit 15eb09b) cruzados com o M07 e uso de cada um | |
| `logs/` | conferências, cobertura do checklist, comparação dos TRs, expressões, simulação, normas, testes | |
| `scripts/` | scripts de análise que geram tudo acima | |

## O que mudou na Fase 10

- `M04.depende_de_expr` em 25 de 59 perguntas (vazia quando a pergunta vale sempre ou só depende de dado dos itens) e `M04.calculo_expr` nas 6 perguntas derivadas dos itens.
- `M05.calculo_expr` e `M05.calculo_ordem` em 9 variáveis (VAR-031, VAR-049, VAR-065, VAR-111, VAR-113, VAR-116, VAR-118, VAR-119, VAR-154). Linhas novas: VAR-156 `numero`, VAR-157 `catmat`, VAR-158 `quantidade` e VAR-159 `valor_unitario` (atributos de item que as regras já usavam).
- `M11.condicional_expr` em 61 perguntas, `preenche_expr` em 159 e `sugere_expr` em 38. O que a regra do M11 não permite traduzir ficou sem expressão e está listado em `logs/f10_expr.txt` (P31).
- `M12_parametros.csv` com 12 parâmetros: nenhuma expressão traz número de lei ou valor monetário.
- M10: literais trocados por `parametros.*` (VAL-004, 017, 020, 025, 026) e por `VAR_099` (VAL-032); mensagem da VAL-033 reescrita sem o padrão de ID.
- Números de processo do corpus trocados por PROC-01 a PROC-12 no M00, no `perguntas_abertas.md` e nos scripts; a correspondência ficou fora do pacote.
- Convenções novas e operadores fora da lista: P31.

## O que mudou da Fase 3 à Fase 9

- Ajuste 1: o item virou entidade (VAR-011 com as colunas VAR-112 a VAR-124 e VAR-153 a VAR-155). Tratamento de ME/EPP calculado pelo valor do item ou do grupo; WZ-09, WZ-13, WZ-18, WZ-20, WZ-24 e WZ-50 são derivadas dos itens. Cenário misto C6 na simulação.
- Checklists técnicos como entrada do sistema: M11 com 276 perguntas (131 de consumo, 145 de permanentes); efeito: PREENCHE 164, JUSTIFICA 50, SUGERE 42, SO_CONTROLE 10, ALERTA 10.
- M04: 59 perguntas. A coluna `pre_preenchida_por` mostra 17 respondidas ou sugeridas pelo checklist, 6 derivadas dos itens e 36 marcadas `DECISAO_JURIDICA` (equipe administrativa). WZ-56 a WZ-59 são novas (comodato, validade excepcional, desinstalação, fabricante ou rede credenciada).
- M05: 159 variáveis; origem: WIZARD 75, CHECKLIST 53, SISTEMA 20, DFD 6, PESQUISA_PRECOS 5. CHECKLIST entrou no domínio de origem (P29).
- Condições em JSON Logic: `M02.condicao_expr`, `M04.liga_expr` e `M04.desliga_expr`, `M08.condicao_expr` e `M10.condicao_expr`. O texto livre continua como comentário. O que não coube está na P27.
- Colunas `validacao` e `comentario_validacao` no M03 e no M04, vazias, para a sua revisão no xlsx.
- P17 e P21 resolvidas; P16 fechada na Fase 10 (Decreto 12.174/2024, art. 2º, conferido no Planalto); P10 atualizada (DFDs chegaram, mas nenhum do processo do par 117/2025).

## Especificação reconstruída (leia antes de revisar M06 a M10)

O texto original do prompt não está disponível nesta sessão (o `attachment.txt` de 22/10/2026 é a lista de tarefas). As colunas abaixo e a lista de achados da seção 5 foram reconstruídas do registro das Fases 0 a 3; confirme ou corrija (P23).

- M06: `bloco_tr`, `secao`, `campos_etp`, `variaveis`, `perguntas_wz`, `classe_origem`, `regra_derivacao`, `teste_par_117`, `evidencia_par_117`, `teste_caso_67_23`, `evidencia_caso_67_23`, `fonte`, `status`.
- M07: `id` (NRM-xxx, estável pela `chave`), `chave`, `norma`, `tipo`, `numero`, `ano`, `orgao`, `dispositivos_citados`, `formas_citadas`, `onde_citada`, `n_citacoes`, `origem` (MODELO_AGU, NOTA_AGU, CORPUS, CHECKLIST, MATRIZ), `situacao` (VIGENTE, REVOGADA, NAO_CONFERIDA), `verificacao` (URL e data), `fonte`, `status`.
- M08: `id` (SET-xx), `tema`, `documento`, `origem_checklist`, `condicao`, `condicao_expr`, `ponto_insercao`, `texto_proposto`, `variaveis`, `perguntas_wz`, `base_no_modelo`, `evidencia_corpus`, `observacao`, `fonte`, `status`.
- M09: `id` (DV-xx), `documento`, `local`, `tipo`, `descricao`, `referencia`, `tratamento_no_sistema`, `achado`, `fonte`, `status`.
- M10: `id` (VAL-xxx), `regra`, `tipo` (BLOQUEIO, ALERTA, INFORMATIVO), `momento`, `condicao`, `condicao_expr`, `mensagem`, `afeta`, `base`, `achado`, `fonte`, `status`.
- M11 (pedida em 22/10/2026): as colunas da tarefa 2, mais `orientacao` (texto literal das instruções da pergunta).
- Achados da seção 5 usados no teste 8: 1 notas do modelo ausentes na matriz 01; 2 arquivo-fonte e linhas da matriz 01; 3 estimativas na matriz 01; 4 ETP 19/2026 incompleto; 5 pares ETP e TR e processos em branco; 6 normas do regime anterior; 7 TRs sobre versões anteriores do modelo; 8 validade de 50% e 75%; 9 participante de IRP; 10 seção 12 do ETP.

## Convenções

- O CSV é a fonte; o xlsx é cópia. UTF-8 com BOM, vírgula, todo campo entre aspas.
- Toda linha tem `fonte` e `status` (`EXTRAIDO`, `INFERIDO`, `A_VERIFICAR`).
- IDs: `ETP-SS.CC`, `TR-<numeração do modelo>`, `NE-001`, `WZ-01`, `VAR-001`, `NRM-001`, `SET-01`, `DV-01`, `VAL-001`, `CK-C-14.2` (checklist de consumo) e `CK-P-13.1` (permanentes; `CAB.xx` para o cabeçalho). Blocos tirados de nota: `TR-NE016.01`. IDs nunca são reaproveitados; o M07 mantém o ID pela chave da norma.
- Nenhum nome de pessoa nem endereço do corpus nas matrizes; onde precisaria, vai o cargo ou `[RESPONSÁVEL]`.
- Norma só é citada se estiver na base (modelo, notas, corpus ou checklist) ou se tiver sido conferida em planalto.gov.br, in.gov.br ou gov.br. Situação no M07: NAO_CONFERIDA 73, REVOGADA 2, VIGENTE 29.

### JSON Logic

- Variáveis: `WZ_07` (resposta da WZ-07; MULTIPLA vira lista), `CK_C_10_1` e `CK_P_13_1` (resposta da pergunta do checklist com o texto literal da opção, ex.: "Sim"; MULTIPLA vira lista; texto da caixa de resposta em `CK_C_12_2_texto`), `VAR_001` (variável do M05), `itens` (lista de itens com os atributos do M05), metadados `textos_livres`, `importacao.*`, `checklist.*`, `parametros.*`.
- Operadores permitidos: `var`, `==`, `!=`, `!`, `!!`, `and`, `or`, `if`, `in`, `merge`, `some`, `none`, `<=`, `>`.
- Fora da lista, só em `M04.calculo_expr` e `M05.calculo_expr` (P31): `reduce`, `+`, `*`, `-`, `/`, `%`.
- Contexto de item: cada elemento de `itens` traz os atributos do M05 e também as variáveis globais (`WZ_`, `CK_`, `VAR_`, `parametros` e metadados); em pergunta do checklist com `por_item = S`, `CK_x_n` dentro do item é a resposta ligada àquele item (ausente se o item não foi indicado). Assim `some` e `none` podem comparar atributo de item com parâmetro. Nas expressões avaliadas por item (`M05.calculo_expr` de `tabela_itens.*` e destinos `itens.<atributo>` do M11) o item é o topo, e `itens_do_grupo` é a lista dos itens com o mesmo rótulo de grupo (ou só o item).
- Em `reduce`, o passo lê `current.<atributo>` e `accumulator`. Dentro de `some` ou `none` sobre uma lista de textos (ex.: `VAR_085` na VAL-029), `{"var": ""}` é o próprio elemento.
- `parametros.<nome>`: valor da linha do M12 com esse `nome`.
- `liga_expr` e `desliga_expr` devolvem a lista de blocos: `{"merge": [{"if": [condição, [IDs], []]}, ...]}`.
- `M02.condicao_expr`: alguma condição que liga E nenhuma que desliga (bloco condicional); nenhuma que desliga (demais); `false` nos separadores 'OU' e nos blocos que não entram na minuta.

### Colunas da Fase 10

- `M04.depende_de_expr`: verdadeira quando a pergunta deve ser feita. 'X diferente de V' é `!=` literal (pergunta anterior sem resposta conta como diferente). Trecho 'VAR-011 (...)' é dependência de dado, não condição.
- `M04.calculo_expr`: valor das perguntas derivadas (WZ-09, 13, 18, 20, 24, 50); `null` quando não se aplica.
- `M05.calculo_expr`: valor do atributo ou da variável; `M05.calculo_ordem`: ordem de cálculo (um cálculo só lê atributo já calculado). Linha `tabela_itens.*` é avaliada item a item.
- `M11.condicional_expr`: quando a pergunta do checklist deve ser respondida.
- `M11.preenche_expr` e `M11.sugere_expr`: objeto `{destino: expressão}`, destino `WZ_xx`, `VAR_xxx` ou `itens.<atributo>`. Só são avaliadas com a pergunta respondida e a condicional verdadeira; resultado `null` não conta. PREENCHE não sobrescreve o que o usuário já respondeu; duas perguntas que preenchem a mesma WZ com valores diferentes deixam a WZ sem resposta e o conflito aparece para a equipe. Destino `VAR_xxx` com várias contribuições: TEXTO junta em linhas, LISTA e TABELA juntam em lista, NUMERO fica com a primeira e acusa conflito se outra for diferente; cada contribuição guarda o ID da pergunta. SUGERE só mostra.
- Ordem de avaliação usada no simulador (sugestão para o motor): entrada; M11 (preenche, na ordem das linhas); M05 por `calculo_ordem`; M04 `calculo_expr`; M04 `depende_de_expr`; M02, M04 liga/desliga, M08 e M10.
- `M12_parametros.csv`: `id` (PAR-01), `nome`, `valor`, `unidade`, `base`, `vigencia`, `usado_em`, `fonte`, `status`.

### Cenários (`cenarios/`)

- C1 a C8: gerados pelo `f10_simulador.py` (implementação independente do motor). `entrada` tem `wizard`, `checklist`, `itens` (com `respostas_por_item` quando a pergunta é por item), `variaveis` e `metadados`, todos fictícios. `esperado` tem `blocos` (M02, na ordem), `clausulas_m08`, `validacoes_m10` e `perguntas_sem_resposta`. O esperado vem do caminho do texto (liga/desliga e depende_de em texto, derivadas em Python); o teste reproduz pelo caminho das expressões. `referencia` é informativa.
- R1 (TR 23/2026) e R2 (TR 58/2026): entrada anonimizada com as respostas tiradas do TR real (`origem_das_respostas`), itens fictícios, blocos que o TR real contém, `divergencias_conhecidas` ligadas ao M09 e, em `referencia.diferencas_simulacao`, o que a simulação monta a mais ou a menos que o TR real.

## Checklists técnicos

Versões mapeadas no M11 (qualquer mudança no checklist exige refazer o M11; ver P30 e VAL-036):

- `Checklists/Checklist_Tecnico_Aquisicao_de_Materiais_Permanentes_em_Saude_ATUALIZADO_SEM_19_3__2_.docx`: SHA-256 `7c6d3cc9bf1632f2ccb6e52eb893c9c94db6b1d278c4755dff4bf8fd17e85d1d`
- `Checklists/Checklist_Tecnico_Medicamentos_e_Materiais_de_Consumo_em_Saude_REVISAO__1_.docx`: SHA-256 `6294e718c983c3990fbdea3a567a22fbe305db798e9a6df0ba8cef35dd679b99`

Divisão de trabalho: o checklist traz os fatos técnicos (M11); o wizard fica com as decisões jurídicas (M04, `DECISAO_JURIDICA`). A tabela de atributos de item por checklist está em `sugestoes_checklist.md`.

## Testes de aceite (Fases 9 e 10)

Resultado completo em `logs/f9_testes.txt`. FALHAS: 0.

- teste 3: M01 com 24 IDs únicos e no padrão
- teste 3: M02 com 499 IDs únicos e no padrão
- teste 3: M03 com 102 IDs únicos e no padrão
- teste 3: M04 com 59 IDs únicos e no padrão
- teste 3: M05 com 159 IDs únicos e no padrão
- teste 3: M06 com 499 IDs únicos e no padrão
- teste 3: M07 com 104 IDs únicos e no padrão
- teste 3: M08 com 22 IDs únicos e no padrão
- teste 3: M09 com 34 IDs únicos e no padrão
- teste 3: M10 com 50 IDs únicos e no padrão
- teste 3: M11 com 276 IDs únicos e no padrão
- teste 3: M12 com 12 IDs únicos e no padrão
- teste 3: referências cruzadas entre M00 e M11: 0 quebradas
- teste 1: 556 de 556 parágrafos não vazios do modelo em exatamente um bloco do M02 (100.00%); blocos tirados das notas (TR-NE*) fora da conta: 9
- teste 2: 102 notas (NE-001 a NE-102) ligadas a bloco existente do M02
- teste 4: normas citadas de M00 a M11 presentes no M07 (104 normas): 0 faltando
- teste 4: norma citada só em texto das matrizes, sem base nem conferência: 0
- teste 5: fonte e status preenchidos e no domínio nas 1863 linhas de M00 a M11
- teste 6: incisos obrigatórios no M01 = ['I', 'IV', 'VI', 'VIII', 'XIII']
- teste 7: nomes de pessoas nos arquivos de saída: 0 (nomes de pessoas identificados no corpus: 46; sobrenomes distintivos: 73)
- teste 8: achados da seção 5 (lista reconstruída, 10) no M09 ou no M10: 1=1, 2=2, 3=2, 4=2, 5=4, 6=6, 7=1, 8=3, 9=2, 10=1

Outras conferências:

- M07: status A_VERIFICAR só em norma não conferida
- M04: colunas de domínio fechado no domínio
- M03: colunas de domínio fechado no domínio
- M05: colunas de domínio fechado no domínio
- M07: colunas de domínio fechado no domínio
- M08: colunas de domínio fechado no domínio
- M10: colunas de domínio fechado no domínio
- M11: colunas de domínio fechado no domínio
- M06: colunas de domínio fechado no domínio
- M06: uma linha por bloco do M02 (499 de 499)
- M11: toda pergunta tem destino ou é SO_CONTROLE com motivo na regra
- M11: hash dos dois checklists da base confere com o registrado nas linhas: Checklist_Tecnico_Aquisicao_de_Materiais... 7c6d3cc9bf16; Checklist_Tecnico_Medicamentos_e_Materia... 6294e718c983
- JSON Logic: 949 expressões em todas as colunas *_expr, JSON válido, só operadores permitidos e variáveis conhecidas (parametros.* no M12)
- operadores fora da lista só em M04.calculo_expr e M05.calculo_expr e registrados na P31: ['%', '*', '+', '-', '/', 'reduce']
- nenhum número de lei ou valor monetário dentro de expressão (números só 0 e 1 de contagem e opção literal do checklist; textos com dígito só se forem opção)
- M04: depende_de_expr preenchida exatamente nas perguntas com condição em depende_de
- M04: calculo_expr nas 6 derivadas: ['WZ-09', 'WZ-13', 'WZ-18', 'WZ-20', 'WZ-24', 'WZ-50']
- M11: preenche_expr só em PREENCHE, sugere_expr só em SUGERE, condicional_expr em toda condicional (61)
- M05: calculo_expr em 9 variáveis, ordem única e cada cálculo só lê atributo já calculado
- M05: atributos de item catmat, quantidade, valor_unitario e numero presentes (achado do compilador)
- M12: 12 parâmetros com fonte e status, todos usados por alguma regra
- VAL-029: some sobre a VAR_085 (lista) acha 'período mínimo' e 'últimos', com e sem inicial maiúscula, em cada item; 7 casos
- PAR-05: valor numérico (30) com unidade 'dias corridos'
- cenarios/: 8 cenários de ouro e 2 casos de reprodução com entrada e esperado completos, IDs existentes e DV-xx do M09
- simulador pelas colunas novas reproduz os 8 cenários (blocos, M08, M10 e perguntas sem resposta)
- controle negativo das colunas novas: 4 erros injetados (depende_de_expr, M05.calculo_expr, preenche_expr, M04.calculo_expr), detectados 4
- números de processo trocados por PROC-xx no M00, no perguntas_abertas.md e nos scripts; entradas dos cenários sem número de processo nem UASG
- VAL-033: mensagem ao usuário sem 'ETP-SS.CC'
- README: lista de operadores igual à da Fase 10 (14 operadores)
- M02: condicao_expr preenchida em todos os blocos (499)
- M08: 23 trechos de evidência conferidos letra a letra no texto do corpus
- travessão (U+2014) fora das colunas literais e nos .md: 0
- simulação do wizard: 8 cenários, TOTAL DE PROBLEMAS: 0
- controle negativo da simulação: 3 erros injetados (condição de bloco, liga_expr, cláusula setorial), detectados 3

## Perguntas que dependem de você

- P09. Gerenciador da IRP 134/2025 (ABERTA)
- P10. DFD do processo do par 117/2025 (ABERTA)
- P19. Seção adicional do ETP, "Justificativas pontuais" (ABERTA)
- P23. Especificação das matrizes M06 a M10 e achados da seção 5 (ABERTA)
- P24. Comodato numa aquisição (ABERTA)
- P25. Atestado que exige "garantia mínima de 12 meses prestada" (ABERTA)
- P26. Leitura por máquina do checklist preenchido no Word (ABERTA, depende da revisão do checklist)
- P28. Lista de classes de TIC para o alerta de escopo (ABERTA)

## Revisão no xlsx

Preencha `validacao` (OK, CORRIGIR ou DUVIDA) e `comentario_validacao` nas abas M03 e M04 e devolva a planilha. O script `importar_validacao.py` leva só essas duas colunas para os CSV, pelo ID, e lista as linhas CORRIGIR e DUVIDA; as correções são feitas nos geradores, e as colunas de revisão são preservadas quando as matrizes são regeneradas.

## Como regenerar

Python 3 com openpyxl; Tesseract com o idioma `por` só na Fase 0. Rode sempre com `python3 -I`. `DOC` é `Licita+/Documentos`, `OUT` é `Licita+/Matrizes_v1`, `T` é uma pasta de trabalho fora da entrega, e `MODELO` é `DOC/TR exemplos/modelo-de-termo-de-referencia-compras-lei-no-14-133-dez-25.docx`.

```
# Fase 0
python3 -I scripts/f0_extrair_texto.py DOC T/text TESSDATA
python3 -I scripts/f0_docx_modelo.py MODELO T/modelo_estrutura.json
python3 -I scripts/f0_inventario_apoio.py DOC T/text T/modelo_estrutura.json OUT/logs/f0_conferencias.txt
python3 -I scripts/f0_gerar_M00.py DOC T/text/_extracao.json OUT
# Fases 1 e 2 (estrutura do modelo e corpus de ETPs)
python3 -I scripts/f1_modelo_estrutura.py MODELO T/f1_modelo.json
python3 -I scripts/f1_blocos.py T/f1_modelo.json T/f1_blocos.json
python3 -I scripts/f2_corpus_etp.py T/text T/f2_corpus_etp.json
# Checklists (leitura estrutural dos docx)
python3 -I scripts/ck_ler.py "DOC/Checklists/<consumo>.docx" T/ck/ck_C.json
python3 -I scripts/ck_ler.py "DOC/Checklists/<permanentes>.docx" T/ck/ck_P.json
# Fase 6, comparação dos TRs 23/2026 e 58/2026 com o modelo (alguns minutos; só se o M02 mudar)
python3 -I scripts/f6_comparar_trs.py OUT/M02_tr_blocos.csv T/text/<TR 23/2026> T/text/<TR 58/2026> T/f6_comparacao.json
# Todas as matrizes, na ordem das dependências, testes incluídos
sh scripts/rodar_fases_4_9.sh T DOC OUT
# Fase 10, uma vez: números de processo (a correspondência fica fora do pacote)
python3 -I scripts/f10_proc.py OUT FORA_DO_PACOTE/correspondencia_processos.csv scripts/f0_gerar_M00.py scripts/f9_testes.py
python3 -I scripts/gerar_readme.py OUT DOC
```
