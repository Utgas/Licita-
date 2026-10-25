import type { Metadata } from "next";
import Link from "next/link";
import { Lacuna, PaginaDeDocumento, Secao, Tabela } from "../componentes/documento.tsx";

export const metadata: Metadata = { title: "Política de Privacidade · Licita+" };

/**
 * Política de privacidade e de cookies (LGPD; decisão 0017). Texto institucional, não regra da minuta: descreve o
 * que o sistema faz hoje. Precisa da revisão do encarregado de dados e da assessoria jurídica da OM antes do piloto;
 * o que só a OM sabe aparece como lacuna marcada.
 */
export default function Privacidade() {
  return (
    <PaginaDeDocumento titulo="Política de Privacidade" versao="Versão 1, de 25/10/2026. Minuta para revisão do encarregado de dados da OM.">
      <p>
        Esta política explica quais dados pessoais o Licita+ usa, para quê, por quanto tempo e como você exerce os seus
        direitos, conforme a Lei Geral de Proteção de Dados Pessoais (LGPD, Lei nº 13.709/2018).
      </p>

      <Secao id="controlador" titulo="1. Quem é responsável pelos dados">
        <p>
          O controlador é a Organização Militar que usa o Licita+ para elaborar Estudos Técnicos Preliminares (ETP) e
          Termos de Referência (TR): <Lacuna>nome da OM, UASG e endereço</Lacuna>.
        </p>
        <p>
          Encarregado pelo tratamento de dados pessoais (LGPD, art. 41): <Lacuna>nome ou função do encarregado e canal de contato</Lacuna>.
        </p>
      </Secao>

      <Secao id="dados" titulo="2. Quais dados usamos e para quê">
        <p>O sistema coleta só o necessário para funcionar. Não há anúncio, rastreamento, estatística de navegação nem venda de dados.</p>
        <Tabela
          titulo="Dados pessoais tratados pelo Licita+"
          colunas={["Dado", "Para quê", "Por quanto tempo"]}
          linhas={[
            ["Nome, e-mail institucional, perfil e OM do usuário", "Dar acesso, separar os processos por OM e identificar quem fez cada ação", <>Enquanto o acesso existir; depois, <Lacuna>prazo após a desativação</Lacuna></>],
            ["Senha", "Entrar no sistema. Guardamos só o resumo cifrado (hash bcrypt), que ninguém consegue reverter, nem a TI", "Até a troca da senha"],
            ["Cookie de sessão", "Manter você conectado entre uma tela e outra (veja a seção 7)", "Até sair ou a sessão expirar"],
            ["Registro de auditoria: data, hora, ação, usuário, processo e resumos (hashes) de arquivos", "Provar quem fez o quê, como exige o controle da administração pública", <><Lacuna>prazo da tabela de temporalidade da OM</Lacuna>; o registro não pode ser alterado nem apagado</>],
            ["Tentativas de login sem sucesso: só um marcador cifrado do e-mail e do endereço IP, nunca os valores", "Bloquear quem tenta adivinhar senhas", "24 horas"],
            ["Dados do processo: número, objeto, respostas do checklist e do wizard, itens", "Montar as minutas de ETP e TR", "Apagados 30 dias depois de o processo ser concluído"],
            ["Dados do responsável técnico que vêm no checklist: nome, posto ou graduação, telefone e e-mail", "Identificar quem prestou as informações técnicas; nome e posto entram na minuta", "Os mesmos 30 dias do processo"],
            ["Pedidos sobre dados pessoais e as respostas", "Atender os seus direitos (seção 6)", <><Lacuna>prazo de guarda dos pedidos</Lacuna></>],
          ]}
        />
        <p>
          Não guardamos o arquivo Word do checklist nem os PDFs gerados: eles são lidos ou montados na hora e descartados;
          fica só o resumo (hash) na auditoria. Não envie ao sistema documento com informação classificada nem dado pessoal
          que a minuta não precise, como CPF ou telefone particular.
        </p>
      </Secao>

      <Secao id="base-legal" titulo="3. Por que podemos usar esses dados">
        <p>
          O tratamento é feito pela administração pública para cumprir as suas competências legais (LGPD, art. 7º, incisos
          II e III, e art. 23): a fase preparatória das contratações, com ETP e TR, é exigida pela Lei nº 14.133/2021 (art.
          18). Por isso o uso dos dados não depende de consentimento.
        </p>
      </Secao>

      <Secao id="compartilhamento" titulo="4. Com quem os dados são compartilhados">
        <p>Os dados não são vendidos nem cedidos. Duas empresas prestam serviço técnico ao sistema, como operadoras (LGPD, art. 39):</p>
        <ul className="list-disc pl-6">
          <li>Vercel: hospeda as telas e o servidor, na região de São Paulo;</li>
          <li>Supabase: guarda o banco de dados e cuida do login, na região de São Paulo.</li>
        </ul>
        <p>
          Os dados ficam armazenados no Brasil, mas as duas empresas têm sede no exterior. <Lacuna>instrumento que autoriza o uso desses serviços e as garantias de transferência internacional (LGPD, art. 33)</Lacuna>.
        </p>
        <p>O sistema não usa inteligência artificial nem envia dado a nenhum outro serviço. Órgãos de controle podem receber dados quando a lei exigir.</p>
      </Secao>

      <Secao id="seguranca" titulo="5. Como protegemos os dados">
        <ul className="list-disc pl-6">
          <li>Conexões sempre cifradas (HTTPS e TLS até o banco) e banco cifrado em repouso;</li>
          <li>Senhas guardadas só como hash; senha provisória da TI vale para um único acesso;</li>
          <li>Bloqueio depois de 5 tentativas de login erradas em 15 minutos;</li>
          <li>Cada usuário vê só os processos da própria OM, regra conferida no próprio banco;</li>
          <li>A TI administra os acessos, mas não abre os processos;</li>
          <li>Toda ação fica registrada numa auditoria que ninguém altera nem apaga;</li>
          <li>Registros técnicos sem o conteúdo dos processos.</li>
        </ul>
        <p>Em caso de incidente de segurança que possa causar risco ou dano relevante, a OM comunica a ANPD e os titulares (LGPD, art. 48).</p>
      </Secao>

      <Secao id="direitos" titulo="6. Seus direitos e como exercê-los">
        <p>Você pode pedir (LGPD, art. 18):</p>
        <ul className="list-disc pl-6">
          <li>confirmação de que tratamos seus dados e acesso a eles;</li>
          <li>correção de dado incompleto, errado ou desatualizado;</li>
          <li>anonimização, bloqueio ou eliminação de dado desnecessário, excessivo ou tratado em desacordo com a lei;</li>
          <li>cópia dos seus dados em formato aberto;</li>
          <li>informação sobre com quem os dados são compartilhados.</li>
        </ul>
        <p>
          <strong>Usuário do sistema:</strong> entre e abra <Link href="/meus-dados" className="underline">Meus dados</Link>. Lá você vê o que está guardado, baixa uma
          cópia e faz o pedido; a TI responde na mesma tela.
        </p>
        <p>
          <strong>Outra pessoa</strong> (por exemplo, o responsável técnico citado num checklist): fale com o encarregado de dados da OM (seção 1).
        </p>
        <p>
          Alguns dados não podem ser apagados enquanto a lei exigir a guarda, como a auditoria (LGPD, art. 16). Se não
          ficar satisfeito com a resposta, você pode reclamar à Autoridade Nacional de Proteção de Dados (ANPD).
        </p>
      </Secao>

      <Secao id="cookies" titulo="7. Cookies">
        <p>
          O Licita+ usa só os cookies estritamente necessários para o login. Não há cookie de publicidade, de estatística
          nem de terceiros. Como esses cookies são indispensáveis ao serviço, eles não dependem de consentimento; você pode
          bloqueá-los no navegador, mas aí não consegue entrar no sistema.
        </p>
        <Tabela
          titulo="Cookies e armazenamento usados pelo Licita+"
          colunas={["Nome", "Para quê", "Duração", "Tipo"]}
          linhas={[
            ["sb-…-auth-token (pode vir dividido em .0, .1…)", "Guarda a sessão de login. Só o servidor lê (httpOnly); só trafega por HTTPS (Secure); não vai para outros sites (SameSite=Lax)", "Até sair ou a sessão expirar", "Necessário, do próprio sistema"],
            ["licita-aviso-cookies (armazenamento local do navegador, não é cookie)", "Lembra que você já viu o aviso de cookies, para não mostrá-lo de novo", "Até você limpar os dados do navegador", "Necessário, do próprio sistema"],
          ]}
        />
      </Secao>

      <Secao id="alteracoes" titulo="8. Alterações desta política">
        <p>Quando a política mudar, a versão e a data no topo desta página mudam também. A OM avisa os usuários quando houver mudança relevante.</p>
        <p>
          Veja também os <Link href="/termos" className="underline">Termos de Uso</Link>.
        </p>
      </Secao>
    </PaginaDeDocumento>
  );
}
