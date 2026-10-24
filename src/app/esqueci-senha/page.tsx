import Link from "next/link";

/** Sem redefinição por e-mail (decisão 0012): a TI define uma senha provisória. */
export default function EsqueciSenha() {
  return (
    <main className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center gap-4 p-6">
      <h1 className="text-2xl font-semibold">Esqueci minha senha</h1>
      <p>
        Procure o responsável pela TI da OM. Ele define uma senha provisória para você, que vale só para o próximo
        acesso: ao entrar, o sistema pede que você crie a sua senha.
      </p>
      <Link href="/login" className="flex min-h-11 items-center text-blue-800 underline">
        Voltar ao login
      </Link>
    </main>
  );
}
