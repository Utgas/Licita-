"use client";
import { useActionState } from "react";
import { Botao, Campo, Mensagem } from "../../componentes/formulario.tsx";
import { CHECKLISTS, MODALIDADES } from "../../componentes/rotulos.ts";
import { criarProcesso } from "../acoes.ts";

export function FormularioNovoProcesso() {
  const [resultado, acao] = useActionState(criarProcesso, null);
  return (
    <form action={acao} className="flex max-w-xl flex-col gap-5">
      <Campo rotulo="Número do processo (NUP)" nome="numero" autoComplete="off" ajuda="Use dados fictícios no ambiente de desenvolvimento." />
      <Campo rotulo="Objeto (resumo)" nome="objeto" autoComplete="off" />
      <fieldset className="flex flex-col gap-2">
        <legend className="text-sm font-medium">Modalidade</legend>
        {Object.entries(MODALIDADES).map(([codigo, rotulo]) => (
          <label key={codigo} className="flex min-h-11 items-center gap-3">
            <input type="radio" name="modalidade" value={codigo} required className="size-5" /> {rotulo}
          </label>
        ))}
      </fieldset>
      <fieldset className="flex flex-col gap-2">
        <legend className="text-sm font-medium">Registro de preços?</legend>
        {[["SIM", "Sim"], ["NAO", "Não"]].map(([codigo, rotulo]) => (
          <label key={codigo} className="flex min-h-11 items-center gap-3">
            <input type="radio" name="registroPrecos" value={codigo} required className="size-5" /> {rotulo}
          </label>
        ))}
      </fieldset>
      <fieldset className="flex flex-col gap-2">
        <legend className="text-sm font-medium">Checklists técnicos usados</legend>
        {Object.entries(CHECKLISTS).map(([codigo, rotulo]) => (
          <label key={codigo} className="flex min-h-11 items-center gap-3">
            <input type="checkbox" name="checklists" value={codigo} className="size-5" /> {rotulo}
          </label>
        ))}
      </fieldset>
      <Mensagem resultado={resultado} />
      <Botao>Criar processo</Botao>
    </form>
  );
}
