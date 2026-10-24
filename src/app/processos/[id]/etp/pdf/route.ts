/**
 * PDF do ETP (Marco 3, passo 7): montado na hora, entregue e descartado. O hash do arquivo e o do ETP vão só para a
 * auditoria, para não contar como PDF do TR (decisão 0015). Só sai com as dúvidas da leitura do checklist resolvidas.
 */
import { createHash } from "node:crypto";
import { EntradaRecusada, gravarNoProcesso } from "@/dados/acesso-processo.ts";
import { documentosDoProcesso } from "@/dados/etp.ts";
import { etpLiberado, hashDoEtp } from "@/exportacao/etp.ts";
import { gerarPdfDoEtp } from "@/exportacao/pdf.tsx";

export async function GET(_request: Request, contexto: RouteContext<"/processos/[id]/etp/pdf">) {
  const { id } = await contexto.params;
  try {
    const { pdf, nome } = await gravarNoProcesso(
      id,
      "PDF_ETP_BAIXADO",
      async (_tx, p) => {
        const { minuta, etp } = documentosDoProcesso(p);
        if (!etpLiberado(minuta)) throw new EntradaRecusada("Há dúvidas da leitura do checklist sem resposta. Resolva-as na tela do checklist antes de baixar o ETP.");
        const pdf = await gerarPdfDoEtp({ etp, numeroDoProcesso: p.processo.numero, cabecalhoDaOm: p.om.cabecalho.length ? p.om.cabecalho : [p.om.nome] });
        const hashPdf = createHash("sha256").update(pdf).digest("hex");
        const nome = `minuta-etp-${p.processo.numero.replace(/[^0-9A-Za-z]+/g, "-")}.pdf`;
        return { resultado: { pdf, nome }, hashPdf, detalhes: { hashEtp: hashDoEtp(etp), pendencias: etp.pendencias.length } };
      },
      { permitirConcluido: true },
    );
    return new Response(new Uint8Array(pdf), {
      headers: {
        "Content-Type": "application/pdf",
        "Content-Disposition": `attachment; filename="${nome}"`,
        "Cache-Control": "no-store",
      },
    });
  } catch (e) {
    if (e instanceof EntradaRecusada) return new Response(e.message, { status: 409, headers: { "Content-Type": "text/plain; charset=utf-8" } });
    throw e;
  }
}
