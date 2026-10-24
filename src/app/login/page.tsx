import { Suspense } from "react";
import { Carregando } from "../componentes/cabecalho.tsx";
import { FormularioLogin } from "./formulario-login.tsx";

export default function PaginaDeLogin({ searchParams }: PageProps<"/login">) {
  return (
    <main className="mx-auto flex w-full max-w-sm flex-1 flex-col justify-center gap-6 p-6">
      <h1 className="text-2xl font-semibold">Licita+</h1>
      <p className="text-zinc-700">Entre com o e-mail e a senha cadastrados pela TI.</p>
      <Suspense fallback={<Carregando />}>
        <Formulario searchParams={searchParams} />
      </Suspense>
    </main>
  );
}

async function Formulario({ searchParams }: Pick<PageProps<"/login">, "searchParams">) {
  const { volta } = await searchParams;
  return <FormularioLogin volta={typeof volta === "string" ? volta : null} />;
}
