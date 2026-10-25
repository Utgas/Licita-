"use client";
/**
 * Aviso de cookies (decisão 0017). O sistema só usa o cookie de sessão, que é necessário e não depende de
 * consentimento; o aviso informa e some depois de "Entendi". A marca de "já visto" fica no armazenamento local do
 * navegador, não em cookie. Sem armazenamento (janela anônima, bloqueio), o aviso volta a cada página, sem quebrar.
 */
import Link from "next/link";
import { useEffect, useState } from "react";
import { classesDoBotao } from "./ui.tsx";

const CHAVE = "licita-aviso-cookies";

export function AvisoDeCookies() {
  const [visivel, setVisivel] = useState(false);
  useEffect(() => {
    let visto = false;
    try {
      visto = window.localStorage.getItem(CHAVE) === "1";
    } catch {
      // armazenamento bloqueado: mostra o aviso
    }
    // Lê o navegador depois de montar, para o servidor e o navegador desenharem a mesma página.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (!visto) setVisivel(true);
  }, []);
  if (!visivel) return null;
  const fechar = () => {
    try {
      window.localStorage.setItem(CHAVE, "1");
    } catch {
      // sem armazenamento, o aviso só some nesta página
    }
    setVisivel(false);
  };
  return (
    // sticky, e não fixed: no fim da página o aviso volta ao seu lugar, depois do rodapé, e não cobre nenhum link.
    <section aria-label="Aviso de cookies" className="sticky bottom-0 z-40 border-t border-linha-forte bg-folha">
      <div className="mx-auto flex w-full max-w-[1400px] flex-wrap items-center justify-between gap-3 px-4 py-3 md:px-6">
        <p className="max-w-3xl text-sm">
          O Licita+ usa só o cookie necessário para manter o seu login. Não há cookie de publicidade, estatística ou de
          terceiros.{" "}
          <Link href="/privacidade#cookies" className="underline">
            Saiba mais
          </Link>
          .
        </p>
        <button type="button" onClick={fechar} className={classesDoBotao("principal")}>
          Entendi
        </button>
      </div>
    </section>
  );
}
