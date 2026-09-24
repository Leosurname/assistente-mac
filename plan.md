# Plano do Projeto — Assistente Mac

## O que é

O Assistente Mac é um assistente de voz que organiza a tela do Mac. Ele fica
parado em segundo plano até ser chamado por um atalho, escuta um pedido em
linguagem natural e executa aquilo nas janelas e nos aplicativos da máquina.

O pedido típico é sobre arranjo de espaço de trabalho:

> "Quero terminal e Safari, e já deixa o Claude Code aberto."

O assistente abre o que falta, não encosta no que não foi pedido, posiciona
as janelas na tela e responde "concluído".

## O fluxo, do começo ao fim

1. **Atalho.** O usuário aperta `Option + 9` em qualquer lugar do sistema. O
   atalho é global: funciona mesmo com outro aplicativo em foco.
2. **Escuta.** O assistente começa a ouvir o microfone imediatamente.
3. **Sobreposição.** Uma caixa de texto aparece sobre tudo o que está na tela,
   sem roubar o foco do aplicativo que o usuário estava usando. Ela mostra a
   transcrição do que está sendo falado, em tempo real, conforme as palavras
   são reconhecidas.
4. **Interpretação.** Quando o usuário para de falar, a transcrição vai para a
   Layla junto com o estado atual da tela (quais aplicativos estão abertos,
   onde estão as janelas, qual o tamanho do monitor). A Layla devolve uma lista
   de ações concretas.
5. **Execução.** O assistente executa as ações: abre aplicativos, move e
   redimensiona janelas, traz para frente o que precisa estar visível.
6. **Confirmação.** A caixa mostra e fala "concluído".
7. **Desaparecimento.** A caixa some sozinha. Ela some quando qualquer uma
   destas coisas acontece primeiro:
   - passam **5 segundos** sem um novo pedido;
   - o usuário **começa a digitar** (sinal claro de que voltou ao trabalho);
   - o usuário aperta `Esc`.

O ponto central do produto é o passo 7. O assistente precisa sumir sem que
ninguém peça. Se ele exigir que o usuário o dispense, ele vira mais uma janela
para gerenciar — exatamente o problema que veio resolver.

## Exemplo completo

| Momento | O que acontece |
|---|---|
| `Option + 9` | Caixa aparece, microfone liga |
| Usuário fala | "quero terminal e safari, e já deixa o claude code aberto" |
| Transcrição | Aparece na caixa enquanto ele fala |
| Silêncio | A transcrição é enviada para a Layla |
| Layla responde | `abrir Terminal`, `abrir Safari`, `abrir Claude Code`, `dividir tela: Terminal à esquerda, Safari à direita` |
| Execução | As janelas se movem |
| Caixa | "Concluído" |
| 5 s depois | A caixa some |

## Arquitetura em uma frase

Um aplicativo nativo de macOS cuida do atalho, do microfone, da caixa e do
controle das janelas; um backend em Python cuida da conversa com a Layla e
traduz o pedido em uma lista de ações. Os dois conversam por WebSocket no
`localhost`. O detalhamento está em [ARCHITECTURE.md](ARCHITECTURE.md).

## Decisões já tomadas

- **Backend em Python.** É onde mora a integração com a Layla, o histórico de
  conversa e a tradução de pedido em ações.
- **Tudo local.** O backend roda na própria máquina. Nada de servidor remoto
  para uma ferramenta que mexe nas janelas do usuário.
- **A sobreposição não rouba foco.** O usuário continua podendo digitar no
  aplicativo que estava usando — e é justamente isso que faz a caixa sumir.
- **A Layla não executa nada.** Ela devolve ações; quem executa é o aplicativo
  nativo, que valida cada uma antes de rodar. Modelo de linguagem não recebe
  acesso direto ao sistema.
- **Aplicativo não pedido fica em paz.** O assistente só mexe no que foi
  citado no pedido. Nada de minimizar, fechar ou mandar para outra área de
  trabalho por conta própria. Quem pede "terminal e Safari" está dizendo o que
  quer ver, não o que quer sumir — e um assistente que rearranja o que ninguém
  mandou custa mais confiança do que economiza tempo.

## Decisões em aberto

Estas ficam registradas aqui até serem resolvidas, e viram issues próprias:

1. **Camada nativa: Swift ou Python com PyObjC?** Swift dá acesso mais direto
   ao reconhecimento de fala e à API de acessibilidade; PyObjC mantém o projeto
   em uma linguagem só. A recomendação é Swift para a camada nativa.
2. **A Layla roda local ou remota?** Muda a latência aceitável no passo 4 e a
   forma de autenticação.
3. **Reconhecimento de fala: `SFSpeechRecognizer` do macOS ou Whisper local?**
   O primeiro é imediato e já vem no sistema; o segundo transcreve melhor
   português misturado com nomes técnicos ("Claude Code", "Safari").

## Etapas de entrega

**Etapa 1 — Esqueleto.** Atalho global, caixa aparecendo e sumindo pelas três
regras (5 segundos, digitação, `Esc`). Sem voz e sem Layla: o texto é digitado.
Serve para validar a sensação de uso, que é o risco maior do projeto.

**Etapa 2 — Voz.** Microfone e transcrição ao vivo na caixa.

**Etapa 3 — Layla.** Backend em Python, conversa com a Layla, pedido virando
lista de ações.

**Etapa 4 — Janelas.** Abertura de aplicativos e posicionamento via API de
acessibilidade. É aqui que o exemplo do terminal com o Safari passa a funcionar
de ponta a ponta.

**Etapa 5 — Acabamento.** Confirmação falada, tratamento de erro ("não achei o
Claude Code"), preferências do usuário.

## Como saber se deu certo

- Do atalho até as janelas no lugar: menos de 3 segundos para um pedido comum.
- A caixa nunca fica na tela sem ter sido chamada.
- Um pedido malfeito nunca quebra o arranjo de janelas que já estava lá.
