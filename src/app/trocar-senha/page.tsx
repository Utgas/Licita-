import { Suspense } from "react";
import { TAMANHO_MINIMO } from "@/auth/senha.ts";
import { exigirUsuario } from "@/auth/sessao.ts";
import { Cabecalho, Carregando } from "../componentes/cabecalho.tsx";
import { FormularioTroca } from "./formulario-troca.tsx";

export default function TrocarSenha() {
  return (
    <Suspense fallback={<Carregando />}>
      <Conteudo />
    </Suspense>
  );
}

async function Conteudo() {
  const usuario = await exigirUsuario(undefined, { permitirSenhaProvisoria: true });
  return (
    <>
      <Cabecalho usuario={usuario} />
      <main className="mx-auto flex w-full max-w-md flex-col gap-4 p-6">
        <h1 className="text-2xl font-semibold">{usuario.senhaProvisoria ? "Crie a sua senha" : "Alterar minha senha"}</h1>
        {usuario.senhaProvisoria && (
          <p className="rounded border border-amber-700 bg-amber-50 p-3 text-amber-950">
            Atenção: você entrou com uma senha provisória da TI. Crie a sua senha para continuar.
          </p>
        )}
        <FormularioTroca provisoria={usuario.senhaProvisoria} tamanhoMinimo={TAMANHO_MINIMO} />
      </main>
    </>
  );
}
