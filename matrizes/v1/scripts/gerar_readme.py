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
         "Estado em 23/10/2026: Fases 0 a 10 concluídas. Na Fase 10 as regras que o motor executa ficaram todas em JSON "
         "Logic (dependências do wizard, condições e preenchimento do checklist, atributos calculados), com os parâmetros "
         "no M12 e os cenários de ouro e de reprodução em `cenarios/`. Antes, na mesma data, a tarefa extra da Fase 10 "
         "conferiu o M07 com o repositório auxiliar ctresb/leis e fechou a P16.", "",
         "## Arquivos", "", "| Arquivo | Conteúdo | Linhas |", "|---|---|---|"]
    o += [f"| `{a}` | {d} | {n[a]} |" for a, d in ARQ]
    o += ["| `matrizes_v1.xlsx` | cópia de leitura e revisão: aba LEIA_ME e uma aba por CSV; colunas de revisão em amarelo no M03 e no M04 | |",
          f"| `cenarios/` | cenários de ouro C1 a C8 ({n_c}) e casos de reprodução R1 e R2 ({n_r}) em JSON, com entrada e esperado | |",
          "| `perguntas_abertas.md` | decisões pendentes e adotadas, P01 a P31 | |",
          "| `sugestoes_checklist.md` | lacunas, duplicidades e ambiguidades dos checklists, com redação proposta | |",
          "| `auditoria_matrizes_01_02.md` | auditoria das matrizes rascunho 01 e 02 (Fase 8) | |",
          "| `log_fase10_repo_leis.md` | arquivos do repositório auxiliar ctresb/leis (commit 15eb09b) cruzados com o M07 e uso de cada um | |",
          "| `logs/` | conferências, cobertura do checklist, comparação dos TRs, expressões, simulação, normas, testes | |",
          "| `scripts/` | scripts de análise que geram tudo acima | |", "",
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
          "## Especificação reconstruída (leia antes de revisar M06 a M10)", "",
          "O texto original do prompt não está disponível nesta sessão (o `attachment.txt` de 22/10/2026 é a lista de tarefas). As "
          "colunas abaixo e a lista de achados da seção 5 foram reconstruídas do registro das Fases 0 a 3; confirme ou corrija (P23).", "",
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
          "- `M12_parametros.csv`: `id` (PAR-01), `nome`, `valor`, `unidade`, `base`, `vigencia`, `usado_em`, `fonte`, `status`.",
          "",
          "### Cenários (`cenarios/`)", "",
          "- C1 a C8: gerados pelo `f10_simulador.py` (implementação independente do motor). `entrada` tem `wizard`, "
          "`checklist`, `itens` (com `respostas_por_item` quando a pergunta é por item), `variaveis` e `metadados`, todos "
          "fictícios. `esperado` tem `blocos` (M02, na ordem), `clausulas_m08`, `validacoes_m10` e "
          "`perguntas_sem_resposta`. O esperado vem do caminho do texto (liga/desliga e depende_de em texto, derivadas em "
          "Python); o teste reproduz pelo caminho das expressões. `referencia` é informativa.",
          "- R1 (TR 23/2026) e R2 (TR 58/2026): entrada anonimizada com as respostas tiradas do TR real "
          "(`origem_das_respostas`), itens fictícios, blocos que o TR real contém, `divergencias_conhecidas` ligadas ao M09 e, em "
          "`referencia.diferencas_simulacao`, o que a simulação monta a mais ou a menos que o TR real.", "",
          "## Checklists técnicos", "",
          "Versões mapeadas no M11 (qualquer mudança no checklist exige refazer o M11; ver P30 e VAL-036):", ""]
    o += [f"- `Checklists/{k}`: SHA-256 `{v}`" for k, v in hashes.items()]
    o += ["", "Divisão de trabalho: o checklist traz os fatos técnicos (M11); o wizard fica com as decisões jurídicas (M04, "
          "`DECISAO_JURIDICA`). A tabela de atributos de item por checklist está em `sugestoes_checklist.md`.", "",
          "## Testes de aceite (Fases 9 e 10)", "",
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
          "sh scripts/rodar_fases_4_9.sh T DOC OUT",
          "# Fase 10, uma vez: números de processo (a correspondência fica fora do pacote)",
          "python3 -I scripts/f10_proc.py OUT FORA_DO_PACOTE/correspondencia_processos.csv scripts/f0_gerar_M00.py scripts/f9_testes.py",
          "python3 -I scripts/gerar_readme.py OUT DOC",
          "```", ""]
    (pasta / "README.md").write_text("\n".join(o), encoding="utf-8")
    print(f"README.md: {len(o)} linhas")


if __name__ == "__main__":
    main()
