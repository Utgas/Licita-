import { Suspense } from "react";
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
      <main className="flex flex-col gap-4 p-6">
        <h1 className="text-2xl font-semibold">Novo processo</h1>
        <FormularioNovoProcesso />
      </main>
    </>
  );
}
