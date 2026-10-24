/**
 * Processo fictício com o ETP quase todo respondido (Marco 3): a entrada do cenário C1 (pregão com registro de
 * preços, consumo) mais as variáveis, respostas do checklist e justificativas que o ETP lê. Tudo fictício.
 */
import { readFileSync } from "node:fs";
import path from "node:path";
import type { EntradaProcesso } from "../../src/motor/entrada.ts";
import { pacoteDasMatrizes } from "./pacote-das-matrizes.ts";

const DIR = path.resolve(import.meta.dirname, "../../matrizes/v1/cenarios");

export const NECESSIDADE_FICTICIA =
  "A unidade fictícia precisa repor o estoque de medicamentos de uso contínuo. Sem a reposição, os atendimentos fictícios do ambulatório ficam sem o material.";

export function entradaDoEtpFicticio(): EntradaProcesso {
  const { pacote, hash } = pacoteDasMatrizes();
  const { entrada } = JSON.parse(readFileSync(path.join(DIR, "C1.json"), "utf8"));
  return {
    pacote,
    hashDoPacote: hash,
    ...structuredClone(entrada),
    checklist: {
      ...entrada.checklist,
      CK_C_2_4: ["Interrupção de tratamento"],
      CK_C_4_6: "Sim",
      CK_C_4_6_texto: "Margem fictícia de dez por cento sobre o consumo médio.",
      CK_C_5_9: "Solução fictícia escolhida por ser a única que atende ao consumo da unidade.",
    },
    justificativas: { WZ_06: "Justificativa fictícia: o medicamento tem especificação usual de mercado." },
    variaveis: {
      ...entrada.variaveis,
      VAR_001: "00000.000000/0000-00",
      VAR_002: "000000",
      VAR_003: "Organização Militar Fictícia",
      VAR_006: "Seção de Saúde Fictícia",
      VAR_007: "Cargo fictício [RESPONSÁVEL]",
      VAR_008: "Aquisição fictícia de medicamentos",
      VAR_010: NECESSIDADE_FICTICIA,
      VAR_012: "Consumo fictício dos últimos doze meses, com a margem de segurança informada.",
      VAR_013: [{ item: 1, valor: 6 }, { item: 2, valor: 30 }],
      VAR_014: 135000,
      VAR_015: "01/10/2026",
      VAR_018: "Bem comum: especificação usual de mercado (texto fictício).",
      VAR_034: 12,
      VAR_035: "assinatura da ata",
      VAR_038: 2026,
      VAR_060: 30,
      VAR_064: [{ endereco: "Rua Fictícia, 100", horario: "8h às 12h", setor: "Almoxarifado fictício" }],
      VAR_098: [{ cargo: "Cargo fictício", nome: "[RESPONSÁVEL]", funcao: "Integrante requisitante" }],
      VAR_101: "Fornecimento fictício parcelado, conforme a necessidade da unidade.",
      VAR_102: "Itens fictícios adjudicados por item, sem prejuízo ao conjunto.",
      VAR_104: "Abastecimento contínuo fictício do ambulatório.",
      VAR_107: "Medicamentos fictícios com registro sanitário válido.",
      VAR_108: "A contratação fictícia é viável, pelos motivos das seções anteriores.",
      VAR_163: "MESES",
    },
  };
}
