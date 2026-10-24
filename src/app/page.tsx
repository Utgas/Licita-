import { redirect } from "next/navigation";
import { Suspense } from "react";
import { exigirUsuario, inicioDoPerfil } from "@/auth/sessao.ts";
import { Carregando } from "./componentes/cabecalho.tsx";

export default function Inicio() {
  return (
    <Suspense fallback={<Carregando />}>
      <Encaminhar />
    </Suspense>
  );
}

async function Encaminhar(): Promise<null> {
  const usuario = await exigirUsuario();
  redirect(inicioDoPerfil(usuario.perfil));
}
