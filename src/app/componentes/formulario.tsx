"use client";
/** Peças de formulário com rótulo, alvo de 44 px e mensagens com texto e ícone (não só cor). */
import type { ReactNode } from "react";
import { useFormStatus } from "react-dom";
import type { Resultado } from "@/auth/acoes.ts";
import { Icone } from "./icones.tsx";
import { CLASSE_DA_CAIXA, classesDoBotao } from "./ui.tsx";

export function Campo(props: { rotulo: string; nome: string; tipo?: string; autoComplete?: string; obrigatorio?: boolean; ajuda?: string; valorInicial?: string }) {
  return (
    <label className="flex flex-col gap-1.5 text-sm font-medium text-tinta">
      {props.rotulo}
      <input name={props.nome} type={props.tipo ?? "text"} autoComplete={props.autoComplete} required={props.obrigatorio ?? true} defaultValue={props.valorInicial} className={CLASSE_DA_CAIXA} />
      {props.ajuda && <span className="font-normal text-tinta-2">{props.ajuda}</span>}
    </label>
  );
}

export function Botao({ children, variante = "principal" }: { children: ReactNode; variante?: "principal" | "secundario" }) {
  const { pending } = useFormStatus();
  return (
    <button type="submit" disabled={pending} className={classesDoBotao(variante)}>
      {pending ? "Aguarde…" : children}
    </button>
  );
}

/** Erro ("Erro:", trava), aviso ("Feito:", ok) e a senha provisória, mostrada uma vez. */
export function Mensagem({ resultado }: { resultado: Resultado }) {
  if (!resultado) return null;
  return (
    <div aria-live="polite" className="flex flex-col gap-2">
      {resultado.erro && (
        <p className="flex items-start gap-2 border border-l-4 border-trava/40 border-l-trava bg-trava-fundo p-3 text-trava">
          <Icone nome="trava" className="mt-0.5" />
          <span>Erro: {resultado.erro}</span>
        </p>
      )}
      {resultado.aviso && (
        <p className="flex items-start gap-2 border border-l-4 border-ok/30 border-l-ok bg-ok-fundo p-3 text-ok">
          <Icone nome="ok" className="mt-0.5" />
          <span>Feito: {resultado.aviso}</span>
        </p>
      )}
      {resultado.senhaProvisoria && (
        <p className="border border-linha-forte bg-folha p-3 text-tinta">
          Senha provisória (aparece só agora): <code className="font-mono text-lg font-medium tracking-wider">{resultado.senhaProvisoria}</code>
        </p>
      )}
    </div>
  );
}
