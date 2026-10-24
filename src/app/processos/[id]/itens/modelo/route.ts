/** Modelo da planilha de itens para baixar (colunas fixas). Exige sessão de operador. */
import { exigirUsuario } from "@/auth/sessao.ts";
import { modeloDaPlanilha } from "@/dados/planilha-itens.ts";

export async function GET() {
  await exigirUsuario("OPERADOR");
  return new Response(Buffer.from(await modeloDaPlanilha()), {
    headers: {
      "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      "Content-Disposition": 'attachment; filename="modelo-itens-licita.xlsx"',
      "Cache-Control": "no-store",
    },
  });
}
