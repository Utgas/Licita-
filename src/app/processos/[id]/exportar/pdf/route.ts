/**
 * PDF da minuta (passo 11): montado na hora, entregue e descartado. Só sai sem travas; o hash do arquivo e o da
 * minuta vão para a exportação e para a auditoria, na mesma transação.
 */
import { createHash } from "node:crypto";
import { EntradaRecusada, gravarNoProcesso } from "@/dados/acesso-processo.ts";
import { exportacao } from "@/dados/esquema.ts";
import { minutaDoProcesso } from "@/dados/processos.ts";
import { gerarPdf } from "@/exportacao/pdf.tsx";
import { hashDaMinuta } from "@/exportacao/secoes.ts";

export async function GET(_request: Request, contexto: RouteContext<"/processos/[id]/exportar/pdf">) {
  const { id } = await contexto.params;
  try {
    const { pdf, nome } = await gravarNoProcesso(
      id,
      "PDF_BAIXADO",
      async (tx, p, usuario) => {
        const minuta = minutaDoProcesso(p);
        if (minuta.bloqueada) throw new EntradaRecusada("A minuta tem travas. Resolva-as na tela da minuta antes de exportar.");
        const pdf = await gerarPdf({ minuta, numeroDoProcesso: p.processo.numero, cabecalhoDaOm: p.om.cabecalho.length ? p.om.cabecalho : [p.om.nome] });
        const hashPdf = createHash("sha256").update(pdf).digest("hex");
        await tx.insert(exportacao).values({ processoId: id, tipo: "PDF", hashPdf, feitoPor: usuario.id });
        const nome = `minuta-tr-${p.processo.numero.replace(/[^0-9A-Za-z]+/g, "-")}.pdf`;
        return { resultado: { pdf, nome }, hashPdf, detalhes: { hashMinuta: hashDaMinuta(minuta), lacunas: minuta.lacunasNoTexto.length } };
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
