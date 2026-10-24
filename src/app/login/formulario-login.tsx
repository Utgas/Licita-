"use client";
import Link from "next/link";
import { useActionState } from "react";
import { entrar } from "@/auth/acoes.ts";
import { Botao, Campo, Mensagem } from "../componentes/formulario.tsx";

export function FormularioLogin({ volta }: { volta: string | null }) {
  const [resultado, acao] = useActionState(entrar, null);
  return (
    <form action={acao} className="flex flex-col gap-4">
      {volta && <input type="hidden" name="volta" value={volta} />}
      <Campo key={resultado?.email} rotulo="E-mail" nome="email" tipo="email" autoComplete="username" valorInicial={resultado?.email} />
      <Campo rotulo="Senha" nome="senha" tipo="password" autoComplete="current-password" />
      <Mensagem resultado={resultado} />
      <Botao>Entrar</Botao>
      <Link href="/esqueci-senha" className="flex min-h-11 w-fit items-center text-link underline">
        Esqueci minha senha
      </Link>
    </form>
  );
}
