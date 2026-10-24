"use client";
/** Botão "Copiar" de cada seção e confirmação de conclusão (passo 11). */
import { Selo, classesDoBotao } from "../../../componentes/ui.tsx";
import { Icone } from "../../../componentes/icones.tsx";
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
    <div className="flex flex-wrap items-center justify-end gap-2">
      <button type="button" onClick={copiar} disabled={pendente} className={classesDoBotao("secundario")}>
        <Icone nome="copiar" tamanho={16} />
        {pendente ? "Copiando…" : "Copiar"}
      </button>
      {estado === "copiado" ? <Selo tipo="ok">Copiado</Selo> : estado === "" ? <Selo tipo="vazio">Não copiado</Selo> : null}
      {estado === "erro" && <Selo tipo="trava">Erro: {mensagem}</Selo>}
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
