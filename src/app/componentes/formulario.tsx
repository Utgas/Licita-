"use client";
/** Peças de formulário com rótulo, alvo de 44 px e mensagens com texto e ícone (não só cor). */
import { type KeyboardEvent, type ReactNode, useId, useState } from "react";
import { useFormStatus } from "react-dom";
import type { Resultado } from "@/auth/acoes.ts";
import { Icone } from "./icones.tsx";
import { CLASSE_DA_CAIXA, classesDoBotao } from "./ui.tsx";

export function Campo(props: { rotulo: string; nome: string; tipo?: string; autoComplete?: string; obrigatorio?: boolean; ajuda?: string; valorInicial?: string }) {
  const id = useId();
  const senha = props.tipo === "password";
  const [visivel, setVisivel] = useState(false);
  const [maiusculas, setMaiusculas] = useState(false);
  // Senha: botão para ver o que foi digitado e aviso de Caps Lock, para o erro de digitação aparecer antes de enviar.
  const conferirMaiusculas = (e: KeyboardEvent<HTMLInputElement>) => setMaiusculas(e.getModifierState("CapsLock"));
  return (
    <div className="flex flex-col gap-1.5 text-sm font-medium text-tinta">
      <label htmlFor={id}>{props.rotulo}</label>
      <div className="flex gap-2">
        <input
          id={id}
          name={props.nome}
          type={senha && visivel ? "text" : (props.tipo ?? "text")}
          autoComplete={props.autoComplete}
          required={props.obrigatorio ?? true}
          defaultValue={props.valorInicial}
          className={CLASSE_DA_CAIXA}
          {...(senha && { autoCapitalize: "none", autoCorrect: "off", spellCheck: false, onKeyUp: conferirMaiusculas, onKeyDown: conferirMaiusculas })}
        />
        {senha && (
          <button type="button" aria-pressed={visivel} onClick={() => setVisivel((v) => !v)} className={`${classesDoBotao("secundario")} shrink-0`}>
            {visivel ? "Ocultar" : "Mostrar"}
          </button>
        )}
      </div>
      {senha && maiusculas && (
        <span className="flex items-center gap-1.5 font-normal text-atencao">
          <Icone nome="atencao" /> Caps Lock ligado.
        </span>
      )}
      {props.ajuda && <span className="font-normal text-tinta-2">{props.ajuda}</span>}
    </div>
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
