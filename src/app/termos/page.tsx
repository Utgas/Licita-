import type { Metadata } from "next";
import Link from "next/link";
import { Lacuna, PaginaDeDocumento, Secao } from "../componentes/documento.tsx";

export const metadata: Metadata = { title: "Termos de Uso · Licita+" };

/**
 * Termos de uso (decisão 0017). Texto institucional, não regra da minuta. Precisa da revisão da assessoria jurídica
 * da OM antes do piloto; o que só a OM sabe aparece como lacuna marcada.
 */
export default function Termos() {
  return (
    <PaginaDeDocumento titulo="Termos de Uso" versao="Versão 1, de 25/10/2026. Minuta para revisão da assessoria jurídica da OM.">
      <p>Ao entrar no Licita+, você concorda com estas regras de uso.</p>

      <Secao id="objeto" titulo="1. O que é o Licita+">
        <p>
          Ferramenta interna de apoio que monta minutas de Estudo Técnico Preliminar (ETP) e de Termo de Referência (TR) no
          modelo da Advocacia-Geral da União, a partir do checklist técnico da área requisitante e das decisões da equipe
          de licitação. É mantido por <Lacuna>OM ou setor responsável pelo sistema</Lacuna>.
        </p>
      </Secao>

      <Secao id="acesso" titulo="2. Quem pode usar">
        <ul className="list-disc pl-6">
          <li>Só agentes públicos da OM cadastrados pela TI, para atividade funcional.</li>
          <li>O acesso é pessoal e intransferível. Não empreste a senha nem use a de outra pessoa.</li>
          <li>A TI pode desativar o acesso de quem deixar a função ou usar o sistema de forma indevida.</li>
        </ul>
      </Secao>

      <Secao id="responsabilidades" titulo="3. Responsabilidades de quem usa">
        <ul className="list-disc pl-6">
          <li>Guardar a senha em sigilo e trocá-la se suspeitar que outra pessoa a conhece; avisar a TI de qualquer acesso estranho.</li>
          <li>Sair do sistema ao terminar, principalmente em computador compartilhado.</li>
          <li>Não enviar documento com informação classificada (Lei nº 12.527/2011) nem dado pessoal que a minuta não precise.</li>
          <li>Usar dados fictícios em qualquer teste ou treinamento.</li>
        </ul>
      </Secao>

      <Secao id="minuta" titulo="4. A minuta é um rascunho">
        <p>
          O texto gerado é uma minuta para revisão. Ele não substitui a análise da equipe, a decisão da autoridade
          competente nem o parecer da assessoria jurídica (Lei nº 14.133/2021, art. 53). Quem elabora, revisa e assina o
          documento responde pelo seu conteúdo. Toda lacuna marcada precisa ser preenchida por uma pessoa: o sistema nunca
          inventa valor, quantidade, prazo ou percentual.
        </p>
      </Secao>

      <Secao id="sigilo" titulo="5. Sigilo e registro das ações">
        <p>
          ETP e TR em elaboração são documentos preparatórios, de acesso restrito à equipe até a publicação (Lei nº
          12.527/2011, art. 7º, § 3º). Cada usuário vê só os processos da própria OM. Toda ação no sistema fica registrada
          na auditoria, que pode ser usada em apuração de uso indevido.
        </p>
      </Secao>

      <Secao id="disponibilidade" titulo="6. Disponibilidade e guarda">
        <p>
          O sistema pode ficar fora do ar para manutenção ou por falha dos serviços de hospedagem. O conteúdo de um processo
          é apagado 30 dias depois de ele ser concluído; guarde o PDF e o texto finais no processo administrativo oficial.
        </p>
      </Secao>

      <Secao id="dados-pessoais" titulo="7. Dados pessoais">
        <p>
          O uso dos seus dados está descrito na <Link href="/privacidade" className="underline">Política de Privacidade</Link>, que inclui os cookies usados e como
          exercer os seus direitos.
        </p>
      </Secao>

      <Secao id="alteracoes" titulo="8. Alterações e contato">
        <p>
          Estes termos podem mudar; a versão e a data ficam no topo da página. Dúvidas: <Lacuna>canal de contato da TI ou do setor responsável</Lacuna>.
        </p>
      </Secao>
    </PaginaDeDocumento>
  );
}
