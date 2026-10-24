"use client";
import { useActionState } from "react";
import { alterarSituacao, criarUsuario, definirSenhaProvisoria } from "@/auth/administracao.ts";
import { Botao, Campo, Mensagem } from "../componentes/formulario.tsx";

export function NovoUsuario() {
  const [resultado, acao] = useActionState(criarUsuario, null);
  return (
    <form action={acao} className="flex max-w-md flex-col gap-4">
      <Campo rotulo="Nome completo" nome="nome" autoComplete="off" />
      <Campo rotulo="E-mail" nome="email" tipo="email" autoComplete="off" />
      <label className="flex flex-col gap-1 text-sm font-medium">
        Perfil
        <select name="perfil" className="min-h-11 rounded border border-zinc-500 px-3 text-base font-normal" defaultValue="OPERADOR">
          <option value="OPERADOR">Operador (elabora TR e ETP)</option>
          <option value="ADMINISTRADOR">Administrador da TI</option>
        </select>
      </label>
      <Mensagem resultado={resultado} />
      <Botao>Criar usuário com senha provisória</Botao>
    </form>
  );
}

/** Botões de uma linha da lista: senha provisória e desativar/reativar. */
export function AcoesDoUsuario({ id, ativo, eVoce }: { id: string; ativo: boolean; eVoce: boolean }) {
  const [senha, acaoSenha] = useActionState(definirSenhaProvisoria, null);
  const [situacao, acaoSituacao] = useActionState(alterarSituacao, null);
  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap gap-2">
        <form action={acaoSenha}>
          <input type="hidden" name="usuario" value={id} />
          <Botao variante="secundario">Definir senha provisória</Botao>
        </form>
        {!eVoce && (
          <form action={acaoSituacao}>
            <input type="hidden" name="usuario" value={id} />
            <Botao variante="secundario">{ativo ? "Desativar acesso" : "Reativar acesso"}</Botao>
          </form>
        )}
      </div>
      <Mensagem resultado={senha} />
      <Mensagem resultado={situacao} />
    </div>
  );
}
