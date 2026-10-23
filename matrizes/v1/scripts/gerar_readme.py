#!/usr/bin/env python3
"""Gera o README.md das Matrizes v1 com as contagens calculadas dos CSV e o resultado dos testes (logs/f9_testes.txt).

Uso: python3 -I gerar_readme.py <pasta_Matrizes_v1> <pasta_Documentos>
"""
import csv
import hashlib
import re
import sys
from collections import Counter
from pathlib import Path


def ler(p):
    return list(csv.DictReader(open(p, encoding="utf-8-sig")))


ARQ = [
    ("M00_inventario.csv", "inventário dos documentos da base (DFDs, ETPs, TRs, checklists, modelo, matrizes rascunho)"),
    ("M01_etp_campos.csv", "campos do ETP Digital, com inciso do art. 18, obrigatoriedade e situação no corpus"),
    ("M02_tr_blocos.csv", "blocos do modelo AGU de TR (DEZ/2025), com texto literal, formatação, condição em texto e em JSON Logic"),
    ("M03_notas_explicativas.csv", "as 102 notas explicativas do modelo, com regra derivada, perguntas e regras afetadas e colunas de revisão"),
    ("M04_wizard.csv", "decisões do wizard (jurídicas e derivadas dos itens), perguntas do checklist que as pré-preenchem, liga/desliga em texto e em JSON Logic, colunas de revisão"),
    ("M05_variaveis.csv", "variáveis de entrada e atributos de item, com origem, validação e onde são usadas"),
    ("M06_derivacao_etp_tr.csv", "derivação ETP para TR por bloco, com o teste no par 117/2025 e o caso 67/2026 x 23/2026"),
    ("M07_normas.csv", "normas e orientações citadas nas matrizes, com origem e situação conferida quando possível"),
    ("M08_clausulas_setoriais.csv", "cláusulas setoriais de saúde que o modelo não traz, com fonte no checklist e evidência no corpus"),
    ("M09_desvios.csv", "desvios encontrados nos documentos da base e nas matrizes rascunho, com o tratamento no sistema"),
    ("M10_validacoes.csv", "validações e alertas, com condição em JSON Logic quando cabe"),
    ("M11_checklist.csv", "uma linha por pergunta dos dois checklists técnicos, com tipo, condicional, destino e efeito, e as "
                          "mesmas regras em JSON Logic"),
    ("M12_parametros.csv", "valores numéricos, limites e marcadores usados pelas regras, com base, vigência e onde são usados"),
]


def main():
    pasta, docs = Path(sys.argv[1]), Path(sys.argv[2])
    n = {a: len(ler(pasta / a)) for a, _ in ARQ}
    m04 = ler(pasta / "M04_wizard.csv")
    m05 = ler(pasta / "M05_variaveis.csv")
    m11 = ler(pasta / "M11_checklist.csv")
    m07 = ler(pasta / "M07_normas.csv")
    dj = sum(1 for r in m04 if r["pre_preenchida_por"].startswith("DECISAO_JURIDICA"))
    deriv = sum(1 for r in m04 if r["pre_preenchida_por"].startswith("DERIVADA"))
    ck = len(m04) - dj - deriv
    hashes = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted((docs / "Checklists").glob("*.docx"))}
    testes = (pasta / "logs" / "f9_testes.txt").read_text(encoding="utf-8").splitlines()
    falhas = next((l for l in testes if l.startswith("FALHAS")), "FALHAS: ?")
    principais = [l for l in testes if l.startswith(("OK    teste", "FALHA teste"))]
    outros = [l for l in testes if l.startswith(("OK    ", "FALHA ")) and l not in principais and not l.endswith("entre aspas")]
    sit = Counter(r["situacao"] for r in m07)
    origem5 = Counter(r["origem"] for r in m05)
    efeito = Counter(r["efeito"] for r in m11)
    abertas = [l[4:] for l in (pasta / "perguntas_abertas.md").read_text(encoding="utf-8").splitlines()
               if l.startswith("### P") and "(ABERTA" in l]

    m12 = ler(pasta / "M12_parametros.csv")
    cen = sorted((pasta / "cenarios").glob("*.json"))
    n_c = sum(1 for f in cen if f.stem.startswith("C"))
    n_r = sum(1 for f in cen if f.stem.startswith("R"))
    dep = sum(1 for r in m04 if r["depende_de_expr"])
    calc5 = [r["id"] for r in m05 if r["calculo_expr"]]
    pre = sum(1 for r in m11 if r["preenche_expr"])
    sug = sum(1 for r in m11 if r["sugere_expr"])
    cnd = sum(1 for r in m11 if r["condicional_expr"])
    o = ["# Licita+ | Matrizes v1", "",
         "Estado em 23/10/2026: Fases 0 a 14 concluídas. A Fase 14 leva para as matrizes as respostas às P34 a P37 e à "
         "reprodução do R1 e do R2: cotas no fim da tabela de itens, mapa de marcadores no M08, valor padrão marcado, um "
         "texto por motivo de revisão e esperado do R1 e do R2 conferido nos TRs reais. A Fase 13 resolve o texto da minuta: cada marcador do M02 ligado "
         "ao que o preenche (`lacunas_mapa`), tabelas montadas a partir dos itens (`tabela_colunas`), ponto e numeração "
         "das cláusulas do M08, fim do 'Sim'/'Não' copiado para campos de texto e revisão do checklist que só destaca a "
         "falta de resposta. A Fase 12 libera a garantia já prestada nos atestados (P25), "
         "estende a leitura do número a todos os 'Outro' de prazo e de garantia (P32) e passa a tomar a validação do M03 e "
         "do M04 do repositório (P33). A Fase 11 leva para as matrizes o lote 1 de respostas (decisão "
         "0008), a decisão de não mudar o checklist distribuído (decisão 0009) e as regras do simulador alinhadas ao motor "
         "(Marco 1). Na Fase 10 as regras que o motor executa ficaram todas em JSON "
         "Logic (dependências do wizard, condições e preenchimento do checklist, atributos calculados), com os parâmetros "
         "no M12 e os cenários de ouro e de reprodução em `cenarios/`. Antes, na mesma data, a tarefa extra da Fase 10 "
         "conferiu o M07 com o repositório auxiliar ctresb/leis e fechou a P16.", "",
         "## Arquivos", "", "| Arquivo | Conteúdo | Linhas |", "|---|---|---|"]
    o += [f"| `{a}` | {d} | {n[a]} |" for a, d in ARQ]
    o += ["| `matrizes_v1.xlsx` | cópia de leitura e revisão: aba LEIA_ME e uma aba por CSV; colunas de revisão em amarelo no M03 e no M04 | |",
          f"| `cenarios/` | cenários de ouro C1 a C8 ({n_c}) e casos de reprodução R1 e R2 ({n_r}) em JSON, com entrada e esperado | |",
          "| `perguntas_abertas.md` | decisões pendentes e adotadas, P01 a P39 | |",
          "| `sugestoes_checklist.md` | lacunas, duplicidades e ambiguidades dos checklists, com redação proposta | |",
          "| `auditoria_matrizes_01_02.md` | auditoria das matrizes rascunho 01 e 02 (Fase 8) | |",
          "| `log_fase10_repo_leis.md` | arquivos do repositório auxiliar ctresb/leis (commit 15eb09b) cruzados com o M07 e uso de cada um | |",
          "| `logs/` | conferências, cobertura do checklist, comparação dos TRs, expressões, simulação, normas, testes | |",
          "| `scripts/` | scripts de análise que geram tudo acima | |", "",
          "## O que mudou na Fase 14", "",
          "- P35: no `tabela_colunas` do TR-1.1.TAB1, os itens ficam com o próprio número e as linhas de cota vão para o "
          "fim da tabela, com os números seguintes ao último item e 'Cota reservada para ME/EPP do item n'.",
          "- P36: coluna `M08.lacunas_mapa` (22 cláusulas, 57 marcadores), no formato do M02; quando a mesma VAR aparece em "
          "vários marcadores, cada um vai para a pergunta do checklist que dá aquela parte, e o resto fica com a equipe. "
          "Texto das cláusulas sem mudança.",
          "- P37: `padrao: true` nas opções que entram sem valor informado (TR-1.7 e TR-AI-3.1.8.1), listadas em "
          "`logs/f13_lacunas.txt`.",
          "- M11: coluna `revisao_motivos` (um texto por motivo: SEM_RESPOSTA, MARCAS_MULTIPLAS, OUTRO_ILEGIVEL, "
          "DIVERGENCIA, RESPOSTA_UNICA_POR_ITEM, CONTRADICAO, NOME_DE_PESSOA); as colunas de revisão anteriores viraram "
          "resumo dela.",
          "- Reprodução: DV-36 a DV-41 no M09; TR-1.4 só para consumo; no R1 e no R2, blocos que a comparação achou por "
          "engano saem do esperado (`correcoes_da_comparacao`).", "",
          "## O que mudou na Fase 13", "",
          "- M02: colunas `lacunas_mapa` (106 blocos, todo marcador na ordem do texto) e `tabela_colunas` (TR-1.1.TAB1, "
          "TR-1.1.1.TAB1 a TAB3, TR-5.2.TAB1), com a linha da cota reservada e o orçamento sigiloso (NE-004). Formato na "
          "seção 'Texto da minuta'.",
          "- M05: VAR-163 a VAR-176 (unidade da vigência, desdobramento de VAR-050, VAR-054, VAR-093 e VAR-096, colunas da "
          "tabela do item 1.1 com quantidade principal e valores da linha e da cota); campos das tabelas VAR-029, VAR-051, "
          "VAR-062, VAR-071, VAR-079 e VAR-091 na descrição; domínio da VAR-081. VAR-160 só calcula com VAR-057.",
          "- M11: as 65 perguntas Sim/Não que copiavam a opção para variável de texto, tabela, lista ou número agora "
          "levam o texto da caixa 'Resposta:' (`CK_x_texto`, 50), só ligam condição (11) ou deixam a variável para a equipe "
          "(4); várias perguntas na mesma variável se acumulam, sem prevalência. Coluna `revisao_pergunta_expr`: a "
          "pergunta ao operador e o bloqueio só com dúvida que muda a minuta; falta de resposta só destaca (P34).",
          "- M08: colunas `inserir_apos`, `nivel` e `inserir_apos_alternativo`.",
          "- Simulador: monta o texto (`f13_texto.py`); cada cenário ganhou `esperado.texto_sem_lacuna` e "
          "`referencia.texto_montado`/`lacunas_do_texto`. VAL-037 descrita pela pergunta que bloqueia.",
          "- Busca de nomes volta a incluir `validacao` e `comentario_validacao`.", "",
          "## O que mudou na Fase 12", "",
          "- P25: WZ-60 nova (atestado com garantia já prestada, só com ATESTADOS na WZ-38), SET-23, VAR-161 (prazo em "
          "meses), VAR-162 (justificativa no ETP), VAL-052 e VAL-053 (bloqueios), PAR-13 (12 meses). A VAL-029 barra "
          "'últimos' e 'período mínimo' sem tratar de garantia; não barra a duração da garantia prestada.",
          "- P32.1: CK-C-16.3, CK-P-19.5, CK-P-19.3, CK-P-13.7 e CK-P-13.1 leem o número do 'Outro' (`CK_x_numero`), com "
          "destaque e pergunta ao operador; '30 dias' corridos na CK-P-19.3 não vira dias úteis.",
          "- Validação: `validacao` e `comentario_validacao` do M03 e do M04 vêm do repositório (4º argumento do "
          "`rodar_fases_4_9.sh`, `f12_validacao_repo.py`) e o teste confere linha a linha (P33).", "",
          "## O que mudou na Fase 11", "",
          f"- M11: colunas `leitura`, `revisao_expr` e `revisao_pergunta` ({sum(1 for r in m11 if r['revisao_expr'])} "
          f"expressões de revisão, {sum(1 for r in m11 if r['revisao_pergunta'])} perguntas ao operador) e "
          f"{sum(1 for r in m11 if r['checklist'] == 'COMPLEMENTO')} complementos do operador (CK-X-01 a CK-X-09). As "
          f"perguntas 10.1 a 10.11 do consumo (comodato) passaram a só controle.",
          "- M12: coluna `tipo` (numero, lista ou texto), que passa a ser a fonte do tipo; a frase 'Tipo do valor' na fonte "
          "continua. PAR-03 corrigido: cita a VAR-160, que agora existe (cota calculada).",
          "- Cota zero (decisão 0008): VAR-160 nova, VAR-113 e VAR-118 refeitas sem ciclo (ordem 4, 5 e 6) e VAL-051 nova.",
          "- Comodato fora do sistema (P24): WZ-56, SET-01 e VAL-027 com expressão `false` e o motivo no texto ('DESLIGADA').",
          "- VAL-001 só com as perguntas 15.3 e 15.5 do checklist de permanentes (P28). ETP-90.01 opcional, sem texto padrão "
          "(P19). DV-35 nova (TR 23/2026, blocos de cota sem cota), ligada ao R1.",
          "- M02: coluna `grupo_ativo_expr` (quando um grupo de alternativas vale), usada pela regra de exatamente uma opção.",
          "- Simulador com as regras do motor: valor ausente, filho sem pai, grupo de alternativas, igualdade estrita, falso "
          "e conta em decimal exato (seção 'Regras do simulador'). Cenários reemitidos; `esperado` ganhou "
          "`bloqueios_grupo_alternativas`.", "",
          "## O que mudou na Fase 10", "",
          f"- `M04.depende_de_expr` em {dep} de {len(m04)} perguntas (vazia quando a pergunta vale sempre ou só depende de "
          f"dado dos itens) e `M04.calculo_expr` nas 6 perguntas derivadas dos itens.",
          f"- `M05.calculo_expr` e `M05.calculo_ordem` em {len(calc5)} variáveis ({', '.join(calc5)}). Linhas novas: VAR-156 "
          f"`numero`, VAR-157 `catmat`, VAR-158 `quantidade` e VAR-159 `valor_unitario` (atributos de item que as regras já usavam).",
          f"- `M11.condicional_expr` em {cnd} perguntas, `preenche_expr` em {pre} e `sugere_expr` em {sug}. O que a regra do M11 "
          f"não permite traduzir ficou sem expressão e está listado em `logs/f10_expr.txt` (P31).",
          f"- `M12_parametros.csv` com {len(m12)} parâmetros: nenhuma expressão traz número de lei ou valor monetário.",
          "- M10: literais trocados por `parametros.*` (VAL-004, 017, 020, 025, 026) e por `VAR_099` (VAL-032); mensagem da "
          "VAL-033 reescrita sem o padrão de ID.",
          "- Números de processo do corpus trocados por PROC-01 a PROC-12 no M00, no `perguntas_abertas.md` e nos scripts; a "
          "correspondência ficou fora do pacote.",
          "- Convenções novas e operadores fora da lista: P31.", "",
          "## O que mudou da Fase 3 à Fase 9", "",
          f"- Ajuste 1: o item virou entidade (VAR-011 com as colunas VAR-112 a VAR-124 e VAR-153 a VAR-155). Tratamento de "
          f"ME/EPP calculado pelo valor do item ou do grupo; WZ-09, WZ-13, WZ-18, WZ-20, WZ-24 e WZ-50 são derivadas dos itens. "
          f"Cenário misto C6 na simulação.",
          f"- Checklists técnicos como entrada do sistema: M11 com {n['M11_checklist.csv']} perguntas "
          f"({sum(1 for r in m11 if r['checklist'] == 'CONSUMO')} de consumo, {sum(1 for r in m11 if r['checklist'] == 'PERMANENTES')} "
          f"de permanentes); efeito: {', '.join(f'{k} {v}' for k, v in efeito.most_common())}.",
          f"- M04: {len(m04)} perguntas. A coluna `pre_preenchida_por` mostra {ck} respondidas ou sugeridas pelo checklist, "
          f"{deriv} derivadas dos itens e {dj} marcadas `DECISAO_JURIDICA` (equipe administrativa). WZ-56 a WZ-59 são novas "
          f"(comodato, validade excepcional, desinstalação, fabricante ou rede credenciada).",
          f"- M05: {len(m05)} variáveis; origem: {', '.join(f'{k} {v}' for k, v in origem5.most_common())}. CHECKLIST entrou no "
          f"domínio de origem (P29).",
          "- Condições em JSON Logic: `M02.condicao_expr`, `M04.liga_expr` e `M04.desliga_expr`, `M08.condicao_expr` e "
          "`M10.condicao_expr`. O texto livre continua como comentário. O que não coube está na P27.",
          "- Colunas `validacao` e `comentario_validacao` no M03 e no M04, vazias, para a sua revisão no xlsx.",
          "- P17 e P21 resolvidas; P16 fechada na Fase 10 (Decreto 12.174/2024, art. 2º, conferido no Planalto); P10 atualizada (DFDs chegaram, mas nenhum do processo do par 117/2025).", "",
          "## Especificação das matrizes M06 a M10 (oficial desde 23/10/2026)", "",
          "Reconstruída do registro das Fases 0 a 3, porque o prompt original não estava disponível; o gestor fechou a P23 e "
          "esta especificação passou a ser a oficial.", "",
          "- M06: `bloco_tr`, `secao`, `campos_etp`, `variaveis`, `perguntas_wz`, `classe_origem`, `regra_derivacao`, "
          "`teste_par_117`, `evidencia_par_117`, `teste_caso_67_23`, `evidencia_caso_67_23`, `fonte`, `status`.",
          "- M07: `id` (NRM-xxx, estável pela `chave`), `chave`, `norma`, `tipo`, `numero`, `ano`, `orgao`, `dispositivos_citados`, "
          "`formas_citadas`, `onde_citada`, `n_citacoes`, `origem` (MODELO_AGU, NOTA_AGU, CORPUS, CHECKLIST, MATRIZ), `situacao` "
          "(VIGENTE, REVOGADA, NAO_CONFERIDA), `verificacao` (URL e data), `fonte`, `status`.",
          "- M08: `id` (SET-xx), `tema`, `documento`, `origem_checklist`, `condicao`, `condicao_expr`, `ponto_insercao`, "
          "`texto_proposto`, `variaveis`, `perguntas_wz`, `base_no_modelo`, `evidencia_corpus`, `observacao`, `fonte`, `status`.",
          "- M09: `id` (DV-xx), `documento`, `local`, `tipo`, `descricao`, `referencia`, `tratamento_no_sistema`, `achado`, "
          "`fonte`, `status`.",
          "- M10: `id` (VAL-xxx), `regra`, `tipo` (BLOQUEIO, ALERTA, INFORMATIVO), `momento`, `condicao`, `condicao_expr`, "
          "`mensagem`, `afeta`, `base`, `achado`, `fonte`, `status`.",
          "- M11 (pedida em 22/10/2026): as colunas da tarefa 2, mais `orientacao` (texto literal das instruções da pergunta).",
          "- Achados da seção 5 usados no teste 8: 1 notas do modelo ausentes na matriz 01; 2 arquivo-fonte e linhas da matriz 01; "
          "3 estimativas na matriz 01; 4 ETP 19/2026 incompleto; 5 pares ETP e TR e processos em branco; 6 normas do regime "
          "anterior; 7 TRs sobre versões anteriores do modelo; 8 validade de 50% e 75%; 9 participante de IRP; 10 seção 12 do ETP.", "",
          "## Convenções", "",
          "- O CSV é a fonte; o xlsx é cópia. UTF-8 com BOM, vírgula, todo campo entre aspas.",
          "- Toda linha tem `fonte` e `status` (`EXTRAIDO`, `INFERIDO`, `A_VERIFICAR`).",
          "- IDs: `ETP-SS.CC`, `TR-<numeração do modelo>`, `NE-001`, `WZ-01`, `VAR-001`, `NRM-001`, `SET-01`, `DV-01`, `VAL-001`, "
          "`CK-C-14.2` (checklist de consumo) e `CK-P-13.1` (permanentes; `CAB.xx` para o cabeçalho). Blocos tirados de nota: "
          "`TR-NE016.01`. IDs nunca são reaproveitados; o M07 mantém o ID pela chave da norma.",
          "- Nenhum nome de pessoa nem endereço do corpus nas matrizes; onde precisaria, vai o cargo ou `[RESPONSÁVEL]`.",
          "- Norma só é citada se estiver na base (modelo, notas, corpus ou checklist) ou se tiver sido conferida em "
          "planalto.gov.br, in.gov.br ou gov.br. Situação no M07: "
          + ", ".join(f"{k} {v}" for k, v in sorted(sit.items())) + ".", "",
          "### JSON Logic", "",
          "- Variáveis: `WZ_07` (resposta da WZ-07; MULTIPLA vira lista), `CK_C_10_1` e `CK_P_13_1` (resposta da pergunta do "
          "checklist com o texto literal da opção, ex.: \"Sim\"; MULTIPLA vira lista; texto da caixa de resposta em "
          "`CK_C_12_2_texto`), `VAR_001` (variável do M05), `itens` (lista de itens com os atributos do M05), metadados "
          "`textos_livres`, `importacao.*`, `checklist.*`, `parametros.*`.",
          "- Operadores permitidos: `var`, `==`, `!=`, `!`, `!!`, `and`, `or`, `if`, `in`, `merge`, `some`, `none`, `<=`, `>`.",
          "- Fora da lista, só em `M04.calculo_expr` e `M05.calculo_expr` (P31): `reduce`, `+`, `*`, `-`, `/`, `%`.",
          "- Contexto de item: cada elemento de `itens` traz os atributos do M05 e também as variáveis globais (`WZ_`, `CK_`, "
          "`VAR_`, `parametros` e metadados); em pergunta do checklist com `por_item = S`, `CK_x_n` dentro do item é a resposta "
          "ligada àquele item (ausente se o item não foi indicado). Assim `some` e `none` podem comparar atributo de item com "
          "parâmetro. Nas expressões avaliadas por item (`M05.calculo_expr` de `tabela_itens.*` e destinos `itens.<atributo>` "
          "do M11) o item é o topo, e `itens_do_grupo` é a lista dos itens com o mesmo rótulo de grupo (ou só o item).",
          "- Em `reduce`, o passo lê `current.<atributo>` e `accumulator`. Dentro de `some` ou `none` sobre uma lista de "
          "textos (ex.: `VAR_085` na VAL-029), `{\"var\": \"\"}` é o próprio elemento.",
          "- `parametros.<nome>`: valor da linha do M12 com esse `nome`.",
          "- `liga_expr` e `desliga_expr` devolvem a lista de blocos: `{\"merge\": [{\"if\": [condição, [IDs], []]}, ...]}`.",
          "- `M02.condicao_expr`: alguma condição que liga E nenhuma que desliga (bloco condicional); nenhuma que desliga "
          "(demais); `false` nos separadores 'OU' e nos blocos que não entram na minuta.", "",
          "### Colunas da Fase 10", "",
          "- `M04.depende_de_expr`: verdadeira quando a pergunta deve ser feita. 'X diferente de V' é `!=` literal (pergunta "
          "anterior sem resposta conta como diferente). Trecho 'VAR-011 (...)' é dependência de dado, não condição.",
          "- `M04.calculo_expr`: valor das perguntas derivadas (WZ-09, 13, 18, 20, 24, 50); `null` quando não se aplica.",
          "- `M05.calculo_expr`: valor do atributo ou da variável; `M05.calculo_ordem`: ordem de cálculo (um cálculo só lê "
          "atributo já calculado). Linha `tabela_itens.*` é avaliada item a item.",
          "- `M11.condicional_expr`: quando a pergunta do checklist deve ser respondida.",
          "- `M11.preenche_expr` e `M11.sugere_expr`: objeto `{destino: expressão}`, destino `WZ_xx`, `VAR_xxx` ou "
          "`itens.<atributo>`. Só são avaliadas com a pergunta respondida e a condicional verdadeira; resultado `null` não "
          "conta. PREENCHE não sobrescreve o que o usuário já respondeu; duas perguntas que preenchem a mesma WZ com valores "
          "diferentes deixam a WZ sem resposta e o conflito aparece para a equipe. Destino `VAR_xxx` com várias contribuições: "
          "TEXTO junta em linhas, LISTA e TABELA juntam em lista, NUMERO fica com a primeira e acusa conflito se outra for "
          "diferente; cada contribuição guarda o ID da pergunta. SUGERE só mostra.",
          "- Ordem de avaliação usada no simulador (sugestão para o motor): entrada; M11 (preenche, na ordem das linhas); "
          "M05 por `calculo_ordem`; M04 `calculo_expr`; M04 `depende_de_expr`; M02, M04 liga/desliga, M08 e M10.",
          "- `M12_parametros.csv`: `id` (PAR-01), `nome`, `valor`, `tipo` (numero, lista ou texto; a coluna é a fonte do "
          "tipo), `unidade`, `base`, `vigencia`, `usado_em`, `fonte`, `status`.",
          "- `M02.grupo_ativo_expr`: nas linhas com `grupo_alternativa`, quando o grupo vale (mesmo valor em todo o grupo).",
          "- Condição desligada: `false` na coluna `_expr`, com o texto da linha começando por 'DESLIGADA' e o motivo.",
          "",
          "### Colunas da Fase 11 no M11 e complementos do operador", "",
          "- `leitura`: como ler a resposta do Word e qual prevalece em duplicidade (texto).",
          "- `revisao_expr`: JSON Logic, só com operadores gerais; verdadeira = resposta destacada para o operador revisar. "
          "Avaliada no fim, com os mesmos dados das validações do M10. Usa os metadados de leitura "
          "`checklist.marcas_multiplas`, `checklist.resposta_unica_por_item` e `checklist.divergencias_leitura` e o "
          "número `CK_x_numero` lido do 'Outro' do prazo (P32).",
          "- `revisao_pergunta`: pergunta que o sistema faz ao operador quando a dúvida muda a minuta; vazia quando basta o "
          "destaque.",
          "- `revisao_motivos` (Fase 14): JSON, uma entrada por motivo `{motivo, expr, texto, bloqueia}`; motivos fixos "
          "SEM_RESPOSTA, MARCAS_MULTIPLAS, OUTRO_ILEGIVEL, DIVERGENCIA, RESPOSTA_UNICA_POR_ITEM, CONTRADICAO e "
          "NOME_DE_PESSOA. `revisao_expr` é o 'or' de todas as `expr`; `revisao_pergunta_expr`, o 'or' das que bloqueiam; "
          "`revisao_pergunta`, os textos das que bloqueiam, separados por ' | '. Bloqueia só a dúvida que muda a minuta "
          "(P34).",
          "- `revisao_pergunta_expr` (Fase 13): JSON Logic; verdadeira = a `revisao_pergunta` é feita e a minuta fica "
          "bloqueada até a resposta (VAL-037). Só duas marcas em pergunta de uma opção, 'Outro' sem número legível, "
          "resposta única para vários itens e as dúvidas específicas (S09). Pergunta sem resposta só fica destacada "
          "(`revisao_expr`); quando ela decide bloco, já aparece como pergunta pendente do wizard.",
          "- Complementos do operador: linhas `CK-X-nn` (dois dígitos, a partir de 01), `checklist = COMPLEMENTO`, seção "
          "'COMPLEMENTO DO OPERADOR', número `X.nn`, variável `CK_X_nn`. Preenchidos no sistema, não existem no Word; ligados "
          "às mesmas variáveis e destinos das perguntas do checklist; sem opção pré-definida que não venha de norma ou de "
          "domínio do M05.",
          "",
          "### Texto da minuta (Fase 13)", "",
          "- `M02.lacunas_mapa`: lista JSON, na ordem do texto, uma entrada por marcador da coluna `lacunas`: `marcador`, "
          "`ocorrencia` (qual ocorrência no `texto_literal`, contada sem sobreposição), `fonte` (VAR_xxx, WZ_xx, CK_..., "
          "itens.atributo ou null) e, quando precisa, `acao`, `campo`, `indice`, `formato`, `unidade`, `texto`, `opcoes`, "
          "`grupo`, `quando`, `remove_antes`, `se_falso`, `estende_desde`, `estende_ate`, `lista_blocos`, "
          "`juntar_restante`, `se_vazio` e `comentario`. Definição de cada chave no cabeçalho do `scripts/f13_lacunas.py`.",
          "- Ações: PREENCHER (padrão), ESCOLHA (fica a opção do modelo cuja condição é verdadeira; marcadores do mesmo "
          "`grupo` viram um trecho só, com os ' OU ' do meio), OPCIONAL (o trecho entra ou sai), TABELA (montada pela "
          "`tabela_colunas`), REMOVER (instrução do modelo), MANTER (assinatura ou campo do fornecedor) e EQUIPE (fonte "
          "null, motivo no `comentario`).",
          "- Formatos: TEXTO, NUMERO_EXTENSO ('30 (trinta)'), PERCENTUAL_EXTENSO ('5% (cinco por cento)'), PERCENTUAL_2 "
          "('25,00%'), MOEDA ('R$ 1.234,56'), MOEDA_POR_EXTENSO, DATA, DIA, MES_EXTENSO, ANO, LISTA_TEXTO ('a, b e c'), "
          "LISTA_LINHAS, MINUSCULA, INICIAL_MINUSCULA, ITEM ('item 2') e POR_ITEM ('item 1: valor; item 3: valor').",
          "- `M08.lacunas_mapa` (Fase 14): mesmo formato; marcador = trecho entre colchetes de primeiro nível do "
          "`texto_proposto`. Cláusula PREENCHE_BLOCO não entra como texto: preenche o bloco.",
          "- `padrao: true` (Fase 14, P37) na opção que dá valor sem ter sido informado; a revisão mostra esses valores.",
          "- Chaves acrescentadas na Fase 14: `alternativas` (fontes de reserva, em ordem), `inicial_minuscula`, "
          "`inicial_maiuscula`, `filtro_item` e o formato NUMEROS_DOS_ITENS ('1, 3 e 5').",
          "- Séries de blocos-lista (`lista_blocos`, ex.: TR-4.1.1 a TR-4.1.3): cada bloco recebe um elemento; bloco sem "
          "elemento sai; o último presente termina em '.', o anterior em '; e', os demais em ';'; o último bloco do modelo "
          "junta os elementos que sobram.",
          "- `M02.tabela_colunas`: JSON com `linhas` (itens ou a VAR da tabela), `colunas` (cabeçalho do modelo e o que "
          "preenche), `orcamento_sigiloso` e, no TR-1.1.TAB1, `linha_cota` (quando entra, onde e com quais valores) e a "
          "numeração das linhas.",
          "- `M08.inserir_apos` (bloco do M02 depois do qual a cláusula entra, com os subitens dele), `M08.nivel` "
          "(MESMO_NIVEL: item seguinte no nível do bloco; SUBITEM: último subitem do bloco; PREENCHE_BLOCO: preenche as "
          "lacunas do bloco) e `M08.inserir_apos_alternativo` ('bloco (nivel)', em ordem, quando o bloco pode faltar). "
          "Várias cláusulas no mesmo ponto entram na ordem do M08.",
          "- Valor ausente vira lacuna marcada (`[[LACUNA ...]]`); o texto nunca recebe 'Sim' ou 'Não' de resposta do "
          "checklist.",
          "",
          "### Regras do simulador (as mesmas do motor, Marco 1)", "",
          "- Valor ausente: conta (`+`, `-`, `*`, `/`, `%`) e comparação de ordem (`<=`, `>`) com valor ausente dão ausente "
          "(`null`), nunca 0; divisão por zero também. Item sem valor unitário fica sem valor da unidade e sem tratamento ME/EPP.",
          "- Igualdade estrita: `==` e `!=` comparam tipo e valor (\"30\" é diferente de 30; 30 é igual a 30.0); `null` só é "
          "igual a `null`.",
          "- Falso para `!`, `!!`, `if`, `and`, `or`, `some` e `none`: `null`, `false`, 0, \"\" e `[]`; o resto é verdadeiro.",
          "- Conta exata: números convertidos para decimal pela forma escrita mais curta e somados e multiplicados em decimal.",
          "- Filho sem o pai não entra: pai é o ID sem o último segmento numérico, de letra ou romano (TR-4.41.1 tem pai "
          "TR-4.41), quando esse ID existe no M02; vale em cascata, na ordem do M02.",
          "- Grupo de alternativas ativo (`grupo_ativo_expr`): exatamente uma opção entra; nenhuma ou mais de uma vai para "
          "`bloqueios_grupo_alternativas`.",
          "",
          "### Cenários (`cenarios/`)", "",
          "- C1 a C8: gerados pelo `f10_simulador.py` (implementação independente do motor). `entrada` tem `wizard`, "
          "`checklist`, `itens` (com `respostas_por_item` quando a pergunta é por item), `variaveis` e `metadados`, todos "
          "fictícios. `esperado` tem `blocos` (M02, na ordem), `clausulas_m08`, `validacoes_m10`, "
          "`perguntas_sem_resposta`, `bloqueios_grupo_alternativas` e `texto_sem_lacuna` (Fase 13: blocos e cláusulas "
          "da minuta, na ordem, que saem sem nenhuma lacuna com as entradas do cenário, pela montagem do `f13_texto.py`). "
          "O esperado vem do caminho do texto (liga/desliga e depende_de em texto, derivadas em "
          "Python); o teste reproduz pelo caminho das expressões. `referencia` é informativa.",
          "- R1 (TR 23/2026) e R2 (TR 58/2026): entrada anonimizada com as respostas tiradas do TR real "
          "(`origem_das_respostas`), itens fictícios, blocos que o TR real contém, `divergencias_conhecidas` ligadas ao M09 e, em "
          "`referencia.diferencas_simulacao`, o que a simulação monta a mais ou a menos que o TR real. Cada divergência traz "
          "`classificacao` ('TR real').", "",
          "## Checklists técnicos", "",
          "Versões mapeadas no M11 (qualquer mudança no checklist exige refazer o M11; ver P30 e VAL-036):", ""]
    o += [f"- `Checklists/{k}`: SHA-256 `{v}`" for k, v in hashes.items()]
    o += ["", "Divisão de trabalho: o checklist traz os fatos técnicos (M11); o wizard fica com as decisões jurídicas (M04, "
          "`DECISAO_JURIDICA`). A tabela de atributos de item por checklist está em `sugestoes_checklist.md`.", "",
          "## Testes de aceite (Fases 9 a 14)", "",
          f"Resultado completo em `logs/f9_testes.txt`. {falhas}.", ""]
    o += [f"- {l[6:]}" if l.startswith("OK") else f"- **FALHA** {l[6:]}" for l in principais]
    o += ["", "Outras conferências:", ""]
    o += [f"- {l[6:]}" if l.startswith("OK") else f"- **FALHA** {l[6:]}" for l in outros]
    o += ["", "## Perguntas que dependem de você", ""]
    o += [f"- {a}" for a in abertas]
    o += ["", "## Revisão no xlsx", "",
          "Preencha `validacao` (OK, CORRIGIR ou DUVIDA) e `comentario_validacao` nas abas M03 e M04 e devolva a planilha. "
          "O script `importar_validacao.py` leva só essas duas colunas para os CSV, pelo ID, e lista as linhas CORRIGIR e "
          "DUVIDA; as correções são feitas nos geradores, e as colunas de revisão são preservadas quando as matrizes são "
          "regeneradas.", "",
          "## Como regenerar", "",
          "Python 3 com openpyxl; Tesseract com o idioma `por` só na Fase 0. Rode sempre com `python3 -I`. `DOC` é "
          "`Licita+/Documentos`, `OUT` é `Licita+/Matrizes_v1`, `T` é uma pasta de trabalho fora da entrega, e `MODELO` é "
          "`DOC/TR exemplos/modelo-de-termo-de-referencia-compras-lei-no-14-133-dez-25.docx`.", "",
          "```",
          "# Fase 0",
          "python3 -I scripts/f0_extrair_texto.py DOC T/text TESSDATA",
          "python3 -I scripts/f0_docx_modelo.py MODELO T/modelo_estrutura.json",
          "python3 -I scripts/f0_inventario_apoio.py DOC T/text T/modelo_estrutura.json OUT/logs/f0_conferencias.txt",
          "python3 -I scripts/f0_gerar_M00.py DOC T/text/_extracao.json OUT",
          "# Fases 1 e 2 (estrutura do modelo e corpus de ETPs)",
          "python3 -I scripts/f1_modelo_estrutura.py MODELO T/f1_modelo.json",
          "python3 -I scripts/f1_blocos.py T/f1_modelo.json T/f1_blocos.json",
          "python3 -I scripts/f2_corpus_etp.py T/text T/f2_corpus_etp.json",
          "# Checklists (leitura estrutural dos docx)",
          "python3 -I scripts/ck_ler.py \"DOC/Checklists/<consumo>.docx\" T/ck/ck_C.json",
          "python3 -I scripts/ck_ler.py \"DOC/Checklists/<permanentes>.docx\" T/ck/ck_P.json",
          "# Fase 6, comparação dos TRs 23/2026 e 58/2026 com o modelo (alguns minutos; só se o M02 mudar)",
          "python3 -I scripts/f6_comparar_trs.py OUT/M02_tr_blocos.csv T/text/<TR 23/2026> T/text/<TR 58/2026> T/f6_comparacao.json",
          "# Todas as matrizes, na ordem das dependências, testes incluídos",
          "sh scripts/rodar_fases_4_9.sh T DOC OUT REPO/matrizes/v1",
          "# Fase 10, uma vez: números de processo (a correspondência fica fora do pacote)",
          "python3 -I scripts/f10_proc.py OUT FORA_DO_PACOTE/correspondencia_processos.csv scripts/f0_gerar_M00.py scripts/f9_testes.py",
          "python3 -I scripts/gerar_readme.py OUT DOC",
          "```", ""]
    (pasta / "README.md").write_text("\n".join(o), encoding="utf-8")
    print(f"README.md: {len(o)} linhas")


if __name__ == "__main__":
    main()
