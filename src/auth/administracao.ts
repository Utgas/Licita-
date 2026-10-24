"use server";
/**
 * Ações do administrador da TI (decisão 0012): criar usuário, definir senha provisória e desativar ou reativar.
 * A chave secreta só mexe no Supabase Auth; a tabela usuario é gravada com o RLS do administrador, que só alcança a
 * própria OM. Toda ação vai para a auditoria, sem a senha.
 */
import { and, eq } from "drizzle-orm";
import { revalidatePath } from "next/cache";
import { z } from "zod";
import { registrar } from "../auditoria/registrar.ts";
import { bancoDaAplicacao, comoUsuario } from "../dados/conexao.ts";
import { PERFIS, usuario } from "../dados/esquema.ts";
import type { Resultado } from "./acoes.ts";
import { gerarSenhaProvisoria } from "./senha.ts";
import { exigirUsuario } from "./sessao.ts";
import { clienteAdministrativo } from "./supabase.ts";

// Banimento longo = acesso desativado no Supabase Auth (não entra mais, nem com a senha certa).
const DESATIVADO = "876000h";

const novoUsuario = z.object({
  nome: z.string().trim().min(3, "Informe o nome completo."),
  email: z.string().trim().toLowerCase().email("E-mail inválido."),
  perfil: z.enum(PERFIS),
});

export async function criarUsuario(_anterior: Resultado, dados: FormData): Promise<Resultado> {
  const admin = await exigirUsuario("ADMINISTRADOR");
  const lido = novoUsuario.safeParse(Object.fromEntries(dados));
  if (!lido.success) return { erro: lido.error.issues[0].message };
  const { nome, email, perfil } = lido.data;
  const senha = gerarSenhaProvisoria();
  const auth = clienteAdministrativo().auth.admin;
  const { data, error } = await auth.createUser({ email, password: senha, email_confirm: true });
  if (error || !data.user) return { erro: error?.message.includes("already") ? "Já existe um usuário com esse e-mail." : "Não foi possível criar o usuário." };
  const id = data.user.id;
  try {
    await comoUsuario(bancoDaAplicacao(), admin.id, async (tx) => {
      await tx.insert(usuario).values({ id, omId: admin.omId, nome, email, perfil, senhaProvisoria: true });
      await registrar(tx, { usuarioId: admin.id, omId: admin.omId, acao: "USUARIO_CRIADO", detalhes: { usuario: id, perfil } });
    });
  } catch {
    await auth.deleteUser(id);
    return { erro: "Não foi possível cadastrar o usuário." };
  }
  revalidatePath("/admin");
  return { aviso: `Usuário criado. Entregue a senha provisória a ${nome}; ela vale só para o primeiro acesso.`, senhaProvisoria: senha };
}

/** Linha do usuário alvo, se for da OM do administrador (o RLS esconde as outras). */
async function alvoDaOm(adminId: string, alvoId: string) {
  const [linha] = await comoUsuario(bancoDaAplicacao(), adminId, (tx) => tx.select().from(usuario).where(eq(usuario.id, alvoId)));
  return linha ?? null;
}

export async function definirSenhaProvisoria(_anterior: Resultado, dados: FormData): Promise<Resultado> {
  const admin = await exigirUsuario("ADMINISTRADOR");
  const alvo = await alvoDaOm(admin.id, String(dados.get("usuario") ?? ""));
  if (!alvo) return { erro: "Usuário não encontrado." };
  const senha = gerarSenhaProvisoria();
  const { error } = await clienteAdministrativo().auth.admin.updateUserById(alvo.id, { password: senha });
  if (error) return { erro: "Não foi possível trocar a senha." };
  await comoUsuario(bancoDaAplicacao(), admin.id, async (tx) => {
    await tx.update(usuario).set({ senhaProvisoria: true }).where(and(eq(usuario.id, alvo.id), eq(usuario.omId, admin.omId)));
    await registrar(tx, { usuarioId: admin.id, omId: admin.omId, acao: "SENHA_PROVISORIA_DEFINIDA", detalhes: { usuario: alvo.id } });
  });
  revalidatePath("/admin");
  return { aviso: `Senha provisória de ${alvo.nome} definida. Entregue a ${alvo.nome}; vale só para o próximo acesso.`, senhaProvisoria: senha };
}

export async function alterarSituacao(_anterior: Resultado, dados: FormData): Promise<Resultado> {
  const admin = await exigirUsuario("ADMINISTRADOR");
  const alvo = await alvoDaOm(admin.id, String(dados.get("usuario") ?? ""));
  if (!alvo) return { erro: "Usuário não encontrado." };
  if (alvo.id === admin.id) return { erro: "Você não pode desativar o próprio acesso." };
  const ativar = !alvo.ativo;
  const { error } = await clienteAdministrativo().auth.admin.updateUserById(alvo.id, { ban_duration: ativar ? "none" : DESATIVADO });
  if (error) return { erro: "Não foi possível alterar o acesso." };
  await comoUsuario(bancoDaAplicacao(), admin.id, async (tx) => {
    await tx.update(usuario).set({ ativo: ativar }).where(and(eq(usuario.id, alvo.id), eq(usuario.omId, admin.omId)));
    await registrar(tx, { usuarioId: admin.id, omId: admin.omId, acao: ativar ? "USUARIO_REATIVADO" : "USUARIO_DESATIVADO", detalhes: { usuario: alvo.id } });
  });
  revalidatePath("/admin");
  return { aviso: `${alvo.nome}: acesso ${ativar ? "reativado" : "desativado"}.` };
}
