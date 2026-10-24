import { Suspense } from "react";
import { exigirUsuario } from "@/auth/sessao.ts";
import { Cabecalho, Carregando } from "../componentes/cabecalho.tsx";

/** Painel do operador. A lista de processos e o novo processo entram no passo 5. */
export default function Processos() {
  return (
    <Suspense fallback={<Carregando />}>
      <Conteudo />
    </Suspense>
  );
}

async function Conteudo() {
  const usuario = await exigirUsuario("OPERADOR");
  return (
    <>
      <Cabecalho usuario={usuario} />
      <main className="flex flex-col gap-4 p-6">
        <h1 className="text-2xl font-semibold">Processos</h1>
        <p className="text-zinc-700">A lista de processos e o formulário de novo processo chegam no passo 5 do Marco 2.</p>
      </main>
    </>
  );
}
