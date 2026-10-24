"use server";
/**
 * Ações de login e de senha (decisão 0012). Cada ação confere a sessão de novo; nada vem de confiança do
 * navegador.
 */
import { sql } from "drizzle-orm";
import { redirect } from "next/navigation";
import { registrar } from "../auditoria/registrar.ts";
import { bancoDaAplicacao, comoUsuario } from "../dados/conexao.ts";
import { problemaDaSenhaNova } from "./senha.ts";
import { carregarUsuario, clienteDaRequisicao, exigirUsuario, inicioDoPerfil } from "./sessao.ts";

/** email: devolvido no erro de login, para o campo não voltar vazio. */
export type Resultado = { erro?: string; aviso?: string; senhaProvisoria?: string; email?: string } | null;

/** Só caminho interno ("/processos/..."), nunca outro site. */
function destinoSeguro(volta: unknown): string | null {
  return typeof volta === "string" && volta.startsWith("/") && !volta.startsWith("//") && !volta.startsWith("/\\") ? volta : null;
}

const texto = (dados: FormData, campo: string) => String(dados.get(campo) ?? "");

export async function entrar(_anterior: Resultado, dados: FormData): Promise<Resultado> {
  const email = texto(dados, "email").trim().toLowerCase();
  const senha = texto(dados, "senha");
  if (!email || !senha) return { erro: "Informe o e-mail e a senha.", email };
  const supabase = await clienteDaRequisicao();
  const { data, error } = await supabase.auth.signInWithPassword({ email, password: senha });
  if (error || !data.user) return { erro: "E-mail ou senha incorretos, ou acesso desativado. Se esqueceu a senha, procure a TI.", email };
  const u = await carregarUsuario(data.user.id);
  if (!u) {
    await supabase.auth.signOut();
    return { erro: "Acesso desativado ou não cadastrado no Licita+. Procure a TI.", email };
  }
  await comoUsuario(bancoDaAplicacao(), u.id, (tx) => registrar(tx, { usuarioId: u.id, omId: u.omId, acao: "LOGIN" }));
  if (u.senhaProvisoria) redirect("/trocar-senha");
  redirect(destinoSeguro(dados.get("volta")) ?? inicioDoPerfil(u.perfil));
}

export async function trocarSenha(_anterior: Resultado, dados: FormData): Promise<Resultado> {
  const u = await exigirUsuario(undefined, { permitirSenhaProvisoria: true });
  const atual = texto(dados, "atual");
  const nova = texto(dados, "nova");
  const problema = problemaDaSenhaNova(nova, texto(dados, "confirmacao"), atual);
  if (problema) return { erro: problema };
  const supabase = await clienteDaRequisicao();
  // Confere a senha atual entrando de novo: quem achou a sessão aberta não troca a senha sem sabê-la.
  const { error: erroAtual } = await supabase.auth.signInWithPassword({ email: u.email, password: atual });
  if (erroAtual) return { erro: "A senha atual não confere." };
  const { error } = await supabase.auth.updateUser({ password: nova });
  if (error) return { erro: "Não foi possível trocar a senha. Tente outra senha." };
  await comoUsuario(bancoDaAplicacao(), u.id, async (tx) => {
    await tx.execute(sql`select privado.concluir_troca_de_senha()`);
    await registrar(tx, { usuarioId: u.id, omId: u.omId, acao: "SENHA_TROCADA" });
  });
  redirect(inicioDoPerfil(u.perfil));
}
