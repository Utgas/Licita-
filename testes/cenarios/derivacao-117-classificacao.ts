/**
 * Classificação dos blocos do par ETP e TR 117/2025 que o M06 testou e não deram CONSISTENTE (Marco 3, passo 5).
 *
 * O Licita+ monta o ETP e o TR das mesmas respostas, então não reproduz a divergência do par real: ela é do
 * documento real. Cada entrada diz qual dado ou pergunta alimenta os dois documentos no sistema (mesmaFonte), e o
 * teste confere que essa fonte é mesmo lida pelos dois lados. Tipos:
 * - documento real: o ETP e o TR reais divergem; no sistema os dois saem da mesma fonte;
 * - não comparado: a comparação do M06 não leu o trecho (NAO_LIDO); nada a reproduzir.
 *
 * `matriz`: observação para o agente das matrizes, quando o M06 deixa de ligar o bloco ao campo do ETP que a
 * própria evidência compara.
 */
export type ClasseDaDerivacao = {
  tipo: "documento real" | "não comparado";
  motivo: string;
  /** VAR ou WZ que alimentam o ETP e o TR no sistema. */
  mesmaFonte: string[];
  dv?: string;
  matriz?: string;
};

export const CLASSIFICACAO_117: Record<string, ClasseDaDerivacao> = {
  "TR-1.1": {
    tipo: "documento real",
    motivo:
      "o TR real acrescentou ao objeto o regime de consignação com comodato, que o ETP não trazia; o comodato está fora do sistema (P24, WZ-56 desligada) e o objeto sai da mesma VAR nos dois",
    mesmaFonte: ["VAR-008"],
  },
  "TR-1.1.TAB1": {
    tipo: "não comparado",
    motivo: "no TR real a tabela de itens está em anexo que a extração não leu (NAO_LIDO); no sistema a tabela do ETP-07.02 é a mesma do TR",
    mesmaFonte: ["VAR-158"],
  },
  "TR-4.1": {
    tipo: "documento real",
    motivo:
      "o ETP real tratou de sustentabilidade numa seção própria e citou a IN SLTI/MP 01/2010, sem conferência; o TR remeteu ao ETP; no sistema os critérios saem da mesma VAR nos dois",
    mesmaFonte: ["VAR-044"],
    dv: "DV-18",
  },
  "TR-4.H04": {
    tipo: "documento real",
    motivo: "o ETP real justificou amostra e o TR real não a previu; no sistema a amostra do TR e a justificativa no ETP saem da mesma pergunta do wizard",
    mesmaFonte: ["WZ-20"],
    matriz: "M06 sem campo do ETP no TR-4.H04, embora a evidência do par 117 compare com o ETP (amostra no ETP-04.01)",
  },
  "TR-5.1": {
    tipo: "documento real",
    motivo: "prazos de entrega com termo inicial diferente no ETP e no TR reais; no sistema prazo e termo inicial saem das mesmas VAR",
    mesmaFonte: ["VAR-060", "VAR-061"],
  },
  "TR-5.4": {
    tipo: "documento real",
    motivo: "endereços de entrega diferentes no ETP e no TR reais; no sistema os dois leem a mesma VAR",
    mesmaFonte: ["VAR-064"],
    matriz: "M06 sem campo do ETP no TR-5.4, embora a VAR-064 esteja no ETP-04.01 (M05.usada_em)",
  },
  "TR-5.5": {
    tipo: "documento real",
    motivo:
      "o TR real trouxe as duas opções de garantia do grupo GA-07 e o ETP não tratou de garantia; no sistema o grupo admite uma opção só, escolhida pela categoria do bem, que é a mesma nos dois",
    mesmaFonte: ["VAR-019"],
    matriz: "M06 sem campo do ETP no TR-5.5; a categoria do bem (VAR-019) já vai para o ETP-06.01 pelo M06 do TR-5.6",
  },
  "TR-9.4": {
    tipo: "documento real",
    motivo: "o ETP real indicou menor preço por item e o TR real, por grupo; no sistema o critério por grupo sai da mesma VAR nos dois",
    mesmaFonte: ["VAR-031", "VAR-112"],
  },
  "TR-9.34": {
    tipo: "documento real",
    motivo: "o ETP real exigiu atestado 'pelo período mínimo de 12 meses', o que a NE-071 veda (VAL-029); o TR real usou o texto genérico; no sistema os atestados saem da mesma VAR nos dois",
    mesmaFonte: ["VAR-085"],
    dv: "DV-12",
  },
};
