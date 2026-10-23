/**
 * Classificação das diferenças entre a minuta do motor e os TRs reais (R1 = TR 23/2026, R2 = TR 58/2026).
 * Tarefa do Marco 1, passo 9. Quatro tipos:
 * - motor: erro do código (tem de ser corrigido; nenhuma diferença pode ficar com este tipo);
 * - matriz: regra que pode estar errada, ou blocos que a comparação automática do agente das matrizes pode ter
 *   achado por engano; vai para o Gabriel decidir;
 * - TR real: erro conhecido do documento, listado em divergencias_conhecidas (campo dv);
 * - lacuna: dado que só existe no processo real e não está na entrada anonimizada.
 *
 * Chave: "<categoria>:<lado>:<ID>". Lado "tr" = só no TR real (ou no esperado); "minuta" = só na minuta do motor.
 * Em todos os casos a minuta do motor é igual à simulação do agente das matrizes (referencia.diferencas_simulacao):
 * nenhuma diferença vem do código.
 */
export type TipoDeDiferenca = "motor" | "matriz" | "TR real" | "lacuna";
export type Classificacao = { tipo: TipoDeDiferenca; motivo: string; dv?: string };

const COMPARACAO =
  "o TR real tem as duas alternativas pela comparação automática (difflib, limiar 0,60), que distingue mal opções de texto quase igual; a resposta lida do TR escolhe a outra";
const TEXTO_PREENCHIDO =
  "bloco de texto quase todo preenchido com dados do processo real; na entrada anonimizada fica como lacuna e a comparação de texto não o acha no TR";
const CABECALHO_E_ASSINATURA = "cabeçalho e assinatura do processo real (órgão, número, local e data); no TR Digital saem fora do corpo do TR";
const ANEXO_I =
  "bloco do Anexo I (contrato substituído por instrumento equivalente); a WZ-43 lida do TR é CONTRATO; conferir se o TR real tem o Anexo I ou se a comparação casou texto parecido do corpo";
const CHECKLIST_REAL = "a condição lê respostas do checklist técnico do processo real, que não estão na entrada (checklist vazio)";

export const CLASSIFICACAO: Record<"R1" | "R2", Record<string, Classificacao>> = {
  R1: {
    "bloco:tr:TR-CAB.02": { tipo: "matriz", motivo: "o M02 tira da minuta o título do modelo AGU, e o TR real o manteve; confirmar a regra" },
    "bloco:tr:TR-1.3": { tipo: "matriz", motivo: `GA-01 com WZ-06 = COMUM: ${COMPARACAO}` },
    "bloco:tr:TR-1.4": { tipo: "matriz", motivo: "declaração de bem que não é de luxo: o M02 liga só para consumo, e o TR real (bem permanente) a manteve; a condição diz que, para permanentes, a decisão é da equipe, mas o M04 não tem pergunta para isso" },
    "bloco:tr:TR-1.6": { tipo: "matriz", motivo: `GA-02 com WZ-14 = NAO_CONTINUO: ${COMPARACAO}` },
    "bloco:tr:TR-4.H08": { tipo: "TR real", dv: "DV-35", motivo: "subtítulo de reserva de cota sem haver cota (decidido)" },
    "bloco:tr:TR-4.41": { tipo: "TR real", dv: "DV-35", motivo: "reserva de cota sem haver cota (decidido)" },
    "bloco:tr:TR-9.33.1": { tipo: "matriz", motivo: "subitem de sociedades estrangeiras sem o item 9.33 (registro em entidade profissional), que a WZ-38 lida do TR não marca; conferir se o subitem vale sozinho" },
    "bloco:tr:TR-11.3": { tipo: "matriz", motivo: "dotação de exercícios seguintes é para fornecimento contínuo plurianual (WZ-14 = NAO_CONTINUO no TR); o TR real manteve o item; confirmar a regra" },
    "bloco:tr:TR-AI-2.1": { tipo: "matriz", motivo: ANEXO_I },
    "bloco:tr:TR-AI-2.3": { tipo: "matriz", motivo: ANEXO_I },
    "bloco:tr:TR-AI-4.1.7.3": { tipo: "matriz", motivo: ANEXO_I },
    "bloco:minuta:TR-CAB.03": { tipo: "lacuna", motivo: CABECALHO_E_ASSINATURA },
    "bloco:minuta:TR-CAB.04": { tipo: "lacuna", motivo: CABECALHO_E_ASSINATURA },
    "bloco:minuta:TR-ASSIN.01": { tipo: "lacuna", motivo: CABECALHO_E_ASSINATURA },
    "bloco:minuta:TR-ASSIN.02": { tipo: "lacuna", motivo: CABECALHO_E_ASSINATURA },
    "bloco:minuta:TR-ASSIN.03": { tipo: "lacuna", motivo: CABECALHO_E_ASSINATURA },
    "bloco:minuta:TR-1.1": { tipo: "lacuna", motivo: TEXTO_PREENCHIDO },
    "bloco:minuta:TR-5.1": { tipo: "lacuna", motivo: TEXTO_PREENCHIDO },
    "bloco:minuta:TR-5.4": { tipo: "lacuna", motivo: TEXTO_PREENCHIDO },
    "bloco:minuta:TR-9.1": { tipo: "lacuna", motivo: TEXTO_PREENCHIDO },
    "bloco:minuta:TR-11.2.III": { tipo: "lacuna", motivo: TEXTO_PREENCHIDO },
    "bloco:minuta:TR-11.2.IV": { tipo: "lacuna", motivo: TEXTO_PREENCHIDO },
    "bloco:minuta:TR-12.1": { tipo: "lacuna", motivo: TEXTO_PREENCHIDO },
    "bloco:minuta:TR-7.2.4.7.1": { tipo: "TR real", dv: "DV-05", motivo: "infração específica sem pertinência com o objeto; o texto do TR real não casa com o do modelo" },
    "bloco:minuta:TR-9.14": { tipo: "TR real", dv: "DV-04", motivo: "o TR real chama a Autorização Especial de 'Autorização de Funcionamento (AE)'; o texto não casa com o do modelo" },
    "bloco:minuta:TR-9.35": { tipo: "TR real", dv: "DV-04", motivo: "o TR real chama a Autorização Especial de 'Autorização de Funcionamento (AE)'; o texto não casa com o do modelo" },
    ...Object.fromEntries(
      ["TR-5.7", "TR-5.8", "TR-5.9", "TR-5.10", "TR-5.11", "TR-5.12", "TR-5.13", "TR-5.14", "TR-5.15", "TR-5.17"].map((id) => [
        `bloco:minuta:${id}`,
        {
          tipo: "matriz",
          motivo: "garantia contratual do bem (GA-07 B, WZ-29 = SIM): o TR real trocou o texto do modelo por redação própria de garantia técnica (item 5.7 e seguintes); conferir se o grupo inteiro deve sair na minuta",
        } satisfies Classificacao,
      ]),
    ),
    "m08:tr:SET-07": { tipo: "lacuna", motivo: CHECKLIST_REAL },
    "m08:tr:SET-08": { tipo: "lacuna", motivo: CHECKLIST_REAL },
    "m08:tr:SET-09": { tipo: "lacuna", motivo: CHECKLIST_REAL },
    "m08:tr:SET-11": { tipo: "lacuna", motivo: CHECKLIST_REAL },
    "m08:tr:SET-12": { tipo: "lacuna", motivo: CHECKLIST_REAL },
    "m10:tr:VAL-041": { tipo: "TR real", dv: "DV-04", motivo: "a VAL-041 lê o texto livre do TR; a entrada anonimizada não traz o texto com 'Autorização de Funcionamento (AE)'" },
    "m10:tr:VAL-042": { tipo: "TR real", dv: "DV-05", motivo: "regra sem expressão (P27): sai na conferência manual" },
    "m10:tr:VAL-043": { tipo: "TR real", dv: "DV-01", motivo: "regra sem expressão (P27): sai na conferência manual" },
    "m10:tr:VAL-044": { tipo: "TR real", dv: "DV-10", motivo: "regra sem expressão (P27): sai na conferência manual" },
    "m10:tr:VAL-045": { tipo: "TR real", dv: "DV-11", motivo: "regra sem expressão (P27): sai na conferência manual" },
    "m10:tr:VAL-029": { tipo: "lacuna", motivo: "a VAL-029 lê o texto dos atestados (VAR-085) do TR real, que não está na entrada" },
    "m10:tr:VAL-052": { tipo: "TR real", dv: "DV-09", motivo: "DV-09 é permitido (P25): com garantia de 12 meses (VAR-161), a VAL-052 não dispara, como deve" },
    "m10:minuta:VAL-025": { tipo: "lacuna", motivo: "item de uma unidade: a justificativa fica no checklist do processo real (CK-C-4.7 / CK-P-4.4), fora da entrada" },
    "m10:minuta:VAL-039": { tipo: "lacuna", motivo: "itens fictícios sem CATMAT" },
  },
  R2: {
    "bloco:tr:TR-CAB.02": { tipo: "matriz", motivo: "o M02 tira da minuta o título do modelo AGU, e o TR real o manteve; confirmar a regra" },
    "bloco:tr:TR-1.3": { tipo: "matriz", motivo: `GA-01 com WZ-06 = COMUM: ${COMPARACAO}` },
    "bloco:tr:TR-1.6": { tipo: "matriz", motivo: `GA-02 com WZ-14 = NAO_CONTINUO: ${COMPARACAO}` },
    "bloco:tr:TR-4.H08": { tipo: "matriz", motivo: "subtítulo de reserva de cota sem haver cota (o próprio TR diz que não haverá cota); mesmo caso da DV-35 do R1, mas o M09 não tem divergência para o TR 58/2026" },
    "bloco:tr:TR-4.41": { tipo: "matriz", motivo: "reserva de cota sem haver cota; mesmo caso da DV-35 do R1, mas o M09 não tem divergência para o TR 58/2026" },
    "bloco:tr:TR-5.2": { tipo: "matriz", motivo: `GA-06 com WZ-26 = REMESSA_UNICA: ${COMPARACAO}` },
    "bloco:tr:TR-9.H03": { tipo: "matriz", motivo: "critério de aceitabilidade de preços de registro de preços com grupo; o TR real (sem registro de preços, sem grupo) manteve o texto; confirmar a regra" },
    "bloco:tr:TR-9.4": { tipo: "matriz", motivo: "critério de aceitabilidade de preços de registro de preços com grupo; o TR real (sem registro de preços, sem grupo) manteve o texto; confirmar a regra" },
    "bloco:tr:TR-9.4.1": { tipo: "matriz", motivo: "critério de aceitabilidade de preços de registro de preços com grupo; o TR real (sem registro de preços, sem grupo) manteve o texto; confirmar a regra" },
    "bloco:tr:TR-11.3": { tipo: "matriz", motivo: "dotação de exercícios seguintes é para fornecimento contínuo plurianual (WZ-14 = NAO_CONTINUO no TR); o TR real manteve o item; confirmar a regra" },
    "bloco:tr:TR-AI-1.2": { tipo: "matriz", motivo: ANEXO_I },
    "bloco:tr:TR-AI-2.1": { tipo: "matriz", motivo: ANEXO_I },
    "bloco:tr:TR-AI-2.3": { tipo: "matriz", motivo: ANEXO_I },
    "bloco:tr:TR-AI-3.1.10": { tipo: "matriz", motivo: ANEXO_I },
    "bloco:tr:TR-AI-4.1.7.3": { tipo: "matriz", motivo: ANEXO_I },
    "bloco:tr:TR-AI-5.11": { tipo: "matriz", motivo: ANEXO_I },
    "bloco:minuta:TR-CAB.03": { tipo: "lacuna", motivo: CABECALHO_E_ASSINATURA },
    "bloco:minuta:TR-CAB.04": { tipo: "lacuna", motivo: CABECALHO_E_ASSINATURA },
    "bloco:minuta:TR-ASSIN.01": { tipo: "lacuna", motivo: CABECALHO_E_ASSINATURA },
    "bloco:minuta:TR-ASSIN.02": { tipo: "lacuna", motivo: CABECALHO_E_ASSINATURA },
    "bloco:minuta:TR-ASSIN.03": { tipo: "lacuna", motivo: CABECALHO_E_ASSINATURA },
    "bloco:minuta:TR-1.1": { tipo: "lacuna", motivo: TEXTO_PREENCHIDO },
    "bloco:minuta:TR-5.1": { tipo: "lacuna", motivo: TEXTO_PREENCHIDO },
    "bloco:minuta:TR-8.41": { tipo: "lacuna", motivo: TEXTO_PREENCHIDO },
    "bloco:minuta:TR-9.3": { tipo: "lacuna", motivo: TEXTO_PREENCHIDO },
    "bloco:minuta:TR-9.14": { tipo: "lacuna", motivo: TEXTO_PREENCHIDO },
    "bloco:minuta:TR-11.2.III": { tipo: "lacuna", motivo: TEXTO_PREENCHIDO },
    "bloco:minuta:TR-11.2.IV": { tipo: "lacuna", motivo: TEXTO_PREENCHIDO },
    "bloco:minuta:TR-9.35": { tipo: "TR real", dv: "DV-06", motivo: "o TR real exige declaração de importação de medicamento num TR de equipamentos; o texto não casa com o do modelo" },
    ...Object.fromEntries(
      ["SET-02", "SET-05", "SET-06", "SET-12", "SET-14", "SET-15", "SET-17"].map((id) => [`m08:tr:${id}`, { tipo: "lacuna", motivo: CHECKLIST_REAL } satisfies Classificacao]),
    ),
    "m08:minuta:SET-13": { tipo: "matriz", motivo: "a SET-13 entra por WZ-29 = SIM (garantia contratual), e o M08 não registra evidência dela no TR 58/2026; conferir" },
    "m10:tr:VAL-042": { tipo: "TR real", dv: "DV-05", motivo: "regra sem expressão (P27): sai na conferência manual" },
    "m10:tr:VAL-043": { tipo: "TR real", dv: "DV-02", motivo: "regra sem expressão (P27): sai na conferência manual" },
    "m10:minuta:VAL-005": { tipo: "lacuna", motivo: "número do processo tirado da entrada anonimizada" },
    "m10:minuta:VAL-039": { tipo: "lacuna", motivo: "itens fictícios sem CATMAT" },
    "m10:minuta:VAL-053": { tipo: "lacuna", motivo: "a justificativa da garantia já prestada (VAR-162) fica no ETP do processo real, fora da entrada" },
    "grupo:minuta:GA-03": { tipo: "lacuna", motivo: "a WZ-16 (PCA detalhado no TR ou só citado) não pode ser lida do TR real; sem resposta, o grupo fica sem opção e bloqueia" },
  },
};
