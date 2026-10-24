import { desc } from "drizzle-orm";
import Link from "next/link";
import { Suspense } from "react";
import { exigirUsuario } from "@/auth/sessao.ts";
import { bancoDaAplicacao, comoUsuario } from "@/dados/conexao.ts";
import { auditoria, usuario } from "@/dados/esquema.ts";
import { Cabecalho, Carregando } from "../../componentes/cabecalho.tsx";

const LIMITE = 300;

/** Auditoria da OM, só leitura (decisão 0012). */
export default function Auditoria() {
  return (
    <Suspense fallback={<Carregando />}>
      <Conteudo />
    </Suspense>
  );
}

async function Conteudo() {
  const admin = await exigirUsuario("ADMINISTRADOR");
  const { linhas, nomes } = await comoUsuario(bancoDaAplicacao(), admin.id, async (tx) => ({
    linhas: await tx.select().from(auditoria).orderBy(desc(auditoria.id)).limit(LIMITE),
    nomes: new Map((await tx.select({ id: usuario.id, nome: usuario.nome }).from(usuario)).map((u) => [u.id, u.nome])),
  }));
  return (
    <>
      <Cabecalho usuario={admin} />
      <main className="flex flex-col gap-4 p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-2xl font-semibold">Auditoria</h1>
          <Link href="/admin" className="flex min-h-11 items-center text-blue-800 underline">
            Voltar aos usuários
          </Link>
        </div>
        <p className="text-zinc-700">Últimos {LIMITE} registros da OM, do mais recente ao mais antigo. Ninguém altera nem apaga estes registros.</p>
        <table className="w-full border-collapse text-left text-sm">
          <thead>
            <tr className="border-b border-zinc-400">
              <th className="p-2">Quando</th>
              <th className="p-2">Quem</th>
              <th className="p-2">Ação</th>
              <th className="p-2">Detalhes</th>
            </tr>
          </thead>
          <tbody>
            {linhas.map((l) => (
              <tr key={l.id} className="border-b border-zinc-200 align-top">
                <td className="p-2 whitespace-nowrap">{new Date(l.em).toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" })}</td>
                <td className="p-2">{l.usuarioId ? (nomes.get(l.usuarioId) ?? l.usuarioId) : "Sistema"}</td>
                <td className="p-2">{l.acao}</td>
                <td className="p-2 font-mono text-xs break-all">
                  {[
                    ...Object.entries(l.detalhes as Record<string, unknown>).map(([k, v]) => `${k}: ${k === "usuario" && typeof v === "string" ? (nomes.get(v) ?? v) : String(v)}`),
                    l.processoId && `processo: ${l.processoId}`,
                    l.hashArquivo && `arquivo: ${l.hashArquivo}`,
                    l.hashPacote && `pacote: ${l.hashPacote}`,
                    l.hashPdf && `PDF: ${l.hashPdf}`,
                  ]
                    .filter(Boolean)
                    .join(" · ")}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </main>
    </>
  );
}
