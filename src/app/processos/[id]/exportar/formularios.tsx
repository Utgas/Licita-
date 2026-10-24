"use client";
/** Botão "Copiar" de cada seção e confirmação de conclusão (passo 11). */
import { useActionState, useState, useTransition } from "react";
import type { Resultado } from "@/auth/acoes.ts";
import { Botao, Mensagem } from "../../../componentes/formulario.tsx";

export function Copiar({ texto, secao, copiada, registrar }: { texto: string; secao: string; copiada: boolean; registrar: (secao: string) => Promise<Resultado> }) {
  const [estado, setEstado] = useState<"" | "copiado" | "erro">(copiada ? "copiado" : "");
  const [mensagem, setMensagem] = useState("");
  const [pendente, iniciar] = useTransition();
  const copiar = () =>
    iniciar(async () => {
      try {
        await navigator.clipboard.writeText(texto);
      } catch {
        setEstado("erro");
        setMensagem("O navegador não deixou copiar. Abra 'Ver o texto' e copie à mão.");
        return;
      }
      const r = await registrar(secao);
      if (r?.erro) {
        setEstado("erro");
        setMensagem(r.erro);
        return;
      }
      setEstado("copiado");
      setMensagem("");
    });
  return (
    <div className="flex flex-wrap items-center gap-3">
      <button type="button" onClick={copiar} disabled={pendente} className="min-h-11 rounded bg-blue-800 px-4 font-medium text-white hover:bg-blue-900 disabled:opacity-60">
        {pendente ? "Copiando…" : "Copiar"}
      </button>
      {estado === "copiado" && <span className="rounded border border-green-800 bg-green-50 px-2 py-1 text-green-900">✓ Copiado</span>}
      {estado === "erro" && <span className="rounded border border-red-800 bg-red-50 px-2 py-1 text-red-900">Erro: {mensagem}</span>}
    </div>
  );
}

export function Concluir({ acao }: { acao: (anterior: Resultado, dados: FormData) => Promise<Resultado> }) {
  const [resultado, enviar] = useActionState(acao, null);
  return (
    <form action={enviar} className="flex flex-col gap-3">
      <label className="flex min-h-11 items-center gap-3">
        <input type="checkbox" name="confirmo" value="sim" required className="size-5" />
        Confirmo que a minuta foi copiada e revisada. Depois de concluído, o processo fica só para leitura e os dados são apagados em 30 dias.
      </label>
      <Mensagem resultado={resultado} />
      <div>
        <Botao>Marcar como concluído</Botao>
      </div>
    </form>
  );
}
