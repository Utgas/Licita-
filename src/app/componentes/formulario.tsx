"use client";
/** Peças de formulário com rótulo, alvo de 44 px e mensagens com texto (não só cor). */
import type { ReactNode } from "react";
import { useFormStatus } from "react-dom";
import type { Resultado } from "@/auth/acoes.ts";

export function Campo(props: { rotulo: string; nome: string; tipo?: string; autoComplete?: string; obrigatorio?: boolean; ajuda?: string; valorInicial?: string }) {
  return (
    <label className="flex flex-col gap-1 text-sm font-medium text-zinc-900">
      {props.rotulo}
      <input
        name={props.nome}
        type={props.tipo ?? "text"}
        autoComplete={props.autoComplete}
        required={props.obrigatorio ?? true}
        defaultValue={props.valorInicial}
        className="min-h-11 rounded border border-zinc-500 px-3 text-base font-normal focus:outline-2 focus:outline-blue-700"
      />
      {props.ajuda && <span className="font-normal text-zinc-700">{props.ajuda}</span>}
    </label>
  );
}

export function Botao({ children, variante = "principal" }: { children: ReactNode; variante?: "principal" | "secundario" }) {
  const { pending } = useFormStatus();
  const estilo =
    variante === "principal"
      ? "bg-blue-800 text-white hover:bg-blue-900"
      : "border border-zinc-600 bg-white text-zinc-900 hover:bg-zinc-100";
  return (
    <button type="submit" disabled={pending} className={`min-h-11 rounded px-4 font-medium disabled:opacity-60 ${estilo}`}>
      {pending ? "Aguarde…" : children}
    </button>
  );
}

/** Erro (vermelho, com "Erro:"), aviso (verde, com "Feito:") e a senha provisória, mostrada uma vez. */
export function Mensagem({ resultado }: { resultado: Resultado }) {
  if (!resultado) return null;
  return (
    <div aria-live="polite" className="flex flex-col gap-2">
      {resultado.erro && <p className="rounded border border-red-800 bg-red-50 p-3 text-red-900">Erro: {resultado.erro}</p>}
      {resultado.aviso && <p className="rounded border border-green-800 bg-green-50 p-3 text-green-900">Feito: {resultado.aviso}</p>}
      {resultado.senhaProvisoria && (
        <p className="rounded border border-zinc-700 bg-zinc-50 p-3 text-zinc-900">
          Senha provisória (aparece só agora): <code className="text-lg font-bold tracking-wider">{resultado.senhaProvisoria}</code>
        </p>
      )}
    </div>
  );
}
