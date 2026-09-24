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
- **A Layla roda local.** Nada de chamada de rede para interpretar o pedido.
  A Layla são os pesos publicados em
  [huggingface.co/l3utterfly](https://huggingface.co/l3utterfly), em formato
  GGUF, servidos na própria máquina pelo `llama-server` do llama.cpp — que
  expõe uma API compatível com OpenAI. Rodar local tira a chave de API da
  configuração, mantém as transcrições de voz dentro do Mac e deixa a latência
  sob controle: o plano tem meta de menos de 3 segundos do fim da fala até as
  janelas no lugar, e uma ida à internet gasta boa parte desse orçamento.
- **A resposta da Layla é restringida por gramática.** Os fine-tunes da Layla
  são feitos para conversa, não para saída estruturada. Pedir JSON no prompt e
  torcer não serve para um backend que depende de uma lista de ações bem
  formada, então a saída é forçada por `json_schema`/GBNF no `llama-server`.
  A validação do backend continua existindo: gramática garante formato, não
  garante sentido.
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
2. **Reconhecimento de fala: `SFSpeechRecognizer` do macOS ou Whisper local?**
   O primeiro é imediato e já vem no sistema; o segundo transcreve melhor
   português misturado com nomes técnicos ("Claude Code", "Safari").
   Só precisa ser resolvida na fase de voz, depois da beta.
3. **Por onde o texto entra na beta?** Pelo terminal (`scripts/pedido.py`) ou
   por um campo de texto na sobreposição. O campo exige rever a regra de que
   digitar faz a caixa sumir.

## Etapas de entrega

**A beta é só texto.** O pedido chega digitado; voz entra numa fase seguinte,
depois da beta.

**Etapa 1 — Esqueleto.** Atalho global, caixa aparecendo e sumindo pelas três
regras (5 segundos, digitação, `Esc`). Serve para validar a sensação de uso,
que é o risco maior do projeto.

**Etapa 2 — Layla.** Backend em Python, conversa com a Layla, pedido virando
lista de ações.

**Etapa 3 — Janelas.** Abertura de aplicativos e posicionamento via API de
acessibilidade. É aqui que o exemplo do terminal com o Safari passa a funcionar
de ponta a ponta, por texto.

**Etapa 4 — Acabamento.** Tratamento de erro ("não achei o Claude Code"),
preferências do usuário. Fecha a beta.

**Depois da beta — Voz.** Microfone, transcrição ao vivo na caixa e
confirmação falada.

## Como saber se deu certo

- Do atalho até as janelas no lugar: menos de 3 segundos para um pedido comum.
- A caixa nunca fica na tela sem ter sido chamada.
- Um pedido malfeito nunca quebra o arranjo de janelas que já estava lá.
