import { asc } from "drizzle-orm";
import { TituloDeSecao } from "../componentes/ui.tsx";
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
      <main id="conteudo" className="mx-auto flex w-full max-w-[1400px] flex-col gap-8 px-4 py-6 md:px-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-2xl font-semibold">Usuários da OM</h1>
          <Link href="/admin/auditoria" className="flex min-h-11 items-center text-link underline">
            Ver a auditoria
          </Link>
        </div>
        <table className="w-full border-collapse border border-linha bg-folha text-left text-sm">
          <thead>
            <tr className="border-b border-linha-forte bg-papel text-xs uppercase tracking-wide text-tinta-2">
              <th className="px-3 py-2.5 font-medium">Nome</th>
              <th className="px-3 py-2.5 font-medium">E-mail</th>
              <th className="px-3 py-2.5 font-medium">Perfil</th>
              <th className="px-3 py-2.5 font-medium">Situação</th>
              <th className="px-3 py-2.5 font-medium">Ações</th>
            </tr>
          </thead>
          <tbody>
            {usuarios.map((u) => (
              <tr key={u.id} className="border-b border-linha align-top">
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
        <section className="flex flex-col gap-4 border border-linha bg-folha p-4 md:p-5">
          <TituloDeSecao>Novo usuário</TituloDeSecao>
          <p className="text-tinta-2">O sistema gera uma senha provisória. Entregue-a à pessoa; no primeiro acesso ela cria a própria senha.</p>
          <NovoUsuario />
        </section>
      </main>
    </>
  );
}
