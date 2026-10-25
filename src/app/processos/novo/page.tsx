import Link from "next/link";
import { Suspense } from "react";
import { Icone } from "../../componentes/icones.tsx";
import { exigirUsuario } from "@/auth/sessao.ts";
import { Cabecalho, Carregando } from "../../componentes/cabecalho.tsx";
import { FormularioNovoProcesso } from "./formulario.tsx";

export default function NovoProcesso() {
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
      <main id="conteudo" className="mx-auto flex w-full max-w-3xl flex-col gap-6 px-4 py-6 md:px-6">
        <div className="flex flex-col gap-1">
          <Link href="/processos" className="flex w-fit items-center gap-1.5 text-sm text-tinta-2 underline decoration-linha-forte hover:text-tinta">
            <Icone nome="voltar" tamanho={14} />
            Processos
          </Link>
          <h1 className="text-2xl font-semibold tracking-tight">Novo processo</h1>
          <p className="text-tinta-2">Dados de identificação. O resto vem do checklist, dos itens e do wizard.</p>
        </div>
        <div className="border border-linha bg-folha p-5 md:p-8">
          <FormularioNovoProcesso />
        </div>
      </main>
    </>
  );
}
