import { Suspense } from "react";
import { PaginaDeAcesso } from "../componentes/acesso.tsx";
import { Carregando } from "../componentes/cabecalho.tsx";
import { FormularioLogin } from "./formulario-login.tsx";

export default function PaginaDeLogin({ searchParams }: PageProps<"/login">) {
  return (
    <PaginaDeAcesso titulo="Entrar">
      <p className="text-tinta-2">Use o e-mail e a senha cadastrados pela TI.</p>
      <Suspense fallback={<Carregando />}>
        <Formulario searchParams={searchParams} />
      </Suspense>
    </PaginaDeAcesso>
  );
}

async function Formulario({ searchParams }: Pick<PageProps<"/login">, "searchParams">) {
  const { volta } = await searchParams;
  return <FormularioLogin volta={typeof volta === "string" ? volta : null} />;
}
