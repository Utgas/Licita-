import Link from "next/link";
import { PaginaDeAcesso } from "../componentes/acesso.tsx";
import { Icone } from "../componentes/icones.tsx";

/** Sem redefinição por e-mail (decisão 0012): a TI define uma senha provisória. */
export default function EsqueciSenha() {
  return (
    <PaginaDeAcesso titulo="Esqueci minha senha">
      <p className="leading-relaxed">
        Procure o responsável pela TI da OM. Ele define uma senha provisória para você, que vale só para o próximo
        acesso: ao entrar, o sistema pede que você crie a sua senha.
      </p>
      <Link href="/login" className="flex min-h-11 w-fit items-center gap-2 underline">
        <Icone nome="voltar" tamanho={16} />
        Voltar ao login
      </Link>
    </PaginaDeAcesso>
  );
}
