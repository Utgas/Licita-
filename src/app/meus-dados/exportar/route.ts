/** Cópia dos dados pessoais do usuário em JSON (LGPD, art. 18, II e V): gerada na hora, entregue e não guardada. */
import { registrar } from "@/auditoria/registrar.ts";
import { exigirUsuario } from "@/auth/sessao.ts";
import { bancoDaAplicacao, comoUsuario } from "@/dados/conexao.ts";
import { dadosPessoais } from "@/dados/dados-pessoais.ts";

export async function GET() {
  const u = await exigirUsuario();
  const dados = await comoUsuario(bancoDaAplicacao(), u.id, async (tx) => {
    const lidos = await dadosPessoais(tx, u);
    await registrar(tx, { usuarioId: u.id, omId: u.omId, acao: "DADOS_PESSOAIS_EXPORTADOS" });
    return lidos;
  });
  return new Response(JSON.stringify({ sistema: "Licita+", ...dados }, null, 2), {
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Content-Disposition": 'attachment; filename="meus-dados-licita.json"',
      "Cache-Control": "no-store",
    },
  });
}
