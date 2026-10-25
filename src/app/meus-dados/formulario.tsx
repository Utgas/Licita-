"use client";
import { useActionState } from "react";
import { fazerSolicitacao, responderSolicitacao } from "@/auth/titular.ts";
import { Botao, Mensagem } from "../componentes/formulario.tsx";
import { TIPOS_DE_SOLICITACAO } from "../componentes/rotulos.ts";
import { CLASSE_DA_CAIXA } from "../componentes/ui.tsx";

export function NovoPedido() {
  const [resultado, acao] = useActionState(fazerSolicitacao, null);
  return (
    <form action={acao} className="flex max-w-2xl flex-col gap-4">
      <label className="flex flex-col gap-1.5 text-sm font-medium">
        O que você pede
        <select name="tipo" required defaultValue="" className={CLASSE_DA_CAIXA}>
          <option value="" disabled>
            Escolha…
          </option>
          {Object.entries(TIPOS_DE_SOLICITACAO).map(([codigo, rotulo]) => (
            <option key={codigo} value={codigo}>
              {rotulo}
            </option>
          ))}
        </select>
      </label>
      <label className="flex flex-col gap-1.5 text-sm font-medium">
        Descreva o pedido
        <textarea name="descricao" required minLength={5} maxLength={2000} rows={4} className={`${CLASSE_DA_CAIXA} py-2`} />
        <span className="font-normal text-tinta-2">Não escreva aqui dados de processos nem de outras pessoas.</span>
      </label>
      <Mensagem resultado={resultado} />
      <div>
        <Botao>Enviar pedido</Botao>
      </div>
    </form>
  );
}

export function ResponderPedido({ id }: { id: number }) {
  const [resultado, acao] = useActionState(responderSolicitacao, null);
  return (
    <form action={acao} className="flex flex-col gap-3">
      <input type="hidden" name="id" value={id} />
      <label className="flex flex-col gap-1.5 text-sm font-medium">
        Resposta ao usuário
        <textarea name="resposta" required minLength={5} maxLength={2000} rows={3} className={`${CLASSE_DA_CAIXA} py-2`} />
      </label>
      <Mensagem resultado={resultado} />
      <div>
        <Botao variante="secundario">Registrar resposta</Botao>
      </div>
    </form>
  );
}
