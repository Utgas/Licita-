#!/bin/sh
# Regenera as matrizes depois da Fase 3, na ordem das dependências (análise, não código do sistema).
# Uso: sh rodar_fases_4_9.sh <pasta_trabalho> <pasta_Documentos> <pasta_Matrizes_v1>
# <pasta_trabalho> tem f1_modelo.json, f1_blocos.json, f2_corpus_etp.json, ck/ck_C.json, ck/ck_P.json, text/ e
# f6_comparacao.json (gerado por f6_comparar_trs.py, que leva alguns minutos e só precisa rodar se o M02 mudar).
set -e
T="$1"; DOC="$2"; OUT="$3"; S="$(dirname "$0")"
MODELO="$DOC/TR exemplos/modelo-de-termo-de-referencia-compras-lei-no-14-133-dez-25.docx"
python3 -I "$S/f1_gerar_M02.py" "$T/f1_blocos.json" "$T/f1_modelo.json" "$OUT"
python3 -I "$S/f2_gerar_M01.py" "$T/f2_corpus_etp.json" "$OUT/M02_tr_blocos.csv" "$OUT"
python3 -I "$S/f6_gerar_M08.py" "$OUT"
python3 -I "$S/f7_gerar_M10.py" "$OUT"
python3 -I "$S/f3_gerar_M04_M05.py" "$OUT/M01_etp_campos.csv" "$OUT/M02_tr_blocos.csv" "$OUT"
python3 -I "$S/ck_gerar_M11.py" "$T/ck/ck_C.json" "$T/ck/ck_P.json" "$OUT" "$OUT/logs/f4_cobertura_checklist.txt"
python3 -I "$S/f1_gerar_M03.py" "$MODELO" "$T/f1_modelo.json" "$T/f1_blocos.json" "$OUT" "$OUT/M04_wizard.csv"
python3 -I "$S/f6_gerar_expr.py" "$OUT" "$OUT/logs/f6_expr.txt"
python3 -I "$S/f4_gerar_M06.py" "$OUT"
python3 -I "$S/f6_gerar_M09.py" "$OUT" "$T/f6_comparacao.json"
python3 -I "$S/f5_gerar_M07.py" "$OUT" "$OUT/logs/f5_normas.txt"
python3 -I "$S/ck_sugestoes.py" "$OUT"
python3 -I "$S/f8_auditoria.py" "$DOC" "$OUT"
python3 -I "$S/f3_simular_wizard.py" "$OUT/M02_tr_blocos.csv" "$OUT/M04_wizard.csv" "$OUT/logs/f6_simulacao_wizard.txt" > /dev/null
python3 -I "$S/gerar_xlsx.py" "$OUT"
python3 -I "$S/verifica_nomes.py" "$T/text" "$OUT" > "$OUT/logs/f9_nomes.txt"
python3 -I "$S/f9_testes.py" "$OUT" "$T/f1_modelo.json" "$DOC" "$T/text" "$OUT/logs/f9_testes.txt"
