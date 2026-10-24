"use client";
import { useActionState } from "react";
import { trocarSenha } from "@/auth/acoes.ts";
import { Botao, Campo, Mensagem } from "../componentes/formulario.tsx";

export function FormularioTroca({ provisoria, tamanhoMinimo }: { provisoria: boolean; tamanhoMinimo: number }) {
  const [resultado, acao] = useActionState(trocarSenha, null);
  return (
    <form action={acao} className="flex flex-col gap-4">
      <Campo rotulo={provisoria ? "Senha provisória (recebida da TI)" : "Senha atual"} nome="atual" tipo="password" autoComplete="current-password" />
      <Campo rotulo="Senha nova" nome="nova" tipo="password" autoComplete="new-password" ajuda={`Pelo menos ${tamanhoMinimo} caracteres, com letras e números.`} />
      <Campo rotulo="Confirme a senha nova" nome="confirmacao" tipo="password" autoComplete="new-password" />
      <Mensagem resultado={resultado} />
      <Botao>Trocar a senha</Botao>
    </form>
  );
}
