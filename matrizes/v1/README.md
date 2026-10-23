# Licita+ | Matrizes v1

Estado em 23/10/2026: Fases 0 a 13 concluídas. A Fase 13 resolve o texto da minuta: cada marcador do M02 ligado ao que o preenche (`lacunas_mapa`), tabelas montadas a partir dos itens (`tabela_colunas`), ponto e numeração das cláusulas do M08, fim do 'Sim'/'Não' copiado para campos de texto e revisão do checklist que só destaca a falta de resposta. A Fase 12 libera a garantia já prestada nos atestados (P25), estende a leitura do número a todos os 'Outro' de prazo e de garantia (P32) e passa a tomar a validação do M03 e do M04 do repositório (P33). A Fase 11 leva para as matrizes o lote 1 de respostas (decisão 0008), a decisão de não mudar o checklist distribuído (decisão 0009) e as regras do simulador alinhadas ao motor (Marco 1). Na Fase 10 as regras que o motor executa ficaram todas em JSON Logic (dependências do wizard, condições e preenchimento do checklist, atributos calculados), com os parâmetros no M12 e os cenários de ouro e de reprodução em `cenarios/`. Antes, na mesma data, a tarefa extra da Fase 10 conferiu o M07 com o repositório auxiliar ctresb/leis e fechou a P16.

## Arquivos

| Arquivo | Conteúdo | Linhas |
|---|---|---|
| `M00_inventario.csv` | inventário dos documentos da base (DFDs, ETPs, TRs, checklists, modelo, matrizes rascunho) | 23 |
| `M01_etp_campos.csv` | campos do ETP Digital, com inciso do art. 18, obrigatoriedade e situação no corpus | 24 |
| `M02_tr_blocos.csv` | blocos do modelo AGU de TR (DEZ/2025), com texto literal, formatação, condição em texto e em JSON Logic | 499 |
| `M03_notas_explicativas.csv` | as 102 notas explicativas do modelo, com regra derivada, perguntas e regras afetadas e colunas de revisão | 102 |
| `M04_wizard.csv` | decisões do wizard (jurídicas e derivadas dos itens), perguntas do checklist que as pré-preenchem, liga/desliga em texto e em JSON Logic, colunas de revisão | 60 |
| `M05_variaveis.csv` | variáveis de entrada e atributos de item, com origem, validação e onde são usadas | 176 |
| `M06_derivacao_etp_tr.csv` | derivação ETP para TR por bloco, com o teste no par 117/2025 e o caso 67/2026 x 23/2026 | 499 |
| `M07_normas.csv` | normas e orientações citadas nas matrizes, com origem e situação conferida quando possível | 104 |
| `M08_clausulas_setoriais.csv` | cláusulas setoriais de saúde que o modelo não traz, com fonte no checklist e evidência no corpus | 23 |
| `M09_desvios.csv` | desvios encontrados nos documentos da base e nas matrizes rascunho, com o tratamento no sistema | 35 |
| `M10_validacoes.csv` | validações e alertas, com condição em JSON Logic quando cabe | 53 |
| `M11_checklist.csv` | uma linha por pergunta dos dois checklists técnicos, com tipo, condicional, destino e efeito, e as mesmas regras em JSON Logic | 285 |
| `M12_parametros.csv` | valores numéricos, limites e marcadores usados pelas regras, com base, vigência e onde são usados | 13 |
| `matrizes_v1.xlsx` | cópia de leitura e revisão: aba LEIA_ME e uma aba por CSV; colunas de revisão em amarelo no M03 e no M04 | |
| `cenarios/` | cenários de ouro C1 a C8 (8) e casos de reprodução R1 e R2 (2) em JSON, com entrada e esperado | |
| `perguntas_abertas.md` | decisões pendentes e adotadas, P01 a P36 | |
| `sugestoes_checklist.md` | lacunas, duplicidades e ambiguidades dos checklists, com redação proposta | |
| `auditoria_matrizes_01_02.md` | auditoria das matrizes rascunho 01 e 02 (Fase 8) | |
| `log_fase10_repo_leis.md` | arquivos do repositório auxiliar ctresb/leis (commit 15eb09b) cruzados com o M07 e uso de cada um | |
| `logs/` | conferências, cobertura do checklist, comparação dos TRs, expressões, simulação, normas, testes | |
| `scripts/` | scripts de análise que geram tudo acima | |

## O que mudou na Fase 13

- M02: colunas `lacunas_mapa` (106 blocos, todo marcador na ordem do texto) e `tabela_colunas` (TR-1.1.TAB1, TR-1.1.1.TAB1 a TAB3, TR-5.2.TAB1), com a linha da cota reservada e o orçamento sigiloso (NE-004). Formato na seção 'Texto da minuta'.
- M05: VAR-163 a VAR-176 (unidade da vigência, desdobramento de VAR-050, VAR-054, VAR-093 e VAR-096, colunas da tabela do item 1.1 com quantidade principal e valores da linha e da cota); campos das tabelas VAR-029, VAR-051, VAR-062, VAR-071, VAR-079 e VAR-091 na descrição; domínio da VAR-081. VAR-160 só calcula com VAR-057.
- M11: as 65 perguntas Sim/Não que copiavam a opção para variável de texto, tabela, lista ou número agora levam o texto da caixa 'Resposta:' (`CK_x_texto`, 50), só ligam condição (11) ou deixam a variável para a equipe (4); várias perguntas na mesma variável se acumulam, sem prevalência. Coluna `revisao_pergunta_expr`: a pergunta ao operador e o bloqueio só com dúvida que muda a minuta; falta de resposta só destaca (P34).
- M08: colunas `inserir_apos`, `nivel` e `inserir_apos_alternativo`.
- Simulador: monta o texto (`f13_texto.py`); cada cenário ganhou `esperado.texto_sem_lacuna` e `referencia.texto_montado`/`lacunas_do_texto`. VAL-037 descrita pela pergunta que bloqueia.
- Busca de nomes volta a incluir `validacao` e `comentario_validacao`.

## O que mudou na Fase 12

- P25: WZ-60 nova (atestado com garantia já prestada, só com ATESTADOS na WZ-38), SET-23, VAR-161 (prazo em meses), VAR-162 (justificativa no ETP), VAL-052 e VAL-053 (bloqueios), PAR-13 (12 meses). A VAL-029 barra 'últimos' e 'período mínimo' sem tratar de garantia; não barra a duração da garantia prestada.
- P32.1: CK-C-16.3, CK-P-19.5, CK-P-19.3, CK-P-13.7 e CK-P-13.1 leem o número do 'Outro' (`CK_x_numero`), com destaque e pergunta ao operador; '30 dias' corridos na CK-P-19.3 não vira dias úteis.
- Validação: `validacao` e `comentario_validacao` do M03 e do M04 vêm do repositório (4º argumento do `rodar_fases_4_9.sh`, `f12_validacao_repo.py`) e o teste confere linha a linha (P33).

## O que mudou na Fase 11

- M11: colunas `leitura`, `revisao_expr` e `revisao_pergunta` (260 expressões de revisão, 75 perguntas ao operador) e 9 complementos do operador (CK-X-01 a CK-X-09). As perguntas 10.1 a 10.11 do consumo (comodato) passaram a só controle.
- M12: coluna `tipo` (numero, lista ou texto), que passa a ser a fonte do tipo; a frase 'Tipo do valor' na fonte continua. PAR-03 corrigido: cita a VAR-160, que agora existe (cota calculada).
- Cota zero (decisão 0008): VAR-160 nova, VAR-113 e VAR-118 refeitas sem ciclo (ordem 4, 5 e 6) e VAL-051 nova.
- Comodato fora do sistema (P24): WZ-56, SET-01 e VAL-027 com expressão `false` e o motivo no texto ('DESLIGADA').
- VAL-001 só com as perguntas 15.3 e 15.5 do checklist de permanentes (P28). ETP-90.01 opcional, sem texto padrão (P19). DV-35 nova (TR 23/2026, blocos de cota sem cota), ligada ao R1.
- M02: coluna `grupo_ativo_expr` (quando um grupo de alternativas vale), usada pela regra de exatamente uma opção.
- Simulador com as regras do motor: valor ausente, filho sem pai, grupo de alternativas, igualdade estrita, falso e conta em decimal exato (seção 'Regras do simulador'). Cenários reemitidos; `esperado` ganhou `bloqueios_grupo_alternativas`.

## O que mudou na Fase 10

- `M04.depende_de_expr` em 26 de 60 perguntas (vazia quando a pergunta vale sempre ou só depende de dado dos itens) e `M04.calculo_expr` nas 6 perguntas derivadas dos itens.
- `M05.calculo_expr` e `M05.calculo_ordem` em 13 variáveis (VAR-031, VAR-049, VAR-065, VAR-111, VAR-113, VAR-116, VAR-118, VAR-119, VAR-154, VAR-160, VAR-174, VAR-175, VAR-176). Linhas novas: VAR-156 `numero`, VAR-157 `catmat`, VAR-158 `quantidade` e VAR-159 `valor_unitario` (atributos de item que as regras já usavam).
- `M11.condicional_expr` em 70 perguntas, `preenche_expr` em 150 e `sugere_expr` em 38. O que a regra do M11 não permite traduzir ficou sem expressão e está listado em `logs/f10_expr.txt` (P31).
- `M12_parametros.csv` com 13 parâmetros: nenhuma expressão traz número de lei ou valor monetário.
- M10: literais trocados por `parametros.*` (VAL-004, 017, 020, 025, 026) e por `VAR_099` (VAL-032); mensagem da VAL-033 reescrita sem o padrão de ID.
- Números de processo do corpus trocados por PROC-01 a PROC-12 no M00, no `perguntas_abertas.md` e nos scripts; a correspondência ficou fora do pacote.
- Convenções novas e operadores fora da lista: P31.

## O que mudou da Fase 3 à Fase 9

- Ajuste 1: o item virou entidade (VAR-011 com as colunas VAR-112 a VAR-124 e VAR-153 a VAR-155). Tratamento de ME/EPP calculado pelo valor do item ou do grupo; WZ-09, WZ-13, WZ-18, WZ-20, WZ-24 e WZ-50 são derivadas dos itens. Cenário misto C6 na simulação.
- Checklists técnicos como entrada do sistema: M11 com 285 perguntas (131 de consumo, 145 de permanentes); efeito: PREENCHE 165, JUSTIFICA 47, SUGERE 42, SO_CONTROLE 21, ALERTA 10.
- M04: 60 perguntas. A coluna `pre_preenchida_por` mostra 17 respondidas ou sugeridas pelo checklist, 6 derivadas dos itens e 37 marcadas `DECISAO_JURIDICA` (equipe administrativa). WZ-56 a WZ-59 são novas (comodato, validade excepcional, desinstalação, fabricante ou rede credenciada).
- M05: 176 variáveis; origem: WIZARD 84, CHECKLIST 53, SISTEMA 26, DFD 8, PESQUISA_PRECOS 5. CHECKLIST entrou no domínio de origem (P29).
- Condições em JSON Logic: `M02.condicao_expr`, `M04.liga_expr` e `M04.desliga_expr`, `M08.condicao_expr` e `M10.condicao_expr`. O texto livre continua como comentário. O que não coube está na P27.
- Colunas `validacao` e `comentario_validacao` no M03 e no M04, vazias, para a sua revisão no xlsx.
- P17 e P21 resolvidas; P16 fechada na Fase 10 (Decreto 12.174/2024, art. 2º, conferido no Planalto); P10 atualizada (DFDs chegaram, mas nenhum do processo do par 117/2025).

## Especificação das matrizes M06 a M10 (oficial desde 23/10/2026)

Reconstruída do registro das Fases 0 a 3, porque o prompt original não estava disponível; o gestor fechou a P23 e esta especificação passou a ser a oficial.

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
- `M12_parametros.csv`: `id` (PAR-01), `nome`, `valor`, `tipo` (numero, lista ou texto; a coluna é a fonte do tipo), `unidade`, `base`, `vigencia`, `usado_em`, `fonte`, `status`.
- `M02.grupo_ativo_expr`: nas linhas com `grupo_alternativa`, quando o grupo vale (mesmo valor em todo o grupo).
- Condição desligada: `false` na coluna `_expr`, com o texto da linha começando por 'DESLIGADA' e o motivo.

### Colunas da Fase 11 no M11 e complementos do operador

- `leitura`: como ler a resposta do Word e qual prevalece em duplicidade (texto).
- `revisao_expr`: JSON Logic, só com operadores gerais; verdadeira = resposta destacada para o operador revisar. Avaliada no fim, com os mesmos dados das validações do M10. Usa os metadados de leitura `checklist.marcas_multiplas`, `checklist.resposta_unica_por_item` e `checklist.divergencias_leitura` e o número `CK_x_numero` lido do 'Outro' do prazo (P32).
- `revisao_pergunta`: pergunta que o sistema faz ao operador quando a dúvida muda a minuta; vazia quando basta o destaque.
- `revisao_pergunta_expr` (Fase 13): JSON Logic; verdadeira = a `revisao_pergunta` é feita e a minuta fica bloqueada até a resposta (VAL-037). Só duas marcas em pergunta de uma opção, 'Outro' sem número legível, resposta única para vários itens e as dúvidas específicas (S09). Pergunta sem resposta só fica destacada (`revisao_expr`); quando ela decide bloco, já aparece como pergunta pendente do wizard.
- Complementos do operador: linhas `CK-X-nn` (dois dígitos, a partir de 01), `checklist = COMPLEMENTO`, seção 'COMPLEMENTO DO OPERADOR', número `X.nn`, variável `CK_X_nn`. Preenchidos no sistema, não existem no Word; ligados às mesmas variáveis e destinos das perguntas do checklist; sem opção pré-definida que não venha de norma ou de domínio do M05.

### Texto da minuta (Fase 13)

- `M02.lacunas_mapa`: lista JSON, na ordem do texto, uma entrada por marcador da coluna `lacunas`: `marcador`, `ocorrencia` (qual ocorrência no `texto_literal`, contada sem sobreposição), `fonte` (VAR_xxx, WZ_xx, CK_..., itens.atributo ou null) e, quando precisa, `acao`, `campo`, `indice`, `formato`, `unidade`, `texto`, `opcoes`, `grupo`, `quando`, `remove_antes`, `se_falso`, `estende_desde`, `estende_ate`, `lista_blocos`, `juntar_restante`, `se_vazio` e `comentario`. Definição de cada chave no cabeçalho do `scripts/f13_lacunas.py`.
- Ações: PREENCHER (padrão), ESCOLHA (fica a opção do modelo cuja condição é verdadeira; marcadores do mesmo `grupo` viram um trecho só, com os ' OU ' do meio), OPCIONAL (o trecho entra ou sai), TABELA (montada pela `tabela_colunas`), REMOVER (instrução do modelo), MANTER (assinatura ou campo do fornecedor) e EQUIPE (fonte null, motivo no `comentario`).
- Formatos: TEXTO, NUMERO_EXTENSO ('30 (trinta)'), PERCENTUAL_EXTENSO ('5% (cinco por cento)'), PERCENTUAL_2 ('25,00%'), MOEDA ('R$ 1.234,56'), MOEDA_POR_EXTENSO, DATA, DIA, MES_EXTENSO, ANO, LISTA_TEXTO ('a, b e c'), LISTA_LINHAS, MINUSCULA, INICIAL_MINUSCULA, ITEM ('item 2') e POR_ITEM ('item 1: valor; item 3: valor').
- Cláusula do M08 com a mesma variável em mais de um marcador fica com lacuna nesses marcadores (P36); cláusula PREENCHE_BLOCO não entra como texto, preenche o bloco.
- Séries de blocos-lista (`lista_blocos`, ex.: TR-4.1.1 a TR-4.1.3): cada bloco recebe um elemento; bloco sem elemento sai; o último presente termina em '.', o anterior em '; e', os demais em ';'; o último bloco do modelo junta os elementos que sobram.
- `M02.tabela_colunas`: JSON com `linhas` (itens ou a VAR da tabela), `colunas` (cabeçalho do modelo e o que preenche), `orcamento_sigiloso` e, no TR-1.1.TAB1, `linha_cota` (quando entra, onde e com quais valores) e a numeração das linhas.
- `M08.inserir_apos` (bloco do M02 depois do qual a cláusula entra, com os subitens dele), `M08.nivel` (MESMO_NIVEL: item seguinte no nível do bloco; SUBITEM: último subitem do bloco; PREENCHE_BLOCO: preenche as lacunas do bloco) e `M08.inserir_apos_alternativo` ('bloco (nivel)', em ordem, quando o bloco pode faltar). Várias cláusulas no mesmo ponto entram na ordem do M08.
- Valor ausente vira lacuna marcada (`[[LACUNA ...]]`); o texto nunca recebe 'Sim' ou 'Não' de resposta do checklist.

### Regras do simulador (as mesmas do motor, Marco 1)

- Valor ausente: conta (`+`, `-`, `*`, `/`, `%`) e comparação de ordem (`<=`, `>`) com valor ausente dão ausente (`null`), nunca 0; divisão por zero também. Item sem valor unitário fica sem valor da unidade e sem tratamento ME/EPP.
- Igualdade estrita: `==` e `!=` comparam tipo e valor ("30" é diferente de 30; 30 é igual a 30.0); `null` só é igual a `null`.
- Falso para `!`, `!!`, `if`, `and`, `or`, `some` e `none`: `null`, `false`, 0, "" e `[]`; o resto é verdadeiro.
- Conta exata: números convertidos para decimal pela forma escrita mais curta e somados e multiplicados em decimal.
- Filho sem o pai não entra: pai é o ID sem o último segmento numérico, de letra ou romano (TR-4.41.1 tem pai TR-4.41), quando esse ID existe no M02; vale em cascata, na ordem do M02.
- Grupo de alternativas ativo (`grupo_ativo_expr`): exatamente uma opção entra; nenhuma ou mais de uma vai para `bloqueios_grupo_alternativas`.

### Cenários (`cenarios/`)

- C1 a C8: gerados pelo `f10_simulador.py` (implementação independente do motor). `entrada` tem `wizard`, `checklist`, `itens` (com `respostas_por_item` quando a pergunta é por item), `variaveis` e `metadados`, todos fictícios. `esperado` tem `blocos` (M02, na ordem), `clausulas_m08`, `validacoes_m10`, `perguntas_sem_resposta`, `bloqueios_grupo_alternativas` e `texto_sem_lacuna` (Fase 13: blocos e cláusulas da minuta, na ordem, que saem sem nenhuma lacuna com as entradas do cenário, pela montagem do `f13_texto.py`). O esperado vem do caminho do texto (liga/desliga e depende_de em texto, derivadas em Python); o teste reproduz pelo caminho das expressões. `referencia` é informativa.
- R1 (TR 23/2026) e R2 (TR 58/2026): entrada anonimizada com as respostas tiradas do TR real (`origem_das_respostas`), itens fictícios, blocos que o TR real contém, `divergencias_conhecidas` ligadas ao M09 e, em `referencia.diferencas_simulacao`, o que a simulação monta a mais ou a menos que o TR real. Cada divergência traz `classificacao` ('TR real').

## Checklists técnicos

Versões mapeadas no M11 (qualquer mudança no checklist exige refazer o M11; ver P30 e VAL-036):

- `Checklists/Checklist_Tecnico_Aquisicao_de_Materiais_Permanentes_em_Saude_ATUALIZADO_SEM_19_3__2_.docx`: SHA-256 `7c6d3cc9bf1632f2ccb6e52eb893c9c94db6b1d278c4755dff4bf8fd17e85d1d`
- `Checklists/Checklist_Tecnico_Medicamentos_e_Materiais_de_Consumo_em_Saude_REVISAO__1_.docx`: SHA-256 `6294e718c983c3990fbdea3a567a22fbe305db798e9a6df0ba8cef35dd679b99`

Divisão de trabalho: o checklist traz os fatos técnicos (M11); o wizard fica com as decisões jurídicas (M04, `DECISAO_JURIDICA`). A tabela de atributos de item por checklist está em `sugestoes_checklist.md`.

## Testes de aceite (Fases 9 a 13)

Resultado completo em `logs/f9_testes.txt`. FALHAS: 0.

- teste 3: M01 com 24 IDs únicos e no padrão
- teste 3: M02 com 499 IDs únicos e no padrão
- teste 3: M03 com 102 IDs únicos e no padrão
- teste 3: M04 com 60 IDs únicos e no padrão
- teste 3: M05 com 176 IDs únicos e no padrão
- teste 3: M06 com 499 IDs únicos e no padrão
- teste 3: M07 com 104 IDs únicos e no padrão
- teste 3: M08 com 23 IDs únicos e no padrão
- teste 3: M09 com 35 IDs únicos e no padrão
- teste 3: M10 com 53 IDs únicos e no padrão
- teste 3: M11 com 285 IDs únicos e no padrão
- teste 3: M12 com 13 IDs únicos e no padrão
- teste 3: referências cruzadas entre M00 e M11: 0 quebradas
- teste 1: 556 de 556 parágrafos não vazios do modelo em exatamente um bloco do M02 (100.00%); blocos tirados das notas (TR-NE*) fora da conta: 9
- teste 2: 102 notas (NE-001 a NE-102) ligadas a bloco existente do M02
- teste 4: normas citadas de M00 a M11 presentes no M07 (104 normas): 0 faltando
- teste 4: norma citada só em texto das matrizes, sem base nem conferência: 0
- teste 5: fonte e status preenchidos e no domínio nas 1896 linhas de M00 a M11
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
- JSON Logic: 1426 expressões em todas as colunas *_expr, JSON válido, só operadores permitidos e variáveis conhecidas (parametros.* no M12)
- operadores fora da lista só em M04.calculo_expr e M05.calculo_expr e registrados na P31: ['%', '*', '+', '-', '/', 'reduce']
- nenhum número de lei ou valor monetário dentro de expressão (números só 0 e 1 de contagem e opção literal do checklist; textos com dígito só se forem opção)
- M04: depende_de_expr preenchida exatamente nas perguntas com condição em depende_de
- M04: calculo_expr nas 6 derivadas: ['WZ-09', 'WZ-13', 'WZ-18', 'WZ-20', 'WZ-24', 'WZ-50']
- M11: preenche_expr só em PREENCHE, sugere_expr só em SUGERE, condicional_expr em toda condicional (70)
- M05: calculo_expr em 13 variáveis, ordem única e cada cálculo só lê atributo já calculado
- M05: atributos de item catmat, quantidade, valor_unitario e numero presentes (achado do compilador)
- M12: 13 parâmetros com fonte e status, todos usados por alguma regra
- M11.revisao_expr: 260 expressões, 721 casos (cada uma dispara e não dispara)
- M11.revisao_expr só com operadores gerais (sem os de cálculo)
- M11: 9 complementos do operador (CK-X-01 a CK-X-09, checklist COMPLEMENTO), com condição e expressão
- comodato fora do sistema: CK-C-10.1 a 10.11 só controle; WZ-56, SET-01 e VAL-027 com expressão false e o motivo no texto
- cota zero: 3 x 25% dá cota 0, item em AMPLA e VAL-051 dispara; 9 x 25% dá cota 2, COTA e VAL-051 não dispara (AMPLA, COTA)
- valor ausente: item sem valor_unitario fica sem valor da unidade e sem tratamento ME/EPP (não vira EXCLUSIVO)
- conta exata no limite: 4 x 20.000,00 = limite dá EXCLUSIVO; 3 x 26.666,67 (80.000,01) não (['EXCLUSIVO', 'AMPLA'])
- M12: coluna tipo em todas as linhas (['lista', 'numero', 'texto'])
- M12: toda VAR citada na fonte e na base existe no M05 (['VAR-057', 'VAR-060', 'VAR-113', 'VAR-118', 'VAR-154', 'VAR-160'])
- VAL-029: some sobre a VAR_085 (lista) acha 'período mínimo' e 'últimos', com e sem inicial maiúscula, em cada item, sem barrar a duração da garantia já prestada (P25); 10 casos
- PAR-05: valor numérico (30) com unidade 'dias corridos'
- cenarios/: 8 cenários de ouro e 2 casos de reprodução com entrada e esperado completos, IDs existentes e DV-xx do M09
- simulador pelas colunas novas reproduz os 8 cenários (blocos, M08, M10 e perguntas sem resposta)
- controle negativo das colunas novas: 4 erros injetados (depende_de_expr, M05.calculo_expr, preenche_expr, M04.calculo_expr), detectados 4
- regras de montagem no simulador: com TR-1 desligado, 5 filhos saem; com duas opções no GA-01 (TR-1.3 ligado à força), bloqueio ['GA-01']
- números de processo trocados por PROC-xx no M00, no perguntas_abertas.md e nos scripts; entradas dos cenários sem número de processo nem UASG
- VAL-033: mensagem ao usuário sem 'ETP-SS.CC'
- README: lista de operadores igual à da Fase 10 (14 operadores)
- M02.lacunas_mapa em todos os 106 blocos com marcador (182 marcadores)
- M02.lacunas_mapa: todo marcador do texto_literal (coluna lacunas) aparece no mapa, na mesma ordem do texto e na mesma quantidade (ocorrência sem sobreposição)
- M02.lacunas_mapa: fonte existe (VAR, WZ, CK ou atributo de item), ação e formato conhecidos, fonte null só com ação e EQUIPE sempre com motivo, condições só com operadores gerais
- M02.tabela_colunas nas 5 tabelas que vêm dos itens ou de tabelas do wizard, com os cabeçalhos do modelo na ordem, fontes existentes, orçamento sigiloso (NE-004) e a linha de cota reservada com valor para cada coluna
- M08: inserir_apos é bloco do M02, nivel MESMO_NIVEL, SUBITEM ou PREENCHE_BLOCO, alternativo quando o bloco pode faltar, nada entre o TR-5.12 e o TR-5.14
- M11: nenhuma pergunta Sim/Não copia a opção para variável de texto, tabela, lista ou número (critério da Fase 13; antes, 65)
- M11.revisao_pergunta_expr: 75 perguntas que bloqueiam, 176 casos (pergunta sem resposta nunca bloqueia; duas marcas e dúvidas específicas bloqueiam); revisao_expr continua destacando em 260
- VAR-160: sem VAR-057 fica vazia (None); com 25% de 10 dá 2
- montagem do texto: 23 casos fixos (escolha, opcional, extenso, moeda, data, série de lista com pontuação, tabela com cota e com sigilo, lacuna sem unidade)
- cenários C1 a C8: esperado.texto_sem_lacuna em todos e nenhum texto da minuta com 'Sim' ou 'Não' vindo de resposta do checklist
- controle negativo: com a cópia antiga da CK-P-16.6 para a VAR-150, o teste de Sim/Não acusa o 'acompanhado de Sim' da SET-19 em algum cenário
- M02: condicao_expr preenchida em todos os blocos (499)
- M08: 25 trechos de evidência conferidos letra a letra no texto do corpus
- travessão (U+2014) fora das colunas literais e nos .md: 0
- simulação do wizard: 8 cenários, TOTAL DE PROBLEMAS: 0
- controle negativo da simulação: 3 erros injetados (condição de bloco, liga_expr, cláusula setorial), detectados 3
- validacao e comentario_validacao do M03 e do M04 iguais aos do repositório (10 linhas validadas lá)

## Perguntas que dependem de você

- P09. Gerenciador da IRP 134/2025 (ABERTA)
- P26. Leitura por máquina do checklist preenchido no Word (ABERTA para o Marco 2; checklist congelado, decisão 0009)
- P35. Numeração da linha de cota reservada na tabela do item 1.1 (ABERTA)
- P36. Marcadores do texto das cláusulas do M08 (ABERTA)

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
sh scripts/rodar_fases_4_9.sh T DOC OUT REPO/matrizes/v1
# Fase 10, uma vez: números de processo (a correspondência fica fora do pacote)
python3 -I scripts/f10_proc.py OUT FORA_DO_PACOTE/correspondencia_processos.csv scripts/f0_gerar_M00.py scripts/f9_testes.py
python3 -I scripts/gerar_readme.py OUT DOC
```
