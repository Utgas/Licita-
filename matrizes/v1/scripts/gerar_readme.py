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
    ("M11_checklist.csv", "uma linha por pergunta dos dois checklists técnicos, com tipo, condicional, destino e efeito"),
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

    o = ["# Licita+ | Matrizes v1", "",
         "Estado em 22/10/2026: Fases 0 a 9 concluídas, com o ajuste 1 da revisão (decisões por item) e as tarefas dos "
         "checklists técnicos. Paro aqui, como pedido, para a sua revisão.", "",
         "## Arquivos", "", "| Arquivo | Conteúdo | Linhas |", "|---|---|---|"]
    o += [f"| `{a}` | {d} | {n[a]} |" for a, d in ARQ]
    o += ["| `matrizes_v1.xlsx` | cópia de leitura e revisão: aba LEIA_ME e uma aba por CSV; colunas de revisão em amarelo no M03 e no M04 | |",
          "| `perguntas_abertas.md` | decisões pendentes e adotadas, P01 a P30 | |",
          "| `sugestoes_checklist.md` | lacunas, duplicidades e ambiguidades dos checklists, com redação proposta | |",
          "| `auditoria_matrizes_01_02.md` | auditoria das matrizes rascunho 01 e 02 (Fase 8) | |",
          "| `logs/` | conferências, cobertura do checklist, comparação dos TRs, expressões, simulação, normas, testes | |",
          "| `scripts/` | scripts de análise que geram tudo acima | |", "",
          "## O que mudou desde a Fase 3", "",
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
          "- P17 e P21 resolvidas; P16 conferida em parte; P10 atualizada (DFDs chegaram, mas nenhum do processo do par 117/2025).", "",
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
          "- Operadores: var, ==, !=, !, !!, and, or, in, some, all, none, if, merge, >, >=, <, <=, +, *.",
          "- `liga_expr` e `desliga_expr` devolvem a lista de blocos: `{\"merge\": [{\"if\": [condição, [IDs], []]}, ...]}`.",
          "- `M02.condicao_expr`: alguma condição que liga E nenhuma que desliga (bloco condicional); nenhuma que desliga "
          "(demais); `false` nos separadores 'OU' e nos blocos que não entram na minuta.", "",
          "## Checklists técnicos", "",
          "Versões mapeadas no M11 (qualquer mudança no checklist exige refazer o M11; ver P30 e VAL-036):", ""]
    o += [f"- `Checklists/{k}`: SHA-256 `{v}`" for k, v in hashes.items()]
    o += ["", "Divisão de trabalho: o checklist traz os fatos técnicos (M11); o wizard fica com as decisões jurídicas (M04, "
          "`DECISAO_JURIDICA`). A tabela de atributos de item por checklist está em `sugestoes_checklist.md`.", "",
          "## Testes de aceite (Fase 9)", "",
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
          "python3 -I scripts/gerar_readme.py OUT DOC",
          "```", ""]
    (pasta / "README.md").write_text("\n".join(o), encoding="utf-8")
    print(f"README.md: {len(o)} linhas")


if __name__ == "__main__":
    main()
