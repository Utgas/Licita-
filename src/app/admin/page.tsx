import { asc } from "drizzle-orm";
import Link from "next/link";
import { Suspense } from "react";
import { exigirUsuario } from "@/auth/sessao.ts";
import { bancoDaAplicacao, comoUsuario } from "@/dados/conexao.ts";
import { usuario } from "@/dados/esquema.ts";
import { Cabecalho, Carregando } from "../componentes/cabecalho.tsx";
import { AcoesDoUsuario, NovoUsuario } from "./formularios.tsx";

/** Tela do administrador da TI (decisão 0012): usuários da OM, senhas provisórias e acesso à auditoria. */
export default function Administracao() {
  return (
    <Suspense fallback={<Carregando />}>
      <Conteudo />
    </Suspense>
  );
}

async function Conteudo() {
  const admin = await exigirUsuario("ADMINISTRADOR");
  const usuarios = await comoUsuario(bancoDaAplicacao(), admin.id, (tx) => tx.select().from(usuario).orderBy(asc(usuario.nome)));
  return (
    <>
      <Cabecalho usuario={admin} />
      <main className="flex flex-col gap-8 p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-2xl font-semibold">Usuários da OM</h1>
          <Link href="/admin/auditoria" className="flex min-h-11 items-center text-blue-800 underline">
            Ver a auditoria
          </Link>
        </div>
        <table className="w-full border-collapse text-left text-sm">
          <thead>
            <tr className="border-b border-zinc-400">
              <th className="p-2">Nome</th>
              <th className="p-2">E-mail</th>
              <th className="p-2">Perfil</th>
              <th className="p-2">Situação</th>
              <th className="p-2">Ações</th>
            </tr>
          </thead>
          <tbody>
            {usuarios.map((u) => (
              <tr key={u.id} className="border-b border-zinc-200 align-top">
                <td className="p-2">{u.nome}</td>
                <td className="p-2">{u.email}</td>
                <td className="p-2">{u.perfil === "ADMINISTRADOR" ? "Administrador da TI" : "Operador"}</td>
                <td className="p-2">
                  {u.ativo ? "Ativo" : "Desativado"}
                  {u.ativo && u.senhaProvisoria ? " (senha provisória)" : ""}
                </td>
                <td className="p-2">
                  <AcoesDoUsuario id={u.id} ativo={u.ativo} eVoce={u.id === admin.id} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <section className="flex flex-col gap-3">
          <h2 className="text-xl font-semibold">Novo usuário</h2>
          <p className="text-zinc-700">O sistema gera uma senha provisória. Entregue-a à pessoa; no primeiro acesso ela cria a própria senha.</p>
          <NovoUsuario />
        </section>
      </main>
    </>
  );
}
